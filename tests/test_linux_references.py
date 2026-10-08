"""Pinned real Elastic inputs; related Sigma detections are NOT golden outputs."""
import hashlib
import json
from pathlib import Path
import unittest

from rule_converter import convert_rule
from tests.helpers import FIXTURES, load_yaml

CORPUS = FIXTURES / 'linux'
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
PAIRS = {pair['case']: pair for pair in MANIFEST['pairs']}


class LinuxReferenceTests(unittest.TestCase):
    def check_draft(self, case, expected_tags, expected_level):
        pair = PAIRS[case]
        source = json.loads((CORPUS / pair['input']).read_text())
        result = convert_rule(source)
        self.assertFalse(result.detection_complete)
        self.assertEqual(result.document['status'], 'unsupported')
        self.assertNotIn('detection', result.document)
        self.assertEqual(result.document['title'], source['name'])
        self.assertEqual(result.document['id'], source['rule_id'])
        self.assertEqual(result.document['description'], source['description'])
        self.assertEqual(result.document['level'], expected_level)
        self.assertEqual(result.document['tags'], expected_tags)
        self.assertEqual(result.document['logsource']['product'], 'linux')
        required = pair['required_diagnostic']
        self.assertTrue(any(d.code == required['code'] and d.path == required['path'] for d in result.diagnostics))
        self.assertTrue(any(d.code == 'incomplete_detection' for d in result.diagnostics))
        self.assertTrue(any(d.code == 'unmapped_field' and d.path == 'risk_score' for d in result.diagnostics))
        reference = load_yaml(CORPUS / pair['reference'])
        self.assertNotEqual(result.document['id'], reference['id'])
        self.assertNotEqual(result.document, reference)

    def test_R01_base64_esql_keeps_metadata_reports_unsupported_semantics(self):
        self.check_draft('base64', ['attack.defense_evasion', 'attack.execution', 'attack.t1027',
                                  'attack.t1140', 'attack.t1059.004', 'attack.t1059.006', 'attack.t1204.002'], 'low')

    def test_R02_chattr_eql_does_not_substitute_sigma_rule(self):
        self.check_draft('chattr', ['attack.defense_evasion', 'attack.t1222.002'], 'medium')

    def test_R03_insmod_eql_does_not_substitute_auditd_detection(self):
        self.check_draft('insmod', ['attack.persistence', 'attack.defense_evasion', 'attack.t1547.006', 'attack.t1014'], 'medium')

    def test_R04_bpf_kql_does_not_drop_source_constraints(self):
        self.check_draft('bpf', ['attack.persistence', 'attack.defense_evasion', 'attack.t1547.006', 'attack.t1014'], 'high')


class ReferenceIntegrityTests(unittest.TestCase):
    """These checks can pass before conversion exists; they verify only test data."""

    def test_reference_bytes_and_query_hashes_match_manifest(self):
        self.assertEqual(set(PAIRS), {'base64', 'chattr', 'insmod', 'bpf'})
        for pair in PAIRS.values():
            with self.subTest(case=pair['case']):
                for path_key, hash_key in [('input', 'input_sha256'), ('reference', 'reference_sha256')]:
                    self.assertEqual(hashlib.sha256((CORPUS / pair[path_key]).read_bytes()).hexdigest(), pair[hash_key])
                source = json.loads((CORPUS / pair['input']).read_text())
                self.assertEqual(hashlib.sha256(source['query'].encode()).hexdigest(), pair['query_sha256'])
                self.assertIn(MANIFEST['elastic_revision'], pair['elastic_url'])
                self.assertIn(MANIFEST['sigma_revision'], pair['sigma_url'])
                self.assertNotEqual(pair['relationship'], 'equivalent')
                reference = load_yaml(CORPUS / pair['reference'])
                self.assertEqual(reference['logsource']['product'], 'linux')
                self.assertIn('detection', reference)

    def test_bpf_pair_has_same_indicator_but_different_constraints(self):
        pair = PAIRS['bpf']
        source = json.loads((CORPUS / pair['input']).read_text())
        reference = load_yaml(CORPUS / pair['reference'])
        self.assertIn('bpf_probe_write_user', source['query'])
        self.assertEqual(reference['detection']['selection'], ['bpf_probe_write_user'])
        self.assertIn('data_stream.dataset:', source['query'])
        self.assertIn('process.name:', source['query'])
        self.assertNotIn('data_stream.dataset', reference['detection'])

    def test_licenses_retained(self):
        for name in ('Elastic-LICENSE.txt', 'Sigma-LICENSE.txt', 'Sigma-DRL-1.1.txt'):
            with self.subTest(name=name):
                self.assertGreater(len((CORPUS / 'licenses' / name).read_text()), 100)
