# 2023 期末考：完整重寫題目

考試日期：2023-05-30。總分 100，7 題。依完整四頁試卷、空白 HDL 模板及匿名技術澄清重寫；不包含原聊天、姓名或學號。各圖的必要內容如下列介面、格子與時序表。

所有數據皆為 unsigned。`Clk` 使用上升緣；需要 `Reset` 的模組使用高有效非同步 reset。測試資料先放入 register file，可假定有效資料已存在。第 5 題必須使用第 4 題，第 6 題必須使用第 2 題，第 7 題必須使用 `DataFetch`。

## Q1：三筆資料旋轉器（10 分）

完成組合旋轉器，三個輸入、三個輸出都為 8 bits。rMode 是 2 bits。

```verilog
module Rotator(Out3, Out2, Out1, In3, In2, In1, rMode);
```

| rMode | Out1 | Out2 | Out3 |
|---:|---|---|---|
| 0 | In1 | In2 | In3 |
| 1 | In2 | In3 | In1 |
| 2 | In3 | In1 | In2 |

原圖沒有定義 mode=3 或未知 mode；本解答補定為三個零，避免組合 latch。原 PDF 的 `Rotaor` 是拼字錯誤，依模板使用 `Rotator`。

## Q2：三讀一寫同步 register file（10 分）

設計同步讀／同步寫 register file，一個 write port、三個 read ports，每個 word 為 8 bits。WE 高有效。10-bit 位址範圍是 0..1023，共 1024 words。

```verilog
module RegisterFile(QA, QB, QC, D, Clk, RAA, RBA, RCA, WE, WA);
```

| Port | 方向／位寬 | 意義 |
|---|---|---|
| QA、QB、QC | output 8 | 三個同步讀取結果 |
| D | input 8 | 寫入資料 |
| Clk | input 1 | 上升緣時脈 |
| RAA、RBA、RCA | input 10 | 三個讀取位址 |
| WE | input 1 | 高有效 write enable |
| WA | input 10 | 寫入位址 |

每個上升緣讀取三個指定 word；若 WE=1，同時把 D 寫入 WA。沒有 reset port。補定同拍讀寫同一位址採 read-first：讀取該拍寫入前的舊值，下一拍才可讀到新值；兩種操作皆用非阻塞賦值實現。

## Q3：二維索引計數器（12 分）

```verilog
module Count2D(XIndex, YIndex, Clk, Reset, En);
parameter COL=50;
parameter ROW=25;
```

XIndex 是 7-bit output，YIndex 是 6-bit output；其餘三個 port 是 1-bit input。參數限制 `1<=COL<128`、`1<=ROW<64`。

Reset 為 1 時立即清成 (0,0)，不等時脈。En=0 保持兩個原值。Reset 解除後，第一個 En=1 的上升緣輸出 (1,1)，X 每拍遞增，掃完 COL 欄後回 1，Y 增加 3，以每次處理三列。持續 En=1 時循環掃描。

原圖時脈週期為 100 ns；關鍵是以下相對上升緣行為。

| 狀態／上升緣 | En | XIndex | YIndex |
|---|---:|---:|---:|
| Reset=1，任意時刻 | 任意 | 0 | 0 |
| Reset=0，但尚未啟用 | 0 | 0 | 0 |
| 第一個啟用緣 | 1 | 1 | 1 |
| 第二個啟用緣 | 1 | 2 | 1 |
| 同一組最後一欄 | 1 | COL | 1 |
| 下一個啟用緣 | 1 | 1 | 4 |
| 再下一組 | 1 | 1..COL | 7 |
| 最後一組之後 | 1 | 1 | 1 |

原參數 ROW=25 的 Y 序列為 `1,4,7,10,13,16,19,22,25`。一般 ROW 若不是 `1 mod 3`，本解答補定下一個 Y 會超過 ROW 時回 1，避免超出參數範圍。

## Q4：列比較器（15 分）

設計組合模組。In1、In2、In3 為 8-bit input，iMode 為 1-bit input；MaxValue 為 8-bit output，MaxPos 為 2-bit output，Valid 為 1-bit output。

```verilog
module RowComparator(MaxValue, MaxPos, Valid, In1, In2, In3, iMode);
```

iMode=0 比較三個輸入，輸出最大值及其位置 1、2、3。iMode=1 直接輸出中心 In2，MaxPos=2，與其他兩筆大小無關。只要任一輸入含任何 X 或 Z bit，Valid=0，MaxValue=MaxPos=0。全為已知資料則 Valid=1。未知 iMode 也補定為無效。

原題保證只有一個最大值；額外相等輸入補定選最前的位置。以下為原 I/O 圖的完整欄位轉錄，X/Z 可代表該輸入存在未知／高阻抗 bit：

| In1 | In2 | In3 | iMode | Valid | MaxValue | MaxPos |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | Z | 5 | 0 | 0 | 0 | 0 |
| 0 | 1 | X | 0 | 0 | 0 | 0 |
| 0 | Z | Z | 0 | 0 | 0 | 0 |
| X | Z | 5 | 0 | 0 | 0 | 0 |
| 1 | 55 | 76 | 0 | 1 | 76 | 3 |
| 99 | 70 | 51 | 0 | 1 | 99 | 1 |
| 88 | 89 | 61 | 1 | 1 | 89 | 2 |
| 9 | 45 | 77 | 1 | 1 | 45 | 2 |
| 10 | 5 | 3 | 0 | 1 | 10 | 1 |
| 6 | 22 | 8 | 0 | 1 | 22 | 2 |
| 93 | 32 | 100 | 0 | 1 | 100 | 3 |

## Q5：3×3 pattern 最大值（20 分）

對三列九個輸入依 Pattern 選定區域，輸出最大值及其在 3×3 中的列／欄。必須使用 Q4 的 RowComparator。

```verilog
module PatternComparator3x3(MaxValue, MaxRow, MaxCol, Valid,
    In1_1, In2_1, In3_1, In1_2, In2_2, In3_2,
    In1_3, In2_3, In3_3, Pattern);
```

九個 input 各 8 bits，Pattern 是 2-bit input；MaxValue 為 8 bits，MaxRow、MaxCol 各 2 bits，Valid 為 1 bit。`In2_3` 代表第 2 欄、第 3 列；若它是最大值，必須輸出 MaxCol=2、MaxRow=3。列由上往下編 1..3，欄由左往右編 1..3。

原圖灰格如下。1 表示比較、0 表示不列入最大值候選。

```text
Pattern 0         Pattern 1         Pattern 2
1 1 1             0 1 0             0 1 0
1 1 1             1 1 1             0 1 0
1 1 1             0 1 0             0 1 0
```

Pattern 0 比九格，Pattern 1 比十字五格，Pattern 2 比中間直條三格。各列的 RowComparator 分別設為 `(0,0,0)`、`(1,0,1)`、`(1,1,1)`。

承接 Q4 的輸入有效性規則，九筆資料都須已知，即使某個角落不在灰格也不能含 X/Z。Valid 表示 MaxValue、MaxRow、MaxCol 均能正確計算；無效時輸出三個零。Pattern=3 或未知補定為無效。相等最大值補定先選較小 row，再選較小 column。

## Q6：同步擷取三列（13 分）

```verilog
module DataFetch(Valid, TopData, MidData, BotData,
    Xindex, YIndex, En, Clk, Reset);
parameter COL=50;
parameter ROW=25;
```

保留模板的大小寫 `Xindex`。Xindex、YIndex 分別為 7-bit、6-bit inputs；TopData、MidData、BotData 是 8-bit outputs，Valid 是 1-bit output。En、Clk、Reset 是 1-bit inputs。必須例化 RegisterFile。

影像使用 row-major，索引從 1 開始：`address(x,y)=(y-1)*COL+x-1`。故 `(1,1)` 位址為 0，`(COL,1)` 為 COL-1，`(1,2)` 為 COL。

每次讀相同 x 的三筆：TopData=`image(x,y)`、MidData=`image(x,y+1)`、BotData=`image(x,y+2)`。例如依計數器掃描，第一組依序是 `(1,1)/(1,2)/(1,3)`、`(2,1)/(2,2)/(2,3)`、……，下一組是 `(1,4)/(1,5)/(1,6)`。

資料與 Valid 同步出現在讀取請求的上升緣之後。DataFetch 的圖中 Clock=1 是第一筆有效讀取資料，而非 Count2D 啟用後的第一緣；兩者串接時有同步 RF 的一拍延遲。

| En 啟用後第幾緣 | Count2D 新索引 | DataFetch 新資料 |
|---:|---|---|
| 1 | (1,1) | 舊索引 (0,0) 無效 |
| 2 | (2,1) | x=1、rows 1/2/3，Valid=1 |
| 3 | (3,1) | x=2、rows 1/2/3，Valid=1 |

Reset 立即令 Valid=0。En=0、索引超出範圍、缺少完整三列或任一位址大於 1023，皆不產生有效資料；Valid=0 時三筆資料標為 X，不能作為有效數字使用。

## Q7：二維影像的滑動 pattern 搜尋（20 分）

```verilog
module MaxSearch2D(MaxValue, MaxXPos, MaxYPos, MaxValid,
    Clk, Reset, En, Pattern);
```

Clk、Reset、En 為 1-bit inputs，Pattern 為 2-bit input。MaxValue 是 8-bit output；MaxXPos 為 7-bit、MaxYPos 為 6-bit absolute image coordinates，MaxValid 為 1 bit。本解答增加與 Count2D 相同的 COL、ROW parameters，原 port 順序不改。

使用 Count2D、DataFetch 與 PatternComparator3x3。三列各用長度 3 的 shift register 保存三個相鄰欄資料；同步 RF 輸出本身是最新一級，再加兩級歷史。因此完整鏈路的第一次有效視窗在 En 後第 4 個上升緣，符合原圖。每個後續相鄰 3×3 視窗依當下 Pattern 計算其局部最大值。

原圖前四欄資料完整如下：

```text
       x=1   x=2   x=3   x=4
y=1     55   168    16    88
y=2     39    39     2    91
y=3    111    15   201   211
```

| 啟用後上升緣 | 現在視窗 | Pattern | MaxValue | (MaxXPos,MaxYPos) | MaxValid |
|---:|---|---:|---:|---|---:|
| 1..3 | 尚未收齊三欄 | 2 | 0 | (0,0) | 0 |
| 4 | columns 1..3，rows 1..3 | 2 | 168 | (2,1) | 1 |
| 5 | columns 2..4，rows 1..3 | 0 | 211 | (4,3) | 1 |

MaxValid 只在三列、三欄都完整且屬於同一列組時為 1。每組的第一、第二欄不得把上一組最後的資料拼進視窗；不足三列的最後一組也無效。

En=0 時 Count2D 停住，RF pipeline 中已接收的上一筆資料可移入歷史，但不輸出新的有效視窗；恢復後不重複或遺失欄位。Reset 清除索引與有效歷史。Pattern 取當下值，不額外註冊延遲。無效結果補定為三個零，判斷結果必須同時查看 MaxValid。

## 原始資料矛盾與明確補定

1. 原模板預設 COL=50、ROW=25，乘積為 1250，但 register file 只有 1024 words。完整影像的參數必須滿足 `COL*ROW<=1024`；本解答保留模板預設值，對不可存取的位址降 Valid，避免 10-bit 截斷後偷偷讀到別處。
2. ROW=25 的最後起始列 25 不足三列。Count2D 仍依題圖走到 25，DataFetch／MaxSearch2D 對這組降 Valid。沒有自動補零生成不存在的影像資料。
3. `Rotator`、`PatternComparator3x3` 與 `endmodule` 採模板／合法 HDL 拼字，修正文件中的漏字。Q7 的座標不可用 2 bits，否則原圖 x=4 便無法表示。
4. 未定義 mode、equal maxima、讀寫碰撞、非 `1 mod 3` 的 ROW、停頓時的有效性，均已在對應題目明示此解答的規則。
