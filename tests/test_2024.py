"""Independent geometric, signed-memory and timing oracles for the 2024 exam.

Runs real Icarus Verilog simulations; generated fixtures exist only in a
temporary directory managed by hdl.simulate. No VCD/waveform artifacts.
"""
import random

from hdl import simulate

SOURCE = ["exams/2024/design.v"]


def coordinates(size):
    """Geometry, rather than the RTL phase/counter implementation."""
    result = []
    for base in range(1, size + 1, 3):
        for row_offset in range(3):
            columns = range(base, base + 3)
            if row_offset == 1:
                columns = reversed(list(columns))
            result.extend((base + row_offset, column) for column in columns)
    return result


def fixtures():
    rng = random.Random(20240604)
    result = []
    # Every legal matrix size, including the last 6-bit coordinate (63,63).
    for size in range(3, 64, 3):
        data = [rng.randrange(-512, 512) for _ in range(size * size)]
        boundary_values = [-512, -1, 0, 511]
        for index, (row, col) in enumerate(coordinates(size)):
            if index % 7 == 0:
                data[(row - 1) * size + col - 1] = boundary_values[(index // 7) % 4]
        result.append((size, data))
    # Exact published example: counts 6,4,2; off-block words are negative to
    # expose accidental full-matrix scanning or inclusion of invalid addresses.
    data = [-512] * 81
    blocks = [
        [-5, -4, 11, 66, -99, -22, 7, -1, -197],
        [-1, -1, 100, 400, -15, 77, 91, -67, 101],
        [10, 90, -90, 101, -11, 99, 17, 17, 88],
    ]
    for block_index, block in enumerate(blocks):
        base = block_index * 3
        for index, value in enumerate(block):
            row, col = divmod(index, 3)
            data[(base + row) * 9 + base + col] = value
    result += [(9, data), (3, [511] * 9), (3, [-512] * 9)]
    return result


def matrix_test():
    cases = fixtures()
    initialization, runs = [], []
    offset = 0
    for case_id, (size, memory) in enumerate(cases):
        for value in memory:
            initialization.append(f"stimulus[{offset}] = 10'h{value & 1023:03x};")
            offset += 1
        runs.append(f"run_case({case_id}, {size}, {offset - len(memory)}, {case_id % 2});")
    bench = """`timescale 1ns/1ps
module tb;
reg Clock=0, Reset=1, StartCal=0, WEBPort=0;
reg [5:0] SizeM=0;
reg [9:0] DPortB=0;
reg [11:0] AddBPort=0;
wire [3:0] NegNo;
wire NBlock;
CalculateNegativeDBlock dut(.NegNo(NegNo),.NBlock(NBlock),.SizeM(SizeM),
 .StartCal(StartCal),.Clock(Clock),.Reset(Reset),.DPortB(DPortB),
 .AddBPort(AddBPort),.WEBPort(WEBPort));
always #5 Clock=~Clock;
reg [9:0] stimulus [0:TOTAL-1];
task run_case;
 input integer id, m, start_address, pulse_start;
 integer address, cycle;
 begin
  @(negedge Clock); Reset=1; StartCal=0; WEBPort=0; SizeM=m;
  #1;
  if (NegNo !== 0 || NBlock !== 0) $fatal(1,"Asynchronous reset failed");
  for (address=0; address<m*m; address=address+1) begin
   @(negedge Clock); AddBPort=address; DPortB=stimulus[start_address+address]; WEBPort=1;
   @(posedge Clock); #1;
  end
  @(negedge Clock); WEBPort=0; Reset=0; StartCal=1;
  for (cycle=0; cycle<3*m+7; cycle=cycle+1) begin
   @(posedge Clock); #1;
   $display("M %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
    id,cycle,dut.RIndx,dut.CIndx,NBlock,NegNo,dut.read_valid,
    dut.read_address,dut.qa_valid,dut.QA,dut.qa_last);
   @(negedge Clock);
   if (pulse_start) StartCal=0;
   // SizeM is captured at launch: changing it later must not change the job.
   if (cycle==2) SizeM=(m==63 ? 3 : 63);
  end
 end
endtask
initial begin
 #1;
INITIALIZATION
RUNS
 $display("PASS matrix simulation");
 $finish;
end
endmodule
""".replace("TOTAL", str(offset)).replace("INITIALIZATION", "\n".join(initialization)).replace("RUNS", "\n".join(runs))
    output = simulate(SOURCE, bench, timeout=120)
    rows = [list(map(int, line.split()[1:])) for line in output.splitlines() if line.startswith("M ")]
    assert len(rows) == sum(3 * size + 7 for size, _ in cases)
    for row in rows:
        case_id, cycle, r, c, nblock, neg, valid, address, qvalid, qa, qlast = row
        size, memory = cases[case_id]
        sequence = coordinates(size)
        count = len(sequence)
        totals = [sum(memory[(rr - 1) * size + cc - 1] < 0 for rr, cc in sequence[start:start + 9])
                  for start in range(0, count, 9)]
        if cycle < count:
            expected_index = sequence[cycle]
            expected_address = (expected_index[0] - 1) * size + expected_index[1] - 1
            expected_valid = 1
        elif cycle == count:
            expected_index = ((size + 1) % 64,) * 2
            expected_address, expected_valid = 0, 0
        else:
            expected_index, expected_address, expected_valid = (0, 0), 0, 0
        expected_nblock = int(cycle <= count and cycle % 9 == 0)
        expected_negative = 0 if cycle < 9 else totals[min(cycle // 9, len(totals)) - 1]
        label = f"M={size}, case={case_id}, cycle={cycle}"
        assert (r, c) == expected_index, (label, "index", (r, c), expected_index)
        assert (valid, address) == (expected_valid, expected_address), (label, "request", valid, address)
        assert (nblock, neg) == (expected_nblock, expected_negative), (label, "boundary/count", nblock, neg)
        assert qvalid == int(1 <= cycle <= count), (label, "RF valid", qvalid)
        assert qlast == int(0 < cycle <= count and cycle % 9 == 0), (label, "last word", qlast)
        if 1 <= cycle <= count:
            rr, cc = sequence[cycle - 1]
            expected_qa = memory[(rr - 1) * size + cc - 1] & 1023
            assert qa == expected_qa, (label, "synchronous QA", qa, expected_qa)
    example = cases[-3]
    assert [sum(example[1][(r - 1) * 9 + c - 1] < 0 for r, c in coordinates(9)[i:i + 9])
            for i in range(0, 27, 9)] == [6, 4, 2]
    print(f"PASS Q6: {len(cases)} matrices, all 21 legal SizeM values and final drain")


def component_test():
    rng = random.Random(20240604)
    vectors = [(rng.randrange(2), rng.randrange(2)) for _ in range(100)]
    # Force both wrap directions and hold, not just random state transitions.
    vectors = [(1, 1)] * 33 + [(0, 1)] * 34 + [(0, 0)] * 3 + vectors
    stimulus = "\n".join(f"direction={direction}; enable={enable}; @(posedge Clock); #1; "
                          f'$display("C {i} %0d %0d",dec,count); @(negedge Clock);'
                          for i, (direction, enable) in enumerate(vectors))
    bench = """`timescale 1ns/1ps
module tb;
reg Clock=0, Reset=0, direction=0, enable=0, Start=0;
wire [4:0] dec, count;
wire up, newblock;
wire [5:0] r,c;
Decrementer q1(dec,Clock,Reset);
Counting q2(count,direction,enable,Clock,Reset);
GenerateUpDownCtr q3(up,Start,Clock,Reset);
GenerateRCIndex q4(newblock,r,c,Start,Clock,Reset);
reg [11:0] adda=0, addb=0;
reg [9:0] db=0;
reg web=0;
wire [9:0] qa;
RFTwoPort q5(qa,adda,db,addb,web,Clock);
always #5 Clock=~Clock;
integer i;
initial begin
 #2; Reset=1; #1;
 if (dec !== 0 || count !== 0 || r !== 0 || c !== 0 || up !== 0 || newblock !== 0)
  $fatal(1,"Asynchronous reset/idle failed");
 @(negedge Clock); Reset=0;
STIMULUS
 // A reset between edges must immediately clear even nonzero state.
 #2; Reset=1; #1;
 if (dec !== 0 || count !== 0) $fatal(1,"Mid-cycle asynchronous reset failed");
 @(negedge Clock); Reset=0; Start=1;
 for (i=0;i<70;i=i+1) begin
  @(posedge Clock); #1;
  $display("I %0d %0d %0d %0d %0d",i,up,newblock,r,c);
  @(negedge Clock); if(i==4) Start=0;
 end
 // Port-B preload, collision, no-edge hold, high address, and WEB=0.
 adda=37; addb=37; db=111; web=1;
 @(posedge Clock); #1;
 @(negedge Clock); web=0;
 @(posedge Clock); #1;
 if(qa !== 111) $fatal(1,"RF preload/read failed");
 @(negedge Clock); web=1; db=777;
 @(posedge Clock); #1;
 if(qa !== 111) $fatal(1,"Same-address collision must return old data");
 @(negedge Clock); web=0;
 @(posedge Clock); #1;
 if(qa !== 777) $fatal(1,"Written value missing on next read");
 #1; adda=4095; #1;
 if(qa !== 777) $fatal(1,"RF read changed without rising edge");
 @(negedge Clock); addb=4095; db=512; web=1;
 @(posedge Clock); #1;
 @(negedge Clock); web=0; db=1;
 @(posedge Clock); #1;
 if(qa !== 512) $fatal(1,"RF address 4095 failed");
 @(posedge Clock); #1;
 if(qa !== 512) $fatal(1,"WEB=0 unexpectedly wrote memory");
 @(negedge Clock); addb=3968; db=511; web=1;
 @(posedge Clock); #1;
 @(negedge Clock); adda=3968; web=0;
 @(posedge Clock); #1;
 if(qa !== 511) $fatal(1,"RF maximum 63x63 matrix address failed");
 $display("PASS components"); $finish;
end
endmodule
""".replace("STIMULUS", stimulus)
    output = simulate(SOURCE, bench)
    counter = 0
    counter_rows = [line for line in output.splitlines() if line.startswith("C ")]
    assert len(counter_rows) == len(vectors)
    for line, (direction, enable) in zip(counter_rows, vectors):
        _, cycle, dec, actual = line.split()
        cycle, dec, actual = map(int, (cycle, dec, actual))
        if enable:
            counter = (counter + (1 if direction else -1)) % 32
        assert dec == (-(cycle + 1)) % 32, (cycle, "decrement", dec)
        assert actual == counter, (cycle, "count", actual, counter)
    indices = coordinates(63)
    index_rows = [line for line in output.splitlines() if line.startswith("I ")]
    assert len(index_rows) == 70
    for line in index_rows:
        cycle, up, nblock, r, c = map(int, line.split()[1:])
        assert (r, c) == indices[cycle], (cycle, "Q4 index", r, c)
        assert nblock == int(cycle % 9 == 0), (cycle, "NewBlock", nblock)
        assert up == int((cycle // 3) % 3 != 1), (cycle, "UpDown", up)
    print("PASS Q1-Q5: async reset, hold/wrap, traversal, synchronous read-first RF")


if __name__ == "__main__":
    component_test()
    matrix_test()
    print(simulate(SOURCE + ["exams/2024/tb.v"], "// Compile the supplied tb.v", top="tb"))
