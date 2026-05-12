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