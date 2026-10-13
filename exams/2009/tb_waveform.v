`timescale 1ns/1ps

module tb_waveform;
    reg clk, rst, Sel1, Sel2, Sel3, LorR;
    reg [1:0] Mode;
    reg [15:0] MyInput;
    wire [15:0] MyOutput;
    MyDesign dut(.Sel1(Sel1), .Sel2(Sel2), .Sel3(Sel3), .Mode(Mode),
                 .LorR(LorR), .MyInput(MyInput), .clk(clk), .rst(rst),
                 .MyOutput(MyOutput));

    always #10 clk = ~clk;

    initial begin
        clk = 1;
        rst = 0;
        Sel1 = 0;
        Sel2 = 1;
        Sel3 = 1;
        LorR = 0;
        Mode = 2'b00;
        MyInput = 16'h001a;
        #1 rst = 1;
        // Inputs change at the drawn 20 ns boundaries in the NBA region.
        // DFFs therefore sample the old, stable interval without an active race.
        #19 Sel1 <= 1; MyInput <= 16'h00ea;
        #20 Sel2 <= 0; Sel3 <= 0; Mode <= 2'b01; MyInput <= 16'h0055;
        #20 Sel1 <= 0; LorR <= 1; Mode <= 2'b10; MyInput <= 16'h008c;
        #20 Mode <= 2'b11; MyInput <= 16'h00ff;
        #24 $finish(0);
    end

    task check;
        input [15:0] expected_x, expected_y, expected_output;
        begin
            if (dut.x !== expected_x || dut.y !== expected_y ||
                MyOutput !== expected_output)
                $fatal(1, "waveform mismatch at %0t", $time);
            $display("t=%0d X=%04h Y=%04h out=%04h", $time, dut.x, dut.y, MyOutput);
        end
    endtask

    initial begin
        #2 check(16'h0000, 16'h0000, 16'h000d);
        #20 check(16'h000d, 16'h0000, 16'h007b);
        #20 check(16'h000d, 16'h0000, 16'h7fd5);
        #20 check(16'h000d, 16'h7fd5, 16'hffac);
        #20 check(16'hffac, 16'hffac, 16'hff56);
        #20 check(16'hff56, 16'hff56, 16'hfeaa);
        $display("PASS waveform rows=6");
    end
endmodule
