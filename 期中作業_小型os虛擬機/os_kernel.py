from io_utils import safe_print
import collections, time, threading
from process   import Process, ProcessState
from memory    import MemoryManager, PAGE_SIZE
from scheduler import Scheduler
from ipc       import MessageQueue
from semaphore import SemaphoreManager
from deadlock  import DeadlockDetector

class SimpleOS:
    def __init__(self, vm):
        self.vm=vm; self.ready_queue=collections.deque()
        self.waiting_list=[]; self.current_process=None
        self.next_pid=1; self.lock=threading.Lock()
        self.memory_mgr=MemoryManager(total_frames=64)
        self.scheduler=Scheduler("ROUND_ROBIN")
        self.ipc=MessageQueue(); self.sem_manager=SemaphoreManager()
        self.deadlock=DeadlockDetector()
        self._all_processes={}; self.on_scheduler_done=None
        self.aging_enabled=True; self.aging_interval=3.0
        self.aging_amount=1; self._last_aging=time.time()
        self.vm.ipc=self.ipc; self.vm.sem_manager=self.sem_manager

    def create_process(self, program, priority=1):
        p=Process(self.next_pid,program,priority)
        try: self.memory_mgr.allocate(p)
        except MemoryError as e: safe_print(str(e)); return None
        self.ipc.register(p.pid); p.transition(ProcessState.READY)
        with self.lock: self.ready_queue.append(p)
        self._all_processes[p.pid]=p
        safe_print(f"[OS] Process {p.pid} created (Priority: {priority}).")
        self.next_pid+=1; return p.pid

    def _context_switch(self, next_process):
        if self.current_process:
            cp=self.current_process
            cp.pc=self.vm.registers['PC']
            cp.registers={k:self.vm.registers[k] for k in ['R1','R2','R3','R4']}
            cp.flags=dict(self.vm.flags); cp.memory=list(self.vm.memory)
            cp.stats.on_context_switch()
            if not self.vm.halted and not self.vm.ipc_recv_block and not self.vm.sem_block:
                cp.transition(ProcessState.READY)
                with self.lock: self.scheduler.requeue(cp,self.ready_queue)
            elif self.vm.ipc_recv_block:
                cp.transition(ProcessState.WAITING); self.ipc.mark_waiting(cp)
                self.waiting_list.append(cp); self.vm.ipc_recv_block=False
            elif self.vm.sem_block:
                sem_id=self.vm._pending_sem_id; self.vm.sem_block=False
                blocked=self.sem_manager.wait(sem_id,cp)
                if blocked:
                    cp.waiting_sem_id=sem_id; cp.transition(ProcessState.WAITING)
                    self.waiting_list.append(cp)
                else:
                    self.sem_manager._holders[sem_id]=cp.pid
                    cp.transition(ProcessState.READY)
                    with self.lock: self.scheduler.requeue(cp,self.ready_queue)
        next_process.transition(ProcessState.RUNNING)
        next_process.stats.on_context_switch()
        self.current_process=next_process
        self.vm.registers['PC']=next_process.pc
        for k,v in next_process.registers.items(): self.vm.registers[k]=v
        self.vm.flags=dict(next_process.flags); self.vm.memory=list(next_process.memory)
        self.vm.halted=False; self.vm.ipc_recv_block=False; self.vm.sem_block=False
        self.vm.current_pid=next_process.pid; self.vm.page_fault_vp=None

    def run(self, time_quantum=2):
        with self.lock: empty=len(self.ready_queue)==0
        if empty and not self.current_process:
            safe_print("[OS] No processes to run."); return
        while True:
            self._wake_up_waiting(); self._apply_aging()
            with self.lock: has_next=len(self.ready_queue)>0
            if not has_next and (not self.current_process or self.vm.halted):
                if self.waiting_list: self._check_deadlock(); time.sleep(0.1); continue
                break
            if has_next:
                with self.lock: next_p=self.scheduler.pick(self.ready_queue)
                self._context_switch(next_p)
                safe_print(f"\n--- [OS] Switching to PID {self.current_process.pid} "
                           f"(Pri:{self.current_process.priority} algo:{self.scheduler.algorithm}) ---")
            for _ in range(time_quantum):
                if self.vm.halted: self._finish_current(); break
                if self.vm.ipc_recv_block or self.vm.sem_block:
                    self._move_current_to_waiting(); break
                if self.vm.page_fault_vp is not None: self._handle_page_fault(); continue
                awakened=self.vm._pending_awakened
                if awakened: self.vm._pending_awakened=None; self._wake_sem_process(awakened)
                self.vm.step()
                if self.current_process: self.current_process.stats.on_instruction()
                time.sleep(0.3)
        if self.on_scheduler_done: self.on_scheduler_done()

    def _finish_current(self):
        if not self.current_process: return
        cp=self.current_process; cp.transition(ProcessState.TERMINATED)
        self.memory_mgr.free(cp.pid); self.ipc.unregister(cp.pid)
        safe_print(f"[OS] Process {cp.pid} finished."); self.current_process=None

    def _move_current_to_waiting(self):
        if not self.current_process: return
        cp = self.current_process
        cp.pc = self.vm.registers['PC']
        cp.registers = {k: self.vm.registers[k] for k in ['R1','R2','R3','R4']}
        cp.flags = dict(self.vm.flags); cp.memory = list(self.vm.memory)
        
        if self.vm.sem_block:
            sem_id = self.vm._pending_sem_id; self.vm.sem_block = False
            try:
                # 嘗試進行 WAIT 操作
                blocked = self.sem_manager.wait(sem_id, cp)
                if blocked:
                    cp.waiting_sem_id = sem_id
                    cp.transition(ProcessState.WAITING)
                    self.waiting_list.append(cp)
                else:
                    self.sem_manager._holders[sem_id] = cp.pid
                    cp.transition(ProcessState.READY)
                    with self.lock: self.scheduler.requeue(cp, self.ready_queue)
            except KeyError as e:
                # 如果號誌不存在，印出錯誤並殺掉行程，不要讓 OS 崩潰
                safe_print(f"[OS] Error: PID {cp.pid} tried to access non-existent {e}")
                self._finish_current() 
                return
        else:
            cp.transition(ProcessState.WAITING)
            if self.vm.ipc_recv_block: self.ipc.mark_waiting(cp); self.vm.ipc_recv_block = False
            self.waiting_list.append(cp)
        self.current_process = None

    def _wake_up_waiting(self):
        for p in self.ipc.pop_awakened():
            if p in self.waiting_list: self.waiting_list.remove(p)
            p.transition(ProcessState.READY)
            with self.lock: self.scheduler.requeue(p,self.ready_queue)
            safe_print(f"[OS] PID {p.pid} woken up (IPC), back to READY.")

    def _wake_sem_process(self, process):
        if process in self.waiting_list: self.waiting_list.remove(process)
        process.waiting_sem_id=None; process.transition(ProcessState.READY)
        with self.lock: self.scheduler.requeue(process,self.ready_queue)
        safe_print(f"[OS] PID {process.pid} woken up (semaphore), back to READY.")

    def _handle_page_fault(self):
        cp=self.current_process; vp=self.vm.page_fault_vp; self.vm.page_fault_vp=None
        safe_print(f"[OS] Page fault: PID {cp.pid} vp={vp}, loading...")
        try: self.memory_mgr.handle_page_fault(cp,vp); self.vm.memory=list(cp.memory)
        except MemoryError as e: safe_print(str(e)); self.vm.halted=True

    def _apply_aging(self):
        if not self.aging_enabled: return
        now=time.time()
        if now-self._last_aging<self.aging_interval: return
        self._last_aging=now
        with self.lock:
            for p in self.ready_queue:
                wait=time.time()-p.stats._ready_since
                if wait>=self.aging_interval:
                    old=p.priority; p.priority+=self.aging_amount
                    safe_print(f"[Aging] PID {p.pid}: priority {old} → {p.priority} (waited {wait:.1f}s)")

    def _check_deadlock(self):
        cycles=self.deadlock.detect(self.sem_manager,self.waiting_list)
        if cycles: safe_print(self.deadlock.report(cycles))

    def kill_process(self, pid):
        if self.current_process and self.current_process.pid==pid:
            self.current_process.transition(ProcessState.TERMINATED)
            self.vm.halted=True; self.memory_mgr.free(pid); self.ipc.unregister(pid)
            self.current_process=None; safe_print(f"\n[OS] Process {pid} killed (was running)."); return
        with self.lock:
            target=next((p for p in self.ready_queue if p.pid==pid),None)
            if target: self.ready_queue.remove(target)
        if target:
            target.transition(ProcessState.TERMINATED); self.memory_mgr.free(pid); self.ipc.unregister(pid)
            safe_print(f"[OS] Process {pid} killed (was ready)."); return
        target=next((p for p in self.waiting_list if p.pid==pid),None)
        if target:
            self.waiting_list.remove(target); target.transition(ProcessState.TERMINATED)
            self.memory_mgr.free(pid); self.ipc.unregister(pid)
            safe_print(f"[OS] Process {pid} killed (was waiting)."); return
        safe_print(f"[OS] Error: Process {pid} not found.")

    def reset_system(self):
        with self.lock: self.ready_queue.clear()
        self.waiting_list.clear(); self.current_process=None
        self.next_pid=1; self._all_processes.clear()
        self.ipc.clear(); self.sem_manager.clear(); self._last_aging=time.time()
        safe_print("[OS] System reset.")

    def get_all_processes(self): return list(self._all_processes.values())
