from io_utils import safe_print

class DeadlockDetector:
    def __init__(self): self.enabled=True
    def detect(self, sem_manager, waiting_list):
        if not self.enabled: return []
        sem_holder=getattr(sem_manager,'_holders',{})
        waiting_pids={p.pid for p in waiting_list}
        wait_for={p.pid:set() for p in waiting_list}
        for process,sem_id in sem_manager.all_waiting():
            if process.pid not in waiting_pids: continue
            holder_pid=sem_holder.get(sem_id)
            if holder_pid and holder_pid!=process.pid: wait_for[process.pid].add(holder_pid)
        return self._find_cycles(wait_for)
    def _find_cycles(self, wait_for):
        visited=set(); in_stack=set(); cycles=[]
        def dfs(node, path):
            visited.add(node); in_stack.add(node); path.append(node)
            for nb in wait_for.get(node,set()):
                if nb not in wait_for: continue
                if nb in in_stack: cycles.append(path[path.index(nb):]+[nb])
                elif nb not in visited: dfs(nb,path)
            path.pop(); in_stack.discard(node)
        for node in list(wait_for.keys()):
            if node not in visited: dfs(node,[])
        return cycles
    def report(self, cycles):
        if not cycles: return "[Deadlock] No deadlock detected."
        lines=[f"[Deadlock] ⚠️  {len(cycles)} deadlock(s) detected!"]
        for i,cycle in enumerate(cycles,1):
            lines.append(f"  Cycle {i}: "+" → ".join(f"PID:{p}" for p in cycle))
        lines.append("[Deadlock] Use 'kill <pid>' or 'deadlock resolve' to break the cycle.")
        return "\n".join(lines)
    def auto_resolve(self, cycles, os_kernel):
        victims=set()
        for cycle in cycles:
            victims.add(min(pid for pid in cycle if pid==cycle[0] or pid!=cycle[-1]))
        for pid in victims:
            safe_print(f"[Deadlock] Auto-killing PID {pid} to resolve deadlock.")
            os_kernel.kill_process(pid)
