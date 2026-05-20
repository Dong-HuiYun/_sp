from io_utils import safe_print
import collections

# ─────────────────────────────────────────────
#  Scheduler：可插拔排程演算法
# ─────────────────────────────────────────────
#
#  支援四種演算法：
#    FIFO        先來先服務，完全按照加入順序
#    PRIORITY    每次都挑優先權最高的（數字越大越優先）
#    ROUND_ROBIN 輪流，時間片到就換下一個（預設）
#    SJF         最短工作優先，按指令數估算剩餘工作量
#
#  用法：
#    sched = Scheduler("PRIORITY")
#    next_p = sched.pick(ready_queue)   ← 回傳並從 queue 移除
#    sched.requeue(process, ready_queue) ← 時間片用完放回去

ALGORITHMS = ["FIFO", "PRIORITY", "ROUND_ROBIN", "SJF"]


class Scheduler:
    def __init__(self, algorithm="ROUND_ROBIN"):
        algorithm = algorithm.upper()
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm '{algorithm}'. Choose from {ALGORITHMS}")
        self.algorithm = algorithm

    # ── 從 queue 取出下一個要執行的 process ──────────────────────────────
    def pick(self, ready_queue: collections.deque):
        """
        從 ready_queue 取出並回傳下一個 process。
        queue 必須非空，呼叫前請先檢查。
        """
        if not ready_queue:
            return None

        if self.algorithm == "FIFO":
            # 直接取最前面（加入順序）
            return ready_queue.popleft()

        elif self.algorithm == "ROUND_ROBIN":
            # 同 FIFO，差異在 requeue 時放回尾端
            return ready_queue.popleft()

        elif self.algorithm == "PRIORITY":
            # 找最高優先權（相同優先權時取最早加入的）
            best = max(ready_queue, key=lambda p: p.priority)
            ready_queue.remove(best)
            return best

        elif self.algorithm == "SJF":
            # 以「剩餘指令數」估算工作量（PC 之後還剩幾條）
            def remaining(p):
                return max(0, len(p.program) - p.pc)
            shortest = min(ready_queue, key=remaining)
            ready_queue.remove(shortest)
            return shortest

    # ── 時間片用完，把 process 放回 queue ────────────────────────────────
    def requeue(self, process, ready_queue: collections.deque):
        """
        FIFO / SJF / PRIORITY：放回尾端（下次仍按各自規則挑選）
        ROUND_ROBIN：同樣放回尾端，保證輪流
        """
        ready_queue.append(process)

    # ── 切換演算法（可在執行中切換）──────────────────────────────────────
    def set_algorithm(self, algorithm: str):
        algorithm = algorithm.upper()
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm '{algorithm}'. Choose from {ALGORITHMS}")
        self.algorithm = algorithm
        safe_print(f"[Scheduler] Algorithm switched to {self.algorithm}.")