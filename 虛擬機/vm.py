from io_utils import safe_print
class VirtualMachine:
    def __init__(self, memory_size=256):
        self.memory    = [0] * memory_size
        self.registers = {
            'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0,
            'PC': 0,
            'IR': None,
        }
        self.flags  = {'ZF': False, 'SF': False}
        self.halted = False

        # IPC 注入點（由 OS kernel 在 context_switch 時設定）
        self.ipc            = None   # MessageQueue 物件
        self.current_pid    = None   # 目前執行中的 pid
        self.ipc_recv_block = False  # True 表示 RECV 因收件匣空而阻塞

    def load_program(self, program):
        for i, instr in enumerate(program):
            if i < len(self.memory):
                self.memory[i] = instr

    def step(self):
        if self.halted:
            return

        # 1. Fetch
        pc = self.registers['PC']
        if pc >= len(self.memory) or self.memory[pc] == 0:
            self.halted = True
            return

        self.registers['IR'] = self.memory[pc]

        # 2. Decode & Execute
        instr    = self.registers['IR']
        op, args = instr[0], instr[1:]
        self._execute(op, args)

        # 3. PC 遞增（JUMP 系列在 _execute 內改 PC，這裡統一 +1）
        if not self.halted and not self.ipc_recv_block:
            self.registers['PC'] += 1

    def _execute(self, op, args):

        # ── 原有指令 ──────────────────────────────────────────────────────
        if op == "SET":
            self.registers[args[0]] = args[1]

        elif op == "ADD":
            self.registers[args[0]] += self.registers[args[1]]

        elif op == "PRINT":
            safe_print(f"[VM Output] {args[0]}: {self.registers[args[0]]}")

        elif op == "HALT":
            self.halted = True

        elif op == "JUMP":
            self.registers['PC'] = args[0] - 1

        # ── 算術指令 ──────────────────────────────────────────────────────
        elif op == "SUB":
            self.registers[args[0]] -= self.registers[args[1]]

        elif op == "MUL":
            self.registers[args[0]] *= self.registers[args[1]]

        # ── 比較與條件跳躍 ────────────────────────────────────────────────
        elif op == "CMP":
            a = self.registers[args[0]]
            b = self.registers[args[1]]
            self.flags['ZF'] = (a == b)
            self.flags['SF'] = (a < b)

        elif op == "JNZ":
            if not self.flags['ZF']:
                self.registers['PC'] = args[0] - 1

        elif op == "JZ":
            if self.flags['ZF']:
                self.registers['PC'] = args[0] - 1

        elif op == "JN":
            if self.flags['SF']:
                self.registers['PC'] = args[0] - 1

        # ── 記憶體存取 ────────────────────────────────────────────────────
        elif op == "LOAD":
            addr = args[1]
            if 0 <= addr < len(self.memory):
                self.registers[args[0]] = self.memory[addr]
            else:
                safe_print(f"[VM] LOAD: address {addr} out of range.")
                self.halted = True

        elif op == "STORE":
            addr = args[1]
            if 0 <= addr < len(self.memory):
                self.memory[addr] = self.registers[args[0]]
            else:
                safe_print(f"[VM] STORE: address {addr} out of range.")
                self.halted = True

        # ── IPC 指令 ──────────────────────────────────────────────────────
        elif op == "SEND":
            # SEND to_pid Rs
            if self.ipc is None:
                safe_print("[VM] SEND: IPC not available.")
                return
            to_pid = args[0]
            value  = self.registers[args[1]]
            self.ipc.send(self.current_pid, to_pid, value)

        elif op == "RECV":
            # RECV Rd
            if self.ipc is None:
                safe_print("[VM] RECV: IPC not available.")
                return
            msg = self.ipc.recv(self.current_pid)
            if msg is not None:
                from_pid, value = msg
                self.registers[args[0]] = value
                safe_print(f"[VM] PID {self.current_pid} RECV: {args[0]}={value} (from PID {from_pid})")
            else:
                self.ipc_recv_block = True
                safe_print(f"[VM] PID {self.current_pid} RECV: inbox empty, entering WAITING.")

        else:
            safe_print(f"[VM] Unknown opcode: {op}")
            self.halted = True