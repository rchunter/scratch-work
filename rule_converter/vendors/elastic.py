"""Best-effort Elastic interpretation, independent of file IO and Sigma rendering."""
from uuid import UUID

from ..diagnostics import Diagnostics
from ..models import Translation
from .kql import QueryError, parse_query


class ElasticAdapter:
    def translate(self, source: dict) -> Translation:
        if not isinstance(source, dict):
            raise TypeError('An Elastic rule must be an object')
        diagnostics = Diagnostics()
        metadata = self._metadata(source, diagnostics)
        detection = self._detection(source, diagnostics)
        metadata['logsource'] = {'definition': 'Elastic rule using ECS fields.'}
        diagnostics.unhandled(source, {'name', 'description', 'rule_id', 'severity', 'references',
                                       'type', 'language', 'query', 'filters', 'exceptions_list', 'alert_suppression'})
        return Translation(metadata, detection, detection is not None, diagnostics.as_list())

    @staticmethod
    def _metadata(source: dict, diagnostics: Diagnostics) -> dict:
        name = source.get('name')
        if not isinstance(name, str) or not name.strip():
            code = 'missing_required' if 'name' not in source else 'invalid_value'
            diagnostics.add(code, 'name', 'Missing or invalid title; using Untitled converted rule.')
            name = 'Untitled converted rule'
        elif len(name) > 256:
            diagnostics.invalid('name', 'Title exceeds 256 characters; truncated.')
            name = name[:256]
        result = {'title': name}
        if 'description' in source:
            description = source['description']
            if isinstance(description, str) and description.strip():
                result['description'] = description
            else:
                diagnostics.invalid('description')
        if 'rule_id' in source:
            value = source['rule_id']
            try:
                valid = isinstance(value, str) and str(UUID(value)) == value
            except ValueError:
                valid = False
            if valid:
                result['id'] = value
            else:
                diagnostics.invalid('rule_id', 'Expected a canonical UUID; id omitted.')
        if 'severity' in source:
            value = source['severity']
            if isinstance(value, str) and value in ('low', 'medium', 'high', 'critical'):
                result['level'] = value
            else:
                diagnostics.invalid('severity', 'Unsupported level; field omitted.')
        if 'references' in source:
            references = source['references']
            if not isinstance(references, list):
                diagnostics.invalid('references')
            else:
                valid = []
                for index, value in enumerate(references):
                    if isinstance(value, str) and value.strip():
                        valid.append(value)
                    else:
                        diagnostics.invalid(f'references[{index}]')
                if valid:
                    result['references'] = valid
        return result

    @staticmethod
    def _detection(source: dict, diagnostics: Diagnostics):
        supported = True
        for key, expected in (('type', 'query'), ('language', 'kuery')):
            if key not in source:
                diagnostics.assume(key, f'Missing field; assuming {expected} for the supported subset.')
            elif source[key] != expected:
                diagnostics.add('unsupported_semantics', key, 'Unsupported detection method; detection omitted.')
                supported = False
        for key in ('filters', 'exceptions_list'):
            if key in source and source[key] != []:
                diagnostics.add('unsupported_semantics', key, 'Additional detection constraints cannot be translated.')
                supported = False
        if source.get('alert_suppression') is not None:
            diagnostics.add('unsupported_semantics', 'alert_suppression', 'Alert suppression cannot be translated.')
            supported = False
        query = source.get('query')
        expression = None
        if not isinstance(query, str) or not query.strip():
            code = 'missing_required' if 'query' not in source else 'invalid_value'
            diagnostics.add(code, 'query', 'A nonempty query string is required for detection.')
        elif supported:
            try:
                expression = parse_query(query)
            except QueryError as error:
                diagnostics.add('unsupported_query', 'query', str(error))
        if expression is None:
            diagnostics.add('incomplete_detection', 'query', 'Detection could not be fully translated; output is a metadata draft.')
        return expression
