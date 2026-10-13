# 2024 春季期末考：題目

課程：Digital System Design and Implementation（數位系統設計與實作）。日期：2024-06-04（113/06/04）。來源為完整四頁 `FinalExam.pdf`。總分 100，六大題。以下中文整理與 [英文 LaTeX 轉錄](questions.tex) 都可對照 [原始試卷](original.pdf)。

原卷要求下載 DSD.v、按學號命名提交檔案、保留模組與埠名稱、不可討論但可查自己的講義。這些是原考試的作答規則。此次提供的資料沒有 DSD.v，因此未能核對模板內的全部埠寬。

各循序題使用 `Clock` 上升緣與高有效非同步 `Reset`。

## Q1：5-bit 遞減計數器（10 分）

完成 `Decrementer(DecOut, Clock, Reset)`。Reset 時 DecOut=0；解除後依時脈遞減，圖 1 序列為 `0,31,30,29,...,1,0,31,...`。

## Q2：可致能的加／減計數器（16 分）

完成 `Counting(CountOut, IorD, Enable, Clock, Reset)`，延伸 Q1。IorD=1 加一，IorD=0 減一；Enable=0 保留狀態。圖 2 的 CountOut 為 `0,0,1,2,3,3,4,...,28,29,28,27,27,27,26,...`，停住的區間對應 Enable=0。

## Q3：區塊掃描的方向控制（16 分）

完成 `GenerateUpDownCtr(UpDown, Start, Clock, Reset)`，以 Start 啟動。矩陣沿對角線有 3×3 方形區塊，區塊內第一列由左往右、第二列由右往左、第三列由左往右，接著進入下一個對角區塊。UpDown 每列持續三拍，列 1、2、3、4 的值分別為 `1,0,1,1`，之後重複每個區塊的三列方向。圖中 Start 啟動後保持為 1。

## Q4：列／欄索引與新區塊標記（24 分）

完成 `GenerateRCIndex(NewBlock, RIndx, CIndx, Start, Clock, Reset)`。索引從 1 開始，矩陣邊長小於 64，RIndx 和 CIndx 各 6 bits。必須例化 Q2 與 Q3，名稱為 `UQ2`、`UQ3`。NewBlock 在每個區塊第一個元素出現時為 1。批改時會置換成正確的 Q2/Q3 子模組。

| 輸出區間 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RIndx | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 3 | 4 | 4 | 4 |
| CIndx | 1 | 2 | 3 | 3 | 2 | 1 | 1 | 2 | 3 | 4 | 5 | 6 |
| NewBlock | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |

啟動前兩個索引及 NewBlock 都為 0。

```verilog
Counting UQ2(.CountOut(), .IorD(), .Enable(), .Clock(), .Reset());
GenerateUpDownCtr UQ3(.UpDown(), .Start(), .Clock(), .Reset());
```

## Q5：雙埠同步暫存器檔（16 分）

完成 `RFTwoPort(QA, AddA, DB, AddB, WEB, Clock)`，儲存 M×M 矩陣，M<64，每個元素 10 bits。A 埠同步讀出 QA，不需要讀取致能；B 埠在 WEB=1 時同步寫入 DB。AddA、AddB 是兩個埠各自的位址。圖 5 右側讀位址誤印成 AddB；文字和模組宣告寫 AddA。

## Q6：計算每個對角區塊的負數個數

完成 `CalculateNegativeDBlock(NegNo, NBlock, SizeM, StartCal, Clock, Reset, DPortB, AddBPort, WEBPort)`。原卷未單獨印 Q6 配分；前五題共 82 分，依總分推得本題 18 分。

矩陣資料為 10-bit 二補數。SizeM 指定 M<64 且 M/3 為整數。資料依列連續儲存，(1,1) 在位址 0、(1,2) 在位址 1。用 Q4 的索引依序讀取各個對角 3×3 區塊；NBlock 有效時，NegNo 更新為**上一個區塊**的負數個數。NBlock 接 Q4.NewBlock，StartCal 接 Q4.Start。必須保留給測試寫資料使用的 DPortB、AddBPort、WEBPort。

```verilog
GenerateRCIndex UQ4(.NewBlock(NBlock), .RIndx(), .CIndx(),
                   .Start(StartCal), .Clock(), .Reset());
RFTwoPort UQ5(.QA(), .AddA(), .DB(DPortB), .AddB(AddBPort),
             .WEB(WEBPort), .Clock());
```

圖 6(a) 的 M=9 範例包含以下三個對角區塊：

```text
Block 1          Block 2          Block 3
 -5   -4   11     -1   -1  100     10   90  -90
 66  -99  -22    400  -15   77    101  -11   99
  7   -1 -197     91  -67  101     17   17   88
```

图 6(b) 的 Internal Signal 在起始零值之後依序是 `-5,-4,11,-22,-99,66,7,-1,-197,-1,-1,...`。NBlock 在第 1、4 列開頭出現脈衝；NegNo 起始為 0，在下一區塊邊界更新為 6。

原文未定義 Start 短脈衝、終止／重啟、超出矩陣、同步讀寫同位址等邊界。Q2 的 5-bit 延伸與 Q4 的 6-bit 要求，以及圖 6 內部資料相對同步 RF 的延遲，也需在實作中明示，見 [完整詳解](solutions.md)。
