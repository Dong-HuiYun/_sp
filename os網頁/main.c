// 組合語言概念對應的 machine code 載入
void load_hello_os(CPU *cpu) {
    uint8_t prog[] = {
        // MOV R0, 'H'
        OP_MOV, 0, 'H',
        OP_PUSH, 0,
        // MOV R0, 'e'
        OP_MOV, 0, 'e',
        OP_PUSH, 0,
        // ... l, l, o, ' ', O, S ...
        OP_MOV, 0, 'l',  OP_PUSH, 0,
        OP_MOV, 0, 'l',  OP_PUSH, 0,
        OP_MOV, 0, 'o',  OP_PUSH, 0,
        OP_MOV, 0, ' ',  OP_PUSH, 0,
        OP_MOV, 0, 'O',  OP_PUSH, 0,
        OP_MOV, 0, 'S',  OP_PUSH, 0,
        // R1 = 8 (字元數量)
        OP_MOV, 1, 8,
        // INT PRINT_STR → 系統呼叫
        OP_INT, INT_PRINT_STR,
        // 額外示範：ADD R4 = R2 + R3
        OP_MOV, 2, 42,
        OP_MOV, 3, 58,
        OP_ADD, 4, 2, 3,
        OP_INT, INT_PRINT_REG,
        // 結束
        OP_INT, INT_EXIT,
        OP_HALT
    };
    memcpy(cpu->memory, prog, sizeof(prog));
}

int main(void) {
    CPU cpu;
    cpu_init(&cpu);
    load_hello_os(&cpu);
    cpu_run(&cpu);
    return 0;
}