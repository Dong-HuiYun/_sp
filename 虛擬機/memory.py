from io_utils import safe_print
# ─────────────────────────────────────────────
#  MemoryManager：簡單分頁（Paging）
# ─────────────────────────────────────────────
#
#  概念：
#    - 實體記憶體切成等大小的「頁框 (frame)」
#    - 每個 process 有自己的「頁表 (page table)」
#      virtual_page → physical_frame
#    - 行程用虛擬位址存取，MemoryManager 負責翻譯成實體位址
#
#  這裡為了簡單示範，每個 process 的虛擬空間就是它的程式
#  指令數向上取整到 PAGE_SIZE 的倍數，分配對應頁框數。

PAGE_SIZE = 16   # 每頁 16 個 slot


class MemoryManager:
    def __init__(self, total_frames=64):
        self.total_frames  = total_frames
        self.frame_size    = PAGE_SIZE
        # 實體記憶體：total_frames * PAGE_SIZE 個 slot
        self._physical_mem = [0] * (total_frames * PAGE_SIZE)
        # 頁框使用狀況：None = 空閒，int = 擁有者 pid
        self._frame_owner  = [None] * total_frames
        # 頁表：pid → {virtual_page: physical_frame}
        self._page_tables  = {}

    # ── 分配 ──────────────────────────────────────────────────────────────
    def allocate(self, process):
        """
        把 process.program 載入實體記憶體，建立頁表，
        並把虛擬記憶體（process.memory）設為「從虛擬位址 0 開始的連續空間」。
        """
        program = process.program
        num_pages = max(1, -(-len(program) // PAGE_SIZE))   # ceiling division

        # 找空閒頁框
        free_frames = [i for i, owner in enumerate(self._frame_owner) if owner is None]
        if len(free_frames) < num_pages:
            raise MemoryError(
                f"[MemoryManager] Out of memory: need {num_pages} frames, "
                f"only {len(free_frames)} free."
            )

        allocated = free_frames[:num_pages]
        page_table = {}

        for vp, pf in enumerate(allocated):
            self._frame_owner[pf] = process.pid
            page_table[vp] = pf
            # 把指令寫入對應實體頁框
            start = pf * PAGE_SIZE
            for offset in range(PAGE_SIZE):
                idx = vp * PAGE_SIZE + offset
                self._physical_mem[start + offset] = program[idx] if idx < len(program) else 0

        self._page_tables[process.pid] = page_table

        # 給 process 一個「虛擬記憶體視圖」（連續列表，供 VM 使用）
        virtual_size = num_pages * PAGE_SIZE
        process.memory = [0] * virtual_size
        for vp, pf in page_table.items():
            src = pf * PAGE_SIZE
            dst = vp * PAGE_SIZE
            process.memory[dst:dst + PAGE_SIZE] = self._physical_mem[src:src + PAGE_SIZE]

        safe_print(
            f"[MemMgr] PID {process.pid}: allocated {num_pages} page(s) "
            f"→ frames {allocated}"
        )

    # ── 釋放 ──────────────────────────────────────────────────────────────
    def free(self, pid):
        """歸還該 process 所有頁框"""
        if pid not in self._page_tables:
            return
        for pf in self._page_tables[pid].values():
            self._frame_owner[pf] = None
            start = pf * PAGE_SIZE
            self._physical_mem[start:start + PAGE_SIZE] = [0] * PAGE_SIZE
        del self._page_tables[pid]
        safe_print(f"[MemMgr] PID {pid}: memory freed.")

    # ── 位址翻譯 ──────────────────────────────────────────────────────────
    def translate(self, pid, virtual_addr):
        """虛擬位址 → 實體位址（供除錯或進階功能用）"""
        if pid not in self._page_tables:
            raise KeyError(f"PID {pid} has no page table.")
        vp     = virtual_addr // PAGE_SIZE
        offset = virtual_addr  % PAGE_SIZE
        pf = self._page_tables[pid].get(vp)
        if pf is None:
            raise ValueError(f"Page fault: PID {pid}, virtual page {vp}")
        return pf * PAGE_SIZE + offset

    # ── 統計 ──────────────────────────────────────────────────────────────
    def status(self):
        used  = sum(1 for o in self._frame_owner if o is not None)
        free  = self.total_frames - used
        lines = [
            f"[MemMgr] Total frames: {self.total_frames} | "
            f"Used: {used} | Free: {free}"
        ]
        for pid, pt in self._page_tables.items():
            lines.append(f"  PID {pid}: pages={list(pt.keys())} → frames={list(pt.values())}")
        return "\n".join(lines)