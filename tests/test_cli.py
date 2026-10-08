"""Real subprocess/file/serialization boundaries: AC-05/06 and T-11/12/25."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from tests.helpers import FIXTURES, ROOT, load_yaml, source_rule


class CliTests(unittest.TestCase):
    def run_cli(self, path):
        return subprocess.run([sys.executable, '-m', 'rule_converter', str(path)],
                              cwd=ROOT, text=True, capture_output=True, timeout=10)

    def logs(self, completed):
        self.assertNotIn('Traceback', completed.stderr,
                         'CLI contract is unimplemented or leaked an internal error')
        diagnostics = []
        for line in completed.stderr.splitlines():
            self.assertTrue(line.startswith('{'), f'Expected JSONL diagnostic: {line!r}')
            item = json.loads(line)
            self.assertEqual(set(item), {'severity', 'code', 'path', 'message'})
            self.assertIn(item['severity'], ('info', 'warning', 'error'))
            self.assertTrue(item['message'])
            diagnostics.append(item)
        return diagnostics

    def test_T11_yaml_and_json_fixture(self):
        source = load_yaml(FIXTURES / 'elastic-input.yaml')
        expected = load_yaml(FIXTURES / 'sigma-expected.yaml')
        logs = []
        with tempfile.TemporaryDirectory() as folder:
            for extension in ('.json', '.yaml', '.yml'):
                with self.subTest(extension=extension):
                    path = Path(folder) / ('rule' + extension)
                    path.write_text(json.dumps(source) if extension == '.json' else yaml.safe_dump(source), encoding='utf-8')
                    completed = self.run_cli(path)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(list(yaml.safe_load_all(completed.stdout)), [expected])
                    diagnostics = self.logs(completed)
                    self.assertTrue(any(d['path'] == 'risk_score' for d in diagnostics))
                    logs.append(diagnostics)
        if logs:
            self.assertTrue(all(items == logs[0] for items in logs))

    def test_T12_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            completed = self.run_cli(Path(folder) / 'absent.json')
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, '')
        self.assertTrue(any(d['code'] == 'input_error' and d['severity'] == 'error' for d in self.logs(completed)))

    def test_T12_invalid_documents(self):
        for filename, content in [('bad.json', '{'), ('bad.yaml', 'key: [unterminated'),
                                  ('list.yaml', '- one\n- two'), ('scalar.json', '42')]:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / filename
                path.write_text(content, encoding='utf-8')
                completed = self.run_cli(path)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stdout, '')
                self.assertTrue(any(d['code'] == 'input_error' and d['path'] == '$' for d in self.logs(completed)))

    def test_T12_yaml_loader_rejects_python_object_tags(self):
        # A non-executing Python object tag proves safe loading without side effects.
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'unsafe.yaml'
            path.write_text('!!python/tuple [1, 2]', encoding='utf-8')
            completed = self.run_cli(path)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, '')
        self.assertTrue(any(d['code'] == 'input_error' for d in self.logs(completed)))

    def test_T25_incomplete_detection_still_outputs_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'partial.json'
            path.write_text(json.dumps(source_rule('unknown.field: "value"', description='Keep this')), encoding='utf-8')
            completed = self.run_cli(path)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        doc = yaml.safe_load(completed.stdout)
        self.assertEqual(doc['status'], 'unsupported')
        self.assertEqual(doc['description'], 'Keep this')
        self.assertNotIn('detection', doc)
        diagnostics = self.logs(completed)
        self.assertTrue(any(d['code'] == 'unsupported_query' and d['path'] == 'query' for d in diagnostics))
        self.assertTrue(any(d['code'] == 'incomplete_detection' for d in diagnostics))
