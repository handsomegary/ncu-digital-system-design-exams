`timescale 1ns/1ps
// Small standalone example: compile with -s tb to choose this top module.
module tb;
    reg Clock = 0, Reset = 1, StartCal = 0, WEBPort = 0;
    reg [5:0] SizeM = 3;
    reg [9:0] DPortB = 0;
    reg [11:0] AddBPort = 0;
    wire [3:0] NegNo;
    wire NBlock;
    CalculateNegativeDBlock dut(.NegNo(NegNo), .NBlock(NBlock), .SizeM(SizeM),
        .StartCal(StartCal), .Clock(Clock), .Reset(Reset), .DPortB(DPortB),
        .AddBPort(AddBPort), .WEBPort(WEBPort));
    always #5 Clock = ~Clock;
    task write_word;
        input [11:0] address;
        input integer value;
        begin
            @(negedge Clock); AddBPort = address; DPortB = value; WEBPort = 1;
            @(posedge Clock); #1;
        end
    endtask
    integer cycle;
    initial begin
        #1;
        write_word(0, -512); write_word(1, -1); write_word(2, 0);
        write_word(3, 511); write_word(4, -5); write_word(5, 6);
        write_word(6, -7); write_word(7, 8); write_word(8, -9);
        @(negedge Clock); WEBPort = 0; Reset = 0; StartCal = 1;
        for (cycle = 0; cycle < 15; cycle = cycle + 1) begin
            @(posedge Clock); #1;
            if (cycle == 0 && (!NBlock || NegNo !== 4'd0))
                $fatal(1, "First block must begin with NegNo=0");
            if (cycle == 9 && (!NBlock || NegNo !== 4'd5))
                $fatal(1, "Final block must publish five negatives at completion");
            if (cycle >= 10 && (NBlock || NegNo !== 4'd5))
                $fatal(1, "Final result must hold without more block pulses");
        end
        $display("PASS 2024 example: five negative words in the 3x3 block");
        $finish;
    end
endmodule
