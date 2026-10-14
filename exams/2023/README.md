# 2023：數位系統設計與實作期末考

題目來源：[原始 PDF](original.pdf)、[可編輯 LaTeX](questions.tex)、[中文題目](questions.md)。

共 7 題、100 分。四頁題面的圖已轉成格子配置與簡短文字時序表，可直接閱讀，不必另找原 PDF。

- [完整題目、介面與時序](questions.md)
- [逐題詳解與完整 RTL／testbench](solutions.md)
- [七題 RTL](dsd2023.v)、[小型 testbench](tb_2023.v)

測試需要 Icarus Verilog 的 `iverilog` 與 `vvp`：

```sh
python tests/test_2023.py
```

從 repo 根目錄執行。測試以固定 seed 即時產生刺激，再用獨立 Python 記憶體／索引／視窗模型逐項核對 RTL 模擬。刺激、模擬執行檔與 log 均位於暫存目錄，測完清除；不產生波形或 VCD。

要取得並保留可直接重跑的全部輸入與實際模擬結果，仍從 repo 根目錄執行：

```sh
python tests/test_2023.py --work-dir simulation/2023
```

工具會在新目錄寫出 `memory.hex` 與 `rotator`、`row`、`pattern`、`rf`、`count`、`fetch`、`max` 七份 `*_vectors.txt`，編譯 Git 中的 `dsd2023.v` 與 `tb_2023.v`，保存 `simulation.vvp`、編譯 stdout/stderr、真正的 `actual.log`／`actual.stderr.txt`、`commands.json` 及核對結果 `summary.json`。這些輸入由 repo 內固定 seed 產生器生成，無須另外下載。現有目錄會被拒絕，重跑請選另一個目錄。

生成完後，可自己進入該目錄再執行保存的 bench：

```sh
cd simulation/2023
vvp simulation.vvp
```

直接編譯／執行 `tb_2023.v` 時，工作目錄需包含上述八份輸入；先執行產生器可避免 `$readmemh`／`$fopen` 找不到檔案。工具缺失、編譯失敗或模擬結果不符時會回傳失敗，不將 model-only 視為執行成功。

`--model-only` 僅檢查 oracle 與刺激設定，不能代替 RTL 模擬。可用 `--iverilog`、`--vvp` 或 `IVERILOG`、`VVP` 環境變數指定工具位置。

原卷第 1 頁要求下載的 `DSD.v` 原模板沒有隨本機資料提供；[附件清單](../../document-companions.json)明列 `not_provided`。目前是依原卷介面與明示規則重新實作的完整 RTL，不以自製刺激代替原模板。原卷印出的模板片段之拼字與容量矛盾已明確列在題面：完整影像需 `COL*ROW<=1024`，不足三列的最後一組不輸出有效視窗。`MaxSearch2D` 的座標輸出使用完整影像座標所需的位寬。
