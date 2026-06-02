from io_utils import safe_print
import time
from enum import Enum, auto

class ProcessState(Enum):
    NEW=auto(); READY=auto(); RUNNING=auto(); WAITING=auto(); TERMINATED=auto()

class ProcessStats:
    def __init__(self):
        self.created_at=time.time(); self.cpu_instructions=0
        self.context_switches=0; self.waiting_time=0.0
        self._ready_since=time.time()
    def on_enter_ready(self): self._ready_since=time.time()
    def on_leave_ready(self): self.waiting_time+=time.time()-self._ready_since
    def on_context_switch(self): self.context_switches+=1
    def on_instruction(self): self.cpu_instructions+=1
    def summary(self, pid, state, priority, original_priority):
        age=time.time()-self.created_at
        aged=f"(+{priority-original_priority})" if priority!=original_priority else ""
        return (f"  PID:{pid:<4} state:{state.name:<11} pri:{priority:<3}{aged:<6} "
                f"instr:{self.cpu_instructions:<6} ctx_sw:{self.context_switches:<4} "
                f"wait:{self.waiting_time:.2f}s  age:{age:.1f}s")

class Process:
    def __init__(self, pid, program, priority=1):
        self.pid=pid; self.program=program; self.priority=priority
        self.original_priority=priority; self.state=ProcessState.NEW
        self.pc=0; self.registers={'R1':0,'R2':0,'R3':0,'R4':0}
        self.flags={'ZF':False,'SF':False}; self.memory=[]
        self.stats=ProcessStats(); self.waiting_sem_id=None
    def transition(self, new_state):
        old=self.state
        if old==ProcessState.READY and new_state!=ProcessState.READY: self.stats.on_leave_ready()
        if new_state==ProcessState.READY and old!=ProcessState.READY: self.stats.on_enter_ready()
        self.state=new_state
