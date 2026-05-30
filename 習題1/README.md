這是一個為你的 **p0 語言編譯器** 量身打造的 `README.md`。它涵蓋了專案簡介、語法定義、核心架構以及如何在不同環境下執行。

---

# P0 語言編譯器與虛擬機 (P0 Compiler & VM)

這是一個用 C 語言實作的微型編譯器系統。它能夠將類 C 語法的 **p0 語言** 原始碼，編譯成中間碼（四元組，Quadruples），並在自製的虛擬機 (Virtual Machine) 上執行。

## 🚀 核心功能

- **完整編譯流程**：包含詞法分析 (Lexer)、語法解析 (Parser) 與中間碼生成。
- **支援算術運算**：支援 `+`, `-`, `*`, `/` 以及括號優先級處理。
- **流程控制**：支援 `if` 條件判斷與 `while` 迴圈（具備回填 Backpatching 技術）。
- **函數系統**：
    - 支援函數定義 (`func`) 與回傳值 (`return`)。
    - 支援**遞迴呼叫**（透過 Stack Frame 管理作用域）。
- **虛擬機 (VM)**：模擬 CPU 暫存器與記憶體堆疊，直接執行生成的四元組指令。

---

## 📋 p0 語法定義 (EBNF)

```ebnf
program       = { function_def | statement } ;
function_def  = "func" identifier "(" [ parameter_list ] ")" "{" { statement } "}" ;
statement     = if_statement | while_statement | assignment | return_statement ;
if_statement  = "if" "(" expression ")" "{" { statement } "}" ;
while_statement = "while" "(" expression ")" "{" { statement } "}" ;
expression    = arith_expr [ ( "==" | "<" | ">" ) arith_expr ] ;
factor        = number | identifier [ "(" [ args ] ")" ] | "(" expression ")" ;
```

---

## 🛠️ 執行環境需求

- 一個 C 語言編譯器（如 `gcc`, `clang` 或 `MSVC`）。
- 若在 Windows 上，建議使用 `MinGW` 或 `WSL`；macOS/Linux 則直接使用內建終端機。

---

## 💻 執行步驟

### 1. 編譯編譯器本身
在終端機（Terminal）中輸入以下指令：
```bash
gcc compiler.c -o compiler
```

### 2. 執行程式
你可以透過以下兩種方式執行：

#### A. 執行內建測試範例（預設 while 測試）
如果你不提供任何參數，程式會執行 `main` 函數中預設的 `i = 0; while (i < 5) { i = i + 1; }` 程式碼：
```bash
# Windows
./compiler.exe

# macOS / Linux
./compiler
```

#### B. 執行自定義的 p0 檔案
先建立一個檔案 `hello.p0`，內容如下：
```c
func factorial(n) {
    if (n == 1) { return 1; }
    return n * factorial(n - 1);
}

result = factorial(5);
```
然後執行：
```bash
./compiler hello.p0
```

---

## 📖 輸出說明

執行後，程式會輸出以下資訊：

1. **Intermediate Code (Quadruples)**：
   顯示編譯後產生的指令流。例如：
   - `IMM 5 - t1` (將立即值 5 存入 t1)
   - `JMP_F cond - 15` (若條件為假，跳轉到第 15 行)
2. **VM Execution Status**：
   顯示虛擬機開始執行的提示。
3. **Global Variables Result**：
   執行結束後，會印出所有**全域變數**的最終數值，這方便你驗證程式邏輯是否正確。

---

## 📂 檔案結構說明

- `compiler.c`: 核心程式碼，包含 Lexer, Parser, VM 全部的實作。
- `bnf.md`: p0 語言的完整語法邏輯定義。
- `README.md`: 本說明文件。

---

## 🧠 核心原理筆記

- **遞迴下降解析 (Recursive Descent)**：透過函數間的遞迴呼叫來處理運算優先級（Expression -> Term -> Factor）。
- **作用域管理**：VM 使用 `sp` (Stack Pointer) 指標。每次進入函數時 `sp++` 建立新 Frame，離開時 `sp--` 銷毀，這保證了遞迴時變數不會互相衝突。
- **回填 (Backpatching)**：在處理 `while` 迴圈時，由於編譯到開頭時還不知道結束位置，因此先用 `?` 佔位，等編譯完本體後再將地址補回。

---

*Enjoy coding with your own p0 language!*