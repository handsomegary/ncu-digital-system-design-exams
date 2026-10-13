`timescale 1ns/1ps
`default_nettype none

module Rotator(Out3, Out2, Out1, In3, In2, In1, rMode);
    input [7:0] In3, In2, In1;
    input [1:0] rMode;
    output reg [7:0] Out3, Out2, Out1;
    always @* begin
        Out1 = 0; Out2 = 0; Out3 = 0;
        case (rMode)
            2'd0: begin Out1 = In1; Out2 = In2; Out3 = In3; end
            2'd1: begin Out1 = In2; Out2 = In3; Out3 = In1; end
            2'd2: begin Out1 = In3; Out2 = In1; Out3 = In2; end
            default: begin Out1 = 0; Out2 = 0; Out3 = 0; end
        endcase
    end
endmodule

module RegisterFile(QA, QB, QC, D, Clk, RAA, RBA, RCA, WE, WA);
    output reg [7:0] QA, QB, QC;
    input [7:0] D;
    input Clk, WE;
    input [9:0] RAA, RBA, RCA, WA;
    reg [7:0] MemArray [0:1023];
    always @(posedge Clk) begin
        QA <= MemArray[RAA];
        QB <= MemArray[RBA];
        QC <= MemArray[RCA];
        if (WE) MemArray[WA] <= D;
    end
endmodule

module Count2D(XIndex, YIndex, Clk, Reset, En);
    parameter COL = 50;
    parameter ROW = 25;
    output reg [6:0] XIndex;
    output reg [5:0] YIndex;
    input Clk, Reset, En;
    always @(posedge Clk or posedge Reset) begin
        if (Reset) begin XIndex <= 0; YIndex <= 0; end
        else if (En) begin
            if (XIndex == 0) begin XIndex <= 1; YIndex <= 1; end
            else if (XIndex == COL) begin
                XIndex <= 1;
                if (YIndex + 3 > ROW) YIndex <= 1;
                else YIndex <= YIndex + 3;
            end else XIndex <= XIndex + 1;
        end
    end
endmodule

module RowComparator(MaxValue, MaxPos, Valid, In1, In2, In3, iMode);
    input [7:0] In1, In2, In3;
    input iMode;
    output reg [7:0] MaxValue;
    output reg [1:0] MaxPos;
    output reg Valid;
    always @* begin
        MaxValue = 0; MaxPos = 0; Valid = 0;
        // Reduction XOR becomes X when any input bit is X or Z.
        if ((^{In1, In2, In3}) !== 1'bx) begin
            case (iMode)
                1'b0: begin
                    Valid = 1;
                    if (In1 >= In2 && In1 >= In3) begin MaxValue = In1; MaxPos = 1; end
                    else if (In2 >= In3) begin MaxValue = In2; MaxPos = 2; end
                    else begin MaxValue = In3; MaxPos = 3; end
                end
                1'b1: begin MaxValue = In2; MaxPos = 2; Valid = 1; end
                default: begin MaxValue = 0; MaxPos = 0; Valid = 0; end
            endcase
        end
    end
endmodule

module PatternComparator3x3(MaxValue, MaxRow, MaxCol, Valid,
    In1_1, In2_1, In3_1, In1_2, In2_2, In3_2, In1_3, In2_3, In3_3, Pattern);
    input [7:0] In1_1, In2_1, In3_1, In1_2, In2_2, In3_2, In1_3, In2_3, In3_3;
    input [1:0] Pattern;
    output reg [7:0] MaxValue;
    output reg [1:0] MaxRow, MaxCol;
    output reg Valid;
    reg top_mode, middle_mode, bottom_mode, pattern_ok;
    wire [7:0] top_value, middle_value, bottom_value, selected_value;
    wire [1:0] top_column, middle_column, bottom_column, selected_row;
    wire top_valid, middle_valid, bottom_valid, selected_valid;
    always @* begin
        top_mode = 0; middle_mode = 0; bottom_mode = 0; pattern_ok = 1;
        case (Pattern)
            2'd0: begin top_mode = 0; middle_mode = 0; bottom_mode = 0; end
            2'd1: begin top_mode = 1; middle_mode = 0; bottom_mode = 1; end
            2'd2: begin top_mode = 1; middle_mode = 1; bottom_mode = 1; end
            default: pattern_ok = 0;
        endcase
    end
    RowComparator top(top_value, top_column, top_valid, In1_1, In2_1, In3_1, top_mode);
    RowComparator middle(middle_value, middle_column, middle_valid, In1_2, In2_2, In3_2, middle_mode);
    RowComparator bottom(bottom_value, bottom_column, bottom_valid, In1_3, In2_3, In3_3, bottom_mode);
    RowComparator rows(selected_value, selected_row, selected_valid, top_value, middle_value, bottom_value, 1'b0);
    always @* begin
        MaxValue = 0; MaxRow = 0; MaxCol = 0; Valid = 0;
        if (pattern_ok && top_valid && middle_valid && bottom_valid && selected_valid) begin
            MaxValue = selected_value; MaxRow = selected_row; Valid = 1;
            case (selected_row)
                2'd1: MaxCol = top_column;
                2'd2: MaxCol = middle_column;
                2'd3: MaxCol = bottom_column;
                default: begin MaxValue = 0; MaxRow = 0; MaxCol = 0; Valid = 0; end
            endcase
        end
    end
endmodule

module DataFetch(Valid, TopData, MidData, BotData, Xindex, YIndex, En, Clk, Reset);
    parameter COL = 50;
    parameter ROW = 25;
    output reg Valid;
    output [7:0] TopData, MidData, BotData;
    input [6:0] Xindex;
    input [5:0] YIndex;
    input En, Clk, Reset;
    reg [9:0] top_address, middle_address, bottom_address;
    reg request_ok;
    integer wide_top, wide_middle, wide_bottom;
    wire [7:0] qa, qb, qc;
    always @* begin
        top_address = 0; middle_address = 0; bottom_address = 0; request_ok = 0;
        wide_top = 0; wide_middle = 0; wide_bottom = 0;
        if (En && Xindex >= 1 && Xindex <= COL && YIndex >= 1 && YIndex + 2 <= ROW) begin
            wide_top = (YIndex - 1) * COL + Xindex - 1;
            wide_middle = YIndex * COL + Xindex - 1;
            wide_bottom = (YIndex + 1) * COL + Xindex - 1;
            if (wide_top >= 0 && wide_bottom < 1024) begin
                top_address = wide_top;
                middle_address = wide_middle;
                bottom_address = wide_bottom;
                request_ok = 1;
            end
        end
    end
    RegisterFile U6_1(qa, qb, qc, 8'd0, Clk, top_address, middle_address, bottom_address, 1'b0, 10'd0);
    always @(posedge Clk or posedge Reset) begin
        if (Reset) Valid <= 0;
        else Valid <= request_ok;
    end
    // Values are intentionally unspecified while Valid is low.
    assign TopData = Valid ? qa : 8'hxx;
    assign MidData = Valid ? qb : 8'hxx;
    assign BotData = Valid ? qc : 8'hxx;
endmodule

module MaxSearch2D(MaxValue, MaxXPos, MaxYPos, MaxValid, Clk, Reset, En, Pattern);
    parameter COL = 50;
    parameter ROW = 25;
    output [7:0] MaxValue;
    output [6:0] MaxXPos;
    output [5:0] MaxYPos;
    output MaxValid;
    input Clk, Reset, En;
    input [1:0] Pattern;
    wire [6:0] counter_x;
    wire [5:0] counter_y;
    wire fetch_valid;
    wire [7:0] top_data, middle_data, bottom_data;
    reg [7:0] top_previous, top_oldest, middle_previous, middle_oldest, bottom_previous, bottom_oldest;
    reg previous_valid, oldest_valid;
    reg [6:0] fetch_x, previous_x, oldest_x;
    reg [5:0] fetch_y, previous_y, oldest_y;
    wire [7:0] window_value;
    wire [1:0] window_row, window_column;
    wire window_valid;
    Count2D #(.COL(COL), .ROW(ROW)) U7_3(counter_x, counter_y, Clk, Reset, En);
    DataFetch #(.COL(COL), .ROW(ROW)) U7_2(fetch_valid, top_data, middle_data, bottom_data, counter_x, counter_y, En, Clk, Reset);
    // The synchronous RF output is the newest of the three shift-register stages.
    always @(posedge Clk or posedge Reset) begin
        if (Reset) begin
            top_previous <= 0; top_oldest <= 0; middle_previous <= 0; middle_oldest <= 0; bottom_previous <= 0; bottom_oldest <= 0;
            previous_valid <= 0; oldest_valid <= 0;
            fetch_x <= 0; previous_x <= 0; oldest_x <= 0;
            fetch_y <= 0; previous_y <= 0; oldest_y <= 0;
        end else begin
            fetch_x <= counter_x; fetch_y <= counter_y;
            if (fetch_valid) begin
                top_oldest <= top_previous; top_previous <= top_data;
                middle_oldest <= middle_previous; middle_previous <= middle_data;
                bottom_oldest <= bottom_previous; bottom_previous <= bottom_data;
                oldest_valid <= previous_valid; previous_valid <= 1;
                oldest_x <= previous_x; previous_x <= fetch_x;
                oldest_y <= previous_y; previous_y <= fetch_y;
            end
        end
    end
    PatternComparator3x3 U7_1(window_value, window_row, window_column, window_valid,
        top_oldest, top_previous, top_data,
        middle_oldest, middle_previous, middle_data,
        bottom_oldest, bottom_previous, bottom_data, Pattern);
    assign MaxValid = !Reset && En && fetch_valid && previous_valid && oldest_valid && window_valid
        && fetch_x >= 3 && previous_x + 1 == fetch_x && oldest_x + 2 == fetch_x
        && previous_y == fetch_y && oldest_y == fetch_y;
    assign MaxValue = MaxValid ? window_value : 8'd0;
    assign MaxXPos = MaxValid ? fetch_x - 3 + window_column : 7'd0;
    assign MaxYPos = MaxValid ? fetch_y - 1 + window_row : 6'd0;
endmodule

`default_nettype wire
