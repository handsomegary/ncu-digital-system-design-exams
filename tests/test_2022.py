"""Independent bit-list, word-memory and valid-item oracles for all seven 2022 questions."""
import argparse
import random
from hdl import simulate, ROOT


def matches(value, pattern, mask=15):
    return all(not (mask >> bit & 1) or (value >> bit & 1) == (pattern >> bit & 1) for bit in range(4))


def bench_text():
    statements = []
    checks = 0
    def expect(signal, value, width=10):
        nonlocal checks
        checks += 1
        statements.append(f'if ({signal} !== {width}\'d{value}) $fatal(1,"check {checks}: {signal} got %0h expected %0h", {signal}, {width}\'d{value});')
    def step(): statements.append('tick;')
    # Reset must act independently of a clock edge.
    statements += ['Reset=1; #1;']
    expect('CounterOut',0)
    expect('Judge',0,1)
    expect('Match',0,1)
    step()
    expect('Count.U1.mem[4]',0)
    expect('Position.U1.mem[7]',0)
    statements += ['Reset=0; En=1;']
    value = 0
    for index in range(2051):
        enabled = int(index % 11 != 7)
        statements.append(f'En={enabled};')
        if enabled: value = value % 1023 + 1
        step(); expect('CounterOut',value)
    statements.append('En=0;')
    # Rotate with an independently re-indexed list of bits.
    for value in range(16):
        bits = [(value >> bit) & 1 for bit in range(3,-1,-1)]
        for amount in range(4):
            rotated = bits[amount:] + bits[:amount]
            result = int(''.join(map(str,rotated)),2)
            statements.append(f'RIn=4\'d{value}; Rb=2\'d{amount}; #1;')
            expect('Rout',result,4)
    # Seed all RF words, then check synchronous read-first collisions and holding.
    memory = [None]*8
    for address in range(8):
        data = address*137%1024
        statements.append(f'WE=1; Add=3\'d{address}; D=10\'d{data};')
        step(); memory[address]=data
    rng = random.Random(20220531)
    old_q = None
    for _ in range(128):
        address,data,write = rng.randrange(8),rng.randrange(1024),rng.randrange(2)
        statements.append(f'Add=3\'d{address}; D=10\'d{data}; WE={write}; #1;')
        if old_q is not None: expect('Q',old_q)
        result = memory[address]
        step(); expect('Q',result)
        if write: memory[address]=data
        expect(f'File.mem[{address}]',memory[address])
        old_q=result
    statements.append('WE=0;')
    # Exact comparisons: all possible patterns and inputs.
    for pattern in range(16):
        statements.append(f'Load=1; UserPattern=4\'d{pattern}; ValidIn=0;')
        step()
        statements.append('Load=0; ValidIn=1;')
        for incoming in range(16):
            statements.append(f'InPattern=4\'d{incoming}; #1;')
            expect('Judge',int(matches(incoming,pattern)),1)
        statements += [f'InPattern=4\'d{pattern}; UserPattern=4\'d{15-pattern}; #1;']
        expect('Judge',1,1)
        statements.append('ValidIn=0; #1;'); expect('Judge',0,1)
    # All 4096 binary mask/pattern/input combinations, including mask=0.
    for mask in range(16):
        for pattern in range(16):
            statements.append(f'Load=1; UserPattern=4\'d{pattern}; Mask=4\'d{mask}; ValidIn=0;')
            step()
            statements.append('Load=0; ValidIn=1;')
            for incoming in range(16):
                statements.append(f'InPattern=4\'d{incoming}; #1;')
                expect('Match',int(matches(incoming,pattern,mask)),1)
            statements += [f'InPattern=4\'d{pattern}; UserPattern=4\'d{15-pattern}; Mask=0; #1;']
            expect('Match',1,1)
            statements.append('ValidIn=0; #1;'); expect('Match',0,1)
    # Count and last position check after every accepted or rejected item.
    for frame, pattern in enumerate([9,0,15]):
        statements.append(f'Reset=1; #1; CLoad=0; CValid=0; PValid=0;')
        step()
        statements.append(f'Reset=0; CLoad=1; CPattern=4\'d{pattern}; CData=4\'d{pattern}; CValid=1;')
        step(); expect('Count.U1.mem[4]',0)
        statements.append('CLoad=0;')
        count,index,last = 0,0,0
        # First frame uses all matching data, so count reaches the largest legal 1022.
        for item in range(1022):
            incoming = pattern if frame==0 else rng.randrange(16)
            pos_data = 9 if frame==0 else rng.randrange(16)
            if item%7==4:
                statements.append(f'CValid=0; PValid=0; CData=4\'d{incoming}; PData=4\'d{pos_data};')
                step(); expect('Count.U1.mem[4]',count); expect('Position.U1.mem[7]',last)
            statements.append(f'CValid=1; PValid=1; CData=4\'d{incoming}; PData=4\'d{pos_data};')
            count += int(incoming==pattern)
            index += 1
            if matches(pos_data,9,11): last=index
            step(); expect('Count.U1.mem[4]',count); expect('Position.U1.mem[7]',last)
        statements.append('CLoad=1; CValid=1;'); step(); expect('Count.U1.mem[4]',0)
        statements.append('CLoad=0; CValid=0; PValid=0;')
    declarations = '''`timescale 1ns/1ps
module tb;
reg Clk=0, Reset=0, En=0;
wire [9:0] CounterOut;
EnCounter Counter(CounterOut,Clk,Reset,En);
// The first vector must create an input event for the Verilog always @* block.
reg [3:0] RIn; reg [1:0] Rb; wire [3:0] Rout;
Rotator Rotate(Rout,RIn,Rb);
reg [9:0] D=0; reg WE=0; reg [2:0] Add=0; wire [9:0] Q;
RegisterFile File(Q,D,Clk,WE,Add);
reg [3:0] InPattern=0, UserPattern=0, Mask=0; reg Load=0, ValidIn=0;
wire Judge, Match;
PatternCheck Exact(Judge,InPattern,ValidIn,UserPattern,Load,Clk,Reset);
MaskPatternCheck Masked(Match,InPattern,ValidIn,Mask,UserPattern,Load,Clk,Reset);
reg [3:0] CData=0, CPattern=0, PData=0; reg CLoad=0,CValid=0,PValid=0;
PatternCount Count(CData,CValid,CPattern,CLoad,Clk,Reset);
PatternPosition Position(PData,PValid,Clk,Reset);
task tick; begin #4; Clk=1; #1; Clk=0; #5; end endtask
initial begin
'''
    return declarations+'\n'.join(statements)+f'\n$display("PASS 2022: {checks} independent HDL checks"); $finish(0);\nend\nendmodule\n',checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-only',action='store_true',help='Generate and audit golden values without claiming HDL simulation')
    args=parser.parse_args()
    bench,count=bench_text()
    assert matches(9,9,13) and matches(11,9,13) and not matches(13,9,13)
    assert matches(9,9,11) and matches(13,9,11) and not matches(11,9,11)
    if args.model_only: print(f'Golden stimulus generated: {count} checks; HDL simulation not run')
    else:
        print(simulate(['exams/2022/design.v'],bench))
        print(simulate(['exams/2022/design.v'],(ROOT/'exams/2022/tb.v').read_text(encoding='utf-8'),top='tb_2022'))


if __name__=='__main__': main()
