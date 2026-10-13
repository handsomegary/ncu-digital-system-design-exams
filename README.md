# 國立中央大學：數位系統設計與實作考古題詳解

依提供資料整理 **4 份考試、21 道大題**，包含手寫題的文字化解法、狀態表、邏輯推導及程式題的完整 Verilog。題目與詳解分頁，全部必要原始碼也完整嵌入各份詳解。保留有可辨識題面的內容；學生作答經核對及更正，沒有把未取得的題目從答案反推成原題。

| 考試 | 保留題目 | 題目 | 詳解與完整程式 |
|---|---|---|---|
| 2008 春季期中 | Q1–Q2，2 題 | [questions](exams/2008/questions.md) | [solutions](exams/2008/solutions.md) |
| 2009 期末 | Q1–Q5，5 題，含子題 | [questions](exams/2009/questions.md) | [solutions](exams/2009/solutions.md) |
| 2022 期末 | Q1–Q7，7 題 | [questions](exams/2022/questions.md) | [solutions](exams/2022/solutions.md) |
| 2023 期末 | Q1–Q7，7 題 | [questions](exams/2023/questions.md) | [solutions](exams/2023/solutions.md) |

2008 原檔雖名為 Final-Exam-2008-Answer，卷首實際寫春季期中，且前兩頁有題目，所以保留其中兩題。2009 的 Answer 檔與正式題目配對，用於核對手寫內容。2022、2023 的波形規則轉為簡短文字表；圖中有明確要求的 Reset、En、延遲與座標仍保留。題面沒有指定或彼此衝突的規則，在各份詳解明示本版處理方式。

## 未收錄的內容

| 資料 | 原因 |
|---|---|
| 2008 Q3 | Fig. 2 被裁切，缺少決定時序的接線與元件，不能唯一求解 |
| Final-Exam-2017.pdf | 只有手寫作答／批改紙，缺原題與必要規格 |
| Final-Exam-2019-Answer.pdf | 只有手寫答案，沒有題面 |
| Final-Exam-2021.txt | 只有未完整的 Verilog 程式，沒有可核對的題目 |

原始 PDF、學生姓名學號、個人檔名與原聊天紀錄均不收錄。2023 的問答只用於匿名的技術澄清。未把只有答案的資料再發成沒有題目的解答頁。

## 編譯與模擬

不同年度有同名模組，請各自編譯，不能將所有年份一次連結。各年份 README 提供獨立用法。需要 Python 3.12 與 Icarus Verilog（`iverilog`、`vvp`），沒有額外 Python 套件。

```sh
python tools/sync_book.py --check
python tests/test_2008.py
python tests/test_2009.py
python tests/test_2022.py
python tests/test_2023.py
python tests/test_book.py
```

測試包括獨立 Python 真值表／位元模型、HDL testbench、Reset 與 En、同步讀写碰撞、圖樣比對、無效資料、管線延遲、X/Z 與座標。`test_book.py` 從詳解抽出原始碼，再編譯並核對完整性。GitHub Actions 在 Linux 安裝 Icarus 並實際執行模擬；不把 Python 模型通過宣稱成 HDL 通過。

## 小型純文字儲存庫

不收錄波形圖片、VCD/FST、模擬執行檔、大量輸出紀錄或展開的測試向量。模擬產物只在臨時目錄，測完清除。CI 只回報測試摘要，沒有上傳波形或其他 artifacts。

[index.json](index.json) 只是題目數及檔案連結索引，不再複製一整份程式資料。修改原始碼後執行 `python tools/sync_book.py`，同步詳解內完整程式；`--check` 供 CI 確認兩者一致。
