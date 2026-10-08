"""Render vendor-neutral expressions as Sigma selections and conditions."""
from copy import deepcopy

from .models import And, Expression, Match, Not, Or, Translation


def _selection(match: Match) -> dict:
    if not match.values or any(not isinstance(value, str) or not value for value in match.values):
        raise ValueError('A match requires nonempty string values')
    if match.operator == 'contains_all':
        return {f'{match.field}|contains|all': list(match.values)}
    if match.operator not in ('exact', 'contains') or len(match.values) != 1:
        raise ValueError('Exact and contains matches require one value')
    field = match.field if match.operator == 'exact' else f'{match.field}|contains'
    return {field: match.values[0]}


def _detection(expression: Expression) -> dict:
    if isinstance(expression, Match):
        return {'selection': _selection(expression), 'condition': 'selection'}

    selections = {}

    def emit(node: Expression) -> str:
        if isinstance(node, Match):
            name = f'selection_{len(selections) + 1}'
            selections[name] = _selection(node)
            return name
        if isinstance(node, Not):
            return f'(not {emit(node.operand)})'
        if isinstance(node, (And, Or)):
            operator = 'and' if isinstance(node, And) else 'or'
            return f'({emit(node.left)} {operator} {emit(node.right)})'
        raise TypeError('Unsupported expression node')

    condition = emit(expression)
    return {**selections, 'condition': condition}


def render_sigma(translation: Translation) -> dict:
    """Return an independent document; incomplete translations contain no detection."""
    document = deepcopy(translation.metadata)
    document.pop('detection', None)
    document['status'] = 'test' if translation.detection_complete else 'unsupported'
    if translation.detection_complete:
        if translation.detection is None:
            raise ValueError('A complete translation requires a detection expression')
        document['detection'] = _detection(translation.detection)
    return document
