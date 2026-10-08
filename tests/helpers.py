"""Test-owned fixtures and a restricted condition interpreter, never production code."""
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def source_rule(query='process.name: "cmd.exe"', **changes):
    rule = {'name': 'Example detection', 'type': 'query', 'language': 'kuery', 'query': query}
    rule.update(changes)
    return rule


def condition_value(condition, values):
    """Evaluate only selection names and Boolean syntax; never eval arbitrary text."""
    tokens = re.findall(r'selection(?:_\d+)?|and|or|not|[()]', condition)
    if ''.join(tokens) != re.sub(r'\s+', '', condition):
        raise AssertionError(f'Unexpected condition syntax: {condition!r}')
    position = 0

    def atom():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == 'not':
            return not atom()
        if token == '(':
            result = expression()
            if tokens[position] != ')':
                raise AssertionError('Unbalanced condition')
            position += 1
            return result
        return values[token]

    def conjunction():
        nonlocal position
        result = atom()
        while position < len(tokens) and tokens[position] == 'and':
            position += 1
            other = atom()
            result = result and other
        return result

    def expression():
        nonlocal position
        result = conjunction()
        while position < len(tokens) and tokens[position] == 'or':
            position += 1
            other = conjunction()
            result = result or other
        return result

    result = expression()
    if position != len(tokens):
        raise AssertionError('Condition has unconsumed tokens')
    return result
