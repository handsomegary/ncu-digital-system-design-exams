"""2008 midterm Q1/Q2: executable tables and Gray-ordered Karnaugh maps."""
import itertools


def _validate(state, *bits):
    if state not in range(4) or any(bit not in (0, 1) for bit in bits):
        raise ValueError("state must be 0..3 and inputs must be bits")


def q1_transition(state, x, y):
    """Implement the original Q1 next-state/output equations."""
    _validate(state, x, y)
    a, b = state >> 1, state & 1
    da = ((1 - x) & b) | (x & y)
    db = (1 - x) & a
    return (da << 1) | db, a & b


Q2_GRAPH = {
    (0b00, 0): (0b10, 0), (0b00, 1): (0b00, 0),
    (0b01, 0): (0b11, 1), (0b01, 1): (0b01, 1),
    (0b10, 0): (0b01, 0), (0b10, 1): (0b11, 0),
    (0b11, 0): (0b00, 0), (0b11, 1): (0b10, 0),
}


def q2_transition(state, x):
    """Read the original eight directed edges; no Boolean minimizer involved."""
    _validate(state, x)
    return Q2_GRAPH[state, x]


def q2_equations(state, x):
    """Separate minimized implementation, to compare against the graph."""
    _validate(state, x)
    a, b = state >> 1, state & 1
    da = ((1 - a) & (1 - x)) | (a & x)
    db = ((1 - a) & b) | (a & (1 - b))
    return (da << 1) | db, (1 - a) & b


def q1_table():
    rows = []
    for a, b, x, y in itertools.product((0, 1), repeat=4):
        future, z = q1_transition((a << 1) | b, x, y)
        rows.append((a, b, x, y, future >> 1, future & 1, z))
    return rows


def q2_table():
    rows = []
    for a, b, x in itertools.product((0, 1), repeat=3):
        future, z = q2_transition((a << 1) | b, x)
        rows.append((a, b, x, future >> 1, future & 1, z))
    return rows


def q2_kmaps():
    """Rows A=0,1; columns Bx=00,01,11,10 (Gray order)."""
    maps = {"DA": [], "DB": [], "z": []}
    for a in (0, 1):
        values = {name: [] for name in maps}
        for b, x in ((0, 0), (0, 1), (1, 1), (1, 0)):
            future, z = q2_transition((a << 1) | b, x)
            for name, value in zip(("DA", "DB", "z"), (future >> 1, future & 1, z)):
                values[name].append(value)
        for name in maps:
            maps[name].append(values[name])
    return maps


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join(lines)


if __name__ == "__main__":
    print("Q1")
    print(markdown_table(("A", "B", "x", "y", "DA", "DB", "z"), q1_table()))
    print("\nQ2")
    print(markdown_table(("A", "B", "x", "DA", "DB", "z"), q2_table()))
    for name, values in q2_kmaps().items():
        print("\nK-map", name)
        print(markdown_table(("A / Bx", "00", "01", "11", "10"),
                             [[a, *row] for a, row in enumerate(values)]))
