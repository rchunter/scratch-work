"""File-only CLI: YAML documents on stdout, structured diagnostics on stderr."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import yaml

from . import convert_rule
from .models import Diagnostic


def _error(code: str, message: str) -> int:
    diagnostic = Diagnostic('error', code, '$', message)
    sys.stderr.write(json.dumps(asdict(diagnostic)) + '\n')
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Convert an Elastic JSON/YAML rule to Sigma with best-effort diagnostics.')
    parser.add_argument('input', type=Path, help='One .json, .yaml, or .yml Elastic rule file')
    args = parser.parse_args()
    suffix = args.input.suffix.lower()
    if suffix not in ('.json', '.yaml', '.yml'):
        return _error('input_error', 'Expected a .json, .yaml, or .yml input file.')
    try:
        text = args.input.read_text(encoding='utf-8')
    except OSError as error:
        return _error('input_error', f'Cannot read input file: {error.strerror}.')
    except UnicodeError:
        return _error('input_error', 'Input must be UTF-8 text.')
    try:
        source = json.loads(text) if suffix == '.json' else yaml.safe_load(text)
    except json.JSONDecodeError as error:
        return _error('input_error', f'Invalid JSON at line {error.lineno}, column {error.colno}.')
    except yaml.YAMLError as error:
        mark = getattr(error, 'problem_mark', None)
        location = f' at line {mark.line + 1}, column {mark.column + 1}' if mark else ''
        return _error('input_error', f'Invalid or unsupported YAML{location}.')
    if not isinstance(source, dict):
        return _error('input_error', 'Input must contain one rule object.')

    result = convert_rule(source)
    try:
        # Serialize both channels first so a serialization failure cannot emit partial YAML.
        document = yaml.safe_dump(result.document, sort_keys=False, allow_unicode=True, indent=4)
        diagnostics = ''.join(json.dumps(asdict(item)) + '\n' for item in result.diagnostics)
    except (yaml.YAMLError, TypeError, ValueError):
        return _error('output_error', 'Could not serialize the conversion result.')
    sys.stdout.write(document)
    sys.stderr.write(diagnostics)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
