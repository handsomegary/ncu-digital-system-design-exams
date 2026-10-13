`timescale 1ns/1ps

// Q1: exact next-state/output equations, independent of clock/reset convention.
module q1_next(
    input wire A, B, x, y,
    output wire DA, DB, z
);
    assign DA = (~x & B) | (x & y);
    assign DB = ~x & A;
    assign z = A & B;
endmodule

// Optional executable illustration: rising clock edge, asynchronous active-high
// reset to 00. Reset was not specified by the paper's equations.
module q1_seq(
    input wire clk, reset, x, y,
    output reg A, B,
    output wire z
);
    wire DA, DB;
    q1_next logic_block(.A(A), .B(B), .x(x), .y(y),
                        .DA(DA), .DB(DB), .z(z));
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            A <= 1'b0;
            B <= 1'b0;
        end else begin
            A <= DA;
            B <= DB;
        end
    end
endmodule

// Q2: minimized equations derived from the eight graph edges.
module q2_next(
    input wire A, B, x,
    output wire DA, DB, z
);
    assign DA = (~A & ~x) | (A & x);
    assign DB = (~A & B) | (A & ~B);
    assign z = ~A & B;
endmodule

module q2_seq(
    input wire clk, reset, x,
    output reg A, B,
    output wire z
);
    wire DA, DB;
    q2_next logic_block(.A(A), .B(B), .x(x), .DA(DA), .DB(DB), .z(z));
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            A <= 1'b0;
            B <= 1'b0;
        end else begin
            A <= DA;
            B <= DB;
        end
    end
endmodule
