# 國立中央大學：數位系統設計與實作考古題詳解

收錄 **5 份考試、27 道完整大題**，每個年份提供原始試卷 PDF、可編輯的英文原題 LaTeX、中文題目整理及詳解。2024 年新增六題完整 Verilog 與模擬測試。原題轉錄保留考試規則、配分、模組介面及必要圖表；解答的邊界補定另行說明。

| 考試 | 完整題數 | 原始試卷 | 原題 LaTeX | 中文題目 | 詳解與完整程式 |
|---|---:|---|---|---|---|
| 2008 春季期中 | 2 | [PDF](exams/2008/original.pdf) | [TeX](exams/2008/questions.tex) | [questions](exams/2008/questions.md) | [solutions](exams/2008/solutions.md) |
| 2009 期末 | 5 | [PDF](exams/2009/original.pdf) | [TeX](exams/2009/questions.tex) | [questions](exams/2009/questions.md) | [solutions](exams/2009/solutions.md) |
| 2022 期末 | 7 | [PDF](exams/2022/original.pdf) | [TeX](exams/2022/questions.tex) | [questions](exams/2022/questions.md) | [solutions](exams/2022/solutions.md) |
| 2023 期末 | 7 | [PDF](exams/2023/original.pdf) | [TeX](exams/2023/questions.tex) | [questions](exams/2023/questions.md) | [solutions](exams/2023/solutions.md) |
| 2024 期末 | 6 | [PDF](exams/2024/original.pdf) | [TeX](exams/2024/questions.tex) | [questions](exams/2024/questions.md) | [solutions](exams/2024/solutions.md) |

2008 原檔雖名為 Final-Exam-2008-Answer，卷首實際寫春季期中；完整保留 Q1、Q2。Q3 的可讀文字附在 TeX 中，但必要電路图被裁切，不反推圖或答案，不計入完整題數。2009 原卷日期與 Spring 2009 年份不一致，轉錄保留原印日期。2022、2023 原卷的語法／拼字錯誤在 TeX 中保留並標示，實作採合法 HDL。

每份 questions.tex 都是獨立文件，可用 `pdflatex questions.tex` 或 XeLaTeX 編譯。電路、圖樣與波形以可編輯 TikZ、表格或序列轉錄；原始 PDF 供完整外觀核對。metadata.json 記錄原檔名稱及 SHA-256，確認原卷未被修改。2024 的 DSD.v 未提供，詳解明示採用的埠寬與同步 RF 時序解讀。

## 編譯與模擬

不同年度有同名模組，請各自編譯。各年份 README 提供獨立用法。需要 Python 3.12 與 Icarus Verilog（`iverilog`、`vvp`），没有額外 Python 套件。

```sh
python tools/sync_book.py --check
python tests/test_2008.py
python tests/test_2009.py
python tests/test_2022.py
python tests/test_2023.py
python tests/test_2024.py
python tests/test_book.py
```

測試包括獨立 Python 模型、HDL testbench、Reset／Enable、同步讀寫碰撞、圖樣比對、有效資料與管線時序。2024 測試涵蓋全部 21 種合法 SizeM、符號邊界、每個區塊的九筆資料、最後區塊結果與 M=63 的索引溢位。`test_book.py` 核對原卷雜湊、TeX 存在性和詳解嵌入的全部原始碼，並編譯抽出的 HDL。GitHub Actions 實際執行 Icarus 模擬。

## 收錄檔案

僅將五份使用者提供的原始試卷 PDF 作為來源檔納入；不收錄生成的波形圖、VCD/FST、編譯執行檔、生成 PDF 或大量向量。模擬產物使用臨時目錄，CI 僅回報摘要。

[index.json](index.json) 提供題數與原卷、LaTeX、題目及解答連結。修改 HDL 後執行 `python tools/sync_book.py` 同步詳解中的完整程式，`--check` 供 CI 確認一致。
