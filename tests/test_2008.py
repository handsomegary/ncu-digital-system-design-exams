"""Independent graph/table and exact implicant-cover checks for 2008 Q1/Q2."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import unittest
from hdl import simulate

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'exams/2008'
spec = importlib.util.spec_from_file_location('model_2008', FOLDER / 'model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

# Explicit state-table oracle, derived independently from the printed equations.
Q1_NEXT = [0, 0, 0, 2, 2, 2, 0, 2, 1, 1, 0, 2, 3, 3, 0, 2]
# Original state-diagram destination/output labels, in ABx binary order.
Q2_EDGES = [(2, 0), (0, 0), (3, 1), (1, 1), (1, 0), (3, 0), (0, 0), (2, 0)]


def exact_cover_cost(on):
    """Enumerate all ternary cubes, then independent coverage DP (3 variables)."""
    ordered = sorted(on)
    best = {0: (0, 0)}
    for pattern in itertools.product((0, 1, None), repeat=3):
        covered = {m for m in range(8)
                   if all(p is None or p == ((m >> (2 - i)) & 1)
                          for i, p in enumerate(pattern))}
        if not covered <= on:
            continue
        mask = sum(1 << i for i, m in enumerate(ordered) if m in covered)
        literals = sum(p is not None for p in pattern)
        for previous, cost in list(best.items()):
            new = previous | mask
            candidate = cost[0] + 1, cost[1] + literals
            if candidate < best.get(new, (99, 99)):
                best[new] = candidate
    return best[(1 << len(ordered)) - 1]


def document_rows(text, tag):
    block = text.split(f'<!-- {tag}_BEGIN -->', 1)[1].split(f'<!-- {tag}_END -->', 1)[0]
    rows = []
    for line in block.splitlines():
        fields = [s.strip() for s in line.strip().strip('|').split('|')]
        if fields and all(s in ('0', '1') for s in fields):
            rows.append(tuple(map(int, fields)))
    return rows


class ModelTests(unittest.TestCase):
    def test_q1_complete_truth_table(self):
        expected = []
        for address, future in enumerate(Q1_NEXT):
            a, b, x, y = ((address >> bit) & 1 for bit in (3, 2, 1, 0))
            z = int(address >= 12)
            self.assertEqual(model.q1_transition((a << 1) | b, x, y), (future, z))
            expected.append((a, b, x, y, future >> 1, future & 1, z))
        self.assertEqual(model.q1_table(), expected)
        self.assertEqual([row[-1] for row in expected[-4:]], [1, 1, 1, 1])

    def test_q2_graph_against_minimized_equations(self):
        expected = []
        for address, (future, z) in enumerate(Q2_EDGES):
            a, b, x = ((address >> bit) & 1 for bit in (2, 1, 0))
            self.assertEqual(model.q2_transition((a << 1) | b, x), (future, z))
            self.assertEqual(model.q2_equations((a << 1) | b, x), (future, z))
            expected.append((a, b, x, future >> 1, future & 1, z))
        self.assertEqual(model.q2_table(), expected)

    def test_q2_gray_maps_and_global_sop_minimum(self):
        expected = {'DA': [[1, 0, 0, 1], [0, 1, 1, 0]],
                    'DB': [[0, 0, 1, 1], [1, 1, 0, 0]],
                    'z': [[0, 0, 1, 1], [0, 0, 0, 0]]}
        self.assertEqual(model.q2_kmaps(), expected)
        on_da = {m for m, (future, _) in enumerate(Q2_EDGES) if future >> 1}
        on_db = {m for m, (future, _) in enumerate(Q2_EDGES) if future & 1}
        on_z = {m for m, (_, z) in enumerate(Q2_EDGES) if z}
        self.assertEqual(on_da, {0, 2, 5, 7})
        self.assertEqual(on_db, {2, 3, 4, 5})
        self.assertEqual(on_z, {2, 3})
        self.assertEqual([exact_cover_cost(on) for on in (on_da, on_db, on_z)],
                         [(2, 4), (2, 4), (1, 2)])

    def test_clock_step_models_with_present_state_outputs(self):
        # All initial states, all four-input-symbol traces of length 4.
        for initial in range(4):
            for symbols in itertools.product(range(4), repeat=4):
                state = golden = initial
                for symbol in symbols:
                    future, z = model.q1_transition(state, symbol >> 1, symbol & 1)
                    self.assertEqual(z, int(golden == 3))
                    golden = Q1_NEXT[(golden << 2) | symbol]
                    self.assertEqual(future, golden)
                    state = future
            # All binary traces of length 6, including both graph self-loops.
            for symbols in itertools.product((0, 1), repeat=6):
                state = golden = initial
                for symbol in symbols:
                    future, z = model.q2_equations(state, symbol)
                    expected, output = Q2_EDGES[(golden << 1) | symbol]
                    self.assertEqual((future, z), (expected, output))
                    state = golden = expected

    def test_model_input_ranges(self):
        for state in (-1, 4):
            with self.assertRaises(ValueError): model.q1_transition(state, 0, 0)
            with self.assertRaises(ValueError): model.q2_transition(state, 0)
        for bit in (-1, 2):
            with self.assertRaises(ValueError): model.q1_transition(0, bit, 0)
            with self.assertRaises(ValueError): model.q1_transition(0, 0, bit)
            with self.assertRaises(ValueError): model.q2_transition(0, bit)

    def test_document_tables_metadata_and_embedded_sources(self):
        text = (FOLDER / 'solutions.md').read_text(encoding='utf-8')
        self.assertEqual(document_rows(text, 'Q1_TABLE'), model.q1_table())
        self.assertEqual(document_rows(text, 'Q2_TABLE'), model.q2_table())
        for name, values in model.q2_kmaps().items():
            self.assertEqual(document_rows(text, 'Q2_' + name + '_MAP'),
                             [(a, *row) for a, row in enumerate(values)])
        metadata = json.loads((FOLDER / 'metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['question_count'], 2)
        self.assertIn('Midterm', metadata['exam'])
        self.assertEqual([q['id'] for q in metadata['excluded_questions']], ['Q3'])
        self.assertEqual(text.count('<!-- SOLUTION_CODE_BEGIN -->'), 1)
        self.assertEqual(text.count('<!-- SOLUTION_CODE_END -->'), 1)
        block = text.split('<!-- SOLUTION_CODE_BEGIN -->')[1].split('<!-- SOLUTION_CODE_END -->')[0]
        for source in metadata['sources']:
            self.assertIn((FOLDER / source).read_text(encoding='utf-8').strip(), block)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-only', action='store_true',
                        help='Check models/documents without claiming HDL simulation')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ModelTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.model_only:
        print('PASS 2008 models: 6 tests; HDL simulation not run')
    else:
        print(simulate(['exams/2008/design.v'], (FOLDER / 'tb.v').read_text(encoding='utf-8'), top='tb_2008'))


if __name__ == '__main__':
    main()
