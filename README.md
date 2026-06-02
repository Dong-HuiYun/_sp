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

      [期中作業]()

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
- **完成狀況：** (已完成 / 未完成)
- **程式碼/檔案路徑：** `path/to/exercise3/`
- **成果說明：**
  *(請在此處說明專案的功能、所使用的開發環境或命令列工具，以及您的修改重點)*

---

### 習題 4 -- 用 AI 寫一本和系統程式有關的书，給大家看，網址貼上來 (放 github 上)
- **完成狀況：** (已完成 / 未完成)
- **電子書 GitHub 網址：** [請貼上您的電子書 Repo 連結](https://...)
- **書籍簡介與成果：**
  *(請在此處簡述這本系統程式書籍的章節架構與核心內容)*

---

### 習題 5 -- thread, race condition, mutex, deadlock 相關的程式
- **完成狀況：** (已完成 / 未完成)
- **程式碼/檔案路徑：** `path/to/exercise5/`
- **成果說明：**
  *(請在此處說明您的程式如何示範或解決多元執行緒中的 race condition、mutex 使用或 deadlock 狀況)*

---

### 習題 6 -- 行程與檔案相關程式 (fork, execvp, close, open, read, write, dup2, stdin 0, stdout 1, stderr 2)
- **完成狀況：** 使用 AI 理解了行程與檔案相關的程式，並讓AI生成了視覺化的html檔解釋相關指令。
- **程式碼/檔案路徑：** `path/to/exercise6/`
- **成果說明：**
  *(請在此處說明程式如何運用 fork、execvp 進行行程控制，以及如何操作檔案描述子與 I/O 重導向)*

---

### 習題 7 -- 請先決定期中作業的題目貼上來
- **確認期中題目：** ：小型虛擬機實作系統程式
- **題目簡述：**
  *(請在此處簡短說明這個題目想實作的內容與目標)*

---

### 期中作業：請寫一份『程式專案 + (報告或學習筆記)』等，必須是和本課程相關的主題！
- **專案名稱：** - **程式碼/報告路徑：** `path/to/midterm_project/`
- **專案詳細說明與心得：**
  *(請在此處詳細撰寫您的期中專案架構、實作技術、遇到的困難與解決方法，以及本課程相關主題的學習筆記)*