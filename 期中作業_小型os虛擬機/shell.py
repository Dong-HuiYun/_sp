from io_utils import safe_print, prompt_input
import threading, os
import readline
from scheduler import ALGORITHMS
from assembler import load_file, disassemble, AssemblerError
from tui import launch_tui

DISK={
    "calc_add":[("SET","R1",10),("SET","R2",20),("ADD","R1","R2"),("PRINT","R1"),("HALT",)],
    "hello":[("SET","R1",999),("PRINT","R1"),("HALT",)],
    "count5":[("SET","R1",0),("SET","R2",1),("SET","R3",5),("ADD","R1","R2"),("PRINT","R1"),("CMP","R1","R3"),("JNZ",3),("HALT",)],
    "factorial":[("SET","R1",1),("SET","R2",5),("SET","R3",1),("MUL","R1","R2"),("SET","R4",1),("SUB","R2","R4"),("CMP","R2","R3"),("JNZ",3),("PRINT","R1"),("HALT",)],
    "ipc_sender":[("SET","R1",42),("SEND",2,"R1"),("PRINT","R1"),("HALT",)],
    "ipc_receiver":[("RECV","R1"),("PRINT","R1"),("HALT",)],
    "mutex_demo":[("WAIT",0),("SET","R1",42),("PRINT","R1"),("SET","R2",1),("ADD","R1","R2"),("PRINT","R1"),("SIGNAL",0),("HALT",)],
}

HELP_TEXT="""
=== Process ===
  ls / run <prog> [pri] / start [quantum] / ps / kill <pid> / reset
=== Monitor ===
  top / mem / ipc / sem [list|create [val] [name]] / deadlock [resolve] / tui
=== Scheduler ===
  sched [algo]   (FIFO / PRIORITY / ROUND_ROBIN / SJF)
  aging [on|off]
=== Loader ===
  load <file.asm> [pri]  /  lsasm [dir]  /  disasm <prog>
=== History ===
  history  /  !<n>
  help / exit
"""

class Shell:
    def __init__(self, os_kernel):
        self.os = os_kernel
        self._os_thread = None
        self._history = []
        
        # 關閉自動紀錄，由我們手動控制 (解決按兩次的問題)
        if readline:
            try:
                readline.set_auto_history(False)
            except AttributeError:
                pass # 某些版本可能沒這個函式，不影響

        self.histfile = os.path.expanduser("~/.mini_os_history")
        try:
            if os.path.exists(self.histfile):
                readline.read_history_file(self.histfile)
                # 重要：同步載入檔案內的紀錄到你的 _history 清單中
                # readline 的索引是從 1 開始的
                for i in range(1, readline.get_current_history_length() + 1):
                    item = readline.get_history_item(i)
                    if item:
                        self._history.append(item)
        except Exception:
            pass

    def run(self):
        safe_print("Welcome to Python-Mini-OS v5.0")
        safe_print('Type "help" for available commands.\n')
        while True:
            try: 
                raw = prompt_input()
            except EOFError: break
            except KeyboardInterrupt:
                print()
                continue
            
            line = raw.strip()
            if not line: continue

            # 1. 處理 !n 轉換 (我們只記錄轉換後的結果)
            if line.startswith("!"):
                line = self._recall(line)
                if line is None: continue
                safe_print(f"  >> {line}")

            # 2. 處理 Readline 系統歷史紀錄 (用於按上下鍵)
            # 取得當前 readline 緩衝區最後一筆
            curr_len = readline.get_current_history_length()
            last_item = readline.get_history_item(curr_len) if curr_len > 0 else None

            # 只有當目前指令不等於上一筆時才加入，避免按上下鍵時卡在重複指令上
            if line != last_item:
                readline.add_history(line)
                try:
                    readline.write_history_file(self.histfile)
                except:
                    pass

            # 3. 更新你自己的 history 清單 (用於 !n 查詢)
            # 也要避免重複加入 self._history 導致 !n 列表太亂
            if not self._history or self._history[-1] != line:
                self._history.append(line)

            # 4. 解析與執行指令
            tokens = line.split()
            cmd, args = tokens[0].lower(), tokens[1:]
            handler = self._commands.get(cmd)
            if handler: handler(self, args)
            else: safe_print(f"Unknown command: '{cmd}'. Type 'help'.")

    def _recall(self, token):
        try: n=int(token[1:])
        except ValueError: safe_print("Usage: !<number>"); return None
        if n<1 or n>len(self._history): safe_print(f"No history entry {n}."); return None
        return self._history[n-1]

    def _cmd_exit(self,a): safe_print("Goodbye."); raise SystemExit(0)
    def _cmd_help(self,a): safe_print(HELP_TEXT)
    def _cmd_ls(self,a):
        safe_print("Built-in programs:")
        for name,prog in DISK.items(): safe_print(f"  {name:<16} ({len(prog)} instructions)")
    def _cmd_run(self,a):
        if not a: safe_print("Usage: run <prog> [priority]"); return
        if a[0] not in DISK: safe_print(f"Error: '{a[0]}' not found."); return
        try: pri=int(a[1]) if len(a)>1 else 1
        except ValueError: safe_print("Error: priority must be int."); return
        self.os.create_process(DISK[a[0]],pri)
    def _cmd_start(self,a):
        if self._os_thread and self._os_thread.is_alive():
            safe_print("[Shell] Scheduler already running."); return
        try: q=int(a[0]) if a else 2
        except ValueError: safe_print("Error: quantum must be int."); return
        def on_done(): safe_print("\n--- [OS] All processes finished. ---")
        self.os.on_scheduler_done=on_done
        self._os_thread=threading.Thread(target=self.os.run,args=(q,),daemon=True)
        self._os_thread.start()
        safe_print(f"[Shell] Scheduler started (quantum={q}, algo={self.os.scheduler.algorithm}).")
    def _cmd_ps(self,a):
        with self.os.lock: ready=list(self.os.ready_queue)
        cur=self.os.current_process; wait=list(self.os.waiting_list)
        safe_print(f"  Running : {f'PID:{cur.pid}(Pri:{cur.priority})' if cur else 'None'}")
        safe_print(f"  Ready   : {[f'PID:{p.pid}(Pri:{p.priority})' for p in ready] or '(empty)'}")
        safe_print(f"  Waiting : {[f'PID:{p.pid}' for p in wait] or '(empty)'}")
    def _cmd_top(self,a):
        procs=self.os.get_all_processes()
        if not procs: safe_print("  (no processes)"); return
        safe_print(f"  {'PID':<5}{'STATE':<12}{'PRI':<10}{'INSTR':<8}{'CTX_SW':<8}{'WAIT':<10}AGE")
        safe_print("  "+"-"*65)
        for p in procs: safe_print(p.stats.summary(p.pid,p.state,p.priority,p.original_priority))
    def _cmd_kill(self,a):
        if not a: safe_print("Usage: kill <pid>"); return
        try: self.os.kill_process(int(a[0]))
        except ValueError: safe_print("Error: PID must be int.")
    def _cmd_reset(self,a): self.os.reset_system(); self._os_thread=None
    def _cmd_mem(self,a): safe_print(self.os.memory_mgr.status())
    def _cmd_ipc(self,a): safe_print("[IPC] Inbox status:\n"+self.os.ipc.status())
    def _cmd_sched(self,a):
        if not a: safe_print(f"Current: {self.os.scheduler.algorithm}  Available: {', '.join(ALGORITHMS)}"); return
        try: self.os.scheduler.set_algorithm(a[0])
        except ValueError as e: safe_print(f"Error: {e}")
    def _cmd_aging(self,a):
        if not a: safe_print(f"Aging: {'ON' if self.os.aging_enabled else 'OFF'}  interval={self.os.aging_interval}s"); return
        if a[0].lower()=="on": self.os.aging_enabled=True; safe_print("[OS] Aging enabled.")
        elif a[0].lower()=="off": self.os.aging_enabled=False; safe_print("[OS] Aging disabled.")
        else: safe_print("Usage: aging [on|off]")
    def _cmd_sem(self,a):
        if not a or a[0]=="list": safe_print("[Semaphores]\n"+self.os.sem_manager.status()); return
        if a[0]=="create":
            val=int(a[1]) if len(a)>1 else 1; name=a[2] if len(a)>2 else ""
            sid=self.os.sem_manager.create(val,name); safe_print(f"Created semaphore id={sid}")
        else: safe_print("Usage: sem [list | create [value] [name]]")
    def _cmd_deadlock(self,a):
        cycles=self.os.deadlock.detect(self.os.sem_manager,self.os.waiting_list)
        safe_print(self.os.deadlock.report(cycles))
        if cycles and a and a[0]=="resolve": self.os.deadlock.auto_resolve(cycles,self.os)
    def _cmd_tui(self,a):
        safe_print("[Shell] Launching TUI... (press q to exit)")
        try: launch_tui(self.os)
        except Exception as e: safe_print(f"[TUI] Error: {e}")
        safe_print("[Shell] TUI closed.")
    def _cmd_load(self,a):
        if not a: safe_print("Usage: load <file.asm> [priority]"); return
        try: pri=int(a[1]) if len(a)>1 else 1
        except ValueError: safe_print("Error: priority must be int."); return
        try: program=load_file(a[0]); self.os.create_process(program,pri)
        except Exception as e: safe_print(f"[ASM] Error: {e}")
    def _cmd_lsasm(self,a):
        d=a[0] if a else "programs"
        if not os.path.isdir(d): safe_print(f"Directory '{d}' not found."); return
        files=[f for f in os.listdir(d) if f.endswith(".asm")]
        if not files: safe_print(f"No .asm files in '{d}'."); return
        safe_print(f".asm files in '{d}':") 
        for f in sorted(files): safe_print(f"  {f}")
    def _cmd_disasm(self,a):
        if not a: safe_print("Usage: disasm <prog>"); return
        if a[0] not in DISK: safe_print(f"Error: '{a[0]}' not in built-in DISK."); return
        safe_print(f"Disassembly of '{a[0]}':\n"+disassemble(DISK[a[0]]))
    def _cmd_history(self,a):
        if not self._history: safe_print("  (no history)"); return
        for i,cmd in enumerate(self._history,1): safe_print(f"  {i:>3}  {cmd}")

    _commands={
        "exit":_cmd_exit,"help":_cmd_help,"ls":_cmd_ls,"run":_cmd_run,
        "start":_cmd_start,"ps":_cmd_ps,"top":_cmd_top,"kill":_cmd_kill,
        "reset":_cmd_reset,"mem":_cmd_mem,"ipc":_cmd_ipc,"sched":_cmd_sched,
        "aging":_cmd_aging,"sem":_cmd_sem,"deadlock":_cmd_deadlock,"tui":_cmd_tui,
        "load":_cmd_load,"lsasm":_cmd_lsasm,"disasm":_cmd_disasm,"history":_cmd_history,
    }
