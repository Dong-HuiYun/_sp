from io_utils import safe_print
import collections
import threading

# ─────────────────────────────────────────────
#  IPC：行程間通訊（Message Passing）
# ─────────────────────────────────────────────
#
#  每個 process 有一個收件匣（inbox）。
#  SEND 指令把訊息放入目標 process 的收件匣。
#  RECV 指令從自己的收件匣取出一則訊息：
#    - 有訊息 → 存入指定暫存器，繼續執行
#    - 無訊息 → process 進入 WAITING 狀態，等有人 SEND 才喚醒
#
#  OS kernel 透過 notify_waiting() 喚醒等待中的 process。

class MessageQueue:
    def __init__(self):
        self._inboxes  = {}           # pid → deque of (from_pid, value)
        self._lock     = threading.Lock()
        # 等待收件的 process：pid → Process 物件
        # OS kernel 負責把它從 waiting 移回 ready
        self._waiting  = {}

    # ── 確保收件匣存在 ────────────────────────────────────────────────────
    def _ensure_inbox(self, pid):
        if pid not in self._inboxes:
            self._inboxes[pid] = collections.deque()

    # ── 登記 process（建立收件匣）────────────────────────────────────────
    def register(self, pid):
        with self._lock:
            self._ensure_inbox(pid)

    # ── 取消登記（process 結束時清除）────────────────────────────────────
    def unregister(self, pid):
        with self._lock:
            self._inboxes.pop(pid, None)
            self._waiting.pop(pid, None)

    # ── SEND：放訊息進目標收件匣 ──────────────────────────────────────────
    def send(self, from_pid, to_pid, value):
        with self._lock:
            self._ensure_inbox(to_pid)
            self._inboxes[to_pid].append((from_pid, value))
            # 如果對方正在等待，標記可喚醒
            was_waiting = to_pid in self._waiting
        safe_print(f"[IPC] PID {from_pid} → PID {to_pid}: value={value}")
        return was_waiting   # 回傳 True 表示 OS 需要喚醒對方

    # ── RECV：從自己的收件匣取訊息 ───────────────────────────────────────
    #  回傳 (from_pid, value) 或 None（收件匣為空）
    def recv(self, pid):
        with self._lock:
            self._ensure_inbox(pid)
            if self._inboxes[pid]:
                return self._inboxes[pid].popleft()
            return None

    # ── 標記 process 進入等待（OS 呼叫）─────────────────────────────────
    def mark_waiting(self, process):
        with self._lock:
            self._waiting[process.pid] = process

    # ── 取出所有可喚醒的 process（OS 定期呼叫）───────────────────────────
    def pop_awakened(self):
        """回傳所有收件匣已有訊息、可從 WAITING 移回 READY 的 process 列表"""
        awakened = []
        with self._lock:
            for pid in list(self._waiting.keys()):
                if self._inboxes.get(pid):
                    awakened.append(self._waiting.pop(pid))
        return awakened

    # ── 清除所有狀態（reset 時呼叫）──────────────────────────────────────
    def clear(self):
        with self._lock:
            self._inboxes.clear()
            self._waiting.clear()

    # ── 顯示各 process 收件匣內容 ────────────────────────────────────────
    def status(self):
        with self._lock:
            if not self._inboxes:
                return "  (no mailboxes)"
            lines = []
            for pid, inbox in self._inboxes.items():
                msgs = list(inbox)
                lines.append(f"  PID {pid}: {len(msgs)} message(s) → {msgs}")
            return "\n".join(lines)