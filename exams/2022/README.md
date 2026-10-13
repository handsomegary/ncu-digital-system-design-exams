# 2022 期末考

[題目](questions.md) · [詳解與完整程式](solutions.md)

七題均有完整題面。涵蓋致能計數器、左旋、同步暫存器檔、完整／遮罩比對、出現次數及最後位置。

```sh
iverilog -g2012 -Wall -s PatternCount design.v
iverilog -g2012 -s tb_2022 -o example.vvp design.v tb.v
vvp example.vvp
```

測試指令應在 repo 根目錄執行 `python tests/test_2022.py`。上方指令由本目錄執行，產生的模擬檔不提交。Q6/Q7 原介面沒有輸出埠，指定結果分別位於 U1.mem[4]、U1.mem[7]。原圖高有效 reset、同拍 match 已轉成文字表；未指定的 read-first 和初始化規則在詳解列出。
