`timescale 1ns/1ps
// 2022 Q1: high-active asynchronous reset, enabled modulo-1023 counter.
module EnCounter(CounterOut, Clk, Reset, En);
    output reg [9:0] CounterOut;
    input Clk, Reset, En;
    always @(posedge Clk or posedge Reset) begin
        if (Reset) CounterOut <= 10'd0;
        else if (En) begin
            if (CounterOut == 10'd1023) CounterOut <= 10'd1;
            else CounterOut <= CounterOut + 10'd1;
        end
    end
endmodule

// Q2: keep the port spelling Rout from the printed module declaration.
module Rotator(Rout, RIn, Rb);
    output reg [3:0] Rout;
    input [3:0] RIn;
    input [1:0] Rb;
    always @(*) begin
        case (Rb)
            2'd0: Rout = RIn;
            2'd1: Rout = {RIn[2:0], RIn[3]};
            2'd2: Rout = {RIn[1:0], RIn[3:2]};
            2'd3: Rout = {RIn[0], RIn[3:1]};
            default: Rout = 4'bxxxx;
        endcase
    end
endmodule

// Q3: synchronous read-first behavior on a read/write collision.
module RegisterFile(Q, D, Clk, WE, Add);
    output reg [9:0] Q;
    input [9:0] D;
    input Clk, WE;
    input [2:0] Add;
    reg [9:0] mem [0:7];
    always @(posedge Clk) begin
        Q <= mem[Add];
        if (WE) mem[Add] <= D;
    end
endmodule

// Q4: register the user pattern, compare the current input without another cycle delay.
module PatternCheck(Judge, InPattern, ValidIn, UserPattern, Load, Clk, Reset);
    output Judge;
    input [3:0] InPattern, UserPattern;
    input ValidIn, Load, Clk, Reset;
    reg [3:0] pattern;
    reg loaded;
    always @(posedge Clk or posedge Reset) begin
        if (Reset) begin pattern <= 4'd0; loaded <= 1'b0; end
        else if (Load) begin pattern <= UserPattern; loaded <= 1'b1; end
    end
    assign Judge = !Reset && !Load && loaded && ValidIn && (InPattern == pattern);
endmodule

// Q5: a mask bit of 1 requires equality; a mask bit of 0 ignores that bit.
module MaskPatternCheck(Match, InPattern, ValidIn, Mask, UserPattern, Load, Clk, Reset);
    output Match;
    input [3:0] InPattern, Mask, UserPattern;
    input ValidIn, Load, Clk, Reset;
    reg [3:0] pattern, mask;
    reg loaded;
    always @(posedge Clk or posedge Reset) begin
        if (Reset) begin pattern <= 4'd0; mask <= 4'd0; loaded <= 1'b0; end
        else if (Load) begin pattern <= UserPattern; mask <= Mask; loaded <= 1'b1; end
    end
    assign Match = !Reset && !Load && loaded && ValidIn && (((InPattern ^ pattern) & mask) == 4'd0);
endmodule

// Q6: no output port was supplied; the specified result is U1.mem[4].
module PatternCount(InPattern, ValidIn, UserPattern, Load, Clk, Reset);
    input [3:0] InPattern, UserPattern;
    input ValidIn, Load, Clk, Reset;
    reg [9:0] count;
    wire match;
    wire [9:0] readback;
    wire [9:0] next_count = count + 10'd1;
    PatternCheck U2(.Judge(match), .InPattern(InPattern), .ValidIn(ValidIn),
                    .UserPattern(UserPattern), .Load(Load), .Clk(Clk), .Reset(Reset));
    always @(posedge Clk or posedge Reset) begin
        if (Reset) count <= 10'd0;
        else if (Load) count <= 10'd0;
        else if (match) count <= next_count;
    end
    RegisterFile U1(.Q(readback), .D((Reset || Load) ? 10'd0 : next_count),
                    .Clk(Clk), .WE(Reset || Load || match), .Add(3'd4));
endmodule

// Q7: count only valid items; save the last rank of a 1?01 item to U1.mem[7].
module PatternPosition(InPattern, ValidIn, Clk, Reset);
    input [3:0] InPattern;
    input ValidIn, Clk, Reset;
    reg [9:0] index;
    wire [9:0] readback;
    wire [9:0] next_index = index + 10'd1;
    wire match = (((InPattern ^ 4'b1001) & 4'b1011) == 4'd0);
    always @(posedge Clk or posedge Reset) begin
        if (Reset) index <= 10'd0;
        else if (ValidIn) index <= next_index;
    end
    RegisterFile U1(.Q(readback), .D(Reset ? 10'd0 : next_index), .Clk(Clk),
                    .WE(Reset || (ValidIn && match)), .Add(3'd7));
endmodule
