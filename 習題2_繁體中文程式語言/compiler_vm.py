"""
繁體中文程式語言 - Compiler (編譯器) 與 Stack-based VM (堆疊虛擬機)
====================================================================

Bytecode 指令集
===============
  PUSH_INT  <int>     — 將整數常數推入堆疊
  PUSH_STR  <str>     — 將字串常數推入堆疊
  LOAD      <name>    — 將變數值推入堆疊
  STORE     <name>    — 從堆疊頂端彈出並存入變數
  DECLARE   <name> <type>  — 宣告新變數（型態檢查用）
  ADD                 — 彈出兩個值，推入相加結果
  SUB                 — 彈出兩個值，推入相減結果
  MUL                 — 彈出兩個值，推入相乘結果
  DIV                 — 彈出兩個值，推入相除結果
  NEG                 — 彈出一個值，推入其負值
  EQ / NEQ            — 等於 / 不等於比較
  GT / LT / GTE / LTE — 大於 / 小於 / 大於等於 / 小於等於
  AND / OR / NOT      — 邏輯運算
  JUMP      <addr>    — 無條件跳轉到指定位址
  JUMP_IF_FALSE <addr>— 若堆疊頂端為 False 則跳轉
  PRINT               — 彈出堆疊頂端並輸出
  HALT                — 程式結束
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto

# ── 從 lexer_parser 引入所有 AST 定義 ────────────────────────
from lexer_parser import (
    Lexer, Parser,
    Program, DeclareStmt, AssignStmt, IndexAssignStmt,
    PrintStmt, IfStmt, WhileStmt,
    BinOp, UnaryOp, IntLiteral, StrLiteral, ListLiteral, IndexExpr, Identifier,
    ASTNode, pretty_print_ast,
)


# ============================================================
# Bytecode 指令定義
# ============================================================

class Op(Enum):
    PUSH_INT        = "PUSH_INT"
    PUSH_STR        = "PUSH_STR"
    LOAD            = "LOAD"
    STORE           = "STORE"
    DECLARE         = "DECLARE"
    ADD             = "ADD"
    SUB             = "SUB"
    MUL             = "MUL"
    DIV             = "DIV"
    NEG             = "NEG"
    EQ              = "EQ"
    NEQ             = "NEQ"
    GT              = "GT"
    LT              = "LT"
    GTE             = "GTE"
    LTE             = "LTE"
    AND             = "AND"
    OR              = "OR"
    NOT             = "NOT"
    BUILD_LIST      = "BUILD_LIST"
    LOAD_INDEX      = "LOAD_INDEX"
    STORE_INDEX     = "STORE_INDEX"
    JUMP            = "JUMP"
    JUMP_IF_FALSE   = "JUMP_IF_FALSE"
    PRINT           = "PRINT"
    HALT            = "HALT"


@dataclass
class Instruction:
    op: Op
    arg: Any = None          # 可選參數（常數值、變數名稱、跳轉位址）
    source_line: int = 0     # 對應原始碼行號（Debug 用）

    def __repr__(self):
        if self.arg is not None:
            return f"{self.op.value:<18} {self.arg!r}"
        return self.op.value


# 型態常數
TYPE_INT      = 'int'
TYPE_STR      = 'str'
TYPE_BOOL     = 'bool'      # 條件運算的內部型態
TYPE_INT_LIST = 'int_list'  # 整數列表
TYPE_STR_LIST = 'str_list'  # 字串列表
TYPE_LIST     = 'list'      # 不限元素型態（IndexExpr 回傳時用）


# ============================================================
# 編譯錯誤
# ============================================================

class CompileError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[編譯錯誤] 第{line}行：{msg}" if line else f"[編譯錯誤] {msg}")
        self.line = line


# ============================================================
# COMPILER 編譯器
# ============================================================

class Compiler:
    """
    將 AST 編譯成 Bytecode 指令列表。

    型態系統：
    - 每個變數宣告時記錄其型態
    - 賦值時檢查右側型態是否相符
    - 算術運算只允許整數
    - 字串加法（加）允許兩個字串串接
    - 比較運算回傳 bool（供 JUMP_IF_FALSE 使用）

    跳轉位址修補（Backpatching）：
    - 編譯 if/while 時，先插入帶有 -1 佔位的 JUMP_IF_FALSE
    - 等待後面的區塊編譯完成後，回頭填入正確位址
    """

    def __init__(self):
        self.code: List[Instruction] = []
        # 變數型態表：name -> 'int' | 'str'
        self.var_types: Dict[str, str] = {}

    # ── 輔助方法 ──────────────────────────────────────────

    def emit(self, op: Op, arg=None, line: int = 0) -> int:
        """發出一條指令，回傳其在 code 中的索引"""
        self.code.append(Instruction(op, arg, line))
        return len(self.code) - 1

    def current_addr(self) -> int:
        """回傳下一條指令的位址"""
        return len(self.code)

    def patch(self, idx: int, addr: int):
        """修補指定位置的跳轉目標位址"""
        self.code[idx].arg = addr

    # ── 型態推導 ──────────────────────────────────────────

    def infer_type(self, node: ASTNode) -> str:
        """靜態推導表達式的型態，回傳 'int'|'str'|'bool'|'int_list'|'str_list'"""
        if isinstance(node, IntLiteral):
            return TYPE_INT
        elif isinstance(node, StrLiteral):
            return TYPE_STR
        elif isinstance(node, Identifier):
            if node.name not in self.var_types:
                raise CompileError(f"使用了未宣告的變數「{node.name}」", node.line)
            return self.var_types[node.name]
        elif isinstance(node, ListLiteral):
            # 推導列表元素型態（空列表暫給 int_list）
            if not node.elements:
                return TYPE_INT_LIST
            elem_t = self.infer_type(node.elements[0])
            for el in node.elements[1:]:
                if self.infer_type(el) != elem_t:
                    raise CompileError("列表元素型態必須一致", node.line)
            return TYPE_INT_LIST if elem_t == TYPE_INT else TYPE_STR_LIST
        elif isinstance(node, IndexExpr):
            # 索引存取：回傳列表的元素型態
            target_t = self.infer_type(node.target)
            if target_t == TYPE_INT_LIST:
                return TYPE_INT
            elif target_t == TYPE_STR_LIST:
                return TYPE_STR
            else:
                raise CompileError(f"「{node.target}」不是列表，無法索引", node.line)
        elif isinstance(node, UnaryOp):
            if node.op == 'neg':
                t = self.infer_type(node.operand)
                if t != TYPE_INT:
                    raise CompileError("「負」只能用於整數", node.line)
                return TYPE_INT
            elif node.op == 'not':
                return TYPE_BOOL
        elif isinstance(node, BinOp):
            if node.op in ('+', '-', '*', '/'):
                lt = self.infer_type(node.left)
                rt = self.infer_type(node.right)
                if node.op == '+' and lt == TYPE_STR and rt == TYPE_STR:
                    return TYPE_STR   # 允許字串串接
                if lt != TYPE_INT or rt != TYPE_INT:
                    raise CompileError(
                        f"算術運算「{node.op}」兩側必須是整數，"
                        f"但得到 {lt} 和 {rt}", node.line)
                return TYPE_INT
            elif node.op in ('==', '!=', '>', '<', '>=', '<='):
                lt = self.infer_type(node.left)
                rt = self.infer_type(node.right)
                if lt != rt:
                    raise CompileError(
                        f"比較運算兩側型態不符：{lt} vs {rt}", node.line)
                return TYPE_BOOL
            elif node.op in ('&&', '||'):
                return TYPE_BOOL
        return TYPE_INT  # fallback

    # ── 編譯入口 ──────────────────────────────────────────

    def compile(self, program: Program) -> List[Instruction]:
        for stmt in program.statements:
            self.compile_stmt(stmt)
        self.emit(Op.HALT)
        return self.code

    # ── 語句編譯 ──────────────────────────────────────────

    def compile_stmt(self, node: ASTNode):
        if isinstance(node, DeclareStmt):
            self.compile_declare(node)
        elif isinstance(node, AssignStmt):
            self.compile_assign(node)
        elif isinstance(node, IndexAssignStmt):
            self.compile_index_assign(node)
        elif isinstance(node, PrintStmt):
            self.compile_print(node)
        elif isinstance(node, IfStmt):
            self.compile_if(node)
        elif isinstance(node, WhileStmt):
            self.compile_while(node)
        else:
            raise CompileError(f"未知的語句節點：{type(node).__name__}")

    def compile_declare(self, node: DeclareStmt):
        """
        令 X 為 整數 等於 expr。         →  DECLARE X int  / STORE X
        令 X 為 整數列表 等於 ［...］。  →  BUILD_LIST n  / DECLARE X int_list / STORE X
        """
        ann = node.type_annotation   # 'int' | 'str' | 'int_list' | 'str_list'
        type_map = {
            'int':      TYPE_INT,
            'str':      TYPE_STR,
            'int_list': TYPE_INT_LIST,
            'str_list': TYPE_STR_LIST,
        }
        if ann not in type_map:
            raise CompileError(f"未知型態標注：{ann}", node.line)
        expected = type_map[ann]

        expr_type = self.infer_type(node.expr)
        # 允許 bool 直接賦給 int（條件運算結果）
        if expr_type == TYPE_BOOL and expected == TYPE_INT:
            pass
        elif expr_type != expected:
            raise CompileError(
                f"變數「{node.name}」宣告為 {ann}，"
                f"但初始值型態為 {expr_type}", node.line)
        if node.name in self.var_types:
            raise CompileError(f"變數「{node.name}」已經宣告過了", node.line)
        self.var_types[node.name] = expected
        self.compile_expr(node.expr)
        self.emit(Op.DECLARE, (node.name, ann), node.line)
        self.emit(Op.STORE, node.name, node.line)

    def compile_assign(self, node: AssignStmt):
        """
        令 X 等於 expr。
        →  compile(expr)
           STORE  X
        """
        if node.name not in self.var_types:
            raise CompileError(f"賦值給未宣告的變數「{node.name}」", node.line)
        expr_type = self.infer_type(node.expr)
        expected = self.var_types[node.name]
        # bool 可賦給 int（條件運算結果），列表間同型態可互賦
        if expr_type != expected and not (expr_type == TYPE_BOOL and expected == TYPE_INT):
            raise CompileError(
                f"變數「{node.name}」是 {expected}，"
                f"但賦值型態為 {expr_type}", node.line)
        self.compile_expr(node.expr)
        self.emit(Op.STORE, node.name, node.line)

    def compile_index_assign(self, node: IndexAssignStmt):
        """
        令 X［idx］ 等於 expr。
        →  compile(idx)
           compile(expr)
           STORE_INDEX  X

        堆疊執行順序（STORE_INDEX 取出時）：
          先 pop → value，後 pop → index
          然後 vars[X][index] = value
        """
        if node.name not in self.var_types:
            raise CompileError(f"索引賦值給未宣告的變數「{node.name}」", node.line)
        var_t = self.var_types[node.name]
        if var_t not in (TYPE_INT_LIST, TYPE_STR_LIST):
            raise CompileError(f"變數「{node.name}」不是列表，無法索引賦值", node.line)
        # 索引必須是整數
        idx_t = self.infer_type(node.index)
        if idx_t != TYPE_INT:
            raise CompileError("列表索引必須是整數", node.line)
        # 元素值型態
        elem_expected = TYPE_INT if var_t == TYPE_INT_LIST else TYPE_STR
        val_t = self.infer_type(node.expr)
        if val_t != elem_expected and not (val_t == TYPE_BOOL and elem_expected == TYPE_INT):
            raise CompileError(
                f"列表「{node.name}」的元素是 {elem_expected}，"
                f"但賦值型態為 {val_t}", node.line)
        self.compile_expr(node.index)   # 先推索引
        self.compile_expr(node.expr)    # 再推值
        self.emit(Op.STORE_INDEX, node.name, node.line)

    def compile_print(self, node: PrintStmt):
        """
        顯示 expr。
        →  compile(expr)
           PRINT
        """
        self.compile_expr(node.expr)
        self.emit(Op.PRINT, None, node.line)

    def compile_if(self, node: IfStmt):
        """
        如果（cond）則：then_block。完 [否則：else_block。完]

        有 else：
          compile(cond)
          JUMP_IF_FALSE  else_start    ← 修補
          compile(then_block)
          JUMP           end           ← 修補
        else_start:
          compile(else_block)
        end:

        無 else：
          compile(cond)
          JUMP_IF_FALSE  end           ← 修補
          compile(then_block)
        end:
        """
        self.compile_expr(node.condition)
        jif_idx = self.emit(Op.JUMP_IF_FALSE, -1, node.line)  # 佔位

        # then 區塊
        for stmt in node.then_block:
            self.compile_stmt(stmt)

        if node.else_block:
            jmp_idx = self.emit(Op.JUMP, -1, node.line)       # 佔位
            else_start = self.current_addr()
            self.patch(jif_idx, else_start)

            for stmt in node.else_block:
                self.compile_stmt(stmt)

            end_addr = self.current_addr()
            self.patch(jmp_idx, end_addr)
        else:
            end_addr = self.current_addr()
            self.patch(jif_idx, end_addr)

    def compile_while(self, node: WhileStmt):
        """
        當（cond）就：body。完

          loop_start:
            compile(cond)
            JUMP_IF_FALSE  loop_end    ← 修補
            compile(body)
            JUMP           loop_start
          loop_end:
        """
        loop_start = self.current_addr()
        self.compile_expr(node.condition)
        jif_idx = self.emit(Op.JUMP_IF_FALSE, -1, node.line)  # 佔位

        for stmt in node.body:
            self.compile_stmt(stmt)

        self.emit(Op.JUMP, loop_start, node.line)
        loop_end = self.current_addr()
        self.patch(jif_idx, loop_end)

    # ── 表達式編譯 ────────────────────────────────────────

    def compile_expr(self, node: ASTNode):
        if isinstance(node, IntLiteral):
            self.emit(Op.PUSH_INT, node.value, node.line)
        elif isinstance(node, StrLiteral):
            self.emit(Op.PUSH_STR, node.value, node.line)
        elif isinstance(node, ListLiteral):
            # 依序編譯每個元素，再用 BUILD_LIST n 打包
            for el in node.elements:
                self.compile_expr(el)
            self.emit(Op.BUILD_LIST, len(node.elements), node.line)
        elif isinstance(node, IndexExpr):
            # 先 LOAD 整個列表，再推索引，最後 LOAD_INDEX
            self.compile_expr(node.target)
            self.compile_expr(node.index)
            self.emit(Op.LOAD_INDEX, None, node.line)
        elif isinstance(node, Identifier):
            if node.name not in self.var_types:
                raise CompileError(f"使用了未宣告的變數「{node.name}」", node.line)
            self.emit(Op.LOAD, node.name, node.line)
        elif isinstance(node, UnaryOp):
            self.compile_expr(node.operand)
            if node.op == 'neg':
                self.emit(Op.NEG, None, node.line)
            elif node.op == 'not':
                self.emit(Op.NOT, None, node.line)
        elif isinstance(node, BinOp):
            self.compile_binop(node)
        else:
            raise CompileError(f"未知的表達式節點：{type(node).__name__}")

    def compile_binop(self, node: BinOp):
        # 短路求值：&& 和 ||
        if node.op == '&&':
            self.compile_expr(node.left)
            # 若左側為 False，跳到末端（結果為 False）
            jif_idx = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
            self.compile_expr(node.right)
            end_idx = self.emit(Op.JUMP, -1, node.line)
            false_addr = self.current_addr()
            self.patch(jif_idx, false_addr)
            self.emit(Op.PUSH_INT, 0)   # False
            end_addr = self.current_addr()
            self.patch(end_idx, end_addr)
            return

        if node.op == '||':
            self.compile_expr(node.left)
            # 若左側為 True，跳到末端（結果為 True）
            # 先複製頂端，若為 True 跳過右側
            jit_idx = self.emit(Op.JUMP_IF_FALSE, -1, node.line)
            self.emit(Op.PUSH_INT, 1)   # True
            jmp_idx = self.emit(Op.JUMP, -1, node.line)
            right_addr = self.current_addr()
            self.patch(jit_idx, right_addr)
            self.compile_expr(node.right)
            end_addr = self.current_addr()
            self.patch(jmp_idx, end_addr)
            return

        # 一般二元運算：先編譯兩側，再發出指令
        self.compile_expr(node.left)
        self.compile_expr(node.right)

        op_map = {
            '+':  Op.ADD,
            '-':  Op.SUB,
            '*':  Op.MUL,
            '/':  Op.DIV,
            '==': Op.EQ,
            '!=': Op.NEQ,
            '>':  Op.GT,
            '<':  Op.LT,
            '>=': Op.GTE,
            '<=': Op.LTE,
        }
        if node.op not in op_map:
            raise CompileError(f"未知的二元運算子：{node.op}", node.line)
        self.emit(op_map[node.op], None, node.line)


# ============================================================
# 執行期錯誤
# ============================================================

class RuntimeError_(Exception):
    def __init__(self, msg: str, pc: int = 0):
        super().__init__(f"[執行錯誤] 指令#{pc}：{msg}")
        self.pc = pc


# ============================================================
# STACK-BASED VM 堆疊虛擬機
# ============================================================

class VM:
    """
    堆疊虛擬機：逐條執行 Bytecode 指令。

    狀態：
    - stack：運算堆疊，存放 int | str | bool
    - vars：變數字典，存放 { name: value }
    - var_types：變數型態，存放 { name: 'int'|'str' }
    - pc：程式計數器（Program Counter）
    - output：程式輸出結果串列（供測試用）
    """

    def __init__(self, code: List[Instruction], debug: bool = False):
        self.code = code
        self.debug = debug
        self.stack: List[Any] = []
        self.vars: Dict[str, Any] = {}
        self.var_types: Dict[str, str] = {}
        self.pc = 0
        self.output: List[str] = []

    def push(self, val: Any):
        self.stack.append(val)

    def pop(self) -> Any:
        if not self.stack:
            raise RuntimeError_("堆疊下溢（Stack Underflow）", self.pc)
        return self.stack.pop()

    def run(self) -> List[str]:
        """執行 Bytecode，回傳所有輸出行"""
        while self.pc < len(self.code):
            instr = self.code[self.pc]
            if self.debug:
                self._print_debug(instr)
            self.pc += 1

            op = instr.op
            arg = instr.arg

            # ── 常數推入 ──────────────────────────────────
            if op == Op.PUSH_INT:
                self.push(int(arg))

            elif op == Op.PUSH_STR:
                self.push(str(arg))

            # ── 變數操作 ──────────────────────────────────
            elif op == Op.DECLARE:
                name, type_ann = arg
                self.var_types[name] = type_ann

            elif op == Op.STORE:
                val = self.pop()
                if arg in self.var_types:
                    self._type_check_store(arg, val, instr)
                self.vars[arg] = val

            elif op == Op.LOAD:
                if arg not in self.vars:
                    raise RuntimeError_(f"變數「{arg}」未初始化", self.pc)
                self.push(self.vars[arg])

            # ── 列表操作 ──────────────────────────────────
            elif op == Op.BUILD_LIST:
                # 從堆疊取出 n 個元素（最先推入的在底部）
                n = arg
                if len(self.stack) < n:
                    raise RuntimeError_(f"BUILD_LIST：堆疊元素不足（需要 {n} 個）", self.pc)
                items = self.stack[-n:]   # 保持推入順序
                del self.stack[-n:]
                self.push(list(items))

            elif op == Op.LOAD_INDEX:
                # 堆疊：[... list, index]  → pop index → pop list → push list[index]
                index = self.pop()
                lst = self.pop()
                if not isinstance(lst, list):
                    raise RuntimeError_(f"LOAD_INDEX：目標不是列表，得到 {type(lst).__name__}", self.pc)
                if not isinstance(index, int):
                    raise RuntimeError_(f"列表索引必須是整數，得到 {type(index).__name__}", self.pc)
                if index < 0 or index >= len(lst):
                    raise RuntimeError_(f"索引 {index} 超出範圍（列表長度 {len(lst)}）", self.pc)
                self.push(lst[index])

            elif op == Op.STORE_INDEX:
                # arg = 變數名稱；堆疊：[... index, value]
                # pop value → pop index → vars[name][index] = value
                val = self.pop()
                index = self.pop()
                name = arg
                if name not in self.vars:
                    raise RuntimeError_(f"變數「{name}」未初始化", self.pc)
                lst = self.vars[name]
                if not isinstance(lst, list):
                    raise RuntimeError_(f"STORE_INDEX：「{name}」不是列表", self.pc)
                if not isinstance(index, int):
                    raise RuntimeError_(f"列表索引必須是整數，得到 {type(index).__name__}", self.pc)
                if index < 0 or index >= len(lst):
                    raise RuntimeError_(f"索引 {index} 超出範圍（列表長度 {len(lst)}）", self.pc)
                lst[index] = val

            # ── 算術運算 ──────────────────────────────────
            elif op == Op.ADD:
                b, a = self.pop(), self.pop()
                if isinstance(a, str) and isinstance(b, str):
                    self.push(a + b)
                elif isinstance(a, int) and isinstance(b, int):
                    self.push(a + b)
                else:
                    raise RuntimeError_(f"加法型態不符：{type(a).__name__} + {type(b).__name__}", self.pc)

            elif op == Op.SUB:
                b, a = self.pop(), self.pop()
                self._assert_int(a, b, "減法", instr)
                self.push(a - b)

            elif op == Op.MUL:
                b, a = self.pop(), self.pop()
                self._assert_int(a, b, "乘法", instr)
                self.push(a * b)

            elif op == Op.DIV:
                b, a = self.pop(), self.pop()
                self._assert_int(a, b, "除法", instr)
                if b == 0:
                    raise RuntimeError_("除以零錯誤", self.pc)
                self.push(a // b)   # 整數除法

            elif op == Op.NEG:
                a = self.pop()
                if not isinstance(a, int):
                    raise RuntimeError_(f"「負」只能用於整數，但得到 {type(a).__name__}", self.pc)
                self.push(-a)

            # ── 比較運算 ──────────────────────────────────
            elif op == Op.EQ:
                b, a = self.pop(), self.pop()
                self.push(1 if a == b else 0)

            elif op == Op.NEQ:
                b, a = self.pop(), self.pop()
                self.push(1 if a != b else 0)

            elif op == Op.GT:
                b, a = self.pop(), self.pop()
                self.push(1 if a > b else 0)

            elif op == Op.LT:
                b, a = self.pop(), self.pop()
                self.push(1 if a < b else 0)

            elif op == Op.GTE:
                b, a = self.pop(), self.pop()
                self.push(1 if a >= b else 0)

            elif op == Op.LTE:
                b, a = self.pop(), self.pop()
                self.push(1 if a <= b else 0)

            # ── 邏輯運算 ──────────────────────────────────
            elif op == Op.AND:
                b, a = self.pop(), self.pop()
                self.push(1 if (a and b) else 0)

            elif op == Op.OR:
                b, a = self.pop(), self.pop()
                self.push(1 if (a or b) else 0)

            elif op == Op.NOT:
                a = self.pop()
                self.push(0 if a else 1)

            # ── 跳轉 ──────────────────────────────────────
            elif op == Op.JUMP:
                self.pc = arg

            elif op == Op.JUMP_IF_FALSE:
                cond = self.pop()
                if not cond:
                    self.pc = arg

            # ── 輸出 ──────────────────────────────────────
            elif op == Op.PRINT:
                val = self.pop()
                if isinstance(val, list):
                    line = "［" + "，".join(str(v) for v in val) + "］"
                else:
                    line = str(val)
                self.output.append(line)
                print(line)

            # ── 結束 ──────────────────────────────────────
            elif op == Op.HALT:
                break

            else:
                raise RuntimeError_(f"未知指令：{op}", self.pc)

        return self.output

    def _type_check_store(self, name: str, val: Any, instr: Instruction):
        expected = self.var_types[name]
        actual = type(val).__name__
        type_map = {
            'int':      (int,),
            'str':      (str,),
            'int_list': (list,),
            'str_list': (list,),
        }
        if expected in type_map and not isinstance(val, type_map[expected]):
            raise RuntimeError_(
                f"型態錯誤：變數「{name}」是 {expected}，"
                f"但賦值為 {actual}", self.pc)
        # 深度檢查列表元素型態
        if expected == 'int_list' and isinstance(val, list):
            for i, el in enumerate(val):
                if not isinstance(el, int):
                    raise RuntimeError_(
                        f"整數列表「{name}」的第 {i} 個元素應為整數，"
                        f"但得到 {type(el).__name__}", self.pc)
        elif expected == 'str_list' and isinstance(val, list):
            for i, el in enumerate(val):
                if not isinstance(el, str):
                    raise RuntimeError_(
                        f"字串列表「{name}」的第 {i} 個元素應為字串，"
                        f"但得到 {type(el).__name__}", self.pc)

    def _assert_int(self, a, b, op_name: str, instr: Instruction):
        if not (isinstance(a, int) and isinstance(b, int)):
            raise RuntimeError_(
                f"{op_name}只允許整數，"
                f"但得到 {type(a).__name__} 和 {type(b).__name__}", self.pc)

    def _print_debug(self, instr: Instruction):
        stack_repr = str(self.stack[-5:]) if self.stack else "[]"
        print(f"  [PC={self.pc:03d}] {str(instr):<30} | 堆疊: {stack_repr}")


# ============================================================
# Bytecode 反組譯器（人類可讀輸出）
# ============================================================

def disassemble(code: List[Instruction]) -> str:
    lines = ["位址  指令              參數"]
    lines.append("─" * 45)
    for i, instr in enumerate(code):
        arg_str = repr(instr.arg) if instr.arg is not None else ""
        lines.append(f"{i:04d}  {instr.op.value:<18} {arg_str}")
    return "\n".join(lines)


# ============================================================
# 統一執行介面
# ============================================================

def run_source(source: str, debug: bool = False, show_ast: bool = False,
               show_bytecode: bool = False) -> List[str]:
    """
    完整執行流程：原始碼 → Lexer → Parser → Compiler → VM

    參數：
        source        — 繁體中文程式碼字串
        debug         — 是否印出 VM 執行追蹤（每條指令 + 堆疊狀態）
        show_ast      — 是否印出 AST
        show_bytecode — 是否印出 Bytecode 反組譯

    回傳：輸出行串列
    """
    # 1. 詞法分析
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # 2. 語法分析
    parser = Parser(tokens)
    ast = parser.parse()

    if show_ast:
        print("\n── AST ──────────────────────────────────────")
        print(pretty_print_ast(ast))

    # 3. 編譯
    compiler = Compiler()
    code = compiler.compile(ast)

    if show_bytecode:
        print("\n── Bytecode 反組譯 ──────────────────────────")
        print(disassemble(code))

    # 4. 執行
    if debug:
        print("\n── VM 執行追蹤 ──────────────────────────────")
    vm = VM(code, debug=debug)
    return vm.run()


# ============================================================
# 互動式 REPL（Read-Eval-Print Loop）
# ============================================================

def repl():
    """
    互動式 REPL：
    逐行輸入程式碼，輸入空行執行，輸入「結束」或 Ctrl+C 離開。
    """
    print("=" * 60)
    print("  繁體中文程式語言 REPL")
    print("  輸入程式碼後按 Enter，空行執行，輸入「結束」離開")
    print("=" * 60)

    while True:
        lines = []
        print()
        try:
            while True:
                try:
                    prompt = ">>> " if not lines else "... "
                    line = input(prompt)
                except EOFError:
                    return
                if line.strip() == "結束":
                    print("再見！")
                    return
                if line == "" and lines:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            print("\n再見！")
            return

        source = "\n".join(lines)
        if not source.strip():
            continue

        try:
            run_source(source)
        except Exception as e:
            print(f"  ✗ {e}")


# ============================================================
# 命令列執行
# ============================================================

def run_file(path: str, debug: bool = False,
             show_ast: bool = False, show_bytecode: bool = False):
    """讀取 .中文 檔案並執行"""
    with open(path, encoding='utf-8') as f:
        source = f.read()
    print(f"執行：{path}")
    print("─" * 45)
    run_source(source, debug=debug, show_ast=show_ast, show_bytecode=show_bytecode)
    print("─" * 45)
    print("執行完畢 ✓")


# ============================================================
# 完整示範
# ============================================================

DEMO_PROGRAMS = {
    "基本輸出與算術": """
令 甲 為 整數 等於 10。
令 乙 為 整數 等於 3。
令 總和 為 整數 等於 甲 加 乙。
令 積 為 整數 等於 甲 乘 乙。
令 商 為 整數 等於 甲 除 乙。
顯示 總和。
顯示 積。
顯示 商。
""",

    "字串操作": """
令 姓 為 字串 等於 「王」。
令 名 為 字串 等於 「小明」。
令 全名 為 字串 等於 姓 加 名。
顯示 全名。
""",

    "條件判斷": """
令 分數 為 整數 等於 85。
如果（分數 大於等於 60）則：
  顯示 「及格」。
。完否則：
  顯示 「不及格」。
。完
""",

    "循環計數": """
令 計數 為 整數 等於 1。
當（計數 小於等於 5）就：
  顯示 計數。
  令 計數 等於 計數 加 1。
。完
""",

    "巢狀條件與循環": """
令 數字 為 整數 等於 1。
當（數字 小於等於 10）就：
  如果（數字 乘 數字 大於 50）則：
    顯示 「平方超過50」。
  。完否則：
    顯示 數字。
  。完
  令 數字 等於 數字 加 1。
。完
""",

    "FizzBuzz": """
令 數 為 整數 等於 1。
當（數 小於等於 15）就：
  如果（數 除 15 乘 15 等於 數）則：
    顯示 「三五」。
  。完否則：
    如果（數 除 3 乘 3 等於 數）則：
      顯示 「三」。
    。完否則：
      如果（數 除 5 乘 5 等於 數）則：
        顯示 「五」。
      。完否則：
        顯示 數。
      。完
    。完
  。完
  令 數 等於 數 加 1。
。完
""",

    "列表基本操作": """
# 宣告整數列表
令 數組 為 整數列表 等於 ［10，20，30，40，50］。
顯示 數組。

# 存取元素
顯示 數組［0］。
顯示 數組［2］。

# 修改元素
令 數組［1］ 等於 99。
顯示 數組。
""",

    "列表走訪與累加": """
令 成績 為 整數列表 等於 ［85，92，78，96，88］。
令 總分 為 整數 等於 0。
令 索引 為 整數 等於 0。
當（索引 小於等於 4）就：
  令 總分 等於 總分 加 成績［索引］。
  令 索引 等於 索引 加 1。
。完
顯示 「總分：」。
顯示 總分。
""",

    "字串列表": """
令 語言 為 字串列表 等於 ［「繁體中文」，「English」，「日本語」］。
顯示 語言［0］。
顯示 語言［1］。
令 語言［2］ 等於 「한국어」。
顯示 語言［2］。
""",
}


def run_all_demos():
    print("=" * 60)
    print("  繁體中文程式語言 — 完整功能示範")
    print("=" * 60)

    for title, src in DEMO_PROGRAMS.items():
        print(f"\n【{title}】")
        print("  程式碼：")
        for line in src.strip().split("\n"):
            print(f"    {line}")
        print("  輸出：")
        try:
            outputs = run_source(src.strip())
            for o in outputs:
                print(f"    {o}")
        except Exception as e:
            print(f"  ✗ {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        # 無參數：執行完整示範
        run_all_demos()
        print("\n" + "=" * 60)
        print("  輸入 python compiler_vm.py repl    → 互動模式")
        print("  輸入 python compiler_vm.py <檔案>  → 執行檔案")
        print("=" * 60)

    elif sys.argv[1] == "repl":
        repl()

    elif sys.argv[1] == "demo":
        name = sys.argv[2] if len(sys.argv) > 2 else list(DEMO_PROGRAMS)[0]
        src = DEMO_PROGRAMS.get(name, list(DEMO_PROGRAMS.values())[0])
        debug = "--debug" in sys.argv
        bc = "--bytecode" in sys.argv
        ast_ = "--ast" in sys.argv
        run_source(src.strip(), debug=debug, show_ast=ast_, show_bytecode=bc)

    else:
        # 當作檔案路徑
        debug = "--debug" in sys.argv
        bc = "--bytecode" in sys.argv
        ast_ = "--ast" in sys.argv
        run_file(sys.argv[1], debug=debug, show_ast=ast_, show_bytecode=bc)