from io_utils import safe_print, prompt_input
import threading
from scheduler import ALGORITHMS

# ── DISK：示範程式（包含新指令集與 IPC 的範例）────────────────────────────
DISK = {
    # 原有程式
    "calc_add": [
        ("SET", "R1", 10), ("SET", "R2", 20), ("ADD", "R1", "R2"),
        ("PRINT", "R1"), ("HALT",)
    ],
    "counter": [
        ("SET", "R1", 1), ("PRINT", "R1"), ("SET", "R2", 1),
        ("ADD", "R1", "R2"), ("PRINT", "R1"), ("HALT",)
    ],
    "hello": [
        ("SET", "R1", 999), ("PRINT", "R1"), ("HALT",)
    ],

    # 新：有終止條件的計數迴圈（用 CMP + JNZ 取代死迴圈）
    # R1 從 1 數到 5：每次 +1，印出，直到 R1 == 5 停止
    "count5": [
        ("SET", "R1", 0),    # 0: R1 = 0
        ("SET", "R2", 1),    # 1: R2 = 1（步進值）
        ("SET", "R3", 5),    # 2: R3 = 5（上限）
        ("ADD", "R1", "R2"), # 3: R1 += 1
        ("PRINT", "R1"),     # 4: 印出
        ("CMP", "R1", "R3"), # 5: 比較 R1 與 R3
        ("JNZ", 3),          # 6: 若 R1 != R3 跳回 index 3
        ("HALT",),           # 7: R1 == R3 時結束
    ],

    # 新：計算 5 的階乘（5! = 120）
    # R1 = 累積乘積，R2 = 當前乘數，R3 = 終止條件 1
    "factorial": [
        ("SET", "R1", 1),    # 0: result = 1
        ("SET", "R2", 5),    # 1: n = 5
        ("SET", "R3", 1),    # 2: stop when n == 1
        ("MUL", "R1", "R2"), # 3: result *= n
        ("SET", "R4", 1),    # 4: R4 = 1（SUB 步進）
        ("SUB", "R2", "R4"), # 5: n -= 1
        ("CMP", "R2", "R3"), # 6: n == 1?
        ("JNZ", 3),          # 7: 不等於就繼續
        ("PRINT", "R1"),     # 8: 印出結果
        ("HALT",),           # 9
    ],

    # 新：IPC 發送方（PID 通常是 1，接收方是 2）
    # 先 run ipc_sender 再 run ipc_receiver，然後 start
    "ipc_sender": [
        ("SET",  "R1", 42),  # 0: 要傳的值
        ("SEND", 2,   "R1"), # 1: 傳給 PID 2
        ("PRINT","R1"),      # 2: 印出已送出的值
        ("HALT",),           # 3
    ],

    # 新：IPC 接收方
    "ipc_receiver": [
        ("RECV", "R1"),      # 0: 等待訊息（若空則 WAITING）
        ("PRINT","R1"),      # 1: 印出收到的值
        ("HALT",),           # 2
    ],
}

HELP_TEXT = """
Commands:
  ls                     列出所有可執行程式
  run <prog> [priority]  建立行程並加入 Ready Queue（priority 預設為 1）
  start [quantum]        在背景啟動排程器（quantum 預設為 2）
  ps                     顯示各佇列中的行程
  kill <pid>             強制終止指定行程
  top                    顯示所有行程的詳細統計資訊
  mem                    顯示記憶體分頁狀態
  ipc                    顯示各行程收件匣狀態
  sched [algo]           查看或切換排程演算法（FIFO/PRIORITY/ROUND_ROBIN/SJF）
  reset                  重置整個系統
  help                   顯示此說明
  exit                   離開
"""


class Shell:
    def __init__(self, os_kernel):
        self.os        = os_kernel
        self._os_thread = None

    def run(self):
        safe_print("Welcome to Python-Mini-OS v4.0")
        safe_print('Type "help" for available commands.\n')
        while True:
            try:
                line = prompt_input().strip().split()
                if not line:
                    continue
                cmd, args = line[0].lower(), line[1:]
            except EOFError:
                break
            handler = self._commands.get(cmd)
            if handler:
                handler(self, args)
            else:
                safe_print(f"Unknown command: '{cmd}'. Type 'help'.")

    # ── handlers ──────────────────────────────────────────────────────────

    def _cmd_exit(self, args):
        safe_print("Goodbye.")
        raise SystemExit(0)

    def _cmd_help(self, args):
        safe_print(HELP_TEXT)

    def _cmd_ls(self, args):
        safe_print("Available programs:")
        for name, prog in DISK.items():
            safe_print(f"  {name:<16} ({len(prog)} instructions)")

    def _cmd_run(self, args):
        if not args:
            safe_print("Usage: run <prog> [priority]")
            return
        name = args[0]
        if name not in DISK:
            safe_print(f"Error: '{name}' not found. Use 'ls'.")
            return
        try:
            priority = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            safe_print("Error: priority must be an integer.")
            return
        self.os.create_process(DISK[name], priority)

    def _cmd_start(self, args):
        if self._os_thread and self._os_thread.is_alive():
            safe_print("[Shell] Scheduler is already running.")
            return
        try:
            quantum = int(args[0]) if args else 2
        except ValueError:
            safe_print("Error: quantum must be an integer.")
            return
        # 排程器跑完後，在輸出一條分隔線，讓使用者知道可以繼續輸入
        def on_done():
            safe_print("\n--- [OS] All processes finished. ---")
        self.os.on_scheduler_done = on_done
        self._os_thread = threading.Thread(
            target=self.os.run, args=(quantum,), daemon=True
        )
        self._os_thread.start()
        safe_print(f"[Shell] Scheduler started (quantum={quantum}, algo={self.os.scheduler.algorithm}).")

    def _cmd_ps(self, args):
        with self.os.lock:
            ready = list(self.os.ready_queue)
        current = self.os.current_process
        waiting = list(self.os.waiting_list)

        safe_print(f"  Running : {f'PID:{current.pid}(Pri:{current.priority})' if current else 'None'}")
        safe_print(f"  Ready   : {[f'PID:{p.pid}(Pri:{p.priority})' for p in ready] or '(empty)'}")
        safe_print(f"  Waiting : {[f'PID:{p.pid}' for p in waiting] or '(empty)'}")

    def _cmd_top(self, args):
        procs = self.os.get_all_processes()
        if not procs:
            safe_print("  (no processes)")
            return
        safe_print(f"  {'PID':<5} {'STATE':<12} {'PRI':<5} {'INSTR':<8} {'CTX_SW':<8} {'WAIT':<10} {'AGE'}")
        safe_print("  " + "-" * 65)
        for p in procs:
            safe_print(p.stats.summary(p.pid, p.state, p.priority))

    def _cmd_mem(self, args):
        safe_print(self.os.memory_mgr.status())

    def _cmd_ipc(self, args):
        safe_print("[IPC] Inbox status:")
        safe_print(self.os.ipc.status())

    def _cmd_sched(self, args):
        if not args:
            safe_print(f"Current algorithm: {self.os.scheduler.algorithm}")
            safe_print(f"Available: {', '.join(ALGORITHMS)}")
            return
        try:
            self.os.scheduler.set_algorithm(args[0])
        except ValueError as e:
            safe_print(f"Error: {e}")

    def _cmd_kill(self, args):
        if not args:
            safe_print("Usage: kill <pid>")
            return
        try:
            self.os.kill_process(int(args[0]))
        except ValueError:
            safe_print("Error: PID must be an integer.")

    def _cmd_reset(self, args):
        self.os.reset_system()
        self._os_thread = None

    _commands = {
        "exit"  : _cmd_exit,
        "help"  : _cmd_help,
        "ls"    : _cmd_ls,
        "run"   : _cmd_run,
        "start" : _cmd_start,
        "ps"    : _cmd_ps,
        "top"   : _cmd_top,
        "mem"   : _cmd_mem,
        "ipc"   : _cmd_ipc,
        "sched" : _cmd_sched,
        "kill"  : _cmd_kill,
        "reset" : _cmd_reset,
    }