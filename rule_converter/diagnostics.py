"""Per-conversion diagnostics, returned to callers instead of emitted from the library."""
from .models import Diagnostic


class Diagnostics:
    def __init__(self):
        self._issues: dict[tuple[str, str], Diagnostic] = {}

    def add(self, code: str, path: str, message: str, severity: str = 'warning') -> None:
        self._issues.setdefault((path, code), Diagnostic(severity, code, path, message))

    def invalid(self, path: str, message: str = 'Invalid value; field omitted.') -> None:
        self.add('invalid_value', path, message)

    def unmapped(self, path: str) -> None:
        self.add('unmapped_field', path, 'No Sigma mapping; field omitted.')

    def assume(self, path: str, message: str) -> None:
        self.add('assumed_value', path, message, severity='info')

    def unhandled(self, source: dict, handled: set[str], prefix: str = '') -> None:
        for key in source:
            if key not in handled:
                self.unmapped(f'{prefix}.{key}' if prefix else str(key))

    def as_list(self) -> list[Diagnostic]:
        return [self._issues[key] for key in sorted(self._issues)]
