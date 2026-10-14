# 2008 春季期中考：數位系統設計

題目內容：[可編輯 LaTeX](questions.tex)、[中文題目](questions.md)。2008 的來源 PDF 不收錄。

轉錄所依據的來源雖然檔名含 Final 與 Answer，卷首實際標示 **Spring 2008 Midterm**。來源的前兩頁包含可辨識的題面，後三頁是第 1 題的手寫參考作答；本儲存庫保留題目轉錄與題解。

- [questions.md](questions.md)：第 1、2 題的繁中重寫題面，共 4 個小題，包含重新繪製的狀態圖。
- [solutions.md](solutions.md)：完整接線說明、狀態表、K-map、Boolean 方程及全部題解程式碼。
- [model.py](model.py)：可執行的狀態表與 K-map 模型。
- [design.v](design.v)、[tb.v](tb.v)：兩題的組合邏輯、補充的 DFF 實作及小型自檢 testbench。

第 3 題的 Fig. 2 被裁切，無法確定時序路徑與完整接線，因此排除；不依文字數字自行補造電路。沒有收錄原始掃描、個人資料、波形、VCD、模擬產物或大量 log。

```sh
python exams/2008/model.py
python tests/test_2008.py --model-only
python tests/test_2008.py
```

以上命令在 repo 根目錄執行。`--model-only` 只驗證 Python 模型及文件，不聲稱已模擬 RTL。預設測試還需要 Icarus Verilog 的 `iverilog` 與 `vvp`；GitHub CI 會安裝並實跑。也可在本目錄手動執行：

```sh
iverilog -g2012 -Wall -s tb_2008 -o /tmp/dsd2008.vvp design.v tb.v
vvp /tmp/dsd2008.vvp
```

測試程式使用暫存目錄存放模擬產物並自動清除。`tb.v` 只列印一行通過摘要，沒有波形輸出。原題沒有要求 Verilog；RTL 是讓答案可執行與驗證的補充。DFF 範例選用上升緣及高有效非同步 reset 到 `00`，這是補充實作約定，不改變題目的狀態表或方程。
