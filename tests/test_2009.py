"""Independent 2009 word/bit models and real Icarus testbench execution.

No waveform dumps or expanded vector/log files are stored in the repository.
The HDL runner compiles and executes exclusively in a temporary directory.
"""

import argparse
import json
from pathlib import Path
import random
import re
import unittest

from hdl import simulate


ROOT = Path(__file__).resolve().parents[1]
YEAR = ROOT / 'exams' / '2009'
MASK = 65535
COUNTS = {'model_checks': 0}


def bit_word(value):
    return list(map(int, format(value, '016b')))


def word_bits(bits):
    return int(''.join(map(str, bits)), 2)


def shifted_bits(value, left):
    bits = bit_word(value)
    moved = bits[1:] + [0] if left else [0] + bits[:-1]
    return word_bits(moved)


def ripple_add(a, b):
    # A bit-list full-adder model, independent of Verilog's word arithmetic.
    first = list(reversed(bit_word(a)))
    second = list(reversed(bit_word(b)))
    result = []
    carry = 0
    for x, y in zip(first, second):
        ones = x + y + carry
        result.append(ones % 2)
        carry = ones // 2
    return word_bits(list(reversed(result)))


def alu_bits(a, b, mode):
    if mode == 0:
        return ripple_add(a, b)
    if mode == 1:
        inverted = word_bits([1 - bit for bit in bit_word(b)])
        return ripple_add(ripple_add(a, inverted), 1)
    if mode == 2:
        return ripple_add(a, 1)
    return ripple_add(a, MASK)


def alu_arithmetic(a, b, mode):
    return (a + b if mode == 0 else a - b if mode == 1 else
            a + 1 if mode == 2 else a - 1) % 65536


STAGES = [
    # Sel1, Sel2, Sel3, LorR, Mode, MyInput
    (0, 1, 1, 0, 0, 0x001A),
    (1, 1, 1, 0, 0, 0x00EA),
    (1, 0, 0, 0, 1, 0x0055),
    (0, 0, 0, 1, 2, 0x008C),
    (0, 0, 0, 1, 3, 0x00FF),
]


def stage_output(x, y, stage):
    _, _, select_x, left, mode, value = stage
    operand = x if select_x else y
    return shifted_bits(alu_bits(operand, value, mode), left)


def timing_rows():
    x, y = 0, 0
    output = stage_output(x, y, STAGES[0])
    rows = [(2, x, y, output)]
    for index, stage in enumerate(STAGES[1:], 1):
        previous = STAGES[index - 1]
        # Both registers sample the same pre-edge output, before new controls.
        x, y = (x if previous[0] else output,
                y if previous[1] else output)
        output = stage_output(x, y, stage)
        rows.append((index * 20 + 2, x, y, output))
    previous = STAGES[-1]
    x, y = (x if previous[0] else output,
            y if previous[1] else output)
    rows.append((102, x, y, stage_output(x, y, previous)))
    return rows


class IndependentModels(unittest.TestCase):
    def test_cheerup_all_32_binary_inputs(self):
        for very_good in range(4):
            for not_bad in range(4):
                vg = format(very_good, '02b')
                nb = format(not_bad, '02b')
                combined = int(''.join('1' if p == '1' or q == '1' else '0'
                                       for p, q in zip(vg, nb)), 2)
                self.assertEqual(combined, very_good | not_bad)
                for selection in (0, 1):
                    chosen_index = 1 if selection else 0
                    fine = int(nb[chosen_index] + vg[chosen_index], 2)
                    bit_index = 0 if selection else 1
                    expected = ((not_bad // (2 ** bit_index)) % 2) * 2
                    expected += (very_good // (2 ** bit_index)) % 2
                    self.assertEqual(fine, expected)
                    COUNTS['model_checks'] += 1

    def test_latch_and_tristate_semantics(self):
        # An explicit sequence distinguishes retaining state from driving Z.
        data_enable = [(0, 0), (1, 1), (0, 0), (0, 1), (1, 0), (1, 1)]
        expected_latch = [None, 1, 1, 0, 0, 1]
        expected_tri = ['Z', 1, 'Z', 0, 'Z', 1]
        saved = None
        for (data, enable), latch, tri in zip(data_enable, expected_latch, expected_tri):
            if enable:
                saved = data
            driven = data if enable else 'Z'
            self.assertEqual(saved, latch)
            self.assertEqual(driven, tri)
            COUNTS['model_checks'] += 2

    def test_all_16_bit_shifts_without_sign_extension(self):
        for value in range(65536):
            self.assertEqual(shifted_bits(value, 0), value // 2)
            self.assertEqual(shifted_bits(value, 1), value * 2 % 65536)
            COUNTS['model_checks'] += 2
        self.assertEqual(shifted_bits(0x8001, 0), 0x4000)
        self.assertEqual(shifted_bits(0x8001, 1), 2)

    def test_alu_word_arithmetic_against_ripple_bits(self):
        edges = [0, 1, 2, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        cases = [(a, b) for a in edges for b in edges]
        rng = random.Random(20090615)
        cases.extend((rng.randrange(65536), rng.randrange(65536)) for _ in range(1024))
        for a, b in cases:
            for mode in range(4):
                self.assertEqual(alu_bits(a, b, mode), alu_arithmetic(a, b, mode))
                COUNTS['model_checks'] += 1
        self.assertEqual(alu_bits(MASK, 0, 2), 0)
        self.assertEqual(alu_bits(0, MASK, 3), MASK)

    def test_datapath_timing_with_old_controls_on_each_edge(self):
        expected = [
            (2, 0x0000, 0x0000, 0x000D),
            (22, 0x000D, 0x0000, 0x007B),
            (42, 0x000D, 0x0000, 0x7FD5),
            (62, 0x000D, 0x7FD5, 0xFFAC),
            (82, 0xFFAC, 0xFFAC, 0xFF56),
            (102, 0xFF56, 0xFF56, 0xFEAA),
        ]
        self.assertEqual(timing_rows(), expected)
        for _, x, y, output in timing_rows():
            self.assertTrue(0 <= x <= MASK and 0 <= y <= MASK and 0 <= output <= MASK)
            COUNTS['model_checks'] += 1

    def test_source_constraints_and_metadata(self):
        source = (YEAR / 'design.v').read_text(encoding='utf-8')
        shifter = re.search(r'module Shifter\b(.*?)endmodule', source, re.S).group(1)
        self.assertNotRegex(shifter, r'<<|>>')
        for source_file in YEAR.glob('*.v'):
            text = source_file.read_text(encoding='utf-8')
            self.assertNotRegex(text, r'\$dumpfile|\$dumpvars')
        metadata = json.loads((YEAR / 'metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['question_count'], 5)
        self.assertEqual(set(metadata['sources']), {'design.v', 'tb_units.v', 'tb_waveform.v'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-only', action='store_true',
                        help='Check independent models; do not claim HDL simulation')
    parser.add_argument('--require-simulator', action='store_true',
                        help='Explicitly require iverilog/vvp (also the default)')
    args = parser.parse_args()
    if args.model_only and args.require_simulator:
        parser.error('--model-only and --require-simulator are mutually exclusive')
    result = unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IndependentModels))
    if not result.wasSuccessful():
        return 1
    print('Independent model checks:', COUNTS['model_checks'])
    if args.model_only:
        print('MODEL ONLY: Verilog simulation not run')
        return 0
    units = simulate(['exams/2009/design.v'],
                     (YEAR / 'tb_units.v').read_text(encoding='utf-8'),
                     top='tb_units', timeout=120)
    assert units == 'PASS units checks=153641', units
    timing = simulate(['exams/2009/design.v'],
                      (YEAR / 'tb_waveform.v').read_text(encoding='utf-8'),
                      top='tb_waveform', timeout=60)
    expected = '\n'.join(f't={time} X={x:04x} Y={y:04x} out={output:04x}'
                         for time, x, y, output in timing_rows())
    assert timing == expected + '\nPASS waveform rows=6', timing
    # Summaries only: no complete simulator output or waveform artifact.
    print(units)
    print('PASS 2009 timing: 6 checked observations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
