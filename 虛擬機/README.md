# Python-Mini-OS v4.0 使用手冊

本系統是一個高度模擬現代作業系統核心功能的教育型虛擬機環境。它包含了 **分頁記憶體管理 (Paging)**、**可插拔排程演算法 (Scheduling)**、**行程間通訊 (IPC)** 以及一個自定義的 **16-bit 虛擬機器 (VM)**。

---

## 一、程式書寫指南 (Programming Guide)

在本系統中，程式是以 Python 列表的形式儲存在 `shell.py` 的 `DISK` 字典中。每個指令是一個 **元組 (Tuple)**。

### 虛擬機器架構
- **暫存器**: `R1`, `R2`, `R3`, `R4` (通用暫存器)
- **特殊暫存器**: `PC` (程式計數器), `IR` (指令暫存器)
- **狀態旗標**: `ZF` (Zero Flag, 零旗標), `SF` (Sign Flag, 負旗標)

### 指令集清單 (ISA)

| 指令 | 格式 | 說明 |
| :--- | :--- | :--- |
| **資料操作** | `("SET", Rd, val)` | 將數值 `val` 存入暫存器 `Rd` |
| | `("LOAD", Rd, addr)` | 從虛擬記憶體位址 `addr` 載入值到 `Rd` |
| | `("STORE", Rs, addr)` | 將暫存器 `Rs` 的值存入虛擬記憶體位址 `addr` |
| **算術運算** | `("ADD", Rd, Rs)` | `Rd = Rd + Rs` |
| | `("SUB", Rd, Rs)` | `Rd = Rd - Rs` |
| | `("MUL", Rd, Rs)` | `Rd = Rd * Rs` |
| **流程控制** | `("CMP", R1, R2)` | 比較兩值，設定 ZF (相等) 與 SF (R1 < R2) |
| | `("JUMP", addr)` | 無條件跳躍至索引 `addr` |
| | `("JZ", addr)` | 若 ZF 為真 (上一次比較相等) 則跳躍 |
| | `("JNZ", addr)` | 若 ZF 為假 (不相等) 則跳躍 |
| | `("HALT",)` | 停止執行，結束行程 |
| **行程通訊** | `("SEND", to_pid, Rs)` | 發送暫存器 `Rs` 的值給目標 PID |
| | `("RECV", Rd)` | 接收訊息並存入 `Rd`。若無訊息則進入 **WAITING** 狀態 |
| **其他** | `("PRINT", Rd)` | 在終端機印出暫存器 `Rd` 的當前值 |

---

## 二、Shell 指令說明

啟動 `main.py` 後，你可以透過 Shell 與 OS 互動：

### 行程管理
*   `ls`: 列出硬碟 (`DISK`) 中所有可用的程式。
*   `run <prog_name> [priority]`: 
    *   將程式載入記憶體並建立一個新行程。
    *   可選參數 `priority`（數字越大越優先，適用於 PRIORITY 演算法）。
*   `ps`: 顯示當前系統中 **Running**、**Ready** 與 **Waiting** 佇列中的行程。
*   `kill <pid>`: 強行終止指定 PID 的行程。
*   `top`: 顯示所有行程的詳細統計（包含執行指令數、上下文切換次數、等待時間等）。

### 系統控制
*   `start [quantum]`: 
    *   啟動 CPU 排程。
    *   `quantum` 為每個行程每次執行的指令數（預設為 2）。
*   `sched [algo]`: 
    *   不帶參數：顯示當前排程演算法。
    *   帶參數：切換演算法。支援 `FIFO` (先來先服務), `PRIORITY` (優先權), `ROUND_ROBIN` (輪轉法), `SJF` (最短工作優先)。
*   `reset`: 清空所有行程，重置記憶體與 IPC 狀態。

### 偵錯與監控
*   `mem`: 顯示實體記憶體頁框 (Frames) 的分配狀況與各行程的頁表 (Page Table)。
*   `ipc`: 檢查各個行程收件匣中的待處理訊息。

---

## 三、輸出訊息解讀

當系統運行時，終端機會印出不同模組的日誌，其含義如下：

#### [MemMgr] 記憶體管理
*   `allocated n page(s) → frames [x, y]`: 表示分頁機制成功執行。虛擬位址被映射到了實體的頁框編號。
*   `memory freed`: 行程結束後，對應的實體頁框已歸還給系統。

#### [OS] 作業系統核心
*   `Process n created`: PCB (行程控制區塊) 已建立，行程進入 Ready 狀態。
*   `Switching to PID n`: 發生了 **Context Switch (上下文切換)**。OS 儲存了舊行程的暫存器，並還原了新行程的狀態。
*   `PID n woken up`: 某行程原本在等待訊息，現在收到 `SEND` 被喚醒移回 Ready Queue。

#### [VM] 虛擬機器執行
*   `[VM Output] R1: 100`: 程式內部的 `PRINT` 指令輸出。
*   `RECV: inbox empty, entering WAITING`: 模擬阻塞型 I/O。行程會交出 CPU 使用權直到滿足條件。

#### [IPC] 行程間通訊
*   `PID 1 → PID 2: value=42`: 表示訊息已成功從來源行程的暫存器傳送到目標行程的收件匣。

---

## 4. 範例操作流程

如果你想測試 **IPC (行程通訊)** 功能：
1. `run ipc_receiver`: 建立接收者 (PID 1)。
2. `run ipc_sender`: 建立發送者 (PID 2)。
3. `ps`: 確認兩者都在 Ready Queue。
4. `start`: 啟動排程。
   *   你會看到 PID 1 先執行 `RECV`，因為收件匣空無一物而進入 `WAITING`。
   *   OS 切換到 PID 2 執行 `SEND`。
   *   OS 偵測到 PID 1 的需求被滿足，將其喚醒。
   *   最後 PID 1 執行剩餘指令並印出收到的值。


## 五. 輸入輸出解析

### 1. 多工處理+記憶體管理+優先權與演算法

#### 1. 檢查可使用程式：

 ```
    mini-os@user:~$ ls
    Available programs:
    calc_add         (5 instructions)
    counter          (6 instructions)
    hello            (3 instructions)
    count5           (8 instructions)
    factorial        (10 instructions)
    ipc_sender       (4 instructions)
    ipc_receiver     (3 instructions)

```
#### 2. 建立行程：

```

mini-os@user:~$ run hello
[MemMgr] PID 1: allocated 1 page(s) → frames [0]
[OS] Process 1 created (Priority: 1).

```

**輸入：**

`mini-os@user:~$ run hello`：要求系統執行名為 hello 的程式。

**輸出：**

`[MemMgr] PID 1: allocated 1 page(s) → frames [0]`：展現分頁機制（Paging），記憶體管理器（MemoryManager）為 PID 1 分配了 1 個頁面（Page），並將其放入實體記憶體的第 0 號頁框（Frame 0）。

`[OS] Process 1 created (Priority: 1).`：作業系統成功建立了 PID 1，預設優先權為 1。

#### 3. 建立行程並手動指定優先權

```

mini-os@user:~$ run calc_add 3
[MemMgr] PID 2: allocated 1 page(s) → frames [1]
[OS] Process 2 created (Priority: 3).

```

**輸入：**

`mini-os@user:~$ run calc_add 3`：執行 calc_add 程式，並手動指定優先權為 3（比 hello 高）。

**輸出：**

`[MemMgr] PID 2: allocated 1 page(s) → frames [1]`：記憶體管理器為 PID 2 分配了 1 個頁面，放入實體記憶體的第 1 號頁框

`[OS] Process 2 created (Priority: 3).`：作業系統建立了 PID 2，優先權設定為 3。

#### 4. 查看行程狀態

```

mini-os@user:~$ ps
  Running : None
  Ready   : ['PID:1(Pri:1)', 'PID:2(Pri:3)']
  Waiting : (empty)

```

**輸入：**

`mini-os@user:~$ ps`：列出目前系統中所有行程的狀態

**輸出：**

`Running : None`：目前沒有任何程式在 CPU 上執行（因為還沒輸入 start）。

`Ready   : ['PID:1(Pri:1)', 'PID:2(Pri:3)']`：PID 1 和 PID 2 都在 就緒佇列（Ready Queue） 等待被挑選。

`Waiting : (empty)`：目前沒有行程因為等待訊息（IPC）而阻塞。

#### 5. 啟動系統排程

```

mini-os@user:~$ start

--- [OS] Switching to PID 1 (Pri:1 algo:ROUND_ROBIN) ---
[Shell] Scheduler started (quantum=2, algo=ROUND_ROBIN).
[VM Output] R1: 999

--- [OS] Switching to PID 2 (Pri:3 algo:ROUND_ROBIN) ---

--- [OS] Switching to PID 1 (Pri:1 algo:ROUND_ROBIN) ---
[MemMgr] PID 1: memory freed.
[OS] Process 1 finished.

--- [OS] Switching to PID 2 (Pri:3 algo:ROUND_ROBIN) ---
[VM Output] R1: 30
[MemMgr] PID 2: memory freed.
[OS] Process 2 finished.

```

**輸入：**

`mini-os@user:~$ start`：啟動 OS 的核心排程迴圈。預設使用 Round Robin (輪轉法)，時間片（Quantum）為 2。

**輸出：**

`--- [OS] Switching to PID 1 (Pri:1 algo:ROUND_ROBIN) ---`：OS 從 Ready Queue 中取出第一個行程 PID 1，並進行 Context Switch（上下文切換），載入暫存器狀態，讓它開始在虛擬機器（VM）上執行。

`[Shell] Scheduler started (quantum=2, algo=ROUND_ROBIN).`：Shell 層發出確認訊息，提示背景排程執行緒已啟動。

`[VM Output] R1: 999`：PID 1 (hello) 執行了其內部的 PRINT R1 指令，印出了 999。

`--- [OS] Switching to PID 2 (Pri:3 algo:ROUND_ROBIN) ---`：因為 PID 1 的時間片用完了（或是到了切換點），OS 將 PID 1 切換下台，換上 PID 2。

`--- [OS] Switching to PID 1 (Pri:1 algo:ROUND_ROBIN) ---`：輪轉法再次切換，讓 PID 1 繼續執行。

`[MemMgr] PID 1: memory freed.` 與 `[OS] Process 1 finished.`：PID 1 執行到了 HALT 指令。OS 回收其佔用的實體記憶體（Frame 0），並將該行程標記為結束。

`--- [OS] Switching to PID 2 (Pri:3 algo:ROUND_ROBIN) ---`：只剩 PID 2 在執行了。

`[VM Output] R1: 30`：PID 2 (calc_add) 執行完加法（10+20）後印出了結果 30。

`[MemMgr] PID 2: memory freed.` 與 `[OS] Process 2 finished.`： PID 2 執行完成，釋放 Frame 1，系統任務全部結束。