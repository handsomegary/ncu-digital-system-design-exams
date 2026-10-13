# 2023：數位系統設計與實作期末考

共 7 題、100 分。四頁題面的圖已轉成格子配置與簡短文字時序表，可直接閱讀，不必另找原 PDF。

- [完整題目、介面與時序](questions.md)
- [逐題詳解與完整 RTL／testbench](solutions.md)
- [七題 RTL](dsd2023.v)、[小型 testbench](tb_2023.v)

測試需要 Icarus Verilog 的 `iverilog` 與 `vvp`：

```sh
python tests/test_2023.py
```

從 repo 根目錄執行。測試以固定 seed 即時產生刺激，再用獨立 Python 記憶體／索引／視窗模型逐項核對 RTL 模擬。刺激、模擬執行檔與 log 均位於暫存目錄，測完清除；不產生波形或 VCD。

`--model-only` 僅檢查 oracle 與刺激設定，不能代替 RTL 模擬。可用 `--iverilog`、`--vvp` 或 `IVERILOG`、`VVP` 環境變數指定工具位置。

原始空白模板的拼字與容量矛盾已明確列在題面：完整影像需 `COL*ROW<=1024`，不足三列的最後一組不輸出有效視窗。保持原 module／port 名稱，`MaxSearch2D` 的座標輸出使用完整影像座標所需的位寬。
