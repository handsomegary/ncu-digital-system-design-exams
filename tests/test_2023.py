"""Independent word-memory, coordinate and sliding-window oracles for the 2023 RTL.

Stimulus, simulation output and compiled HDL exist only in a temporary directory.
No waveform/VCD files are generated.
"""
import argparse
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "exams/2023"


def pattern_max(values, pattern):
    if pattern not in (0, 1, 2):
        return (0, 0, 0, 0)
    candidates = [(r, c) for r in range(3) for c in range(3)
                  if pattern == 0 or c == 1 or (pattern == 1 and r == 1)]
    # Row-major order makes the documented tie rule explicit.
    r, c = max(candidates, key=lambda p: values[p[0] * 3 + p[1]])
    return (values[r * 3 + c], r + 1, c + 1, 1)


def fetch_word(memory, x, y, enable, col, row):
    addresses = [(y + offset - 1) * col + x - 1 for offset in range(3)]
    if not enable or not 1 <= x <= col or not 1 <= y <= row - 2 or not all(0 <= a < 1024 for a in addresses):
        return None
    return tuple(memory[address] for address in addresses)


def next_index(index, enable, reset, col=4, row=7):
    x, y = index
    if reset:
        return (0, 0)
    if not enable:
        return index
    if x == 0:
        return (1, 1)
    if x < col:
        return (x + 1, y)
    return (1, y + 3 if y + 3 <= row else 1)


def max_trace(memory, vectors):
    """One registered read plus two history stages; Pattern is combinational."""
    index = (0, 0)
    fetched = None
    history = []
    results = []
    for reset, enable, pattern in vectors:
        if reset:
            index, fetched, history = (0, 0), None, []
            results.append((0, 0, 0, 0))
            continue
        old_index = index
        old_fetched = fetched
        index = next_index(index, enable, False)
        words = fetch_word(memory, *old_index, enable, 4, 7)
        fetched = (old_index, words) if words is not None else None
        if old_fetched is not None:
            history = (history + [old_fetched])[-2:]
        output = (0, 0, 0, 0)
        if enable and fetched is not None and len(history) == 2:
            (x, y), newest = fetched
            coordinates = [entry[0] for entry in history]
            if coordinates == [(x - 2, y), (x - 1, y)] and x >= 3:
                columns = [history[0][1], history[1][1], newest]
                values = [columns[c][r] for r in range(3) for c in range(3)]
                value, r, c, valid = pattern_max(values, pattern)
                if valid:
                    output = (value, x - 3 + c, y - 1 + r, 1)
        results.append(output)
    return results


def fixture():
    rng = random.Random(20230530)
    memory = [(address * 37 + 19) % 256 for address in range(1024)]
    memory[:12] = [55, 168, 16, 88, 39, 39, 2, 91, 111, 15, 201, 211]
    memory[12:28] = [rng.randrange(256) for _ in range(16)]
    rotator = [(mode, rng.randrange(256), rng.randrange(256), rng.randrange(256))
               for mode in range(4) for _ in range(128)]
    rows = [(mode, rng.randrange(256), rng.randrange(256), rng.randrange(256))
            for mode in range(2) for _ in range(256)]
    rows += [(0, 1, 55, 76), (0, 99, 70, 51), (1, 88, 89, 61),
             (1, 9, 45, 77), (0, 10, 5, 3), (0, 6, 22, 8), (0, 93, 32, 100)]
    rows += [(mode, a, b, c) for mode in range(2)
             for a, b, c in [(0, 0, 0), (255, 255, 255), (255, 255, 1), (1, 255, 255)]]
    patterns = [(mode, *[rng.randrange(256) for _ in range(9)])
                for mode in range(4) for _ in range(128)]
    patterns += [(mode, *([57] * 9)) for mode in range(3)]
    patterns += [(2, *[55, 168, 16, 39, 39, 2, 111, 15, 201])]
    registers = [(1, 37, 42, 37, 41, 1023), (0, 37, 99, 37, 41, 1023)]
    for _ in range(128):
        wa, data, enable = rng.randrange(1024), rng.randrange(256), rng.randrange(2)
        registers.append((enable, wa, data, wa if rng.randrange(2) else rng.randrange(1024),
                          rng.randrange(1024), rng.randrange(1024)))
    counts = [(1, 0), (0, 0)] + [(0, 1)] * 26
    counts += [(int(i % 31 == 17), rng.randrange(2)) for i in range(128)]
    fetches = [(x, y, enable) for x in range(6) for y in range(9) for enable in range(2)]
    fetches += [(x, y, 1) for x, y in [(50, 1), (1, 16), (24, 19), (25, 19), (1, 22), (1, 25), (127, 1)]]
    maximum = [(1, 0, 2)] + [(0, 1, 2)] * 4 + [(0, 1, 0)]
    maximum += [(0, 1, i % 3) for i in range(36)]
    maximum += [(int(i % 53 == 37), int(i % 7 not in (1, 2)), rng.randrange(4)) for i in range(320)]
    maximum += [(0, 1, 0)] * 8
    trace = max_trace(memory, maximum)
    assert trace[4] == (168, 2, 1, 1)  # Fourth enabled rising edge, PDF window 1.
    assert trace[5] == (211, 4, 3, 1)  # PDF window 2, absolute coordinates.
    assert all(result == (0, 0, 0, 0) for result in trace[1:4])
    assert fetch_word(memory, 24, 19, 1, 50, 25) is not None
    assert fetch_word(memory, 25, 19, 1, 50, 25) is None
    assert fetch_word(memory, 1, 7, 1, 4, 7) is None
    return memory, {"rotator": rotator, "row": rows, "pattern": patterns,
                    "rf": registers, "count": counts, "fetch": fetches, "max": maximum}


def expected_records(memory, vectors):
    expected = {}
    for i, (mode, a, b, c) in enumerate(vectors["rotator"]):
        values = [a, b, c]
        expected[("ROT", i)] = tuple(values[mode:] + values[:mode]) if mode < 3 else (0, 0, 0)
    for i, (mode, a, b, c) in enumerate(vectors["row"]):
        values = [a, b, c]
        position = 1 if mode else values.index(max(values))
        expected[("ROW", i)] = (values[position], position + 1, 1)
    for i, (mode, *values) in enumerate(vectors["pattern"]):
        expected[("PAT", i)] = pattern_max(values, mode)
    contents = list(memory)
    for i, (we, wa, data, ra, rb, rc) in enumerate(vectors["rf"]):
        expected[("RF", i)] = (contents[ra], contents[rb], contents[rc])
        if we:
            contents[wa] = data
    index = (0, 0)
    for i, (reset, enable) in enumerate(vectors["count"]):
        index = next_index(index, enable, reset)
        expected[("COUNT", i)] = index
    for i, (x, y, enable) in enumerate(vectors["fetch"]):
        for label, col, row in [("FETCH", 4, 7), ("DEFAULT_FETCH", 50, 25)]:
            values = fetch_word(memory, x, y, enable, col, row)
            expected[(label, i)] = (1, *values) if values is not None else (0, "xx", "xx", "xx")
    for i, result in enumerate(max_trace(memory, vectors["max"])):
        expected[("MAX", i)] = result
    return expected


def verify_output(output, expected):
    visited = set()
    unknown_counts = {"ROW_UNKNOWN": 0, "PAT_UNKNOWN": 0}
    events = set()
    for line in output.splitlines():
        words = line.split()
        if not words:
            continue
        tag = words[0]
        if tag in {"ROT", "ROW", "PAT", "RF", "COUNT", "FETCH", "DEFAULT_FETCH", "MAX"}:
            key = (tag, int(words[1]))
            assert key in expected and key not in visited, line
            visited.add(key)
            if tag in ("FETCH", "DEFAULT_FETCH"):
                actual = (int(words[2]), *[word if "x" in word.lower() or "z" in word.lower() else int(word, 16) for word in words[3:]])
            else:
                actual = tuple(map(int, words[2:]))
            assert actual == expected[key], (key, actual, expected[key])
        elif tag in unknown_counts:
            unknown_counts[tag] += 1
            assert all(word == "0" for word in words[2:]), line
        elif tag == "RF_HOLD":
            assert words[1] == words[2], line
            events.add(tag)
        elif tag in {"ROT_UNKNOWN", "COUNT_ASYNC", "FETCH_UNKNOWN", "FETCH_ASYNC", "MAX_ASYNC", "MAX_UNKNOWN"}:
            assert all(word == "0" for word in words[1:]), line
            events.add(tag)
        elif tag == "DONE":
            events.add(tag)
        else:
            raise AssertionError("Unexpected simulator output: " + line)
    assert visited == set(expected), set(expected) - visited
    assert unknown_counts == {"ROW_UNKNOWN": 97, "PAT_UNKNOWN": 55}, unknown_counts
    assert events == {"RF_HOLD", "ROT_UNKNOWN", "COUNT_ASYNC", "FETCH_UNKNOWN", "FETCH_ASYNC", "MAX_ASYNC", "MAX_UNKNOWN", "DONE"}, events
    return len(expected) + sum(unknown_counts.values()) + len(events) - 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iverilog", default=os.environ.get("IVERILOG", "iverilog"))
    parser.add_argument("--vvp", default=os.environ.get("VVP", "vvp"))
    parser.add_argument("--model-only", action="store_true", help="Audit golden stimulus without claiming HDL simulation")
    args = parser.parse_args()
    memory, vectors = fixture()
    expected = expected_records(memory, vectors)
    if args.model_only:
        print(f"2023 golden stimulus audited: {len(expected)} vector observations; HDL simulation not run")
        return
    if not shutil.which(args.iverilog) or not shutil.which(args.vvp):
        raise RuntimeError("Install Icarus Verilog (iverilog and vvp); CI installs it automatically.")
    with tempfile.TemporaryDirectory(prefix="dsd2023_") as temporary:
        folder = Path(temporary)
        (folder / "memory.hex").write_text("\n".join(f"{value:02x}" for value in memory) + "\n", encoding="ascii")
        for name, rows in vectors.items():
            (folder / (name + "_vectors.txt")).write_text("\n".join(" ".join(map(str, row)) for row in rows) + "\n", encoding="ascii")
        executable = folder / "simulation.vvp"
        result = subprocess.run([args.iverilog, "-g2012", "-Wall", "-s", "tb_2023", "-o", str(executable),
                                 str(FOLDER / "dsd2023.v"), str(FOLDER / "tb_2023.v")],
                                text=True, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        result = subprocess.run([args.vvp, str(executable)], cwd=folder, text=True, capture_output=True, timeout=60)
        assert result.returncode == 0 and not result.stderr, result.stdout + result.stderr
        count = verify_output(result.stdout, expected)
    print(f"PASS 2023: all 7 modules, {count} independent observations; fourth-edge validity, pauses, X/Z and capacity boundaries.")


if __name__ == "__main__":
    main()
