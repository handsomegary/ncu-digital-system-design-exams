# 2024 期末考：六題詳解

[完整題目與時序](questions.md)。以下解答保留題目的 module、port 與指定 instance 名稱 `UQ2`、`UQ3`、`UQ4`、`UQ5`。

原始 `DSD.v` 未隨題目提供，所以採用下列明確介面：Q1 為 5-bit；Q2 的 `WIDTH` 預設 5，Q4 例化時設為 6；Q4 索引與 `SizeM` 為 6-bit；RF 資料為 10-bit、地址為 12-bit；`NegNo` 為 4-bit（0～9）。若要放回課程原模板，須先核對模板的宣告。題面只給 Q4 六位寬，不能宣稱其他位寬就是原模板設定。

`Reset` 是非同步、active-high。`Start`／`StartCal` 在 reset 後第一次被取樣為高時啟動；可以保持為高或只拉高一拍。一次計算中的後續 `Start` 不重新啟動，下一次計算須 reset。Q6 啟動時保存 `SizeM`，計算中改變輸入不影響地址。

## Q1：5-bit 遞減

reset 清成 0，每個上升緣減 1。五位運算自然以 32 為模數，故序列是 0、31、30……1、0、31。`always @(posedge Clock or posedge Reset)` 實現非同步 reset，暫存器以非阻塞賦值更新。

## Q2：方向及使能

由圖 2 得知 `IorD=1` 加一，`IorD=0` 減一。`Enable=0` 不對暫存器賦值，即保持。此方向對應 Q3 的向右／向左掃描。參數只調整位寬，不改動任何題目要求的 port。

## Q3：九拍週期

每個 3×3 block 的方向是三拍高、三拍低、三拍高。下一個 block 又從高開始，因此跨 block 時連續高六拍，而不是永遠三拍高、三拍低。`phase=0..8` 循環，0～2、6～8 輸出高，3～5 輸出低；尚未啟動時為低。

## Q4：蛇形掃描

啟動的那一拍令列索引為 1，並讓 Q2 由 0 加到 1。每三個元素換列：

| phase | RIndx | CIndx（第一個 block） | 下一拍的 column 操作 |
|---|---:|---:|---|
| 0、1、2 | 1 | 1、2、3 | 加、加、保持 |
| 3、4、5 | 2 | 3、2、1 | 減、減、保持 |
| 6、7、8 | 3 | 1、2、3 | 加、加、加 |

跨列的兩次保持維持蛇形掃描端點；phase 8 的加一則進入下一個對角 block 的左上角 (4,4)。phase 2、5、8 之後列索引加一。`NewBlock = running && phase==0`，在 (1,1)、(4,4)、(7,7)……各持續一拍。

Q4 沒有矩陣大小輸入，因此獨立使用時持續掃描，索引以 64 為模數。Q6 負責合法範圍檢查與完成後停止。

## Q5：同步 read-first RF

最大矩陣為 63×63，共 3969 個 word，需要 12-bit 地址。宣告 4096×10 的 `MemArray`，在正緣更新 `QA` 並在 `WEB=1` 時寫入。若同一拍 `AddA==AddB` 且寫入，`QA` 取得舊值，下一次讀取才得到新值：兩條非阻塞賦值都使用該拍前的記憶體內容。

地址改變但沒有正緣時，`QA` 不變。題目沒有 RF reset，因此記憶體與 `QA` 的初始值未知；testbench 必須先經 port B 寫入要讀的資料。本解答不把未初始化內容當成零。

## Q6：同步讀取、負數計數與最後一個 block

row-major 地址為 `(RIndx-1)*M + CIndx-1`。先用完整 integer 計算與檢查，再縮成 12-bit，避免截位後錯把越界地址當成合法值。十位二補數的最高位 `QA[9]` 就是符號位；每 block 累加九個符號位，範圍 0～9。

Q4 在正緣後產生索引，Q5 要到下一個正緣才讀出該索引的 word；Q6 的 sequential 累計又會在下一個正緣看見該 word。以 `qa_valid`、`qa_last`、`qa_final` 保存與 Q5 同拍讀取的地址標籤，才能避開初始零索引與末端多餘資料。

為讓 `NegNo` 在 `NBlock` 出現時就更新，對最後一個 word 使用組合加法：

| 正緣後 | Q4 的索引 | QA | 已保存的累計 | NegNo |
|---|---|---|---|---|
| E0：啟動 | 第 1 筆 (1,1)，NBlock=1 | 尚無有效資料 | 0 | 0 |
| E1 | 第 2 筆 | 第 1 筆 | 0 | 0 |
| E2 | 第 3 筆 | 第 2 筆 | 第 1 筆的符號 | 0 |
| E8 | 第 9 筆 (3,3) | 第 8 筆 | 前 7 筆 | 0 |
| E9 | 下一 block 第 1 筆，NBlock=1 | 前 block 第 9 筆 | 前 8 筆 | 前 8 筆 + 第 9 筆的符號 |
| E10 | 下一 block 第 2 筆 | 下一 block 第 1 筆 | 已清成 0 | 保存的前 block 結果 |

E9 的非阻塞賦值完成後，RF 的最後一筆及標籤已更新，累計也已包含前八筆；組合輸出因此與 `NBlock` 同時公布正確總數。E10 保存同一總數，使 `NBlock` 拉低時結果保持。這不是將 RF 改成非同步讀取。

圖 6 的 `Internal Signal` 畫成幾乎與索引同拍的序列，不能與 Q4 正緣更新、Q5 正緣同步讀取同時完全符合。本解答保留題目明定的同步 RF，內部 QA 比新索引晚一拍；公開 `NegNo`／`NBlock` 以以上最後一筆 bypass 對齊。

最後一個 block 也使用 Q4 自然產生的下一次 `NewBlock` 公布結果；這個脈衝是完成邊界，沒有把下一 block 的資料當作有效讀取。M=63 時下一個索引在六位寬中回到 0，仍會產生 phase 0 的完成脈衝；有效性檢查拒絕零索引。下一正緣保存最終結果後，`index_done` 將 UQ4 維持在 reset，停止後續脈衝。

初始、越界與完成後的 RF 地址均設為 0，`qa_valid=0` 時不累計。RF 介面沒有 read enable，所以仍會物理讀取地址 0；這是無效的安全讀取，不算矩陣的一筆，也不產生 phantom block。合法 `SizeM` 是 3、6……63；不合法值不啟動有效讀取。

題目的 9×9 範例三個 block 分別有 6、4、2 個負數，`NegNo` 在後續三次邊界依序公布 6、4、2。

## 驗證

`python tests/test_2024.py` 以獨立 Python 模型建立 row-major 記憶體及蛇形座標，再核對實際 Icarus Verilog 模擬。包括全部 21 種合法 M、原題 9×9 範例、全正／全負 3×3、符號邊界 -512／-1／0／511、每個 block 的九次有效讀取、最後一個 block 的結果、M=63 的索引溢位，以及完成後沒有新的有效存取或脈衝。Q1～Q5 另測非同步 reset、使能保持、加減溢位、方向週期、同步讀取與同址 read-first。

<!-- SOLUTION_CODE_BEGIN -->

### `design.v`

```verilog
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
```

### `tb.v`

```verilog
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
```

<!-- SOLUTION_CODE_END -->
