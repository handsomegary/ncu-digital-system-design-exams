# 2009 期末考

納入五大題、九個作答項目，包含錯誤修正、latch／三態判斷、四個 16 位元模組、資料路徑與原時序刺激。完整繁中題面見 [questions.md](questions.md)，逐題詳解及完整 RTL／testbench 見 [solutions.md](solutions.md)。原卷年份／日期、未指定極性及初始化的採用規則均明列。

在儲存庫根目錄執行：

```sh
python tests/test_2009.py
```

預設需要 Icarus Verilog 的 `iverilog` 和 `vvp`，CI 會安裝。兩支 testbench 實際檢查元件與接線；獨立 Python 模型另檢查數值、16 位邊界及原時序。缺少模擬器只想先檢查模型時，明確加 `--model-only`，這不表示 HDL 已通過。

tb_waveform.v 是小型時序刺激與自動檢查原始碼，**不輸出 VCD 或任何波形檔**。必要時序只用短表呈現。編譯與模擬產物自動放入暫存目錄後刪除；不保存波形圖、模擬日誌或展開的大量向量。
