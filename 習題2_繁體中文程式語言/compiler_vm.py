"""
繁體中文程式語言 v3 - Compiler + Stack VM
====================================================================

新增 Bytecode 指令
==================
  MOD                      — 餘數 %
  POW                      — 次方 **
  INPUT       <varname>    — 從 stdin 讀入字串，存入變數
  CALL        <name,argc>  — 呼叫函數（argc 個引數已在堆疊上）
  RETURN                   — 從函數回傳（堆疊頂端為回傳值）
  APPEND      <name>       — 彈出值，append 到 vars[name]
  POP_LIST    <name>       — pop vars[name]，若有 dest 則存入 dest
  LIST_LEN               — 彈出列表，推入其長度
  BREAK_LOOP               — 跳出迴圈（特殊跳轉標記）
  CONTINUE_LOOP            — 繼續迴圈（特殊跳轉標記）
  TRY_BEGIN   <handler>   — 設定錯誤處理點
  TRY_END                  — 清除錯誤處理點
  IMPORT      <name>       — 引入模組（執行另一個 .中文 檔）
"""
from __future__ import annotations
import os, sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

from lexer_parser import (
    Lexer, Parser, pretty_print_ast,
    Program, DeclareStmt, AssignStmt, IndexAssignStmt,
    PrintStmt, AskStmt, IfStmt, WhileStmt, ForStmt,
    ReturnStmt, BreakStmt, ContinueStmt,
    AppendStmt, PopStmt, TryStmt, FuncDefStmt, ImportStmt,
    BinOp, UnaryOp, IntLiteral, StrLiteral, ListLiteral,
    IndexExpr, Identifier, CallExpr, BuiltinCall, ASTNode,
)


# ============================================================
# Op 指令集
# ============================================================

class Op(Enum):
    PUSH_INT      = "PUSH_INT"
    PUSH_STR      = "PUSH_STR"
    LOAD          = "LOAD"
    STORE         = "STORE"
    DECLARE       = "DECLARE"
    BUILD_LIST    = "BUILD_LIST"
    LOAD_INDEX    = "LOAD_INDEX"
    STORE_INDEX   = "STORE_INDEX"
    APPEND        = "APPEND"
    POP_LIST      = "POP_LIST"
    LIST_LEN      = "LIST_LEN"
    ADD           = "ADD"
    SUB           = "SUB"
    MUL           = "MUL"
    DIV           = "DIV"
    MOD           = "MOD"
    POW           = "POW"
    NEG           = "NEG"
    EQ  = "EQ";  NEQ = "NEQ"
    GT  = "GT";  LT  = "LT"
    GTE = "GTE"; LTE = "LTE"
    AND = "AND"; OR  = "OR"; NOT = "NOT"
    JUMP          = "JUMP"
    JUMP_IF_FALSE = "JUMP_IF_FALSE"
    PRINT         = "PRINT"
    INPUT         = "INPUT"
    CALL          = "CALL"
    RETURN        = "RETURN"
    TRY_BEGIN     = "TRY_BEGIN"
    TRY_END       = "TRY_END"
    IMPORT        = "IMPORT"
    HALT          = "HALT"


@dataclass
class Instruction:
    op: Op; arg: Any = None; source_line: int = 0
    def __repr__(self):
        return f"{self.op.value:<18} {self.arg!r}" if self.arg is not None else self.op.value


# 型態常數
T_INT  = 'int';  T_STR  = 'str';  T_BOOL = 'bool'
T_ILIST = 'int_list'; T_SLIST = 'str_list'; T_ANY = 'any'


# ============================================================
# 錯誤
# ============================================================

class CompileError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(f"[編譯錯誤] 第{line}行：{msg}" if line else f"[編譯錯誤] {msg}")

class ZhRuntimeError(Exception):
    def __init__(self, msg, pc=0):
        super().__init__(f"[執行錯誤] 指令#{pc}：{msg}")

# 流程控制信號（不是真正的錯誤）
class _ReturnSignal(Exception):
    def __init__(self, value): self.value = value
class _BreakSignal(Exception): pass
class _ContinueSignal(Exception): pass


# ============================================================
# COMPILER
# ============================================================

class Compiler:
    def __init__(self, func_table: Optional[Dict] = None):
        self.code: List[Instruction] = []
        self.var_types: Dict[str, str] = {}
        # 函數表：name → (params, body)  — 供 infer_type 的函數呼叫型態推導
        self.func_table: Dict = func_table or {}

    def emit(self, op, arg=None, line=0):
        self.code.append(Instruction(op, arg, line)); return len(self.code)-1

    def current_addr(self): return len(self.code)

    def patch(self, idx, addr): self.code[idx].arg = addr

    # ── 型態推導 ─────────────────────────────────────────────

    def infer(self, node) -> str:
        if isinstance(node, IntLiteral): return T_INT
        if isinstance(node, StrLiteral): return T_STR
        if isinstance(node, ListLiteral):
            if not node.elements: return T_ILIST
            et = self.infer(node.elements[0])
            return T_ILIST if et == T_INT else T_SLIST
        if isinstance(node, Identifier):
            if node.name not in self.var_types:
                raise CompileError(f"未宣告的變數「{node.name}」", node.line)
            return self.var_types[node.name]
        if isinstance(node, IndexExpr):
            tt = self.infer(node.target)
            return T_INT if tt == T_ILIST else (T_STR if tt == T_SLIST else T_ANY)
        if isinstance(node, UnaryOp):
            return T_INT if node.op == 'neg' else T_BOOL
        if isinstance(node, BinOp):
            if node.op in ('+','-','*','/','%','**'):
                lt, rt = self.infer(node.left), self.infer(node.right)
                if node.op == '+' and lt == T_STR and rt == T_STR: return T_STR
                return T_INT
            return T_BOOL
        if isinstance(node, BuiltinCall):
            if node.func == '長度': return T_INT
        if isinstance(node, CallExpr): return T_ANY  # 函數回傳型態不做靜態推導
        return T_ANY

    # ── 編譯入口 ─────────────────────────────────────────────

    def compile(self, program: Program):
        # 先掃描所有函數定義，登記到 func_table
        for stmt in program.statements:
            if isinstance(stmt, FuncDefStmt):
                self.func_table[stmt.name] = stmt
        for stmt in program.statements:
            self.compile_stmt(stmt)
        self.emit(Op.HALT)
        return self.code

    # ── 語句編譯 ─────────────────────────────────────────────

    def compile_stmt(self, node):
        if   isinstance(node, FuncDefStmt):      self.compile_funcdef(node)
        elif isinstance(node, ImportStmt):        self.emit(Op.IMPORT, node.module, node.line)
        elif isinstance(node, DeclareStmt):       self.compile_declare(node)
        elif isinstance(node, AssignStmt):        self.compile_assign(node)
        elif isinstance(node, IndexAssignStmt):   self.compile_index_assign(node)
        elif isinstance(node, PrintStmt):
            self.compile_expr(node.expr)
            self.emit(Op.PRINT, None, node.line)
        elif isinstance(node, AskStmt):
            # 自動宣告接收變數（字串型態）
            if node.varname not in self.var_types:
                self.var_types[node.varname] = T_STR
            self.emit(Op.INPUT, (node.prompt, node.varname), node.line)
        elif isinstance(node, IfStmt):            self.compile_if(node)
        elif isinstance(node, WhileStmt):         self.compile_while(node)
        elif isinstance(node, ForStmt):           self.compile_for(node)
        elif isinstance(node, ReturnStmt):
            self.compile_expr(node.expr); self.emit(Op.RETURN, None, node.line)
        elif isinstance(node, BreakStmt):
            self.emit(Op.JUMP, '__break__', node.line)   # placeholder
        elif isinstance(node, ContinueStmt):
            self.emit(Op.JUMP, '__continue__', node.line)
        elif isinstance(node, AppendStmt):        self.compile_append(node)
        elif isinstance(node, PopStmt):           self.compile_pop(node)
        elif isinstance(node, TryStmt):           self.compile_try(node)
        else:
            raise CompileError(f"未知語句：{type(node).__name__}")

    # ── 函數定義 ─────────────────────────────────────────────

    def compile_funcdef(self, node: FuncDefStmt):
        """
        編譯函數定義。函數體編譯成獨立的 Bytecode，以 CALL 指令呼叫時由 VM 執行。
        在主程式碼流程中插入 JUMP 跳過函數體。

        佈局：
          JUMP  func_end      ← 跳過函數體
        func_start:
          ... 函數體 bytecode ...
          RETURN              ← 隱式 return（若無明確 return）
        func_end:
        """
        jmp_idx = self.emit(Op.JUMP, -1, node.line)
        func_start = self.current_addr()

        # 建立子編譯器（繼承 func_table，但獨立的 var_types）
        sub = Compiler(func_table=self.func_table)
        # 參數預設型態為 any（執行期決定）
        for p in node.params:
            sub.var_types[p] = T_ANY
        for stmt in node.body:
            sub.compile_stmt(stmt)
        sub.emit(Op.PUSH_INT, 0)  # 隱式 return 0
        sub.emit(Op.RETURN)

        # 把子編譯器的 code 移植到主 code，修正位址偏移
        offset = len(self.code)
        for instr in sub.code:
            new_instr = Instruction(instr.op, instr.arg, instr.source_line)
            # 修正跳轉位址
            if instr.op in (Op.JUMP, Op.JUMP_IF_FALSE, Op.TRY_BEGIN) and isinstance(instr.arg, int):
                new_instr.arg = instr.arg + offset
            self.code.append(new_instr)

        func_end = self.current_addr()
        self.patch(jmp_idx, func_end)

        # 記錄函數資訊：(起始位址, 參數列表)
        self.func_table[node.name] = ('compiled', func_start, node.params)

    # ── 宣告 / 賦值 ──────────────────────────────────────────

    def compile_declare(self, node: DeclareStmt):
        ann = node.type_annotation
        type_map = {'int':T_INT,'str':T_STR,'int_list':T_ILIST,'str_list':T_SLIST}
        expected = type_map.get(ann, T_ANY)
        if node.name in self.var_types:
            # 已宣告：退化為賦值（允許重複使用同名變數）
            self.compile_expr(node.expr)
            self.emit(Op.STORE, node.name, node.line)
            return
        self.var_types[node.name] = expected
        self.compile_expr(node.expr)
        self.emit(Op.DECLARE, (node.name, ann), node.line)
        self.emit(Op.STORE, node.name, node.line)

    def compile_assign(self, node: AssignStmt):
        if node.name not in self.var_types:
            raise CompileError(f"賦值給未宣告的變數「{node.name}」", node.line)
        self.compile_expr(node.expr)
        self.emit(Op.STORE, node.name, node.line)

    def compile_index_assign(self, node: IndexAssignStmt):
        if node.name not in self.var_types:
            raise CompileError(f"索引賦值給未宣告的變數「{node.name}」", node.line)
        self.compile_expr(node.index)
        self.compile_expr(node.expr)
        self.emit(Op.STORE_INDEX, node.name, node.line)

    # ── if / while / for ─────────────────────────────────────

    def compile_if(self, node: IfStmt):
        self.compile_expr(node.condition)
        jif = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
        for s in node.then_block: self.compile_stmt(s)
        if node.else_block:
            jmp = self.emit(Op.JUMP, -1, node.line)
            self.patch(jif, self.current_addr())
            for s in node.else_block: self.compile_stmt(s)
            self.patch(jmp, self.current_addr())
        else:
            self.patch(jif, self.current_addr())

    def compile_while(self, node: WhileStmt):
        loop_start = self.current_addr()
        self.compile_expr(node.condition)
        jif = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
        body_start = len(self.code)
        for s in node.body: self.compile_stmt(s)
        self.emit(Op.JUMP, loop_start, node.line)
        loop_end = self.current_addr()
        self.patch(jif, loop_end)
        # 修補 break / continue
        self._patch_loop_controls(body_start, len(self.code)-1, loop_end, loop_start)

    def compile_for(self, node: ForStmt):
        """
        從 start 到 end 以 var 做：body

        編譯成：
          DECLARE var int (若未宣告)
          compile(start) → STORE var
          loop_start:
            LOAD var <= compile(end) → JUMP_IF_FALSE loop_end
            body
            LOAD var + 1 → STORE var
            JUMP loop_start
          loop_end:
        """
        ln = node.line
        # 宣告或使用循環變數
        if node.varname not in self.var_types:
            self.var_types[node.varname] = T_INT
            self.compile_expr(node.start)
            self.emit(Op.DECLARE, (node.varname, 'int'), ln)
            self.emit(Op.STORE, node.varname, ln)
        else:
            self.compile_expr(node.start)
            self.emit(Op.STORE, node.varname, ln)

        loop_start = self.current_addr()
        # 條件：var <= end
        self.emit(Op.LOAD, node.varname, ln)
        self.compile_expr(node.end)
        self.emit(Op.LTE, None, ln)
        jif = self.emit(Op.JUMP_IF_FALSE, -1, ln)

        body_start = len(self.code)
        for s in node.body: self.compile_stmt(s)
        continue_addr = self.current_addr()
        # var = var + 1
        self.emit(Op.LOAD, node.varname, ln)
        self.emit(Op.PUSH_INT, 1, ln)
        self.emit(Op.ADD, None, ln)
        self.emit(Op.STORE, node.varname, ln)
        self.emit(Op.JUMP, loop_start, ln)

        loop_end = self.current_addr()
        self.patch(jif, loop_end)
        self._patch_loop_controls(body_start, continue_addr-1, loop_end, continue_addr)

    def _patch_loop_controls(self, start, end, break_addr, continue_addr):
        """將範圍內的 break/continue 佔位修補為實際位址"""
        for i in range(start, min(end+1, len(self.code))):
            instr = self.code[i]
            if instr.op == Op.JUMP:
                if instr.arg == '__break__':    instr.arg = break_addr
                elif instr.arg == '__continue__': instr.arg = continue_addr

    # ── append / pop ─────────────────────────────────────────

    def compile_append(self, node: AppendStmt):
        if node.listname not in self.var_types:
            raise CompileError(f"未宣告的列表「{node.listname}」", node.line)
        self.compile_expr(node.expr)
        self.emit(Op.APPEND, node.listname, node.line)

    def compile_pop(self, node: PopStmt):
        if node.listname not in self.var_types:
            raise CompileError(f"未宣告的列表「{node.listname}」", node.line)
        if node.varname and node.varname not in self.var_types:
            # 自動宣告接收變數
            self.var_types[node.varname] = T_ANY
            self.emit(Op.POP_LIST, (node.listname, node.varname), node.line)
            self.emit(Op.DECLARE, (node.varname, 'any'), node.line)
        else:
            self.emit(Op.POP_LIST, (node.listname, node.varname), node.line)

    # ── try / except ─────────────────────────────────────────

    def compile_try(self, node: TryStmt):
        """
          TRY_BEGIN handler_addr
          try_body
          TRY_END
          JUMP after
        handler_addr:
          except_body
        after:
        """
        try_begin_idx = self.emit(Op.TRY_BEGIN, -1, node.line)
        for s in node.try_block: self.compile_stmt(s)
        self.emit(Op.TRY_END)
        jmp = self.emit(Op.JUMP, -1, node.line)
        handler_addr = self.current_addr()
        self.patch(try_begin_idx, handler_addr)
        for s in node.except_block: self.compile_stmt(s)
        self.patch(jmp, self.current_addr())

    # ── 表達式 ───────────────────────────────────────────────

    def compile_expr(self, node):
        if isinstance(node, IntLiteral):
            self.emit(Op.PUSH_INT, node.value, node.line)
        elif isinstance(node, StrLiteral):
            self.emit(Op.PUSH_STR, node.value, node.line)
        elif isinstance(node, ListLiteral):
            for el in node.elements: self.compile_expr(el)
            self.emit(Op.BUILD_LIST, len(node.elements), node.line)
        elif isinstance(node, IndexExpr):
            self.compile_expr(node.target)
            self.compile_expr(node.index)
            self.emit(Op.LOAD_INDEX, None, node.line)
        elif isinstance(node, Identifier):
            if node.name not in self.var_types:
                raise CompileError(f"未宣告的變數「{node.name}」", node.line)
            self.emit(Op.LOAD, node.name, node.line)
        elif isinstance(node, BuiltinCall):
            for a in node.args: self.compile_expr(a)
            if node.func == '長度': self.emit(Op.LIST_LEN, None, node.line)
        elif isinstance(node, CallExpr):
            for a in node.args: self.compile_expr(a)
            self.emit(Op.CALL, (node.name, len(node.args)), node.line)
        elif isinstance(node, UnaryOp):
            self.compile_expr(node.operand)
            self.emit(Op.NEG if node.op=='neg' else Op.NOT, None, node.line)
        elif isinstance(node, BinOp):
            self.compile_binop(node)
        else:
            raise CompileError(f"未知表達式：{type(node).__name__}")

    def compile_binop(self, node: BinOp):
        # 短路
        if node.op == '&&':
            self.compile_expr(node.left)
            jif = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
            self.compile_expr(node.right)
            jmp = self.emit(Op.JUMP, -1)
            self.patch(jif, self.current_addr()); self.emit(Op.PUSH_INT, 0)
            self.patch(jmp, self.current_addr()); return
        if node.op == '||':
            self.compile_expr(node.left)
            jif = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
            self.emit(Op.PUSH_INT, 1)
            jmp = self.emit(Op.JUMP, -1)
            self.patch(jif, self.current_addr())
            self.compile_expr(node.right)
            self.patch(jmp, self.current_addr()); return
        self.compile_expr(node.left)
        self.compile_expr(node.right)
        op_map = {'+':Op.ADD,'-':Op.SUB,'*':Op.MUL,'/':Op.DIV,'%':Op.MOD,'**':Op.POW,
                  '==':Op.EQ,'!=':Op.NEQ,'>':Op.GT,'<':Op.LT,'>=':Op.GTE,'<=':Op.LTE}
        if node.op not in op_map:
            raise CompileError(f"未知運算子：{node.op}")
        self.emit(op_map[node.op], None, node.line)


# ============================================================
# VM
# ============================================================

class VM:
    def __init__(self, code, debug=False, input_fn=None, base_dir='.'):
        self.code    = code
        self.debug   = debug
        self.input_fn = input_fn or input  # 可替換供測試
        self.base_dir = base_dir
        self.stack: List[Any]       = []
        self.vars:  Dict[str, Any]  = {}
        self.var_types: Dict[str,str] = {}
        self.pc     = 0
        self.output: List[str] = []
        # 函數呼叫堆疊：[(return_pc, saved_vars, saved_var_types), ...]
        self.call_stack: List = []
        # 函數表：name → ('compiled', start_addr, params)
        self.func_table: Dict = {}
        # 錯誤處理堆疊：[handler_addr, ...]
        self.try_stack: List[int] = []

    def push(self, v): self.stack.append(v)
    def pop(self):
        if not self.stack: raise ZhRuntimeError("堆疊下溢", self.pc)
        return self.stack.pop()

    def run(self):
        while self.pc < len(self.code):
            instr = self.code[self.pc]
            if self.debug: self._dbg(instr)
            self.pc += 1
            try:
                self._exec(instr)
            except (ZhRuntimeError, IndexError, ZeroDivisionError, Exception) as e:
                if self.try_stack:
                    # 跳到錯誤處理器
                    handler = self.try_stack.pop()
                    self.pc = handler
                    # 清空多餘堆疊（保留基底）
                else:
                    raise
        return self.output

    def _exec(self, instr):
        op, arg = instr.op, instr.arg

        if   op == Op.PUSH_INT:   self.push(int(arg))
        elif op == Op.PUSH_STR:   self.push(str(arg))
        elif op == Op.LOAD:
            if arg not in self.vars: raise ZhRuntimeError(f"變數「{arg}」未初始化", self.pc)
            self.push(self.vars[arg])
        elif op == Op.STORE:      self.vars[arg] = self.pop()
        elif op == Op.DECLARE:
            name, type_ann = arg; self.var_types[name] = type_ann

        # ── 列表 ──────────────────────────────────────────
        elif op == Op.BUILD_LIST:
            n = arg
            items = self.stack[-n:]; del self.stack[-n:]
            self.push(list(items))
        elif op == Op.LOAD_INDEX:
            idx = self.pop(); lst = self.pop()
            if not isinstance(lst, list): raise ZhRuntimeError(f"不是列表", self.pc)
            if not isinstance(idx, int):  raise ZhRuntimeError(f"索引必須是整數", self.pc)
            if idx < 0 or idx >= len(lst): raise ZhRuntimeError(f"索引 {idx} 超出範圍（長度{len(lst)}）", self.pc)
            self.push(lst[idx])
        elif op == Op.STORE_INDEX:
            val = self.pop(); idx = self.pop()
            lst = self.vars.get(arg)
            if not isinstance(lst, list): raise ZhRuntimeError(f"「{arg}」不是列表", self.pc)
            if idx < 0 or idx >= len(lst): raise ZhRuntimeError(f"索引 {idx} 超出範圍", self.pc)
            lst[idx] = val
        elif op == Op.APPEND:
            val = self.pop(); lst = self.vars.get(arg)
            if not isinstance(lst, list): raise ZhRuntimeError(f"「{arg}」不是列表", self.pc)
            lst.append(val)
        elif op == Op.POP_LIST:
            listname, dest = arg
            lst = self.vars.get(listname)
            if not isinstance(lst, list): raise ZhRuntimeError(f"「{listname}」不是列表", self.pc)
            if not lst: raise ZhRuntimeError(f"列表「{listname}」已空，無法彈出", self.pc)
            val = lst.pop()
            if dest: self.vars[dest] = val
        elif op == Op.LIST_LEN:
            v = self.pop()
            if isinstance(v, (list, str)): self.push(len(v))
            else: raise ZhRuntimeError(f"長度只能用於列表或字串", self.pc)

        # ── 算術 ──────────────────────────────────────────
        elif op == Op.ADD:
            b, a = self.pop(), self.pop()
            if isinstance(a, str) and isinstance(b, str): self.push(a+b)
            elif isinstance(a, int) and isinstance(b, int): self.push(a+b)
            else: raise ZhRuntimeError(f"加法型態不符：{type(a).__name__}+{type(b).__name__}", self.pc)
        elif op == Op.SUB:  b,a=self.pop(),self.pop(); self.push(a-b)
        elif op == Op.MUL:  b,a=self.pop(),self.pop(); self.push(a*b)
        elif op == Op.DIV:
            b,a=self.pop(),self.pop()
            if b==0: raise ZhRuntimeError("除以零", self.pc)
            self.push(a//b)
        elif op == Op.MOD:
            b,a=self.pop(),self.pop()
            if b==0: raise ZhRuntimeError("餘數除以零", self.pc)
            self.push(a%b)
        elif op == Op.POW:  b,a=self.pop(),self.pop(); self.push(a**b)
        elif op == Op.NEG:  self.push(-self.pop())

        # ── 比較 / 邏輯 ───────────────────────────────────
        elif op == Op.EQ:  b,a=self.pop(),self.pop(); self.push(1 if a==b else 0)
        elif op == Op.NEQ: b,a=self.pop(),self.pop(); self.push(1 if a!=b else 0)
        elif op == Op.GT:  b,a=self.pop(),self.pop(); self.push(1 if a>b  else 0)
        elif op == Op.LT:  b,a=self.pop(),self.pop(); self.push(1 if a<b  else 0)
        elif op == Op.GTE: b,a=self.pop(),self.pop(); self.push(1 if a>=b else 0)
        elif op == Op.LTE: b,a=self.pop(),self.pop(); self.push(1 if a<=b else 0)
        elif op == Op.AND: b,a=self.pop(),self.pop(); self.push(1 if (a and b) else 0)
        elif op == Op.OR:  b,a=self.pop(),self.pop(); self.push(1 if (a or  b) else 0)
        elif op == Op.NOT: self.push(0 if self.pop() else 1)

        # ── 跳轉 ──────────────────────────────────────────
        elif op == Op.JUMP:           self.pc = arg
        elif op == Op.JUMP_IF_FALSE:
            if not self.pop(): self.pc = arg

        # ── 輸入/輸出 ─────────────────────────────────────
        elif op == Op.PRINT:
            val = self.pop()
            line = "［"+"，".join(str(v) for v in val)+"］" if isinstance(val, list) else str(val)
            self.output.append(line); print(line)
        elif op == Op.INPUT:
            prompt, varname = arg
            try:
                val = self.input_fn(prompt + " ")
            except EOFError:
                val = ""
            self.vars[varname] = val
            if varname not in self.var_types: self.var_types[varname] = 'str'

        # ── 函數 ──────────────────────────────────────────
        elif op == Op.CALL:
            fname, argc = arg
            if fname not in self.func_table:
                raise ZhRuntimeError(f"未知函數「{fname}」", self.pc)
            entry = self.func_table[fname]
            args = list(reversed([self.pop() for _ in range(argc)]))
            if entry[0] == 'compiled':
                _, start_addr, params = entry
                if len(args) != len(params):
                    raise ZhRuntimeError(f"函數「{fname}」需要 {len(params)} 個引數，但給了 {len(args)} 個", self.pc)
                self.call_stack.append((self.pc, dict(self.vars), dict(self.var_types)))
                self.vars = {p: v for p, v in zip(params, args)}
                self.var_types = {p: 'any' for p in params}
                self.pc = start_addr
            elif entry[0] == 'external':
                _, mod_vm, start_addr, params = entry
                if len(args) != len(params):
                    raise ZhRuntimeError(f"函數「{fname}」需要 {len(params)} 個引數，但給了 {len(args)} 個", self.pc)
                # 在模組 VM 上執行函數
                mod_vm.stack = list(args)  # 把引數放入模組 VM 的堆疊
                mod_vm.vars = {p: v for p, v in zip(params, args)}
                mod_vm.var_types = {p: 'any' for p in params}
                mod_vm.call_stack = []
                mod_vm.pc = start_addr
                # 執行直到函數 RETURN（用 call_stack 深度判斷）
                from lexer_parser import ASTNode  # ensure import not needed
                initial_depth = len(mod_vm.call_stack)
                mod_vm.call_stack = []   # 清空，讓 RETURN 能正確回到這裡
                initial_stack_len = len(mod_vm.stack)
                # 把引數推入 mod_vm stack 並設置呼叫幀
                # 使用 mod_vm 的 compiled CALL 機制
                mod_vm.stack = []
                mod_vm.vars = {p: v for p, v in zip(params, args)}
                mod_vm.var_types = {p: 'any' for p in params}
                mod_vm.pc = start_addr
                # 執行，RETURN 會把值推入 mod_vm.stack 並設 pc 超出範圍
                try:
                    while mod_vm.pc < len(mod_vm.code):
                        mi = mod_vm.code[mod_vm.pc]; mod_vm.pc += 1
                        if mi.op.value == 'RETURN':
                            # 執行 RETURN：若 call_stack 空，則這是頂層 return
                            if not mod_vm.call_stack:
                                ret_val = mod_vm.pop()
                                self.push(ret_val)
                                break
                        mod_vm._exec(mi)
                    else:
                        ret = mod_vm.stack[-1] if mod_vm.stack else 0
                        self.push(ret)
                except Exception as e:
                    raise ZhRuntimeError(f"外部函數「{fname}」執行錯誤：{e}", self.pc)
            else:
                raise ZhRuntimeError(f"函數「{fname}」格式錯誤", self.pc)
        elif op == Op.RETURN:
            ret_val = self.pop()
            if not self.call_stack:
                self.push(ret_val); self.pc = len(self.code); return
            ret_pc, saved_vars, saved_types = self.call_stack.pop()
            self.vars = saved_vars; self.var_types = saved_types
            self.pc = ret_pc
            self.push(ret_val)

        # ── 錯誤處理 ──────────────────────────────────────
        elif op == Op.TRY_BEGIN:   self.try_stack.append(arg)
        elif op == Op.TRY_END:
            if self.try_stack: self.try_stack.pop()

        # ── 引入 ──────────────────────────────────────────
        elif op == Op.IMPORT:
            self._do_import(arg)

        elif op == Op.HALT: self.pc = len(self.code)

    def _do_import(self, module_name: str):
        """引入另一個 .中文 檔案，執行後其函數可在本 VM 中呼叫"""
        candidates = [
            os.path.join(self.base_dir, f"{module_name}.中文"),
            os.path.join(self.base_dir, f"{module_name}.txt"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            raise ZhRuntimeError(f"找不到模組「{module_name}」（找過：{candidates}）", self.pc)
        with open(path, encoding='utf-8') as f:
            src = f.read()
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        comp   = Compiler()
        code   = comp.compile(ast)
        # 建立模組專屬 VM 並執行（執行頂層程式碼）
        mod_vm = VM(code, base_dir=self.base_dir, input_fn=self.input_fn)
        mod_vm.func_table = {}
        mod_vm.run()
        # 把模組自身的函數表設置好（供遞迴呼叫使用）
        for fname, entry in comp.func_table.items():
            if entry[0] == 'compiled':
                mod_vm.func_table[fname] = entry   # 使用 compiled 格式，位址在 mod_vm.code
        # 合併函數表：把模組的函數包裝成「帶 vm 的條目」，供外部呼叫
        for fname, entry in comp.func_table.items():
            if entry[0] == 'compiled':
                _, start_addr, params = entry
                self.func_table[fname] = ('external', mod_vm, start_addr, params)

    def _dbg(self, instr):
        s = str(self.stack[-4:]) if self.stack else "[]"
        print(f"  [PC={self.pc:03d}] {str(instr):<30} | 堆疊:{s}")


# ============================================================
# 反組譯器
# ============================================================

def disassemble(code):
    lines = ["位址  指令              參數", "─"*50]
    for i, ins in enumerate(code):
        a = repr(ins.arg) if ins.arg is not None else ""
        lines.append(f"{i:04d}  {ins.op.value:<20} {a}")
    return "\n".join(lines)


# ============================================================
# 統一執行介面
# ============================================================

def run_source(source: str, debug=False, show_ast=False, show_bytecode=False,
               input_fn=None, base_dir=None) -> List[str]:
    # base_dir 未指定時，預設使用 compiler_vm.py 本身所在的目錄
    # 這樣不管從哪裡執行（終端機、GUI、其他腳本），引入模組都能找到正確路徑
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    tokens  = Lexer(source).tokenize()
    ast     = Parser(tokens).parse()
    if show_ast:
        print("\n── AST ──────────────────────────────")
        print(pretty_print_ast(ast))
    comp    = Compiler()
    code    = comp.compile(ast)
    if show_bytecode:
        print("\n── Bytecode ─────────────────────────")
        print(disassemble(code))
    if debug: print("\n── VM 追蹤 ──────────────────────────")
    vm = VM(code, debug=debug, input_fn=input_fn, base_dir=base_dir)
    vm.func_table = comp.func_table
    return vm.run()


def run_file(path: str, debug=False, show_ast=False, show_bytecode=False):
    with open(path, encoding='utf-8') as f: src = f.read()
    print(f"執行：{path}\n{'─'*45}")
    run_source(src, debug=debug, show_ast=show_ast, show_bytecode=show_bytecode,
               base_dir=os.path.dirname(os.path.abspath(path)))
    print(f"{'─'*45}\n執行完畢 ✓")


def repl():
    print("="*55)
    print("  繁體中文程式語言  REPL")
    print("  空行執行  /  「結束」離開")
    print("="*55)
    while True:
        lines = []; print()
        try:
            while True:
                try: line = input(">>> " if not lines else "... ")
                except EOFError: return
                if line.strip() == "結束": print("再見！"); return
                if line == "" and lines: break
                lines.append(line)
        except KeyboardInterrupt: print("\n再見！"); return
        src = "\n".join(lines)
        if not src.strip(): continue
        try: run_source(src)
        except Exception as e: print(f"  ✗ {e}")


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("用法："); print("  python compiler_vm.py <檔案.中文>  [--debug] [--ast] [--bytecode]")
        print("  python compiler_vm.py repl")
    elif args[0] == "repl": repl()
    else:
        run_file(args[0],
                 debug="--debug" in args,
                 show_ast="--ast" in args,
                 show_bytecode="--bytecode" in args)