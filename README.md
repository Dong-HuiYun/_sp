# 課程：系統程式 -- 筆記、習題與報告

欄位 | 內容
-----|--------
學期 | 114 學年下學期
學生 |  董惠筠
學號末兩碼 | 31
教師 | [陳鍾誠](https://www.nqu.edu.tw/educsie/index.php?act=blog&code=list&ids=4)
學校科系 | [金門大學資訊工程系](https://www.nqu.edu.tw/educsie/index.php)
課程教材 | https://github.com/ccc114b/cpu2os



# 課程作業繳交報告

## AI 使用與原創聲明
 - **是否使用 AI：** 使用 AI ，並透過對話理解程式中的內容
 - **對應習題使用的 AI 工具、AI對話記錄連結：**

      [習題1](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C1)：[Google AI Studio 對話連結](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221chDpbNUfRiMtLmSJMenMdjvk-iIIkVxJ%22%5D,%22action%22:%22open%22,%22userId%22:%22104108532823114063447%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing,)

      [習題2](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C2_%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87%E7%A8%8B%E5%BC%8F%E8%AA%9E%E8%A8%80)：[Claude 對話連結](https://claude.ai/share/13652214-81eb-4dde-b28d-385f0f947496)、[Google AI Studio 對話連結](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221HBlnETdXpNfCEdiofFVheLA1G81_8xfh%22%5D,%22action%22:%22open%22,%22userId%22:%22104108532823114063447%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing,)、[豆包對話連結-生成ui圖](https://www.doubao.com/thread/w4e45414a6b57c657)
      
      [習題3](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C3)：[豆包對話連結-生成劇情圖](https://www.doubao.com/thread/wf6ab0ee2300897cf)、[DeepSeek 對話連結-美化網頁界面](https://www.doubao.com/thread/wf6ab0ee2300897cf)、[Gemini 對話連結](https://gemini.google.com/share/ef86477cc5f8)、[Gemini 對話連結-詢問導入本地模型做法](https://gemini.google.com/share/2800d06c2d1c)

      [習題4](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C4_%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E6%9B%B8%E7%B1%8D)：詢問了opencode

      [習題5](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C5)：[Claude 對話連結](https://claude.ai/share/7f65db1d-ba39-497d-a4b6-5cb96e25fe8f)、

      [習題6](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C6)：[Claude 對話連結](https://claude.ai/share/ca437078-65ff-4527-a530-da686e456c39)、[DeepSeek 對話連結](https://chat.deepseek.com/share/p4zp1vt1k6w8kx45xt)

      [期中作業](https://github.com/Dong-HuiYun/_sp/tree/master/%E6%9C%9F%E4%B8%AD%E4%BD%9C%E6%A5%AD_%E5%B0%8F%E5%9E%8Bos%E8%99%9B%E6%93%AC%E6%A9%9F)：[Google AI Studio 對話連結](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221XtG8ithix-0xhlGqBKfcKzhDTM-MKLfr%22%5D,%22action%22:%22open%22,%22userId%22:%22104108532823114063447%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing)、[Google AI Studio 對話連結2](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221ks5kTr6wlNKlY_GhG6KbDkyHaV2j7jma%22%5D,%22action%22:%22open%22,%22userId%22:%22104108532823114063447%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing)、[Google AI Studio 對話連結3](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2218nsOjE9-7m9TePbpy2AMR9kgNvmtMdZo%22%5D,%22action%22:%22open%22,%22userId%22:%22104108532823114063447%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing)、[Claude 對話連結](https://claude.ai/share/de6a31a4-c11c-47e3-9a41-144df663bc55)、[DeepSeek 對話連結](https://chat.deepseek.com/share/lkagehnq54qne1vl27)

---

## 習題與作業內容

### 習題 1 -- 請為 p0 編譯器加上 while 語法，並說明其函數呼叫機制是怎麼運作的

- **完成狀況：** 使用 AI ，理解了 EBNF 的語法定義，以及執行 while 迴圈下的編譯器生成的中間碼呼叫機制的運作方式。

- **程式碼/檔案路徑：** [習題1](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C1)

- **成果說明：**[成果説明](https://github.com/Dong-HuiYun/_sp/blob/master/%E7%BF%92%E9%A1%8C1/README.md)

---

### 習題 2 -- 請重新設計一個全新的程式語言，並寫出其編譯器或解釋器 (建議用 AI)

- **完成狀況：** 使用 AI，實作了繁體程式語言的編寫，程式目前已能夠支持基礎運算與資料形態、條件判斷、雙重循環系統、中斷及繼續迴圈的精細控制、函數式編程、 動態列表操作、健壯性與模組化。另外還新增了GUI圖形化界面，語法部分高亮顯示，並存在指令工作箱，可以在忘記語法時使用；執行報錯時2，能把出錯的那一行程式碼以紅底注釋，方便修改；還新增了快捷鍵支援，儲存、開啟檔名為 `.中文` 的程式碼。界面還有 UI 的設計，擺脫 Python 預設外觀。

- **程式碼/檔案路徑：** [習題2](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C2_%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87%E7%A8%8B%E5%BC%8F%E8%AA%9E%E8%A8%80)

- **成果說明：**[成果説明](https://github.com/Dong-HuiYun/_sp/blob/master/%E7%BF%92%E9%A1%8C2_%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87%E7%A8%8B%E5%BC%8F%E8%AA%9E%E8%A8%80/README.md)

---

### 習題 3 -- 請用 AI 的 IDE，或命令列方式，做一個軟體專案 (或延伸其他專案修改)
- **完成狀況：** 藉由AI的幫助實作了C0模擬器以及簡易的文字冒險游戲。

- **程式碼/檔案路徑：** [習題3](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C3)

- **成果說明：**[成果説明](https://github.com/Dong-HuiYun/_sp/blob/master/%E7%BF%92%E9%A1%8C3/README.md)

---

### 習題 4 -- 用 AI 寫一本和系統程式有關的书，給大家看，網址貼上來 (放 github 上)

- **完成狀況：** 使用 OpenCode 書寫了一本描述系統程式的書籍，並大致理解了書中所描述的內容

- **電子書網址：** [習題4](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C4_%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E6%9B%B8%E7%B1%8D)

- **書籍成果：**從系統程式的基礎概念到進階應用，並附帶實際的程式碼説明，系統性地探討系統程式的所有核心領域。


---

### 習題 5 -- thread, race condition, mutex, deadlock 相關的程式

- **完成狀況：** 使用 AI 理解thread, race condition, mutex, deadlock，並實作了銀行存提款、消費者與生產者、哲學家用餐問題。

- **程式碼/檔案路徑：** [習題5](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C5)

- **成果說明：**[成果説明](https://github.com/Dong-HuiYun/_sp/blob/master/%E7%BF%92%E9%A1%8C5/README.md)


---

### 習題 6 -- 行程與檔案相關程式 (fork, execvp, close, open, read, write, dup2, stdin 0, stdout 1, stderr 2)

- **完成狀況：** 使用 AI 理解了行程與檔案相關的程式，並讓AI生成了視覺化的html檔解釋相關指令。

- **程式碼/檔案路徑：** [習題6](https://github.com/Dong-HuiYun/_sp/tree/master/%E7%BF%92%E9%A1%8C6)、[行程與檔案視覺化網站](https://dong-huiyun.github.io/_sp/習題6/行程與檔案.html)

- **成果說明：**[成果説明](https://github.com/Dong-HuiYun/_sp/blob/master/%E7%BF%92%E9%A1%8C6/README.md)


---

### 習題 7 -- 請先決定期中作業的題目貼上來

- **確認期中題目：** ：小型虛擬機實作系統程式

- **題目簡述：**模擬作業系統的操作，讓使用者能動態調整行程優先權、觸發死結偵測，並深入理解分頁錯誤與虛擬記憶體映射的技術細節。


---

### 期中作業：請寫一份『程式專案 + (報告或學習筆記)』等，必須是和本課程相關的主題！

- **專案名稱：** - **程式碼/報告路徑：** [期中作業](https://github.com/Dong-HuiYun/_sp/tree/master/%E6%9C%9F%E4%B8%AD%E4%BD%9C%E6%A5%AD_%E5%B0%8F%E5%9E%8Bos%E8%99%9B%E6%93%AC%E6%A9%9F)

- **專案詳細說明與心得：**本專案利用 Python 實作了一個微型作業系統與虛擬機，核心涵蓋 CPU 指令模擬、行程五狀態轉換及分頁記憶體管理。系統不僅支援多樣化的排程演算法（如 RR、SJF）與老化機制，更整合了死結偵測與號誌同步功能，並提供 CLI 指令列與 WSL 環境下的 PyQt6 視覺化儀表板。透過不斷詢問AI，新增更多系統程式相關的功能，而界面部分，從一開始的終端機指令輸入，到後續新增了GUI圖形化界面，讓人能直觀地看出作業系統的排程操作。