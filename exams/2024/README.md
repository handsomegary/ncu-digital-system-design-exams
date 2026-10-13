# 2024：數位系統設計與實作期末考

共 6 題、100 分，考試日期為 113/06/04。

題目來源：[原始 PDF](original.pdf)、[可編輯 LaTeX](questions.tex)。

- [完整題目、介面與圖的文字重建](questions.md)
- [逐題詳解及完整 RTL／testbench](solutions.md)
- [六題 RTL](design.v)、[範例 testbench](tb.v)

從 repo 根目錄執行：

```sh
python tests/test_2024.py
```

需要 Icarus Verilog 的 `iverilog` 與 `vvp`；可用 `IVERILOG`、`VVP` 環境變數指定完整路徑。測試涵蓋全部 21 種合法矩陣大小（3、6……63）、題目中的 9×9 範例、全正／全負資料、同步 RF 讀寫碰撞、計數器保持與溢位，以及末端 pipeline 的排空。測試不生成波形檔。

原始 `DSD.v` 空白模板未提供；本解答明列位寬與啟動語義。Q6 保留同步 RF，利用最後一筆資料的組合加法，使 `NegNo` 與 `NBlock` 同時更新。最後一個 block 也會公布結果，完成後停住索引產生器；詳見解答中的逐拍表。
