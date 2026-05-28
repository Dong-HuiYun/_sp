import collections, threading
from io_utils import safe_print

class MessageQueue:
    def __init__(self):
        self._inboxes={}; self._lock=threading.Lock(); self._waiting={}
    def _ensure_inbox(self, pid):
        if pid not in self._inboxes: self._inboxes[pid]=collections.deque()
    def register(self, pid):
        with self._lock: self._ensure_inbox(pid)
    def unregister(self, pid):
        with self._lock: self._inboxes.pop(pid,None); self._waiting.pop(pid,None)
    def send(self, from_pid, to_pid, value):
        with self._lock:
            self._ensure_inbox(to_pid)
            self._inboxes[to_pid].append((from_pid,value))
            was_waiting=to_pid in self._waiting
        safe_print(f"[IPC] PID {from_pid} → PID {to_pid}: value={value}")
        return was_waiting
    def recv(self, pid):
        with self._lock:
            self._ensure_inbox(pid)
            return self._inboxes[pid].popleft() if self._inboxes[pid] else None
    def mark_waiting(self, process):
        with self._lock: self._waiting[process.pid]=process
    def pop_awakened(self):
        awakened=[]
        with self._lock:
            for pid in list(self._waiting.keys()):
                if self._inboxes.get(pid): awakened.append(self._waiting.pop(pid))
        return awakened
    def clear(self):
        with self._lock: self._inboxes.clear(); self._waiting.clear()
    def status(self):
        with self._lock:
            if not self._inboxes: return "  (no mailboxes)"
            return "\n".join(f"  PID {pid}: {len(list(inbox))} msg(s) → {list(inbox)}" for pid,inbox in self._inboxes.items())
