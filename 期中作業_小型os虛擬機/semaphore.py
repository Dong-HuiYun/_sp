import threading
from io_utils import safe_print

class Semaphore:
    def __init__(self, sem_id, initial_value=1, name=""):
        self.sem_id=sem_id; self.value=initial_value
        self.name=name or f"sem_{sem_id}"; self._wait_queue=[]; self._lock=threading.Lock()
    def wait(self, process):
        with self._lock:
            self.value-=1
            if self.value<0:
                self._wait_queue.append(process)
                safe_print(f"[SEM] {self.name}: PID {process.pid} blocked (value={self.value})")
                return True
            return False
    def signal(self, from_pid=None):
        with self._lock:
            self.value+=1; awakened=None
            if self.value<=0 and self._wait_queue:
                awakened=self._wait_queue.pop(0)
                safe_print(f"[SEM] {self.name}: PID {awakened.pid} awakened"+(f" by PID {from_pid}" if from_pid else "")+f" (value={self.value})")
            return awakened
    def status(self):
        with self._lock:
            return f"  [{self.sem_id}] {self.name:<12} value={self.value:<4} waiting={[p.pid for p in self._wait_queue]}"

class SemaphoreManager:
    def __init__(self):
        self._sems={}; self._lock=threading.Lock(); self._next_id=0; self._holders={}
    def create(self, initial_value=1, name="") -> int:
        with self._lock: sid=self._next_id; self._next_id+=1
        self._sems[sid]=Semaphore(sid,initial_value,name)
        safe_print(f"[SEM] Created '{self._sems[sid].name}' (id={sid}, init={initial_value})")
        return sid
    def get(self, sem_id):
        s=self._sems.get(sem_id)
        if s is None: raise KeyError(f"Semaphore {sem_id} does not exist.")
        return s
    def wait(self, sem_id, process):
        blocked=self.get(sem_id).wait(process)
        if not blocked: self._holders[sem_id]=process.pid
        return blocked
    def signal(self, sem_id, from_pid=None):
        awakened=self.get(sem_id).signal(from_pid)
        if from_pid: self._holders.pop(sem_id,None)
        return awakened
    def status(self):
        if not self._sems: return "  (no semaphores)"
        return "\n".join(s.status() for s in self._sems.values())
    def all_waiting(self):
        result=[]
        for sid,sem in self._sems.items():
            with sem._lock:
                for p in sem._wait_queue: result.append((p,sid))
        return result
    def clear(self):
        self._sems.clear(); self._next_id=0; self._holders.clear()
