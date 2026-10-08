"""Public conversion contract: AC-01–AC-08, cases T-01–T-28."""
from copy import deepcopy
from itertools import product
import unittest

from rule_converter import convert_rule
from tests.helpers import FIXTURES, condition_value, load_yaml, source_rule


class ConverterTests(unittest.TestCase):
    def diagnostic(self, result, code, path):
        matches = [d for d in result.diagnostics if d.code == code and d.path == path]
        self.assertTrue(matches, f'Missing {code} diagnostic at {path}: {result.diagnostics}')
        for d in matches:
            self.assertIn(d.severity, ('info', 'warning'))
            self.assertTrue(d.message.strip())
        return matches[0]

    def incomplete(self, result):
        self.assertFalse(result.detection_complete)
        self.assertEqual(result.document['status'], 'unsupported')
        self.assertNotIn('detection', result.document)
        self.assertTrue(any(d.code == 'incomplete_detection' for d in result.diagnostics))

    def test_T01_human_fixture_pair(self):
        result = convert_rule(load_yaml(FIXTURES / 'elastic-input.yaml'))
        self.assertEqual(result.document, load_yaml(FIXTURES / 'sigma-expected.yaml'))
        self.assertTrue(result.detection_complete)
        self.diagnostic(result, 'unmapped_field', 'risk_score')
        self.diagnostic(result, 'assumed_value', 'language')

    def test_T01_exact_field_preserved(self):
        for field in ('process.name', 'process.executable', 'process.parent.name',
                      'process.parent.executable', 'host.os.type', 'event.category'):
            with self.subTest(field=field):
                result = convert_rule(source_rule(f'{field}: "value"'))
                self.assertTrue(result.detection_complete)
                self.assertEqual(result.document['detection'], {
                    'selection': {field: 'value'}, 'condition': 'selection'})

    def test_T02_boolean_precedence(self):
        result = convert_rule(source_rule(
            'process.name: "a" OR process.name: "b" AND process.name: "c"'))
        detection = result.document['detection']
        self.assertEqual(detection, {
            'selection_1': {'process.name': 'a'},
            'selection_2': {'process.name': 'b'},
            'selection_3': {'process.name': 'c'},
            'condition': '(selection_1 or (selection_2 and selection_3))'})
        for a, b, c in product((False, True), repeat=3):
            self.assertEqual(condition_value(detection['condition'], {
                'selection_1': a, 'selection_2': b, 'selection_3': c}), a or (b and c))

    def test_T03_grouping_negation_and_repeated_fields(self):
        detection = convert_rule(source_rule(
            '(process.name: "a" OR process.name: "b") AND NOT process.parent.name: "c"'
        )).document['detection']
        self.assertEqual(detection['selection_1'], {'process.name': 'a'})
        self.assertEqual(detection['selection_2'], {'process.name': 'b'})
        self.assertEqual(detection['selection_3'], {'process.parent.name': 'c'})
        for a, b, c in product((False, True), repeat=3):
            self.assertEqual(condition_value(detection['condition'], {
                'selection_1': a, 'selection_2': b, 'selection_3': c}), (a or b) and not c)

    def test_T04_lowercase_and_double_negation(self):
        detection = convert_rule(source_rule(
            'not not process.name: "AND OR NOT" or process.name: "b"'
        )).document['detection']
        self.assertEqual(detection['selection_1'], {'process.name': 'AND OR NOT'})
        for a, b in product((False, True), repeat=2):
            self.assertEqual(condition_value(detection['condition'], {
                'selection_1': a, 'selection_2': b}), a or b)

    def test_T04_quoted_escapes(self):
        result = convert_rule(source_rule(r'process.executable: "C:\\Tools\\a\"b.exe"'))
        self.assertEqual(result.document['detection']['selection'], {
            'process.executable': 'C:\\Tools\\a"b.exe'})

    def test_T05_metadata(self):
        rule = source_rule(name='A different title', description='Investigate a process.',
                           rule_id='84d6c392-537e-46ad-a11e-4c4be03324ae', severity='high',
                           references=['https://example.org/detection'])
        doc = convert_rule(rule).document
        for key, value in {'title': rule['name'], 'description': rule['description'],
                           'id': rule['rule_id'], 'level': 'high', 'status': 'test',
                           'references': rule['references']}.items():
            self.assertEqual(doc[key], value)
        self.assertNotIn('name', doc)
        self.assertNotIn('severity', doc)

    def test_T06_absent_optional_values_quiet(self):
        result = convert_rule(source_rule())
        for key in ('description', 'id', 'level', 'references', 'tags'):
            self.assertNotIn(key, result.document)
        optional = {'description', 'rule_id', 'severity', 'references', 'tags', 'threat'}
        self.assertFalse(any(d.path in optional for d in result.diagnostics))

    def test_T06_invalid_identifier_diagnosed(self):
        result = convert_rule(source_rule(rule_id='vendor-specific-name'))
        self.assertNotIn('id', result.document)
        self.diagnostic(result, 'invalid_value', 'rule_id')
        self.assertTrue(result.detection_complete)

    def test_T07_unsupported_settings_preserve_metadata(self):
        settings = [('type', 'eql'), ('language', 'lucene'), ('language', 'eql'),
                    ('filters', [{'query': {'match': {'event.action': 'start'}}}]),
                    ('exceptions_list', [{'id': 'example-exception'}]),
                    ('alert_suppression', {'group_by': ['host.name']})]
        for field, value in settings:
            with self.subTest(field=field, value=value):
                result = convert_rule(source_rule(description='Keep this', **{field: value}))
                self.incomplete(result)
                self.assertEqual(result.document['description'], 'Keep this')
                self.diagnostic(result, 'unsupported_semantics', field)

    def test_T07_missing_type_and_language_defaults(self):
        rule = source_rule()
        del rule['type'], rule['language']
        result = convert_rule(rule)
        self.assertTrue(result.detection_complete)
        for field in ('type', 'language'):
            self.diagnostic(result, 'assumed_value', field)

    def test_T07_empty_optional_semantic_settings(self):
        result = convert_rule(source_rule(filters=[], exceptions_list=[], alert_suppression=None))
        self.assertTrue(result.detection_complete)
        self.assertFalse(any(d.code == 'unsupported_semantics' for d in result.diagnostics))

    def test_T08_unsupported_query_constructs(self):
        queries = [
            'process.name: bash', 'process.name: "bash*"', 'process.name: *',
            'process.pid > 10', 'unknown.field: "value"', 'process.name: "a" junk',
            'process.command_line: foo*', 'process.command_line: *foo',
            'process.command_line: *fo*o*', 'process.command_line: *fo?o*',
            'process.command_line:(*a* OR *b*)', 'process.command_line:(*a* AND NOT *b*)',
            'process.command_line:((*a* AND *b*))', 'process.command_line: "exact"',
        ]
        for query in queries:
            with self.subTest(query=query):
                result = convert_rule(source_rule(query))
                self.incomplete(result)
                self.diagnostic(result, 'unsupported_query', 'query')

    def test_T09_malformed_and_empty_queries(self):
        for query in ('', ' ', 'process.name: ""', '(process.name: "a"',
                      'process.name: "unterminated', r'process.name: "bad\q"',
                      'process.command_line: **'):
            with self.subTest(query=query):
                result = convert_rule(source_rule(query))
                self.incomplete(result)
                self.assertTrue(any(d.path == 'query' for d in result.diagnostics))

    def test_T10_title_boundaries(self):
        for length in (1, 256):
            with self.subTest(length=length):
                self.assertEqual(convert_rule(source_rule(name='x' * length)).document['title'], 'x' * length)
        result = convert_rule(source_rule(name='x' * 257))
        self.assertEqual(result.document['title'], 'x' * 256)
        self.diagnostic(result, 'invalid_value', 'name')

    def test_T10_title_fallbacks(self):
        for value in ('', '  ', None, 42):
            with self.subTest(value=value):
                result = convert_rule(source_rule(name=value))
                self.assertEqual(result.document['title'], 'Untitled converted rule')
                self.assertTrue(any(d.path == 'name' for d in result.diagnostics))

    def test_T10_severities(self):
        for severity in ('low', 'medium', 'high', 'critical'):
            with self.subTest(severity=severity):
                self.assertEqual(convert_rule(source_rule(severity=severity)).document['level'], severity)
        result = convert_rule(source_rule(severity='urgent'))
        self.assertNotIn('level', result.document)
        self.diagnostic(result, 'invalid_value', 'severity')
        self.assertTrue(result.detection_complete)

    def test_T13_determinism_and_input_immutability(self):
        rule = load_yaml(FIXTURES / 'elastic-input.yaml')
        original = deepcopy(rule)
        first = convert_rule(rule)
        convert_rule(source_rule(tags=['OS: Linux'], references=['https://example.org/other']))
        second = convert_rule(rule)
        self.assertEqual(first, second)
        self.assertEqual(rule, original)

    def test_T14_os_tags(self):
        for label, expected in [('Windows', 'windows'), ('Linux', 'linux'), ('macOS', 'macos')]:
            with self.subTest(label=label):
                result = convert_rule(source_rule(tags=[f'OS: {label}'], index=['winlogbeat-*']))
                self.assertEqual(result.document['logsource']['product'], expected)

    def test_T14_mixed_index_windows_hint(self):
        result = convert_rule(source_rule(index=['winlogbeat-*', 'logs-endpoint.events.*']))
        self.assertEqual(result.document['logsource']['product'], 'windows')
        self.assertTrue(any(d.code == 'assumed_value' for d in result.diagnostics))

    def test_T15_conflicting_unknown_and_duplicate_tags(self):
        for tags in (['OS: Linux', 'OS: Windows'], ['OS: Unknown']):
            with self.subTest(tags=tags):
                result = convert_rule(source_rule(tags=tags, index=['winlogbeat-*']))
                self.assertNotIn('product', result.document['logsource'])
                self.assertTrue(any(d.path.startswith('tags') for d in result.diagnostics))
        result = convert_rule(source_rule(tags=['OS: Linux', 'OS: Linux']))
        self.assertEqual(result.document['logsource']['product'], 'linux')

    def test_T16_process_category_heuristic(self):
        doc = convert_rule(source_rule('process.command_line: *curl* AND process.name: "bash"')).document
        self.assertEqual(doc['logsource'], {'category': 'process_creation'})
        doc = convert_rule(source_rule('process.command_line: *curl* AND host.os.type: "linux"')).document
        self.assertNotIn('category', doc['logsource'])
        self.assertNotIn('product', doc['logsource'])
        self.assertIn('definition', doc['logsource'])

    def test_T16_definition_fallback(self):
        self.assertEqual(convert_rule(source_rule()).document['logsource'], {
            'definition': 'Elastic rule using ECS fields.'})
        result = convert_rule(source_rule(index=['custom-b-*', 'custom-a-*']))
        self.assertEqual(result.document['logsource'], {
            'definition': 'Elastic rule using ECS fields. Source index patterns: custom-b-*, custom-a-*'})

    def test_T17_contains_group_generalizes(self):
        for terms in (('curl', 'example.org'), ('IEX', 'powershell', 'Net.WebClient'),
                      ('wget', '--quiet', 'payload.sh')):
            with self.subTest(terms=terms):
                query = 'process.command_line:(' + ' AND '.join(f'*{t}*' for t in terms) + ')'
                result = convert_rule(source_rule(query))
                self.assertEqual(result.document['detection'], {
                    'selection': {'CommandLine|contains|all': list(terms)}, 'condition': 'selection'})
                # Independent interpretation checks the emitted all-list, not production helpers.
                emitted = result.document['detection']['selection']['CommandLine|contains|all']
                for command, expected in [(' '.join(terms), True), (terms[0], False), ('unrelated', False)]:
                    self.assertEqual(all(t.lower() in command.lower() for t in emitted), expected)

    def test_T17_single_contains(self):
        result = convert_rule(source_rule('process.command_line: *wget*'))
        self.assertEqual(result.document['detection'], {
            'selection': {'CommandLine|contains': 'wget'}, 'condition': 'selection'})

    def test_T18_contains_group_in_outer_boolean(self):
        detection = convert_rule(source_rule(
            'process.command_line:(*curl* AND *example.org*) AND NOT process.name: "trusted"'
        )).document['detection']
        self.assertEqual(detection['selection_1'], {'CommandLine|contains|all': ['curl', 'example.org']})
        self.assertEqual(detection['selection_2'], {'process.name': 'trusted'})
        for a, b in product((False, True), repeat=2):
            self.assertEqual(condition_value(detection['condition'], {'selection_1': a, 'selection_2': b}), a and not b)

    def test_T19_structured_tags_deduplicated(self):
        threat = [{'framework': 'MITRE ATT&CK', 'tactic': {'name': 'Execution'},
                   'technique': [{'id': 'T1059', 'subtechnique': [{'id': 'T1059.001'}, {'id': 'T1059.001'}]},
                                 {'id': 'T1105'}]},
                  {'framework': 'MITRE ATT&CK', 'tactic': {'name': 'Persistence'},
                   'technique': [{'id': 'T1105'}]}]
        doc = convert_rule(source_rule(threat=threat)).document
        self.assertEqual(doc['tags'], ['attack.execution', 'attack.persistence', 'attack.t1059.001', 'attack.t1105'])

    def test_T19_invalid_subtechnique_falls_back_to_parent(self):
        result = convert_rule(source_rule(threat=[{'framework': 'MITRE ATT&CK',
            'technique': [{'id': 'T1059', 'subtechnique': [{'id': 'invalid'}]}]}]))
        self.assertEqual(result.document['tags'], ['attack.t1059'])
        self.diagnostic(result, 'invalid_value', 'threat[0].technique[0].subtechnique[0].id')

    def test_T20_flat_tags_fallback(self):
        result = convert_rule(source_rule(tags=['Execution', 'T1059.001', 'Execution', 'Vendor Label']))
        self.assertEqual(result.document['tags'], ['attack.execution', 'attack.t1059.001'])
        self.diagnostic(result, 'unmapped_field', 'tags[3]')

    def test_T20_structured_tags_take_precedence(self):
        result = convert_rule(source_rule(tags=['Execution', 'T1105'], threat=[{
            'framework': 'MITRE ATT&CK', 'tactic': {'name': 'Execution'},
            'technique': [{'id': 'T1059'}]}]))
        self.assertEqual(result.document['tags'], ['attack.execution', 'attack.t1059'])
        self.assertFalse(any(d.path == 'tags[0]' for d in result.diagnostics))
        self.diagnostic(result, 'unmapped_field', 'tags[1]')

    def test_T20_no_mapped_tags(self):
        result = convert_rule(source_rule(tags=['Some Product']))
        self.assertNotIn('tags', result.document)
        self.diagnostic(result, 'unmapped_field', 'tags[0]')

    def test_T21_no_title_or_literal_platform_guess(self):
        result = convert_rule(source_rule('process.command_line: *powershell*', name='Windows PowerShell'))
        self.assertNotIn('product', result.document['logsource'])
        self.assertEqual(result.document['title'], 'Windows PowerShell')

    def test_T22_incomplete_fields_accumulate_diagnostics(self):
        result = convert_rule({'description': 'Keep the valid information', 'severity': 'urgent', 'rule_id': 'invalid'})
        self.incomplete(result)
        self.assertEqual(result.document['title'], 'Untitled converted rule')
        self.assertEqual(result.document['description'], 'Keep the valid information')
        for path in ('query', 'name', 'severity', 'rule_id'):
            self.assertTrue(any(d.path == path for d in result.diagnostics), path)

    def test_T23_unknown_objects_and_valid_siblings(self):
        result = convert_rule(source_rule(risk_score=73, vendor_extension={'nested': 'opaque'},
            references=['https://example.org/valid', 17], threat=[{
                'framework': 'MITRE ATT&CK', 'technique': [{'id': 'T1105'}, {'id': 'bad'}]}]))
        self.assertEqual(result.document['references'], ['https://example.org/valid'])
        self.assertEqual(result.document['tags'], ['attack.t1105'])
        for code, path in [('unmapped_field', 'risk_score'), ('unmapped_field', 'vendor_extension'),
                           ('invalid_value', 'references[1]'), ('invalid_value', 'threat[0].technique[1].id')]:
            self.diagnostic(result, code, path)
        paths = [(d.path, d.code) for d in result.diagnostics]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_T24_unsupported_predicate_never_dropped(self):
        good, bad = 'process.name: "bash"', 'unsupported.field: "value"'
        for query in (f'{good} AND {bad}', f'{bad} AND {good}', f'{good} OR {bad}',
                      f'{bad} OR {good}', f'{good} AND NOT {bad}', f'NOT ({good} OR {bad})'):
            with self.subTest(query=query):
                result = convert_rule(source_rule(query))
                self.incomplete(result)
                self.diagnostic(result, 'unsupported_query', 'query')

    def test_T26_represented_tags_not_lost_and_routing_diagnosed(self):
        result = convert_rule(load_yaml(FIXTURES / 'elastic-input.yaml'))
        self.assertFalse(any(d.code == 'unmapped_field' and d.path.startswith('tags') for d in result.diagnostics))
        self.assertTrue(any(d.code == 'assumed_value' for d in result.diagnostics))
        self.assertTrue(any(d.path == 'index' and d.severity == 'warning' for d in result.diagnostics))

    def test_T28_wrong_optional_container_types(self):
        for field, value in [('name', []), ('severity', None), ('tags', 'OS: Linux'),
                             ('index', 42), ('threat', 'MITRE ATT&CK'), ('references', {}),
                             ('description', ['not a string'])]:
            with self.subTest(field=field):
                result = convert_rule(source_rule(**{field: value}))
                self.assertTrue(result.detection_complete)
                self.assertTrue(any(d.path == field for d in result.diagnostics))

    def test_T28_malformed_threat_siblings(self):
        result = convert_rule(source_rule(threat=[None, {'framework': 'MITRE ATT&CK',
            'technique': [None, {'id': 'T1105'}]}]))
        self.assertEqual(result.document['tags'], ['attack.t1105'])
        for path in ('threat[0]', 'threat[1].technique[0]'):
            self.diagnostic(result, 'invalid_value', path)

    def test_T28_wrong_query_type(self):
        for value in (None, 123, [], {}):
            with self.subTest(value=value):
                result = convert_rule(source_rule(value))
                self.incomplete(result)
                self.assertTrue(any(d.path == 'query' for d in result.diagnostics))

    def test_T08_query_error_includes_position_without_echoing_query(self):
        query = 'process.name: "valid" AND unexpected.field: "unique-sensitive-marker"'
        result = convert_rule(source_rule(query))
        diagnostic = self.diagnostic(result, 'unsupported_query', 'query')
        self.assertRegex(diagnostic.message.lower(), r'(position|character|offset)\s*:?\s*\d+')
        self.assertNotIn('unique-sensitive-marker', diagnostic.message)
        self.assertNotIn(query, diagnostic.message)

    def test_T17_supported_linux_example_is_explicitly_synthetic(self):
        # Curated subset example, NOT a rewrite of the upstream ES|QL rule.
        result = convert_rule(source_rule(
            'process.command_line:(*base64* AND *--decode*)',
            name='Synthetic Linux decoding example', tags=['OS: Linux', 'T1140']))
        self.assertTrue(result.detection_complete)
        self.assertEqual(result.document, {
            'title': 'Synthetic Linux decoding example', 'status': 'test',
            'logsource': {'category': 'process_creation', 'product': 'linux'},
            'detection': {'selection': {'CommandLine|contains|all': ['base64', '--decode']},
                          'condition': 'selection'},
            'tags': ['attack.t1140']})

    def test_T07_library_returns_diagnostics_without_writing_streams(self):
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = convert_rule(source_rule(risk_score=42))
        self.diagnostic(result, 'unmapped_field', 'risk_score')
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
