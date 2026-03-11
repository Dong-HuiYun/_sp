# P0 Compiler 設計原理說明

## 一、while 迴圈處理機制設計原理

### 1. 語法解析流程

在 `statement()` 函數中，當遇到 `TK_WHILE` token 時，編譯器會按照以下步驟處理：

```c
else if (cur_token.type == TK_WHILE) {
    next_token(); // 略過 while
    next_token(); // 略過 (
    
    int cond_start_pc = quad_count; // ① 記錄條件判斷起點
    char cond[32];
    expression(cond);               // ② 解析條件表達式
    
    next_token(); // 略過 )
    next_token(); // 略過 {
    
    int jmp_f_idx = quad_count;
    emit("JMP_F", cond, "-", "?");  // ③ 條件為假時跳出的位置
    
    while (cur_token.type != TK_RBRACE) statement(); // ④ 解析迴圈本體
    next_token(); // 略過 }
    
    char back_addr[10];
    sprintf(back_addr, "%d", cond_start_pc);
    emit("JMP", "-", "-", back_addr); // ⑤ 無條件跳回條件判斷
    
    sprintf(quads[jmp_f_idx].result, "%d", quad_count); // ⑥ 回填 JMP_F 目的地
}
```

### 2. 中間碼生成策略

while 迴圈的編譯採用**「條件判斷前置」**的設計模式，生成三種關鍵的中間碼指令：

1. **條件計算指令**：由 `expression()` 產生，計算迴圈條件
2. **條件跳轉指令**：`JMP_F`，條件為假時跳出迴圈
3. **無條件跳轉指令**：`JMP`，執行完迴圈本體後跳回條件判斷

### 3. 回填技術 (Backpatching)

為了處理跳轉目標未知的問題，採用**回填技術**：
- 生成 `JMP_F` 指令時，目的地暫設為 "?" 
- 待迴圈本體編譯完成後，再將實際地址回填到 `quads[jmp_f_idx].result`

這種設計確保了在單次掃描中就能正確生成迴圈結構的中間碼。

## 二、P0 Compiler 函數呼叫機制

### 1. 呼叫端處理

#### 參數傳遞（PARAM 指令）
```c
// 解析函數呼叫參數
while (cur_token.type != TK_RPAREN) {
    char arg[32]; expression(arg);
    emit("PARAM", arg, "-", "-"); // 生成 PARAM 指令
    count++;
    if (cur_token.type == TK_COMMA) next_token();
}
```

呼叫端會：
- 從右向左（依解析順序）計算每個參數的值
- 生成 `PARAM` 指令將參數壓入參數堆疊（param_stack）
- 記錄參數數量供後續使用

#### 函數呼叫（CALL 指令）
```c
char c_str[10]; sprintf(c_str, "%d", count);
emit("CALL", name, c_str, res); // 生成 CALL 指令
```

`CALL` 指令包含：
- 函數名稱（arg1）
- 參數數量（arg2）
- 返回值存放位置（result）

### 2. 被呼叫端處理

#### 形式參數綁定（FORMAL 指令）
```c
else if (strcmp(q.op, "FORMAL") == 0) {
    set_var(q.arg1, stack[sp].incoming_args[stack[sp].formal_idx++]);
}
```

- `FORMAL` 指令出現在函數開頭
- 將傳入的實際參數值綁定到形式參數名稱
- 使用 `formal_idx` 追蹤目前處理到第幾個參數

### 3. 堆疊框架管理

#### 框架結構 (Frame)
```c
typedef struct {
    char names[100][32];   // 變數名稱
    int values[100];       // 變數值
    int count;             // 變數數量
    int ret_pc;            // 返回地址
    char ret_var[32];      // 返回值存放位置
    int incoming_args[10]; // 傳入參數值
    int formal_idx;        // 參數索引
} Frame;
```

#### 框架切換流程

**呼叫時**：
1. 參數已存入 `param_stack`
2. 建立新框架（sp++）
3. 保存返回地址（`pc + 1`）
4. 保存返回值存放位置
5. 複製參數到 `incoming_args`
6. 跳轉到函數入口

**返回時**：
1. 取得返回值
2. 恢復上一層框架（sp--）
3. 將返回值存入指定位置
4. 跳回返回地址

### 4. 執行時期運作示意

以程式碼 `result = add(3, 4);` 為例：

```
步驟 1: 參數傳遞
    PARAM 3 - -      // param_stack: [3]
    PARAM 4 - -      // param_stack: [3, 4]

步驟 2: 函數呼叫
    CALL add 2 t1    // 建立新框架，跳轉到 add

步驟 3: 形式參數綁定
    FORMAL a - -     // a = 3
    FORMAL b - -     // b = 4

步驟 4: 函數執行
    ...              // 執行函數本體
    RET_VAL t2 - -   // 返回值並恢復框架

步驟 5: 返回後
                     // t1 得到返回值
```

### 5. 設計特點

1. **靜態作用域**：每個函數有獨立的變數空間
2. **傳值呼叫**：參數傳遞採用傳值方式
3. **巢狀呼叫支援**：堆疊框架支援多層函數呼叫
4. **遞迴支援**：每次呼叫建立新框架，自然支援遞迴

### 6. 執行方法

```

wsl
gcc compiler.c -o compiler
./compiler.out p0/add.p0

```