# Unix 行程與檔案系統呼叫 — Python 範例說明

本文件說明六個 Python 程式，示範如何透過 `os` 模組直接呼叫 Unix 系統呼叫，  
包含行程管理（fork、exec、wait）與低階檔案 I/O（open、read、write、close、dup2）。

> **注意：** `os.fork()` 僅在 Linux / macOS 可用，Windows 不支援。

> **執行：** 進入 `wsl` 環境中，輸入`python3 檔名`執行程式。

---

## 目錄

1. [背景知識](#背景知識)
2. [01_fork.py](#01_fork)
3. [02_fork_execvp](#02_fork_execvp)
4. [03_open_read_write](#03_open_read_write)
5. [04_dup2_redirect](#04_dup2_redirect)
6. [05_pipe_fork](#05_pipe_fork)
7. [06_pipe_bidirectional](#06_pipe_bidirectional)

---

## 背景知識

檔案描述符（File Descriptor）

每個行程都持有一張 **fd 表**，由 kernel 維護：

| fd | 名稱   | 預設連接 |
|----|--------|---------|
| 0  | stdin  | 鍵盤    |
| 1  | stdout | 終端機  |
| 2  | stderr | 終端機  |
| 3+ | 使用者 | `open()` 依序分配 |

程式啟動時，fd 0、1、2 已自動開啟。呼叫 `open()` 會從最小可用號碼（通常是 3）開始分配。

---

## 01_fork

檔名：`01_fork.py`

 `fork()` 建立子行程

### 目的

示範 `fork()` 如何將目前行程複製成父子兩個行程，以及如何用 `waitpid()` 等待子行程結束。

### 程式碼

```python

import os
import sys

pid = os.fork()

if pid < 0:
    print("fork 失敗", file=sys.stderr)
    sys.exit(1)

elif pid == 0:
    # 子行程
    print(f"[子] pid={os.getpid()}, 父 pid={os.getppid()}")
    sys.exit(0)

else:
    # 父行程
    print(f"[父] pid={os.getpid()}, 子 pid={pid}")
    _, status = os.waitpid(pid, 0)
    print(f"[父] 子行程結束，exit code={os.WEXITSTATUS(status)}")

```

### 說明

`os.fork()` 複製一個子行程，呼叫一次，**回傳兩次**：

- 父行程得到子行程的 pid（正整數）
- 子行程得到 `0`
- 失敗則回傳負數

`os.waitpid(pid, 0)` 讓父行程阻塞，直到子行程結束，避免產生殭屍行程（zombie process）。  
`os.WEXITSTATUS(status)` 從 wait 的狀態值中取出結束狀態碼（exit code）。
| 狀態碼 | 代表意義   | 出現時機 |
|----|--------|---------|
| 0  | 成功 (Success)  | 程式完美執行結束。    |
| 1  | 通用錯誤 (General Error) | 程式出錯，但沒有特別歸類。  |
| 2	| 語法或用法錯誤 | 呼叫指令時輸入了錯誤的參數

### 執行結果

PID 是 OS 動態分配的 id，每次執行程式都會重新發放，因此每次執行程式的pid不一定相同。當父形成呼叫fork()建立子行程時，系統為子行程分配下一個可用的 PID。

![01執行結果圖](images/01.png)

## 02_fork_execvp

`fork()` + `execvp()` 執行新程式

### 目的

在子行程中用 `execvp()` 載入並執行另一個程式（此例為 `ls -l`），  
父行程繼續等待子行程完成。

### 程式碼

```python

import os
import sys

pid = os.fork()

if pid == 0:
    os.execvp("ls", ["ls", "-l"])
    print("execvp 失敗", file=sys.stderr)
    sys.exit(1)

else:
    _, status = os.waitpid(pid, 0)
    print(f"[父] ls 結束，exit code={os.WEXITSTATUS(status)}")

```

### 說明

`pid = os.fork()` 建立子行程

`os.execvp(file, args)` 用指定的程式**取代**目前子行程的記憶體映像：

- 第一個參數是程式名稱，會在 `PATH` 中搜尋
- 第二個參數是引數串列，慣例上 `args[0]` 與程式名相同
- **成功後不會返回**；失敗才會繼續執行後面的 `perror`

這是 shell 實作命令執行的核心機制：先 `fork()` 再 `exec()`。

`os.execvp("ls", ["ls", "-l"])`：替換子行程的程式內容，變成執行 `ls -l`。

`_, status = os.waitpid(pid, 0)`：回傳兩個值(returned_pid, status)，忽略結束的子行程 PID，僅保留子行程的結束狀態編碼。父行程等待子行程結束後，並取得其結束狀態。

### 執行結果

執行程式與在終端機輸入`ls -l`達到了相同的效果。

![02執行結果圖](images/02.png)

## 03_open_read_write

檔名：`03_open_read_write.py`

低階檔案 I/O

### 目的

示範不經過 Python 標準函式庫，直接用系統呼叫層級的 `open`、`read`、`write`、`close` 操作檔案。

### 程式碼

```python

import os

# 寫入
fd = os.open("hello.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
os.write(fd, b"Hello, File I/O!\n")
os.close(fd)

# 讀取
fd = os.open("hello.txt", os.O_RDONLY)
while True:
    data = os.read(fd, 128)
    if not data:
        break
    os.write(1, data)  # 直接寫到 stdout (fd=1)
os.close(fd)

# 附加
fd = os.open("hello.txt", os.O_WRONLY | os.O_APPEND)
os.write(fd, "附加一行\n".encode())
os.close(fd)

```

### 說明

**`os.open()` 旗標：**

| 旗標         | 意義                 |
|--------------|----------------------|
| `O_RDONLY`   | 唯讀                 |
| `O_WRONLY`   | 唯寫                 |
| `O_CREAT`    | 不存在則建立         |
| `O_TRUNC`    | 開啟時截斷為空       |
| `O_APPEND`   | 每次寫入自動移到末尾 |

第三個參數 `0o644` 是建立新檔時的權限（擁有者可讀寫，群組/其他人唯讀）。

`os.read(fd, n)` 最多讀取 `n` bytes，回傳空 bytes `b""` 代表到達 EOF。  
`os.write(fd, data)` 回傳實際寫入的 bytes 數，正式程式應在迴圈中確認寫完。

### 執行結果

![03執行結果圖](images/03.png)

---

## 04_dup2_redirect

`dup2()` 重新導向 stdout

### 目的

示範如何用 `dup2()` 把標準輸出（fd 1）重新導向到一個檔案（out.txt），  
這正是 shell 中 `> file` 的底層實作。

### 程式碼

```python

import os

fd = os.open("out.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

os.dup2(fd, 1)   # fd 1 (stdout) → out.txt
os.close(fd)

os.write(1, b"這行會寫進 out.txt\n")
os.write(2, b"這行還是去終端機 (stderr)\n")

```

### 說明

`os.dup2(oldfd, newfd)` 讓 `newfd` 成為 `oldfd` 的複製：

- 若 `newfd` 已開啟，會先關閉它
- 之後對 `newfd` 的所有操作，效果與 `oldfd` 相同

呼叫 `dup2(fd, 1)` 後，`fd` 和 `1` 都指向同一個檔案，  
所以要 `close(fd)` 把原本的 fd 釋放，避免浪費。

**常見用途：**

| 目的             | 呼叫                   | 對應 shell 語法 |
|------------------|------------------------|-----------------|
| stdout → 檔案    | `dup2(fd, 1)`          | `> file`        |
| stdin ← 檔案     | `dup2(fd, 0)`          | `< file`        |
| stderr → stdout  | `dup2(1, 2)`           | `2>&1`          |

### 執行結果

![04執行結果圖](images/04.png)

## 05_pipe_fork

`pipe()` + `fork()` 模擬 `ls | wc -l`

### 目的

用 `pipe()` 建立單向通道，結合 `fork()` 和 `dup2()` 連接兩個行程的 stdout / stdin，  
實作 shell pipeline 的底層機制。

### 程式碼

```python

import os

r_fd, w_fd = os.pipe()

pid = os.fork()

if pid == 0:
    # 子行程：ls，stdout → pipe 寫端
    os.close(r_fd)
    os.dup2(w_fd, 1)
    os.close(w_fd)
    os.execvp("ls", ["ls"])

else:
    # 父行程：wc -l，stdin ← pipe 讀端
    os.close(w_fd)
    os.dup2(r_fd, 0)
    os.close(r_fd)
    os.execvp("wc", ["wc", "-l"])

```

### 說明

 `ls` 的輸出會透過已經設定好的 pipe 送給父行程的 `wc -l`。也就是先執行 `ls` 列出檔案，再把結果送給 `wc -l` 計算行數。

`os.pipe()` 建立管道，建立一對相連的 fd，

`r_fd`是管道的讀取端（read），`w_fd`是管道的寫入端（write）

`s.execvp("ls", ["ls"]) `中的第一個 ls 是「告訴系統要執行哪個程式檔案」，第二個 ls 是「把它變成 ls 程式內部的 argv[0]」

```

子行程 stdout → [w_fd] ===pipe=== [r_fd] → 父行程 stdin

```

**關閉不需要的端很重要：**

- 子行程不讀，所以 `close(r_fd)`
- 父行程不寫，所以 `close(w_fd)`
- 若父行程沒有 `close(w_fd)`，`wc` 的 `read()` 永遠不會得到 EOF，程式會卡住

### 執行結果

![05執行結果圖](images/05.png)

（當前目錄有 10 個檔案）

---

## 06_pipe_bidirectional

雙向 pipe 通訊

### 目的
使用兩條 pipe 實現父子行程的雙向互傳訊息（ping-pong），  
示範多 fd 管理的基本模式。

### 程式碼

```python

import os

p2c_r, p2c_w = os.pipe()   # 父 → 子 (父行程寫，子行程讀，父傳訊息給子)
c2p_r, c2p_w = os.pipe()   # 子 → 父（子行程寫，父行程讀，子傳訊息給父）

pid = os.fork()

if pid == 0:
    os.close(p2c_w) # 關閉 父 → 子 的寫入端
    os.close(c2p_r) # 關閉 子 → 父 的讀取端

    msg = os.read(p2c_r, 256) # 沒訊息時阻塞等待
    print(f"[子] 收到：{msg.decode().strip()}")
    os.close(p2c_r)

    os.write(c2p_w, b"pong\n")
    os.close(c2p_w)

else:
    os.close(p2c_r) # 父 → 子
    os.close(c2p_w) # 子 → 父

    os.write(p2c_w, b"ping\n")
    os.close(p2c_w)

    reply = os.read(c2p_r, 256)
    print(f"[父] 收到：{reply.decode().strip()}")
    os.close(c2p_r)

    os.waitpid(pid, 0) # 回收資源
```

### 說明

一條 pipe 只能單向流動，所以雙向通訊需要兩條：

1. 父行程 透過第一條管道（p2c）發送 "ping" 給 子行程

2. 子行程 收到 "ping" 後，回傳 "pong" 給父行程（透過第二條管道 c2p）

3. 父行程 收到 "pong" 後印出來

```

父行程 ──[p2c_w]──pipe──[p2c_r]──▶ 子行程
父行程 ◀──[c2p_r]──pipe──[c2p_w]── 子行程

```

`fork()` 後，父子行程都持有四個 fd 的副本，各自關閉不會用到的那端：

| 行程 | 關閉         | 保留         |
|------|--------------|--------------|
| 子   | `p2c_w`, `c2p_r` | `p2c_r`（讀）, `c2p_w`（寫）|
| 父   | `p2c_r`, `c2p_w` | `p2c_w`（寫）, `c2p_r`（讀）|

寫完後必須 `close(p2c_w)`，讓子行程的 `read()` 能夠得到 EOF，否則會死鎖。

### 執行結果

![06執行結果圖](images/06.png)

## 系統呼叫對照表

| Unix C 函式            | Python `os` 模組          | 說明                          |
|------------------------|---------------------------|-------------------------------|
| `fork()`               | `os.fork()`               | 複製行程                      |
| `execvp(f, argv)`      | `os.execvp(f, argv)`      | 載入新程式取代目前行程        |
| `waitpid(pid, 0)`      | `os.waitpid(pid, 0)`      | 等待子行程結束                |
| `open(path, flags, mode)` | `os.open(path, flags, mode)` | 開啟/建立檔案            |
| `read(fd, n)`          | `os.read(fd, n)`          | 從 fd 讀取最多 n bytes        |
| `write(fd, buf)`       | `os.write(fd, buf)`       | 向 fd 寫入 bytes              |
| `close(fd)`            | `os.close(fd)`            | 關閉 fd                       |
| `dup2(old, new)`       | `os.dup2(old, new)`       | 複製 fd，讓 new 指向 old      |
| `pipe()`               | `os.pipe()`               | 建立單向通道，回傳 (r, w)     |
