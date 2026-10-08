"""Elastic log-source hints and ATT&CK metadata; no query parsing or IO."""
import re

from ..diagnostics import Diagnostics
from ..models import And, Expression, Match, Not, Or

OS_TAGS = {'OS: Windows': 'windows', 'OS: Linux': 'linux', 'OS: macOS': 'macos'}
TACTICS = frozenset({
    'reconnaissance', 'resource development', 'initial access', 'execution',
    'persistence', 'privilege escalation', 'defense evasion', 'credential access',
    'discovery', 'lateral movement', 'collection', 'command and control',
    'exfiltration', 'impact',
})
TECHNIQUE = re.compile(r'T\d{4}(?:\.\d{3})?')
SUBTECHNIQUE = re.compile(r'T\d{4}\.\d{3}')


def string_items(source: dict, field: str, diagnostics: Diagnostics) -> list[tuple[str, str]]:
    """Keep original array positions when invalid siblings are omitted."""
    if field not in source:
        return []
    values = source[field]
    if not isinstance(values, list):
        diagnostics.invalid(field, 'Expected a list of strings; field omitted.')
        return []
    result = []
    for index, value in enumerate(values):
        path = f'{field}[{index}]'
        if isinstance(value, str) and value.strip():
            result.append((path, value))
        else:
            diagnostics.invalid(path)
    return result


def _fields(expression: Expression | None) -> set[str]:
    if isinstance(expression, Match):
        return {expression.field}
    if isinstance(expression, (And, Or)):
        return _fields(expression.left) | _fields(expression.right)
    if isinstance(expression, Not):
        return _fields(expression.operand)
    return set()


def logsource(source: dict, tags: list[tuple[str, str]], expression: Expression | None,
              diagnostics: Diagnostics) -> dict:
    indexes = string_items(source, 'index', diagnostics)
    source_os_tags = [(path, tag) for path, tag in tags if tag.startswith('OS: ')]
    result = {}
    if source_os_tags:
        products = set()
        unknown = False
        for path, tag in source_os_tags:
            if tag in OS_TAGS:
                products.add(OS_TAGS[tag])
            else:
                diagnostics.invalid(path, 'Unknown OS tag; log-source product not inferred.')
                unknown = True
        if not unknown and len(products) == 1:
            result['product'] = next(iter(products))
            diagnostics.assume('tags', 'Log-source product inferred from OS tags.')
        elif len(products) > 1:
            diagnostics.invalid('tags', 'Conflicting OS tags; log-source product not inferred.')
    elif any(pattern.startswith('winlogbeat-') for _, pattern in indexes):
        result['product'] = 'windows'
        diagnostics.assume('index', 'Windows telemetry inferred from a winlogbeat index pattern.')

    fields = _fields(expression)
    if 'CommandLine' in fields and all(field == 'CommandLine' or field.startswith('process.') for field in fields):
        result['category'] = 'process_creation'
        diagnostics.assume('query', 'Process-creation telemetry assumed from process command-line fields.')
    if not result:
        definition = 'Elastic rule using ECS fields.'
        if indexes:
            definition += ' Source index patterns: ' + ', '.join(pattern for _, pattern in indexes)
        result['definition'] = definition
    if indexes:
        diagnostics.add('unmapped_field', 'index', 'Source index routing is not enforced by the translated logsource.')
    return result


def _tactic_tag(value: object) -> str | None:
    if isinstance(value, str) and value.lower() in TACTICS:
        return 'attack.' + value.lower().replace(' ', '_')
    return None


def _technique_tag(value: object, *, subtechnique: bool = False) -> str | None:
    pattern = SUBTECHNIQUE if subtechnique else TECHNIQUE
    if isinstance(value, str) and pattern.fullmatch(value):
        return 'attack.' + value.lower()
    return None


def _objects(source: dict, key: str, prefix: str, diagnostics: Diagnostics):
    if key not in source:
        return
    path = f'{prefix}.{key}' if prefix else key
    values = source[key]
    if not isinstance(values, list):
        diagnostics.invalid(path, 'Expected a list of objects; field omitted.')
        return
    for index, value in enumerate(values):
        item_path = f'{path}[{index}]'
        if isinstance(value, dict):
            yield item_path, value
        else:
            diagnostics.invalid(item_path, 'Expected an object; item omitted.')


def _technique_tags(technique: dict, path: str, diagnostics: Diagnostics) -> list[str]:
    parent = _technique_tag(technique.get('id'))
    if parent is None:
        code = 'invalid_value' if 'id' in technique else 'missing_required'
        diagnostics.add(code, path + '.id', 'Expected an ATT&CK technique ID; parent tag omitted.')
    children = []
    for child_path, child in _objects(technique, 'subtechnique', path, diagnostics):
        tag = _technique_tag(child.get('id'), subtechnique=True)
        if tag is None:
            code = 'invalid_value' if 'id' in child else 'missing_required'
            diagnostics.add(code, child_path + '.id', 'Expected an ATT&CK subtechnique ID; tag omitted.')
        else:
            children.append(tag)
        diagnostics.unhandled(child, {'id'}, child_path)
    # Preserve more specific tags without adding their parent as another detection claim.
    diagnostics.unhandled(technique, {'id', 'subtechnique'}, path)
    return children or ([parent] if parent else [])


def attack_tags(source: dict, flat_tags: list[tuple[str, str]], diagnostics: Diagnostics) -> list[str]:
    tactics = []
    techniques = []
    structured = False
    for path, entry in _objects(source, 'threat', '', diagnostics):
        if entry.get('framework') != 'MITRE ATT&CK':
            diagnostics.unmapped(path)
            continue
        structured = True
        if 'tactic' in entry:
            tactic = entry['tactic']
            if not isinstance(tactic, dict):
                diagnostics.invalid(path + '.tactic', 'Expected a tactic object; field omitted.')
            else:
                tag = _tactic_tag(tactic.get('name'))
                if tag:
                    tactics.append(tag)
                else:
                    diagnostics.invalid(path + '.tactic.name', 'Unknown ATT&CK tactic name; tag omitted.')
                diagnostics.unhandled(tactic, {'name'}, path + '.tactic')
        for technique_path, technique in _objects(entry, 'technique', path, diagnostics):
            techniques.extend(_technique_tags(technique, technique_path, diagnostics))
        diagnostics.unhandled(entry, {'framework', 'tactic', 'technique'}, path)

    mapped = list(dict.fromkeys(tactics + techniques))
    represented = set(mapped)
    fallback_tactics = []
    fallback_techniques = []
    for path, value in flat_tags:
        if value.startswith('OS: '):
            continue  # Consumed (or diagnosed) by log-source mapping.
        tactic = _tactic_tag(value)
        technique = _technique_tag(value)
        tag = tactic or technique
        if structured:
            if tag not in represented:
                diagnostics.unmapped(path)
        elif tactic:
            fallback_tactics.append(tactic)
        elif technique:
            fallback_techniques.append(technique)
        else:
            diagnostics.unmapped(path)
    return mapped if structured else list(dict.fromkeys(fallback_tactics + fallback_techniques))
