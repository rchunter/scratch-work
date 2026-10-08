"""File-independent entry point for best-effort Elastic-to-Sigma conversion."""
from .models import ConversionResult
from .sigma import render_sigma
from .vendors.elastic import ElasticAdapter


def convert_rule(rule: dict) -> ConversionResult:
    translation = ElasticAdapter().translate(rule)
    return ConversionResult(render_sigma(translation), translation.diagnostics, translation.detection_complete)
