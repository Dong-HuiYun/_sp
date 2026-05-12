#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MEM_SIZE    65536   // 64KB
#define REG_COUNT   8
#define STACK_BASE  0xFFFF  // SP 從最高位往下長

typedef struct {
    uint16_t regs[REG_COUNT]; // R0 ~ R7
    uint16_t pc;              // Program Counter
    uint16_t sp;              // Stack Pointer
    uint8_t  memory[MEM_SIZE];

    // CPU Flags
    uint8_t flag_zero;
    uint8_t flag_neg;
    uint8_t flag_carry;
    uint8_t halted;
} CPU;

void cpu_init(CPU *cpu) {
    memset(cpu, 0, sizeof(CPU));
    cpu->sp = STACK_BASE;
    cpu->halted = 0;
}

typedef enum {
    OP_NOP   = 0x00,  // 空指令
    OP_MOV   = 0x01,  // MOV Rdst, imm  → Rdst = imm
    OP_ADD   = 0x02,  // ADD Rdst, Ra, Rb → Rdst = Ra + Rb
    OP_SUB   = 0x03,  // SUB Rdst, Ra, Rb → Rdst = Ra - Rb
    OP_CMP   = 0x04,  // CMP Ra, Rb       → 設置 flags，不寫回
    OP_JMP   = 0x05,  // JMP addr         → 無條件跳轉
    OP_JZ    = 0x06,  // JZ  addr         → zero flag 為 1 時跳轉
    OP_PUSH  = 0x07,  // PUSH Rsrc        → 壓棧
    OP_POP   = 0x08,  // POP  Rdst        → 彈棧
    OP_INT   = 0x09,  // INT  num         → 觸發系統呼叫
    OP_HALT  = 0xFF,  // HALT             → 停機
} Opcode;

// 系統呼叫號碼
#define INT_PRINT_STR  0x01   // 從 stack 印出字串
#define INT_PRINT_REG  0x02   // 印出暫存器值
#define INT_EXIT       0xFF   // 結束程式

// ── Fetch：讀取下一個 byte ──────────────────────────
static inline uint8_t fetch(CPU *cpu) {
    return cpu->memory[cpu->pc++];
}

void syscall_handler(CPU *cpu, uint8_t int_num) {
    switch (int_num) {

    
    case INT_PRINT_STR: {
        int count = cpu->regs[1];
        printf("[OS] ");
        
        // 從最後一個進去的（i=0）到第一個進去的（i=count-1）
        // 為了修正順序，我們反向遍歷索引
        for (int i = count - 1; i >= 0; i--) {
            // 修正後的索引計算：
            // (i * 2) 確保跳過 16-bit 的間隔
            // +1 是因為字元存放在 16-bit 的低位 byte
            uint8_t ch = cpu->memory[cpu->sp + 1 + (i * 2)];
            if (ch != 0) putchar(ch);
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