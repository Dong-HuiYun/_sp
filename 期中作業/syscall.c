void syscall_handler(CPU *cpu, uint8_t int_num) {
    switch (int_num) {

    case INT_PRINT_STR: {
        // 協定: R1 存字元數量，字元已 PUSH 到 stack（逆序）
        int count = cpu->regs[1];
        printf("[OS] ");
        // 從 stack 反向讀取（最先 PUSH 的在底部）
        for (int i = count - 1; i >= 0; i--) {
            uint8_t ch = cpu->memory[cpu->sp + 2 + (i * 2)];
            putchar(ch);
        }
        printf("\n");
        break;
    }

    case INT_PRINT_REG: {
        // 協定: 印出 R4 的值
        printf("[OS] R4 = %d (0x%04X)\n", cpu->regs[4], cpu->regs[4]);
        break;
    }

    case INT_EXIT:
        printf("[OS] Process exited with code 0\n");
        cpu->halted = 1;
        break;

    default:
        fprintf(stderr, "[OS] Unknown syscall: 0x%02X\n", int_num);
    }
}