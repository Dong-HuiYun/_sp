from io_utils import safe_print

PAGE_SIZE = 16

class PageFault(Exception):
    def __init__(self, pid, virtual_page):
        self.pid=pid; self.virtual_page=virtual_page
        super().__init__(f"Page fault: PID {pid}, virtual page {virtual_page}")

class MemoryManager:
    def __init__(self, total_frames=64):
        self.total_frames=total_frames
        self._physical_mem=[0]*(total_frames*PAGE_SIZE)
        self._frame_owner=[None]*total_frames
        self._page_tables={}; self._on_disk={}
        self.page_fault_count=0

    def allocate(self, process):
        program=process.program
        num_pages=max(1,-(-len(program)//PAGE_SIZE))
        free=[i for i,o in enumerate(self._frame_owner) if o is None]
        if not free: raise MemoryError(f"[MemMgr] Out of memory for PID {process.pid}.")
        pid=process.pid; self._page_tables[pid]={}; self._on_disk[pid]={}
        pages=[]
        for vp in range(num_pages):
            s=vp*PAGE_SIZE; d=list(process.program[s:s+PAGE_SIZE])
            d+=[0]*(PAGE_SIZE-len(d)); pages.append(d)
        pf=free[0]; self._frame_owner[pf]=pid; self._page_tables[pid][0]=pf
        ps=pf*PAGE_SIZE; self._physical_mem[ps:ps+PAGE_SIZE]=pages[0]
        for vp in range(1,num_pages): self._on_disk[pid][vp]=pages[vp]
        virtual_size=num_pages*PAGE_SIZE; process.memory=[0]*virtual_size
        process.memory[:PAGE_SIZE]=pages[0]
        safe_print(f"[MemMgr] PID {pid}: {num_pages} page(s), loaded=1, on_disk={num_pages-1}, frame=[{pf}]")

    def handle_page_fault(self, process, vp):
        pid=process.pid; self.page_fault_count+=1
        if pid not in self._on_disk or vp not in self._on_disk[pid]:
            raise MemoryError(f"[MemMgr] PID {pid}: page {vp} not on disk.")
        free=[i for i,o in enumerate(self._frame_owner) if o is None]
        pf=free[0] if free else self._evict(pid)
        page_data=self._on_disk[pid].pop(vp)
        ps=pf*PAGE_SIZE; self._physical_mem[ps:ps+PAGE_SIZE]=page_data
        self._frame_owner[pf]=pid; self._page_tables[pid][vp]=pf
        vs=vp*PAGE_SIZE; process.memory[vs:vs+PAGE_SIZE]=page_data
        safe_print(f"[MemMgr] Page fault resolved: PID {pid} vp={vp}→frame={pf} (total={self.page_fault_count})")

    def _evict(self, pid):
        pt=self._page_tables.get(pid,{})
        if not pt: raise MemoryError(f"[MemMgr] Cannot evict for PID {pid}.")
        victim_vp=min(pt.keys()); victim_pf=pt.pop(victim_vp)
        ps=victim_pf*PAGE_SIZE; evicted=list(self._physical_mem[ps:ps+PAGE_SIZE])
        self._on_disk[pid][victim_vp]=evicted; self._frame_owner[victim_pf]=None
        safe_print(f"[MemMgr] Evicted PID {pid} vp={victim_vp} from frame={victim_pf}")
        return victim_pf

    def free(self, pid):
        if pid in self._page_tables:
            for pf in self._page_tables[pid].values():
                self._frame_owner[pf]=None; s=pf*PAGE_SIZE
                self._physical_mem[s:s+PAGE_SIZE]=[0]*PAGE_SIZE
            del self._page_tables[pid]
        self._on_disk.pop(pid,None)
        safe_print(f"[MemMgr] PID {pid}: memory freed.")

    def status(self):
        used=sum(1 for o in self._frame_owner if o is not None); free=self.total_frames-used
        lines=[f"[MemMgr] Frames:{self.total_frames} Used:{used} Free:{free} | Page faults:{self.page_fault_count}"]
        for pid in sorted(self._page_tables.keys()):
            loaded=list(self._page_tables[pid].keys()); on_disk=list(self._on_disk.get(pid,{}).keys())
            frames=list(self._page_tables[pid].values())
            lines.append(f"  PID {pid}: loaded={loaded}→frames={frames} | on_disk={on_disk}")
        return "\n".join(lines)
