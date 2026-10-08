"""Public renderer stub for vendor-neutral acceptance tests."""
from .models import Translation


def render_sigma(translation: Translation) -> dict:
    raise NotImplementedError('Sigma rendering has not been implemented')
