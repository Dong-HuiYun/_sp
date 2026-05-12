class VirtualMachine:
    def __init__(self, memory_size=256):
        self.memory = [0] * memory_size  # 實體記憶體 (RAM)
        self.registers = {
            'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0,
            'PC': 0,   # 程式計數器
            'IR': None # 指令暫存器
        }
        self.halted = False

    def load_program(self, program):
        """將指令載入記憶體 (從位址 0 開始)"""
        for i, instr in enumerate(program):
            if i < len(self.memory):
                self.memory[i] = instr

    def step(self):
        """Fetch-Decode-Execute 週期"""
        if self.halted: return

        # 1. Fetch
        pc = self.registers['PC']
        if pc >= len(self.memory) or self.memory[pc] == 0:
            self.halted = True
            return
        
        self.registers['IR'] = self.memory[pc]
        
        # 2. Decode & Execute
        instr = self.registers['IR']
        op, args = instr[0], instr[1:]
        
        if op == "SET":      # SET R1 10
            self.registers[args[0]] = args[1]
        elif op == "ADD":    # ADD R1 R2
            self.registers[args[0]] += self.registers[args[1]]
        elif op == "PRINT":  # PRINT R1
            print(f"[VM Output] {args[0]}: {self.registers[args[0]]}")
        elif op == "HALT":
            self.halted = True
        elif op == "JUMP":  # JUMP <位址>
            # 設定 PC 為目標位址 (-1 是因為 step 最後會 PC += 1)
            self.registers['PC'] = args[0] - 1
        # 3. PC 遞增
        self.registers['PC'] += 1