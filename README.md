# 國立中央大學：數位系統設計與實作考古題詳解

收錄 **5 份考試、27 道完整大題**，每個年份提供可編輯的英文原題 LaTeX、中文題目整理及詳解；2009、2022、2023、2024 另附原始試卷 PDF，共 4 份。2024 年新增六題完整 Verilog 與模擬測試。原題轉錄保留考試規則、配分、模組介面及必要圖表；解答的邊界補定另行說明。

| 考試 | 完整題數 | 原始試卷 | 原題 LaTeX | 中文題目 | 詳解與完整程式 |
|---|---:|---|---|---|---|
| 2008 春季期中 | 2 | 不收錄 | [TeX](exams/2008/questions.tex) | [questions](exams/2008/questions.md) | [solutions](exams/2008/solutions.md) |
| 2009 期末 | 5 | [PDF](exams/2009/Final-Exam-2009.pdf) | [TeX](exams/2009/questions.tex) | [questions](exams/2009/questions.md) | [solutions](exams/2009/solutions.md) |
| 2022 期末 | 7 | [PDF](exams/2022/original.pdf) | [TeX](exams/2022/questions.tex) | [questions](exams/2022/questions.md) | [solutions](exams/2022/solutions.md) |
| 2023 期末 | 7 | [PDF](exams/2023/original.pdf) | [TeX](exams/2023/questions.tex) | [questions](exams/2023/questions.md) | [solutions](exams/2023/solutions.md) |
| 2024 期末 | 6 | [PDF](exams/2024/original.pdf) | [TeX](exams/2024/questions.tex) | [questions](exams/2024/questions.md) | [solutions](exams/2024/solutions.md) |

2008 原檔雖名為 Final-Exam-2008-Answer，卷首實際寫春季期中；完整保留 Q1、Q2。Q3 的可讀文字附在 TeX 中，但必要電路图被裁切，不反推圖或答案，不計入完整題數。2009 原卷日期與 Spring 2009 年份不一致，轉錄保留原印日期。2022、2023 原卷的語法／拼字錯誤在 TeX 中保留並標示，實作採合法 HDL。

每份 questions.tex 都是獨立文件，可用 `pdflatex questions.tex` 或 XeLaTeX 編譯。電路、圖樣與波形以可編輯 TikZ、表格或序列轉錄；附上的 4 份原始 PDF 供完整外觀核對，2008 僅提供文字轉錄與題解。收錄的 PDF 在 metadata.json 記錄來源檔名稱及 SHA-256；2008 則標示不收錄來源 PDF。**2023 與 2024 原卷第 1 頁都要求下載 DSD.v，但提供資料沒有這兩年的原模板**；詳解明示重寫介面與採用的時序規則，完整 RTL 可獨立執行，不宣稱就是原模板。

2026-10-14 擴大保存核對：原始文件、程式、資料與附件均應保存，只排除編譯產物及可再生暫存。2008 原掃描先前未收錄，目前原來源已不可取得，因此仍列為缺件；現有文字轉錄不能取代原件。2023、2024 的官方 DSD.v 也仍未提供。

原卷附檔參照、原件 SHA256、不可取得的模板及自製向量來源見 [document-companions.json](document-companions.json)。2009 的時序刺激印在原卷第 2 頁，2022 由自己撰寫所有模組，兩者沒有另要求外部資料檔。數位系統可執行的重寫 RTL 與原課程附件的齊全程度在清單中分開記錄。

## 編譯與模擬

不同年度有同名模組，請各自編譯。各年份 README 提供獨立用法。需要 Python 3.12 與 Icarus Verilog（`iverilog`、`vvp`），没有額外 Python 套件。

```sh
python tools/sync_book.py --check
python tools/check_document_companions.py
python tests/test_2008.py
python tests/test_2009.py
python tests/test_2022.py
python tests/test_2023.py
python tests/test_2024.py
python tests/test_book.py
```

測試包括獨立 Python 模型、HDL testbench、Reset／Enable、同步讀寫碰撞、圖樣比對、有效資料與管線時序。2024 測試涵蓋全部 21 種合法 SizeM、符號邊界、每個區塊的九筆資料、最後區塊結果與 M=63 的索引溢位。`test_book.py` 核對原卷雜湊、TeX 存在性和詳解嵌入的全部原始碼，並編譯抽出的 HDL。GitHub Actions 實際執行 Icarus 模擬。

## 收錄檔案

收錄使用者提供的 4 份原始試卷 PDF：2009、2022、2023、2024。2008 的來源 PDF 不收錄，保留原題 LaTeX、中文題目及詳解。不收錄生成的波形圖、VCD/FST、編譯執行檔、生成 PDF 或大量向量。模擬產物使用臨時目錄，CI 僅回報摘要。

所需向量的固定 seed 產生器已附齊，不依賴未上傳的本機檔案。2023 可用 `python tests/test_2023.py --work-dir simulation/2023` 保留記憶體、全部向量、真正的 Icarus 輸出與執行檔，詳見該年 README。指定目錄必須尚未存在。

[index.json](index.json) 提供題數與原卷、LaTeX、題目及解答連結。修改 HDL 後執行 `python tools/sync_book.py` 同步詳解中的完整程式，`--check` 供 CI 確認一致。
