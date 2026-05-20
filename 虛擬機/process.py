from io_utils import safe_print
import time
from enum import Enum, auto

# ─────────────────────────────────────────────
#  Process 狀態機
# ─────────────────────────────────────────────
#
#   NEW ──► READY ──► RUNNING ──► TERMINATED
#                ▲       │
#                │       ▼
#             WAITING ◄──┘  (等待 I/O 或 IPC 訊息)
#
class ProcessState(Enum):
    NEW        = auto()
    READY      = auto()
    RUNNING    = auto()
    WAITING    = auto()   # 等待 IPC 訊息（RECV 時收件匣為空）
    TERMINATED = auto()


# ─────────────────────────────────────────────
#  統計資訊
# ─────────────────────────────────────────────
class ProcessStats:
    def __init__(self):
        self.created_at          = time.time()   # 建立時刻 (Unix timestamp)
        self.cpu_instructions    = 0             # 執行過幾條指令
        self.context_switches    = 0             # 被切換幾次
        self.waiting_time        = 0.0           # 在 READY queue 等待的累積秒數
        self._ready_since        = time.time()   # 上次進入 READY 的時刻

    # ── 狀態轉換時呼叫 ────────────────────────────────────────────────────
    def on_enter_ready(self):
        self._ready_since = time.time()

    def on_leave_ready(self):
        self.waiting_time += time.time() - self._ready_since

    def on_context_switch(self):
        self.context_switches += 1

    def on_instruction(self):
        self.cpu_instructions += 1

    # ── 格式化輸出（給 `top` 指令用）────────────────────────────────────
    def summary(self, pid, state, priority):
        age = time.time() - self.created_at
        return (
            f"  PID:{pid:<4} state:{state.name:<11} pri:{priority:<3} "
            f"instr:{self.cpu_instructions:<6} "
            f"ctx_sw:{self.context_switches:<4} "
            f"wait:{self.waiting_time:.2f}s  "
            f"age:{age:.1f}s"
        )


# ─────────────────────────────────────────────
#  Process（含分頁欄位，由 MemoryManager 填入）
# ─────────────────────────────────────────────
class Process:
    def __init__(self, pid, program, priority=1):
        self.pid      = pid
        self.program  = program
        self.priority = priority

        # 狀態機
        self.state = ProcessState.NEW

        # CPU 快照（context switch 時儲存/還原）
        self.pc        = 0
        self.registers = {'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0}
        self.flags     = {'ZF': False, 'SF': False}  # Zero / Sign flag
        self.memory    = []   # 由 MemoryManager 分配後填入

        # 統計
        self.stats = ProcessStats()

    def transition(self, new_state: ProcessState):
        """集中管理狀態轉換，順便觸發統計 hook"""
        old = self.state

        # 離開 READY → 停止計時等待時間
        if old == ProcessState.READY and new_state != ProcessState.READY:
            self.stats.on_leave_ready()

        # 進入 READY → 開始計時等待時間
        if new_state == ProcessState.READY and old != ProcessState.READY:
            self.stats.on_enter_ready()

        self.state = new_state