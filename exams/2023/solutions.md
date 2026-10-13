# 2023 期末考：七題詳解

[完整重寫題目與介面](questions.md)。以下逐題解釋邏輯與時序，最後包含全部 RTL 與小型 testbench；測試刺激由 Python 即時產生，不在 repo 保存模擬產物。

## Q1：以 mux 表達旋轉

三個 8-bit word 是三個整體，沒有旋轉 word 內部的 bits。由對照表直接得到 Out1 的三個候選 In1/In2/In3；Out2 為 In2/In3/In1；Out3 為 In3/In1/In2。`always @*` 與完整 case 讓輸入改變後立即更新。每條路徑都賦值，所以不產生 latch。補定 mode=3 或 unknown 時輸出零。

## Q2：非阻塞賦值實現同步 read-first

宣告 `reg [7:0] MemArray [0:1023]`。同一個 `posedge Clk` 先計算三個讀取 RHS，再安排 write。所有 `<=` 都在 NBA 階段更新，因此若 RAA=WA 且 WE=1，QA 收到的是舊 MemArray 值，而記憶體在同拍末更新成 D。WE=0 不更新記憶體，三個讀埠仍會正常讀取。地址改變但沒有上升緣時，QA/QB/QC 維持原同步輸出。

沒有 reset 或預填資料，故真實有效內容由 testbench 或上層的寫入流程提供。測試會初始化資料再驗證讀寫碰撞及 WE=0，沒有用一份硬編的讀取答案取代 memory。

## Q3：X 線性掃描、Y 以三列為組

reset 使用 `always @(posedge Clk or posedge Reset)`，立即清零。第一次啟用時從零進入 (1,1)。其後若 X<COL，僅增加 X；若 X=COL，X 回 1，Y 增 3 或循環回 1。沒有 En 分支的 assignment 就自然保持原暫存器值。

判斷下一個 Y 是否超過 ROW，再決定跳回 1，使任何合法 ROW 都可循環。不能只檢查 `Y==ROW`，否則 ROW=6 的序列 1、4、7……永遠碰不到 6。加法以足夠寬度比較，不能先在 6-bit 中溢位再判斷。

## Q4：比較模式與四態有效性

`^{In1,In2,In3}` 是全部 24 bits 的 reduction XOR：只要存在 X 或 Z，結果就是 X。用 case inequality `!== 1'bx` 判斷全部資料已知；不能以一般 `== 8'bz` 比較，它遇到未知值會得到未知，而非可靠的 boolean。

mode 0 的比較依序測試 In1 是否不小於其他兩筆，否則測 In2>=In3，否則取 In3。原題的唯一最大值會正確選中；補充的相等輸入依序選最小 position。mode 1 在全部輸入已知時直接回 In2／position 2。MaxValue、MaxPos、Valid 每條路徑都有預設，不會因之前一次有效結果留下 Valid=1。

## Q5：列內比較，再比較三列結果

第一層三個 RowComparator：

- Pattern 0：三列均比較全列。
- Pattern 1：第一、第三列只取中心，第二列比較全列。
- Pattern 2：三列均只取中心。

第四個 RowComparator 比較三個列結果，選出的 position 就是 MaxRow，再依所選列取對應列內 position 作為 MaxCol。Valid 是三個列 Valid、最後一層 Valid 與合法 Pattern 的 conjunction。這樣每一個模式都實際使用題目指定的 RowComparator，且遇到 X/Z 的 row 不會參加有效最大值計算。

先決定各列唯一候選，再選列間最大值，可證明結果是整個指定 pattern 的最大值。相等時第一層偏向小 column、第二層偏向小 row，形成穩定 row-major tie rule。

## Q6：資料與 valid 同拍對齊

三個線性位址是：

```text
Top: (YIndex-1)*COL + Xindex-1
Mid:  YIndex   *COL + Xindex-1
Bot: (YIndex+1)*COL + Xindex-1
```

先以寬 integer 算位址，再檢查範圍，最後才送入 10-bit 位址埠。若先把地址截成 10 bits，再檢查就無法發現 1024 被折回 0 的錯誤。

此模組例化 RegisterFile U6_1，三個同步讀埠分別連接 Top/Mid/Bot。依題意資料已由 testbench 放入，DataFetch 不增加寫入 port，將 WE 固定為 0。Valid 在同一個上升緣保存該次請求的合法性，因而與三個讀取結果一起更新。reset 立即把 Valid 拉低；無效時資料輸出 X，不讓後續元件誤把它當成有效零值。

同時檢查 En、`1<=Xindex<=COL`、`1<=YIndex`、`YIndex+2<=ROW`、三個位址在 0..1023。這涵蓋初始零索引、末端不足三列及模板預設容量衝突。

## Q7：把同步 RF 輸出納入三級 shift register

每列最新的一格就是 DataFetch 的同步 RF output；另保存 previous、oldest 兩格，整列總共恰有三個同步儲存級。若再加三個 history FF，會比原圖多一拍。

令 E1 為 Reset 解除後第一次 En=1 的上升緣。時序如下：

| 緣 | Counter 更新後 | RF 最新資料 | previous | oldest | 可用視窗 |
|---|---|---|---|---|---|
| E1 | x=1 | 舊 x=0 無效 | 無效 | 無效 | 無 |
| E2 | x=2 | col 1 | 無效 | 無效 | 無 |
| E3 | x=3 | col 2 | col 1 | 無效 | 無 |
| E4 | x=4 | col 3 | col 2 | col 1 | columns 1..3 |

不同 always block 的非阻塞賦值是關鍵：E4 的 RF 讀舊 Counter x=3，而 history 保存舊 RF col 2，oldest 保存舊 previous col 1。三個資料列都按同一規則前進，正好構成 3×3。

另同步保存每個 RF 結果的 (x,y)，history 也帶著座標。只有座標依序為 `(x-2,y)`、`(x-1,y)`、`(x,y)` 時才承認完整視窗；因此換列組時不會用上一組最後兩欄拼出假的結果。暫停 En 時可排空上一拍已收到的 RF 資料到 history，恢復後只接受一次目前 column，不重複移位。

由 PatternComparator3x3 得到局部 row／col，再轉絕對影像座標：

```text
MaxXPos = 最新讀入 x - 3 + MaxCol
MaxYPos = 此列組起始 y - 1 + MaxRow
```

Pattern 是當下的組合輸入，沒有額外延遲；每個完整視窗各自輸出其 pattern 最大值。原圖 E4 的中心直條是 168、39、15，故最大 168 在 (2,1)；E5 改用全九格、視窗 columns 2..4，故最大 211 在 (4,3)。輸出座標使用 7/6 bits，能表示原圖的 x=4 與完整參數範圍。

## 驗證方法

`tests/test_2023.py` 生成固定 seed 的小型刺激檔，Icarus 只編譯與模擬真正 RTL。Python oracle 分別以 list 旋轉、word memory、坐標遞推、明確候選格枚舉及時間序列視窗模型計算答案；模擬的每個結果逐項比較。

涵蓋：三個合法旋轉模式及 invalid mode、兩個列模式與相等值、全部 pattern、每個 bit 的 X/Z、同步三讀一寫與 read-first、非同步 reset、enable 保持、首 valid 第四緣、Pattern 即時變更、row 邊界、pause/resume、局部最大值下降的情況、partial row、1023/1024 位址邊界。刺激、執行檔和 stdout capture 在 TemporaryDirectory 中，沒有 VCD、波形圖或永久 log。

`--model-only` 只核對 oracle 的圖例與邊界，不宣稱完成 RTL 模擬。正式測試必須安裝並實際執行 iverilog/vvp；CI 會跑此流程。

## 完整 RTL 與 testbench

<!-- SOLUTION_CODE_BEGIN -->

### `dsd2023.v`

```verilog
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
```

### `tb_2023.v`

```verilog
`timescale 1ns/1ps
`default_nettype none
module tb_2023;
    reg Clk;
    integer handle, status, index, j, bit_number, which;
    integer a, b, c, mode, v0, v1, v2, v3, v4, v5, v6, v7, v8;
    integer enable_value, reset_value, write_address, data_value, ra, rb, rc;
    reg [7:0] rotate_a, rotate_b, rotate_c;
    reg [1:0] rotate_mode;
    wire [7:0] rotate_o1, rotate_o2, rotate_o3;
    Rotator rotate(rotate_o3, rotate_o2, rotate_o1, rotate_c, rotate_b, rotate_a, rotate_mode);

    reg [7:0] row_a, row_b, row_c;
    reg row_mode;
    wire [7:0] row_value;
    wire [1:0] row_position;
    wire row_valid;
    RowComparator row(row_value, row_position, row_valid, row_a, row_b, row_c, row_mode);

    reg [71:0] pattern_data;
    reg [1:0] pattern_mode;
    wire [7:0] pattern_value;
    wire [1:0] pattern_row, pattern_column;
    wire pattern_valid;
    PatternComparator3x3 pattern(pattern_value, pattern_row, pattern_column, pattern_valid,
        pattern_data[7:0], pattern_data[15:8], pattern_data[23:16],
        pattern_data[31:24], pattern_data[39:32], pattern_data[47:40],
        pattern_data[55:48], pattern_data[63:56], pattern_data[71:64], pattern_mode);

    reg rf_we;
    reg [7:0] rf_data;
    reg [9:0] rf_wa, rf_ra, rf_rb, rf_rc;
    wire [7:0] rf_qa, rf_qb, rf_qc;
    RegisterFile rf(rf_qa, rf_qb, rf_qc, rf_data, Clk, rf_ra, rf_rb, rf_rc, rf_we, rf_wa);

    reg count_reset, count_enable;
    wire [6:0] count_x;
    wire [5:0] count_y;
    Count2D #(.COL(4), .ROW(7)) counter(count_x, count_y, Clk, count_reset, count_enable);

    reg fetch_reset, fetch_enable;
    reg [6:0] fetch_x;
    reg [5:0] fetch_y;
    wire fetch_valid, default_valid;
    wire [7:0] fetch_top, fetch_middle, fetch_bottom, default_top, default_middle, default_bottom;
    DataFetch #(.COL(4), .ROW(7)) fetch(fetch_valid, fetch_top, fetch_middle, fetch_bottom, fetch_x, fetch_y, fetch_enable, Clk, fetch_reset);
    DataFetch default_fetch(default_valid, default_top, default_middle, default_bottom, fetch_x, fetch_y, fetch_enable, Clk, fetch_reset);

    reg max_reset, max_enable;
    reg [1:0] max_pattern;
    wire [7:0] max_value;
    wire [6:0] max_x;
    wire [5:0] max_y;
    wire max_valid;
    MaxSearch2D #(.COL(4), .ROW(7)) maximum(max_value, max_x, max_y, max_valid, Clk, max_reset, max_enable, max_pattern);

    task tick;
        begin #5; Clk = 1; #1; end
    endtask
    task tock;
        begin #4; Clk = 0; #1; end
    endtask

    initial begin
        Clk = 0;
        rotate_a = 0; rotate_b = 0; rotate_c = 0; rotate_mode = 0;
        row_a = 0; row_b = 0; row_c = 0; row_mode = 0;
        pattern_data = 0; pattern_mode = 0;
        rf_we = 0; rf_data = 0; rf_wa = 0; rf_ra = 0; rf_rb = 0; rf_rc = 0;
        count_reset = 1; count_enable = 0;
        fetch_reset = 1; fetch_enable = 0; fetch_x = 0; fetch_y = 0;
        max_reset = 1; max_enable = 0; max_pattern = 2;
        $readmemh("memory.hex", rf.MemArray);
        $readmemh("memory.hex", fetch.U6_1.MemArray);
        $readmemh("memory.hex", default_fetch.U6_1.MemArray);
        $readmemh("memory.hex", maximum.U7_2.U6_1.MemArray);
        #1;

        handle = $fopen("rotator_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing rotator vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        while (status == 4) begin
            rotate_mode = mode; rotate_a = a; rotate_b = b; rotate_c = c;
            #1;
            $display("ROT %0d %0d %0d %0d", index, rotate_o1, rotate_o2, rotate_o3);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        end
        $fclose(handle);
        rotate_mode = 2'bx1; #1;
        $display("ROT_UNKNOWN %0d %0d %0d", rotate_o1, rotate_o2, rotate_o3);

        handle = $fopen("row_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing row vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        while (status == 4) begin
            row_mode = mode; row_a = a; row_b = b; row_c = c; #1;
            $display("ROW %0d %0d %0d %0d", index, row_value, row_position, row_valid);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d\n", mode, a, b, c);
        end
        $fclose(handle);
        index = 0;
        for (mode = 0; mode < 2; mode = mode + 1)
            for (which = 0; which < 3; which = which + 1)
                for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                    for (j = 0; j < 2; j = j + 1) begin
                        row_mode = mode; row_a = 93; row_b = 57; row_c = 11;
                        if (which == 0) row_a[bit_number] = j ? 1'bz : 1'bx;
                        if (which == 1) row_b[bit_number] = j ? 1'bz : 1'bx;
                        if (which == 2) row_c[bit_number] = j ? 1'bz : 1'bx;
                        #1; $display("ROW_UNKNOWN %0d %0d %0d %0d", index, row_value, row_position, row_valid);
                        index = index + 1;
                    end
        row_a = 1; row_b = 2; row_c = 3; row_mode = 1'bx; #1;
        $display("ROW_UNKNOWN %0d %0d %0d %0d", index, row_value, row_position, row_valid);

        handle = $fopen("pattern_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing pattern vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d %d %d %d %d %d %d\n", mode, v0, v1, v2, v3, v4, v5, v6, v7, v8);
        while (status == 10) begin
            pattern_mode = mode;
            pattern_data = {v8[7:0], v7[7:0], v6[7:0], v5[7:0], v4[7:0], v3[7:0], v2[7:0], v1[7:0], v0[7:0]};
            #1; $display("PAT %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d %d %d %d %d %d %d\n", mode, v0, v1, v2, v3, v4, v5, v6, v7, v8);
        end
        $fclose(handle);
        index = 0;
        for (mode = 0; mode < 3; mode = mode + 1)
            for (which = 0; which < 9; which = which + 1)
                for (j = 0; j < 2; j = j + 1) begin
                    pattern_mode = mode; pattern_data = {9{8'd57}};
                    pattern_data[8 * which + 3] = j ? 1'bz : 1'bx;
                    #1; $display("PAT_UNKNOWN %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);
                    index = index + 1;
                end
        pattern_mode = 2'bx0; pattern_data = {9{8'd1}}; #1;
        $display("PAT_UNKNOWN %0d %0d %0d %0d %0d", index, pattern_value, pattern_row, pattern_column, pattern_valid);

        handle = $fopen("rf_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing register file vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d %d %d %d\n", enable_value, write_address, data_value, ra, rb, rc);
        while (status == 6) begin
            rf_we = enable_value; rf_wa = write_address; rf_data = data_value;
            rf_ra = ra; rf_rb = rb; rf_rc = rc;
            tick; $display("RF %0d %0d %0d %0d", index, rf_qa, rf_qb, rf_qc); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d %d %d %d %d\n", enable_value, write_address, data_value, ra, rb, rc);
        end
        $fclose(handle); rf_we = 0;
        v0 = rf_qa; rf_ra = rf_ra + 1; #1;
        $display("RF_HOLD %0d %0d", v0, rf_qa);

        count_reset = 0; count_enable = 1; tick; tock; tick; tock;
        count_reset = 1; #1;
        $display("COUNT_ASYNC %0d %0d", count_x, count_y);
        count_reset = 0;
        handle = $fopen("count_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing counter vectors");
        index = 0;
        status = $fscanf(handle, "%d %d\n", reset_value, enable_value);
        while (status == 2) begin
            count_reset = reset_value; count_enable = enable_value;
            tick; $display("COUNT %0d %0d %0d", index, count_x, count_y); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d\n", reset_value, enable_value);
        end
        $fclose(handle); count_enable = 0;

        fetch_reset = 0;
        handle = $fopen("fetch_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing fetch vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d\n", ra, rb, enable_value);
        while (status == 3) begin
            fetch_x = ra; fetch_y = rb; fetch_enable = enable_value;
            tick;
            $display("FETCH %0d %0d %h %h %h", index, fetch_valid, fetch_top, fetch_middle, fetch_bottom);
            $display("DEFAULT_FETCH %0d %0d %h %h %h", index, default_valid, default_top, default_middle, default_bottom);
            tock; index = index + 1;
            status = $fscanf(handle, "%d %d %d\n", ra, rb, enable_value);
        end
        $fclose(handle);
        fetch_x = 7'hxx; fetch_y = 1; fetch_enable = 1;
        tick; $display("FETCH_UNKNOWN %0d", fetch_valid); tock;
        fetch_reset = 1; #1; $display("FETCH_ASYNC %0d", fetch_valid);
        fetch_enable = 0;

        handle = $fopen("max_vectors.txt", "r");
        if (handle == 0) $fatal(1, "Missing maximum search vectors");
        index = 0;
        status = $fscanf(handle, "%d %d %d\n", reset_value, enable_value, mode);
        while (status == 3) begin
            max_reset = reset_value; max_enable = enable_value; max_pattern = mode;
            tick; $display("MAX %0d %0d %0d %0d %0d", index, max_value, max_x, max_y, max_valid); tock;
            index = index + 1;
            status = $fscanf(handle, "%d %d %d\n", reset_value, enable_value, mode);
        end
        $fclose(handle);
        max_reset = 1; #1; $display("MAX_ASYNC %0d %0d %0d %0d", max_value, max_x, max_y, max_valid);
        maximum.U7_2.U6_1.MemArray[0] = 8'b000x0000;
        max_reset = 0; max_enable = 1; max_pattern = 2;
        for (j = 0; j < 4; j = j + 1) begin tick; tock; end
        $display("MAX_UNKNOWN %0d %0d %0d %0d", max_value, max_x, max_y, max_valid);
        $display("DONE");
        $finish;
    end
endmodule
`default_nettype wire
```

<!-- SOLUTION_CODE_END -->
