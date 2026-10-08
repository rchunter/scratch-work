"""Parse the supported Elastic KQL subset into vendor-neutral expressions.

See README.md and KQL_DESIGN.md alongside this module for grammar, data flow,
error handling, and the implementation reading route.
"""
from dataclasses import dataclass
import re

from ..models import And, Expression, Match, Not, Or

EXACT_FIELDS = frozenset({
    'process.name', 'process.executable', 'process.parent.name',
    'process.parent.executable', 'host.os.type', 'event.category',
})
FIELD = re.compile(r'[A-Za-z_][A-Za-z0-9_.]*')
CONTAINS = re.compile(r"""\*([^\s():"'\\*?]+)\*""")


class QueryError(ValueError):
    """An expected unsupported query, without source values in its message."""

    def __init__(self, reason: str, position: int):
        super().__init__(f'{reason} at character {position}; detection omitted.')


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


def _tokens(query: str) -> list[Token]:
    tokens = []
    position = 0
    while position < len(query):
        char = query[position]
        if char.isspace():
            position += 1
            continue
        start = position
        if char in '():':
            tokens.append(Token(char, char, start))
            position += 1
        elif char == '"':
            position += 1
            value = []
            while position < len(query) and query[position] != '"':
                if query[position] == '\\':
                    position += 1
                    if position == len(query) or query[position] not in ('"', '\\'):
                        raise QueryError('Unsupported string escape', position - 1)
                value.append(query[position])
                position += 1
            if position == len(query):
                raise QueryError('Unterminated string', start)
            tokens.append(Token('STRING', ''.join(value), start))
            position += 1
        else:
            while position < len(query) and not query[position].isspace() and query[position] not in '():"':
                position += 1
            value = query[start:position]
            kind = value.upper() if value.upper() in ('AND', 'OR', 'NOT') else 'WORD'
            tokens.append(Token(kind, value, start))
    tokens.append(Token('END', '', len(query)))
    return tokens


class _Parser:
    def __init__(self, query: str):
        self.tokens = _tokens(query)
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def take(self, kind: str) -> Token:
        token = self.current
        if token.kind != kind:
            raise QueryError(f'Expected {kind.lower()}', token.position)
        self.position += 1
        return token

    def expression(self) -> Expression:
        node = self.conjunction()
        while self.current.kind == 'OR':
            self.take('OR')
            node = Or(node, self.conjunction())
        return node

    def conjunction(self) -> Expression:
        node = self.unary()
        while self.current.kind == 'AND':
            self.take('AND')
            node = And(node, self.unary())
        return node

    def unary(self) -> Expression:
        if self.current.kind == 'NOT':
            self.take('NOT')
            return Not(self.unary())
        if self.current.kind == '(':
            self.take('(')
            node = self.expression()
            self.take(')')
            return node
        return self.comparison()

    def contains(self) -> str:
        token = self.take('WORD')
        matched = CONTAINS.fullmatch(token.value)
        if matched is None:
            raise QueryError('Expected a contains term with only surrounding wildcards', token.position)
        return matched[1]

    def comparison(self) -> Match:
        field = self.take('WORD')
        if not FIELD.fullmatch(field.value):
            raise QueryError('Unsupported field syntax', field.position)
        if field.value not in EXACT_FIELDS and field.value != 'process.command_line':
            raise QueryError('Unsupported field', field.position)
        self.take(':')
        if field.value in EXACT_FIELDS:
            value = self.take('STRING')
            if not value.value or '*' in value.value or '?' in value.value:
                raise QueryError('Expected a nonempty exact string without wildcards', value.position)
            return Match(field.value, 'exact', (value.value,))
        if self.current.kind == '(':
            self.take('(')
            values = [self.contains()]
            # A field group is specifically an AND list of at least two terms.
            self.take('AND')
            values.append(self.contains())
            while self.current.kind == 'AND':
                self.take('AND')
                values.append(self.contains())
            self.take(')')
            return Match('CommandLine', 'contains_all', tuple(values))
        return Match('CommandLine', 'contains', (self.contains(),))


def parse_query(query: str) -> Expression:
    parser = _Parser(query)
    expression = parser.expression()
    parser.take('END')
    return expression
