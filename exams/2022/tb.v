`timescale 1ns/1ps
// Small executable example; exhaustive independent checks are in tests/test_2022.py.
module tb_2022;
    reg Clk=0, Reset=0, Load=0, ValidIn=0;
    reg [3:0] InPattern=0, UserPattern=0;
    wire Judge;
    PatternCheck DUT(Judge,InPattern,ValidIn,UserPattern,Load,Clk,Reset);
    PatternCount Count(InPattern,ValidIn,UserPattern,Load,Clk,Reset);
    always #5 Clk=~Clk;
    initial begin
        #1; Reset=1;
        #5; Reset=0;
        @(negedge Clk); Load=1; UserPattern=3;
        @(negedge Clk); Load=0; ValidIn=1; InPattern=3;
        #1; if(Judge !== 1'b1) $fatal(1,"same-interval comparison failed");
        @(negedge Clk); if(Count.U1.mem[4] !== 10'd1) $fatal(1,"count must include first item");
        InPattern=4;
        @(negedge Clk); InPattern=3; ValidIn=0;
        @(negedge Clk); ValidIn=1;
        @(negedge Clk); ValidIn=0;
        if(Count.U1.mem[4] !== 10'd2) $fatal(1,"invalid input counted or final update lost");
        $display("PASS 2022 example: U1.mem[4]=2");
        $finish;
    end
endmodule
