import collections
import time

class Process:
    def __init__(self, pid, program, priority=1, memory_size=256):
        self.pid = pid
        self.program = program
        self.priority = priority
        self.pc = 0
        self.registers = {'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0, 'PC': 0}
        self.state = "READY"
        
        # 記憶體隔離：每個行程擁有自己的虛擬空間
        self.memory = [0] * memory_size
        for i, instr in enumerate(program):
            self.memory[i] = instr

class SimpleOS:
    def __init__(self, vm):
        self.vm = vm
        self.ready_queue = collections.deque()
        self.current_process = None
        self.next_pid = 1

    def create_process(self, program, priority=1):
        new_p = Process(self.next_pid, program, priority)
        self.ready_queue.append(new_p)
        print(f"[OS] Process {self.next_pid} created (Priority: {priority}).")
        self.next_pid += 1

    def context_switch(self, next_process):
        """核心：上下文切換 + 記憶體快照"""
        # 1. 儲存舊行程狀態
        if self.current_process:
            self.current_process.pc = self.vm.registers['PC']
            self.current_process.registers = {k: self.vm.registers[k] for k in ['R1', 'R2', 'R3', 'R4']}
            self.current_process.memory = list(self.vm.memory) # 記憶體快照備份
            
            if not self.vm.halted:
                self.ready_queue.append(self.current_process)

        # 2. 載入新行程狀態
        self.current_process = next_process
        self.vm.registers['PC'] = next_process.pc
        for k, v in next_process.registers.items():
            self.vm.registers[k] = v
        
        self.vm.memory = list(next_process.memory) # 還原記憶體空間
        self.vm.halted = False

    def run(self, time_quantum=2):
        """排程器迴圈"""
        if not self.ready_queue and not self.current_process:
            print("[OS] No processes to run.")
            return

        # 依優先權重新排序 Ready Queue (優先權高的在前)
        sorted_list = sorted(list(self.ready_queue), key=lambda p: p.priority, reverse=True)
        self.ready_queue = collections.deque(sorted_list)

        while self.ready_queue or (self.current_process and not self.vm.halted):
            if self.ready_queue:
                self.context_switch(self.ready_queue.popleft())
                print(f"\n--- [OS] Switching to PID {self.current_process.pid} (Priority: {self.current_process.priority}) ---")

            for _ in range(time_quantum):
                if not self.vm.halted:
                    self.vm.step()
                    time.sleep(0.5)
                else:
                    print(f"[OS] Process {self.current_process.pid} finished.")
                    self.current_process = None
                    break

    def kill_process(self, pid):
            # 1. 檢查是否是正在執行的行程
            if self.current_process and self.current_process.pid == pid:
                self.vm.halted = True # 強制停止 VM
                self.current_process = None
                print(f"\n[OS] Current Process {pid} has been killed by Kernel.")
                return

            # 2. 檢查是否在準備佇列中
            target = next((p for p in self.ready_queue if p.pid == pid), None)
            if target:
                self.ready_queue.remove(target)
                print(f"[OS] Process {pid} killed from Ready Queue.")
            else:
                print(f"[OS] Error: Process {pid} not found.")

    def reset_system(self):
        self.ready_queue.clear()
        self.current_process = None
        self.next_pid = 1
        print("[OS] System reset.")