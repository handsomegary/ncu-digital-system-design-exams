# 2022 期末考題目整理

課程：國立中央大學「數位系統設計與實作」，2022 春季期末，原題共 100 分。保留七題的模块及埠介面；依原題圖表重建為文字。原卷用學號命名檔案，本公開版改用通用 `design.v`。

## Q1：致能計數器（10 分）

實作 `EnCounter(CounterOut, Clk, Reset, En)`，上升緣觸發、非同步 Reset。只有 En=1 才計數，數值 1→2→…→1023→1。CounterOut 寬 10 bits。

圖示 Reset 是**高有效**，Reset 後值為 0；En 首次有效的上升緣才變 1。原圖範例在連續觀察區間顯示 `0,0,0,0,1,2,2,3,3`，停止 En 時維持原值，時脈週期 100 ns。

## Q2：四位元左旋（10 分）

實作 `Rotator(Rout, RIn, Rb)`。RIn 及 Rout 各 4 bits，Rb 為 2 bits，表示左旋 0、1、2 或 3 位。移出最高位的 bit 回到最低位，不補 0。

原文字把輸出寫為 ROut，而 module 宣告為 Rout；本版依宣告採 **Rout**，這是大小寫差異，不增加第二個埠。

## Q3：同步暫存器檔（10 分）

實作 `RegisterFile(Q, D, Clk, WE, Add)`，容量 8 words×10 bits，同步讀、同步寫，WE 高有效。Add 為 3 bits，D 及 Q 為 10 bits。未指定初始化、reset 或讀寫同位址衝突規則；詳解明示採上升緣 read-first。

## Q4：完全相符圖樣偵測（15 分）

實作 `PatternCheck(Judge, InPattern, ValidIn, UserPattern, Load, Clk, Reset)`。四位元 UserPattern 在 Load 有效時載入；之後送入四位元 InPattern，ValidIn=1 才有效。輸入當下與已載入圖樣完全相等時，Judge 應在**同一個輸入區間**為 1；不增加一拍輸出延遲。

| 埠 | 方向 | 寬度 |
|---|---|---|
| Judge | 輸出 | 1 |
| InPattern、UserPattern | 輸入 | 4 |
| ValidIn、Load、Clk、Reset | 輸入 | 1 |

原圖 Reset 高有效；Load 的有效時段跨過上升緣。以使用者圖樣 p=7 為具體例，輸入圖樣在載入完成後依序 `a,f,4,7,e,9`（十六進位），ValidIn 均為 1，Judge 依序 `0,0,0,1,0,0`。p 的原始範圍為 0–15，選 7 只用於此文字範例。

## Q5：帶遮罩的圖樣偵測（15 分）

實作 `MaskPatternCheck(Match, InPattern, ValidIn, Mask, UserPattern, Load, Clk, Reset)`。新增四位元 Mask：mask bit=1 的位置必須與 UserPattern 相同；mask bit=0 的位置不比較。其他時序與 Q4 相同。Mask 與 UserPattern 同時在 Load 有效的上升緣保存。

原例要辨識 `10?1`：UserPattern=`1001`，Mask=`1101`。輸入 `1001` 或 `1011` 都符合。原圖的資料與 Match 對照為：

| InPattern | 0001 | 0010 | 0011 | 1011 | 1010 | 1001 |
|---|---|---|---|---|---|---|
| Match | 0 | 0 | 0 | 1 | 0 | 1 |

`?` 代表規格中的 don't-care，不能直接把合成用 pattern 寫成含 x 的比較常數取代 mask。

## Q6：圖樣出現次數（20 分）

序列長度小於 1023，每筆四位元。統計已載入的 UserPattern 出現次數，ValidIn=0 的資料不計。將結果存入暫存器檔**位址 4**，實例名稱必須為 **U1**；除 RegisterFile 外，可重用前題模組。

介面為 `PatternCount(InPattern, ValidIn, UserPattern, Load, Clk, Reset)`；原卷多打一個左括號，本版修正語法。原介面沒有結果輸出埠；結果在 U1 的指定 word，測試可經階層讀取檢查。

## Q7：最後一次出現位置（20 分）

序列長度小於 1023，找出固定遮罩圖樣 `1?01`（pattern=`1001`、mask=`1011`）最後一次出現的位置，存入 RegisterFile 實例 **U1** 的**位址 7**。第一筆 ValidIn 指示的有效資料位置為 1；ValidIn=0 不接受資料、不寫入位置結果。

介面為 `PatternPosition(InPattern, ValidIn, Clk, Reset)`；同樣修正原 module 宣告多餘的左括號。本版以有效資料的順位作位置，無效週期不占順位；没有匹配時保留初始化結果 0。這些邊界規則在詳解明示。

[完整詳解與全部 Verilog](solutions.md)
