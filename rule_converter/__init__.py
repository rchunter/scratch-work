"""Public contract stub; conversion deliberately unimplemented for red TDD."""
from .models import ConversionResult


def convert_rule(rule: dict) -> ConversionResult:
    raise NotImplementedError('Elastic conversion has not been implemented')
