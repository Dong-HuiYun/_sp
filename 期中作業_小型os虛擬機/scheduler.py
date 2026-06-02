import collections
from io_utils import safe_print

ALGORITHMS = ["FIFO","PRIORITY","ROUND_ROBIN","SJF"]

class Scheduler:
    def __init__(self, algorithm="ROUND_ROBIN"):
        self.algorithm=algorithm.upper()
    def pick(self, ready_queue):
        if not ready_queue: return None
        if self.algorithm in ("FIFO","ROUND_ROBIN"): return ready_queue.popleft()
        elif self.algorithm=="PRIORITY":
            best=max(ready_queue,key=lambda p:p.priority); ready_queue.remove(best); return best
        elif self.algorithm=="SJF":
            shortest=min(ready_queue,key=lambda p:max(0,len(p.program)-p.pc))
            ready_queue.remove(shortest); return shortest
    def requeue(self, process, ready_queue): ready_queue.append(process)
    def set_algorithm(self, algo):
        algo=algo.upper()
        if algo not in ALGORITHMS: raise ValueError(f"Unknown algorithm '{algo}'. Choose from {ALGORITHMS}")
        self.algorithm=algo; safe_print(f"[Scheduler] Algorithm switched to {self.algorithm}.")
