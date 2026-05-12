// ── Fetch：讀取下一個 byte ──────────────────────────
static inline uint8_t fetch(CPU *cpu) {
    return cpu->memory[cpu->pc++];
}

// ── Decode & Execute：解碼並執行 ────────────────────
void execute_one(CPU *cpu) {
    uint8_t op = fetch(cpu);

    switch (op) {

    case OP_MOV: {
        uint8_t dst = fetch(cpu);
        uint8_t val = fetch(cpu);
        cpu->regs[dst] = val;
        break;
    }

    case OP_ADD: {
        uint8_t dst = fetch(cpu), ra = fetch(cpu), rb = fetch(cpu);
        uint32_t result = cpu->regs[ra] + cpu->regs[rb];
        cpu->regs[dst]   = (uint16_t)result;
        cpu->flag_zero   = (cpu->regs[dst] == 0);
        cpu->flag_carry  = (result > 0xFFFF);
        cpu->flag_neg    = (cpu->regs[dst] >> 15) & 1;
        break;
    }

    case OP_SUB: {
        uint8_t dst = fetch(cpu), ra = fetch(cpu), rb = fetch(cpu);
        int32_t result   = cpu->regs[ra] - cpu->regs[rb];
        cpu->regs[dst]   = (uint16_t)result;
        cpu->flag_zero   = (cpu->regs[dst] == 0);
        cpu->flag_neg    = (result < 0);
        break;
    }

    case OP_JMP: {
        uint8_t addr = fetch(cpu);
        cpu->pc = addr;
        break;
    }

    case OP_JZ: {
        uint8_t addr = fetch(cpu);
        if (cpu->flag_zero) cpu->pc = addr;
        break;
    }

    case OP_PUSH: {
        uint8_t src = fetch(cpu);
        // SP 往下移動，寫入高 byte 再寫 低 byte
        cpu->memory[cpu->sp--] = (cpu->regs[src] >> 8) & 0xFF;
        cpu->memory[cpu->sp--] = cpu->regs[src] & 0xFF;
        break;
    }

    case OP_POP: {
        uint8_t dst = fetch(cpu);
        uint8_t lo  = cpu->memory[++cpu->sp];
        uint8_t hi  = cpu->memory[++cpu->sp];
        cpu->regs[dst] = (hi << 8) | lo;
        break;
    }

    case OP_INT:
        syscall_handler(cpu, fetch(cpu));
        break;

    case OP_HALT:
        cpu->halted = 1;
        break;

    default:
        fprintf(stderr, "[FAULT] Unknown opcode: 0x%02X at PC=0x%04X\n", op, cpu->pc - 1);
        cpu->halted = 1;
    }
}

// ── 主迴圈 ────────────────────────────────────────────
void cpu_run(CPU *cpu) {
    while (!cpu->halted) {
        execute_one(cpu);
    }
}