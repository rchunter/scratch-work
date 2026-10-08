"""AC-09 / T-27: exercise a vendor-neutral model without an Elastic input rule."""
from itertools import product
import unittest

from rule_converter.models import And, Match, Not, Or, Translation
from rule_converter.sigma import render_sigma
from tests.helpers import condition_value


class SigmaRendererTests(unittest.TestCase):
    def translation(self, expression, complete=True):
        return Translation(metadata={'title': 'Independent model', 'logsource': {'product': 'linux'}},
                           detection=expression, detection_complete=complete, diagnostics=[])

    def test_T27_exact_match_from_shared_model(self):
        doc = render_sigma(self.translation(Match('Image', 'exact', ('/usr/bin/example',))))
        self.assertEqual(doc, {'title': 'Independent model', 'logsource': {'product': 'linux'},
                              'status': 'test', 'detection': {
                                  'selection': {'Image': '/usr/bin/example'}, 'condition': 'selection'}})

    def test_T27_contains_scalar(self):
        doc = render_sigma(self.translation(Match('CommandLine', 'contains', ('--decode',))))
        self.assertEqual(doc['detection'], {
            'selection': {'CommandLine|contains': '--decode'}, 'condition': 'selection'})

    def test_T27_contains_all(self):
        doc = render_sigma(self.translation(Match('CommandLine', 'contains_all', ('base64', '--decode'))))
        self.assertEqual(doc['detection'], {
            'selection': {'CommandLine|contains|all': ['base64', '--decode']}, 'condition': 'selection'})

    def test_T27_shared_boolean_tree(self):
        expression = And(Or(Match('Image', 'exact', ('/bin/a',)), Match('Image', 'exact', ('/bin/b',))),
                         Not(Match('User', 'exact', ('root',))))
        detection = render_sigma(self.translation(expression))['detection']
        self.assertEqual(detection['selection_1'], {'Image': '/bin/a'})
        self.assertEqual(detection['selection_2'], {'Image': '/bin/b'})
        self.assertEqual(detection['selection_3'], {'User': 'root'})
        for a, b, c in product((False, True), repeat=3):
            self.assertEqual(condition_value(detection['condition'], {
                'selection_1': a, 'selection_2': b, 'selection_3': c}), (a or b) and not c)

    def test_T27_incomplete_shared_model(self):
        self.assertEqual(render_sigma(self.translation(None, complete=False)), {
            'title': 'Independent model', 'logsource': {'product': 'linux'}, 'status': 'unsupported'})
