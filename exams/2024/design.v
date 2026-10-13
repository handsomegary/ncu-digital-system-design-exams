`timescale 1ns/1ps
// 2024 final exam. Original DSD.v was not supplied: explicit widths below.
// Start/StartCal launches once after Reset; Reset is required for another run.
module Decrementer(DecOut, Clock, Reset);
    output reg [4:0] DecOut;
    input Clock, Reset;
    always @(posedge Clock or posedge Reset)
        if (Reset) DecOut <= 5'd0;
        else DecOut <= DecOut - 5'd1;
endmodule

module Counting #(parameter WIDTH = 5)(CountOut, IorD, Enable, Clock, Reset);
    output reg [WIDTH-1:0] CountOut;
    input IorD, Enable, Clock, Reset;
    always @(posedge Clock or posedge Reset)
        if (Reset) CountOut <= {WIDTH{1'b0}};
        else if (Enable) begin
            if (IorD) CountOut <= CountOut + 1'b1;
            else CountOut <= CountOut - 1'b1;
        end
endmodule

module GenerateUpDownCtr(UpDown, Start, Clock, Reset);
    output UpDown;
    input Start, Clock, Reset;
    reg running;
    reg [3:0] phase;
    // Nine cells per block: right, left, right for three cells each.
    // Adjacent blocks finish/start with rightward rows, so high lasts six clocks.
    assign UpDown = running && ((phase < 4'd3) || (phase >= 4'd6));
    always @(posedge Clock or posedge Reset)
        if (Reset) begin
            running <= 1'b0;
            phase <= 4'd0;
        end else if (!running) begin
            if (Start) begin
                running <= 1'b1;
                phase <= 4'd0;
            end
        end else if (phase == 4'd8) phase <= 4'd0;
        else phase <= phase + 1'b1;
endmodule

module GenerateRCIndex(NewBlock, RIndx, CIndx, Start, Clock, Reset);
    output NewBlock;
    output reg [5:0] RIndx;
    output [5:0] CIndx;
    input Start, Clock, Reset;
    reg running;
    reg [3:0] phase;
    wire UpDown;
    wire launch = Start && !running;
    wire count_enable = launch || (running && phase != 4'd2 && phase != 4'd5);
    wire count_direction = launch || UpDown;
    Counting #(.WIDTH(6)) UQ2(.CountOut(CIndx), .IorD(count_direction),
        .Enable(count_enable), .Clock(Clock), .Reset(Reset));
    GenerateUpDownCtr UQ3(.UpDown(UpDown), .Start(Start),
        .Clock(Clock), .Reset(Reset));
    assign NewBlock = running && phase == 4'd0;
    always @(posedge Clock or posedge Reset)
        if (Reset) begin
            running <= 1'b0;
            phase <= 4'd0;
            RIndx <= 6'd0;
        end else if (!running) begin
            if (Start) begin
                running <= 1'b1;
                phase <= 4'd0;
                RIndx <= 6'd1;
            end
        end else begin
            if (phase == 4'd2 || phase == 4'd5 || phase == 4'd8)
                RIndx <= RIndx + 1'b1;
            if (phase == 4'd8) phase <= 4'd0;
            else phase <= phase + 1'b1;
        end
endmodule

module RFTwoPort(QA, AddA, DB, AddB, WEB, Clock);
    output reg [9:0] QA;
    input [11:0] AddA, AddB;
    input [9:0] DB;
    input WEB, Clock;
    reg [9:0] MemArray [0:4095];
    // Synchronous read-first: a same-address write returns the OLD word.
    // Memory is intentionally not reset; load it through port B before use.
    always @(posedge Clock) begin
        QA <= MemArray[AddA];
        if (WEB) MemArray[AddB] <= DB;
    end
endmodule

module CalculateNegativeDBlock(NegNo, NBlock, SizeM, StartCal, Clock, Reset,
                              DPortB, AddBPort, WEBPort);
    output [3:0] NegNo;
    output NBlock;
    input [5:0] SizeM;
    input StartCal, Clock, Reset;
    input [9:0] DPortB;
    input [11:0] AddBPort;
    input WEBPort;
    wire [5:0] RIndx, CIndx;
    wire [9:0] QA;
    reg started, legal_size, index_done;
    reg [5:0] matrix_size;
    reg qa_valid, qa_last, qa_final;
    reg [3:0] negative_count, saved_negative;
    integer linear_address;
    reg read_valid;
    reg [11:0] read_address;
    wire index_reset = Reset || index_done;
    wire [3:0] complete_count = negative_count + {3'b000, QA[9]};
    // QA and its last tag update together. At NewBlock, the accumulator has
    // already consumed the preceding eight words; include this ninth word
    // combinationally, then save the same total on the following rising edge.
    assign NegNo = (NBlock && qa_valid && qa_last) ? complete_count : saved_negative;
    GenerateRCIndex UQ4(.NewBlock(NBlock), .RIndx(RIndx), .CIndx(CIndx),
        .Start(StartCal), .Clock(Clock), .Reset(index_reset));
    RFTwoPort UQ5(.QA(QA), .AddA(read_address), .DB(DPortB),
        .AddB(AddBPort), .WEB(WEBPort), .Clock(Clock));
    // Calculate in integer width before truncating. Never issue an out-of-range
    // request. This also rejects the 6-bit wrap to zero after row/column 63.
    always @* begin
        linear_address = 0;
        read_valid = 1'b0;
        read_address = 12'd0;
        if (started && legal_size && !index_done &&
            RIndx >= 1 && RIndx <= matrix_size &&
            CIndx >= 1 && CIndx <= matrix_size) begin
            linear_address = (RIndx - 1) * matrix_size + CIndx - 1;
            if (linear_address >= 0 && linear_address < 4096) begin
                read_valid = 1'b1;
                read_address = linear_address;
            end
        end
    end
    always @(posedge Clock or posedge Reset)
        if (Reset) begin
            started <= 1'b0;
            legal_size <= 1'b0;
            matrix_size <= 6'd0;
            index_done <= 1'b0;
            qa_valid <= 1'b0;
            qa_last <= 1'b0;
            qa_final <= 1'b0;
            negative_count <= 4'd0;
            saved_negative <= 4'd0;
        end else begin
            if (StartCal && !started) begin
                started <= 1'b1;
                matrix_size <= SizeM;
                legal_size <= SizeM >= 6'd3 && (SizeM % 3) == 0;
                if (!(SizeM >= 6'd3 && (SizeM % 3) == 0)) index_done <= 1'b1;
            end
            // These tags describe the SAME address sampled by UQ5 this edge.
            qa_valid <= read_valid;
            qa_last <= read_valid && (RIndx % 3) == 0 && CIndx == RIndx;
            qa_final <= read_valid && RIndx == matrix_size && CIndx == matrix_size;
            // Nonblocking assignments read the PREVIOUS QA and previous tags.
            if (qa_valid) begin
                if (qa_last) begin
                    saved_negative <= complete_count;
                    negative_count <= 4'd0;
                    if (qa_final) index_done <= 1'b1;
                end else negative_count <= complete_count;
            end
        end
endmodule
