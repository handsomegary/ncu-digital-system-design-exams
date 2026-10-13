`timescale 1ns/1ps

module CheerUp(AndYou, IamFine, VeryGood, NotBad, Sel);
    output wire [1:0] AndYou;
    output reg [1:0] IamFine;
    input wire [1:0] VeryGood, NotBad;
    input wire Sel;
    assign AndYou = VeryGood | NotBad;
    always @* begin
        IamFine[0] = Sel ? VeryGood[0] : VeryGood[1];
        IamFine[1] = Sel ? NotBad[0] : NotBad[1];
    end
endmodule

module EnabledLatch(input wire ina, input wire en, output reg outsig);
    always @* begin
        if (en) outsig = ina;
    end
endmodule

module TriStateBuffer(input wire ina, input wire en, output wire outsig);
    assign outsig = en ? ina : 1'bz;
endmodule

// The source does not define selection polarity. We adopt the readable
// reference's convention: sel=1 selects ina, sel=0 selects inb.
module MUX21(input wire [15:0] ina, inb, input wire sel,
             output wire [15:0] out);
    assign out = sel ? ina : inb;
endmodule

// rst is asynchronous and active low. Sequential assignments are nonblocking.
module DFF16(output reg [15:0] Q, input wire [15:0] D,
             input wire clk, rst);
    always @(posedge clk or negedge rst) begin
        if (!rst) Q <= 16'h0000;
        else Q <= D;
    end
endmodule

module Shifter(output wire [15:0] ShOut, input wire [15:0] C,
               input wire LR);
    assign ShOut = LR ? {C[14:0], 1'b0} : {1'b0, C[15:1]};
endmodule

module ALU(output reg [15:0] ALUOut, input wire [15:0] A, B,
           input wire [1:0] CTR);
    always @* begin
        case (CTR)
            2'b00: ALUOut = A + B;
            2'b01: ALUOut = A - B;
            2'b10: ALUOut = A + 16'd1;
            2'b11: ALUOut = A - 16'd1;
            default: ALUOut = 16'hxxxx;
        endcase
    end
endmodule

module MyDesign(input wire Sel1, Sel2, Sel3,
                input wire [1:0] Mode,
                input wire LorR,
                input wire [15:0] MyInput,
                input wire clk, rst,
                output wire [15:0] MyOutput);
    wire [15:0] x, y, dx, dy, operand_a, alu_result;
    MUX21 load_x(.ina(x), .inb(MyOutput), .sel(Sel1), .out(dx));
    MUX21 load_y(.ina(y), .inb(MyOutput), .sel(Sel2), .out(dy));
    DFF16 register_x(.Q(x), .D(dx), .clk(clk), .rst(rst));
    DFF16 register_y(.Q(y), .D(dy), .clk(clk), .rst(rst));
    MUX21 choose_a(.ina(x), .inb(y), .sel(Sel3), .out(operand_a));
    ALU arithmetic(.ALUOut(alu_result), .A(operand_a), .B(MyInput), .CTR(Mode));
    Shifter shift_result(.ShOut(MyOutput), .C(alu_result), .LR(LorR));
endmodule
