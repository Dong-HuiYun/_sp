from io_utils import safe_print
import collections
import time
import threading

from process   import Process, ProcessState
from memory    import MemoryManager
from scheduler import Scheduler
from ipc       import MessageQueue


class SimpleOS:
    def __init__(self, vm):
        self.vm              = vm
        self.ready_queue     = collections.deque()
        self.waiting_list    = []
        self.current_process = None
        self.next_pid        = 1
        self.lock            = threading.Lock()

        # 子模組
        self.memory_mgr = MemoryManager(total_frames=64)
        self.scheduler  = Scheduler("ROUND_ROBIN")
        self.ipc        = MessageQueue()

        # 所有曾建立的 process（含已結束），供 top 指令查閱
        self._all_processes = {}
        self.on_scheduler_done = None  # shell 設定的 callback

        # 注入 IPC 到 VM
        self.vm.ipc = self.ipc

    # ── 建立行程 ──────────────────────────────────────────────────────────
    def create_process(self, program, priority=1):
        p = Process(self.next_pid, program, priority)

        try:
            self.memory_mgr.allocate(p)
        except MemoryError as e:
            safe_print(e)
            return

        self.ipc.register(p.pid)
        p.transition(ProcessState.READY)

        with self.lock:
            self.ready_queue.append(p)
        self._all_processes[p.pid] = p

        safe_print(f"[OS] Process {p.pid} created (Priority: {priority}).")
        self.next_pid += 1

    # ── Context Switch ────────────────────────────────────────────────────
    def _context_switch(self, next_process):
        # 1. 儲存舊行程狀態
        if self.current_process:
            cp           = self.current_process
            cp.pc        = self.vm.registers['PC']
            cp.registers = {k: self.vm.registers[k] for k in ['R1','R2','R3','R4']}
            cp.flags     = dict(self.vm.flags)
            cp.memory    = list(self.vm.memory)
            cp.stats.on_context_switch()

            if not self.vm.halted and not self.vm.ipc_recv_block:
                cp.transition(ProcessState.READY)
                with self.lock:
                    self.scheduler.requeue(cp, self.ready_queue)
            elif self.vm.ipc_recv_block:
                cp.transition(ProcessState.WAITING)
                self.ipc.mark_waiting(cp)
                self.waiting_list.append(cp)
                self.vm.ipc_recv_block = False

        # 2. 載入新行程狀態
        next_process.transition(ProcessState.RUNNING)
        next_process.stats.on_context_switch()

        self.current_process    = next_process
        self.vm.registers['PC'] = next_process.pc
        for k, v in next_process.registers.items():
            self.vm.registers[k] = v
        self.vm.flags           = dict(next_process.flags)
        self.vm.memory          = list(next_process.memory)
        self.vm.halted          = False
        self.vm.ipc_recv_block  = False
        self.vm.current_pid     = next_process.pid

    # ── 排程器主迴圈 ──────────────────────────────────────────────────────
    def run(self, time_quantum=2):
        with self.lock:
            empty = len(self.ready_queue) == 0
        if empty and not self.current_process:
            safe_print("[OS] No processes to run.")
            return

        while True:
            self._wake_up_waiting()

            with self.lock:
                has_next = len(self.ready_queue) > 0

            if not has_next and (not self.current_process or self.vm.halted):
                if self.waiting_list:
                    time.sleep(0.1)
                    continue
                break

            if has_next:
                with self.lock:
                    next_p = self.scheduler.pick(self.ready_queue)
                self._context_switch(next_p)
                safe_print(
                    f"\n--- [OS] Switching to PID {self.current_process.pid} "
                    f"(Pri:{self.current_process.priority} "
                    f"algo:{self.scheduler.algorithm}) ---"
                )

            for _ in range(time_quantum):
                if self.vm.halted:
                    self._finish_current()
                    break
                if self.vm.ipc_recv_block:
                    self._move_current_to_waiting()
                    break
                self.vm.step()
                if self.current_process:
                    self.current_process.stats.on_instruction()
                time.sleep(0.3)

        # 所有 process 執行完畢，通知 shell 重新顯示提示符號
        if self.on_scheduler_done:
            self.on_scheduler_done()

    # ── 輔助 ──────────────────────────────────────────────────────────────
    def _finish_current(self):
        if not self.current_process:
            return
        cp = self.current_process
        cp.transition(ProcessState.TERMINATED)
        self.memory_mgr.free(cp.pid)
        self.ipc.unregister(cp.pid)
        safe_print(f"[OS] Process {cp.pid} finished.")
        self.current_process = None

    def _move_current_to_waiting(self):
        if not self.current_process:
            return
        cp           = self.current_process
        cp.pc        = self.vm.registers['PC']
        cp.registers = {k: self.vm.registers[k] for k in ['R1','R2','R3','R4']}
        cp.flags     = dict(self.vm.flags)
        cp.memory    = list(self.vm.memory)
        cp.transition(ProcessState.WAITING)
        self.ipc.mark_waiting(cp)
        self.waiting_list.append(cp)
        self.current_process   = None
        self.vm.ipc_recv_block = False

    def _wake_up_waiting(self):
        for p in self.ipc.pop_awakened():
            if p in self.waiting_list:
                self.waiting_list.remove(p)
            p.transition(ProcessState.READY)
            with self.lock:
                self.scheduler.requeue(p, self.ready_queue)
            safe_print(f"[OS] PID {p.pid} woken up, back to READY.")

    # ── Kill ──────────────────────────────────────────────────────────────
    def kill_process(self, pid):
        if self.current_process and self.current_process.pid == pid:
            self.current_process.transition(ProcessState.TERMINATED)
            self.vm.halted = True
            self.memory_mgr.free(pid)
            self.ipc.unregister(pid)
            self.current_process = None
            safe_print(f"\n[OS] Process {pid} killed (was running).")
            return

        with self.lock:
            target = next((p for p in self.ready_queue if p.pid == pid), None)
            if target:
                self.ready_queue.remove(target)
        if target:
            target.transition(ProcessState.TERMINATED)
            self.memory_mgr.free(pid)
            self.ipc.unregister(pid)
            safe_print(f"[OS] Process {pid} killed (was ready).")
            return

        target = next((p for p in self.waiting_list if p.pid == pid), None)
        if target:
            self.waiting_list.remove(target)
            target.transition(ProcessState.TERMINATED)
            self.memory_mgr.free(pid)
            self.ipc.unregister(pid)
            safe_print(f"[OS] Process {pid} killed (was waiting).")
            return

        safe_print(f"[OS] Error: Process {pid} not found.")

    # ── Reset ─────────────────────────────────────────────────────────────
    def reset_system(self):
        with self.lock:
            self.ready_queue.clear()
        self.waiting_list.clear()
        self.current_process = None
        self.next_pid        = 1
        self._all_processes.clear()
        self.ipc.clear()
        safe_print("[OS] System reset.")

    def get_all_processes(self):
        return list(self._all_processes.values())