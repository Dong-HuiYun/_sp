"""
繁體中文程式語言 v3 - Lexer + Parser
====================================================================

EBNF 語法規則（完整版）
========================

程式         ::= { 頂層語句 }
頂層語句      ::= 函數定義 | 引入語句 | 語句
語句列表      ::= { 語句 }

函數定義      ::= 「定義」 識別字 「（」 [ 參數列表 ] 「）」 「為」 「：」 語句列表 「。完」
參數列表      ::= 識別字 { 「，」 識別字 }
引入語句      ::= 「引入」 識別字 「。」

語句         ::= 宣告語句 | 賦值語句 | 索引賦值語句
               | 顯示語句 | 詢問語句
               | 判斷語句 | 當循環 | 從到循環
               | 回傳語句 | 跳出語句 | 繼續語句
               | 嘗試語句 | 表達式語句
               | 添加語句 | 彈出語句

宣告語句      ::= 「令」 識別字 「為」 類型 「等於」 表達式 「。」
賦值語句      ::= 「令」 識別字 「等於」 表達式 「。」
索引賦值語句  ::= 「令」 識別字 「［」 表達式 「］」 「等於」 表達式 「。」
顯示語句      ::= 「顯示」 表達式 「。」
詢問語句      ::= 「詢問」 字串字面值 「並存入」 識別字 「。」
回傳語句      ::= 「回傳」 表達式 「。」
跳出語句      ::= 「跳出」 「。」
繼續語句      ::= 「繼續」 「。」
添加語句      ::= 「添加」 表達式 「於」 識別字 「。」
彈出語句      ::= 「彈出」 識別字 「。」
              | 「彈出」 識別字 「並存入」 識別字 「。」

判斷語句      ::= 「如果」 「（」 條件 「）」 「則」 區塊 [ 「否則」 區塊 ]
當循環        ::= 「當」 「（」 條件 「）」 「就」 區塊
從到循環      ::= 「從」 表達式 「到」 表達式 「以」 識別字 「做」 區塊
嘗試語句      ::= 「嘗試」 「：」 語句列表 「。完」 「若出錯」 「：」 語句列表 「。完」

區塊         ::= 「：」 語句列表 「。完」

類型         ::= 「整數」 | 「字串」 | 「整數列表」 | 「字串列表」

表達式       ::= 加減表達式
加減表達式    ::= 乘除餘表達式 { ( 「加」|「減」 ) 乘除餘表達式 }
乘除餘表達式  ::= 次方表達式 { ( 「乘」|「除」|「餘」 ) 次方表達式 }
次方表達式    ::= 一元表達式 [ 「次方」 一元表達式 ]
一元表達式    ::= [ 「負」 ] 後綴表達式
後綴表達式    ::= 基本表達式 { 「［」 表達式 「］」 }
基本表達式    ::= 整數字面值 | 字串字面值 | 列表字面值
               | 識別字 [ 「（」 引數列表 「）」 ]
               | 內建函數呼叫
               | 「（」 表達式 「）」

內建函數呼叫  ::= 「長度」 「（」 表達式 「）」
引數列表      ::= [ 表達式 { 「，」 表達式 } ]

條件         ::= 比較 { ( 「且」|「或」 ) 比較 }
               | 「非」 「（」 條件 「）」
比較         ::= 表達式 [ 比較運算子 表達式 ]
比較運算子    ::= 「等於」|「不等於」|「大於」|「小於」|「大於等於」|「小於等於」
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Any


# ============================================================
# Token 類型
# ============================================================

class TokenType(Enum):
    # ── 關鍵字 ──────────────────────────────────────────────
    LING              = "令"
    WEI               = "為"
    DENGYU            = "等於"
    BUDENGYU          = "不等於"
    XIANSHI           = "顯示"
    XUNWEN            = "詢問"        # input
    BINGCUNRU         = "並存入"      # and store into
    RUGUO             = "如果"
    ZE                = "則"
    FOUZE             = "否則"
    DANG              = "當"
    JIU               = "就"
    CONG              = "從"          # for-from
    DAO               = "到"          # for-to
    YI                = "以"          # for-as
    ZUO               = "做"          # for-do
    DINGY             = "定義"        # def
    HUITAN            = "回傳"        # return
    TIAOCHU           = "跳出"        # break
    JIXU              = "繼續"        # continue
    YINRU             = "引入"        # import
    SHICHANG          = "嘗試"        # try
    RUOCHUCUO         = "若出錯"      # except
    TIANJIA           = "添加"        # append
    YU                = "於"          # to (for append)
    TANCHU            = "彈出"        # pop
    CHANGDU           = "長度"        # len()
    # 算術
    JIA               = "加"
    JIAN              = "減"
    CHENG             = "乘"
    CHU               = "除"
    YU_SHU            = "餘"          # modulo
    CIFANG            = "次方"        # power
    FU                = "負"
    # 邏輯
    QIE               = "且"
    HUO               = "或"
    FEI               = "非"
    # 比較
    DAYÜ              = "大於"
    XIAOYÜ            = "小於"
    DAYÜDENGYU        = "大於等於"
    XIAOYÜDENGYU      = "小於等於"
    # 類型
    ZHENSHU           = "整數"
    ZIFUCHUAN         = "字串"
    ZHENSHU_LIEBIAO   = "整數列表"
    ZIFUCHUAN_LIEBIAO = "字串列表"
    # 完
    WANBI             = "完"
    # ── 標點 ────────────────────────────────────────────────
    MAOHAO   = "："
    WANHAO   = "。"
    ZUOKUO   = "（"
    YOUKUO   = "）"
    FANG_ZUO = "［"
    FANG_YOU = "］"
    DOUHAO   = "，"
    # ── 字面值與識別字 ───────────────────────────────────────
    INT_LIT  = "整數字面值"
    STR_LIT  = "字串字面值"
    IDENT    = "識別字"
    EOF      = "EOF"


# ============================================================
# Token
# ============================================================

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line})"


# ============================================================
# 錯誤
# ============================================================

class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[詞法錯誤] 第{line}行 第{col}列：{msg}")

class ParseError(Exception):
    def __init__(self, msg, token: Token):
        super().__init__(
            f"[語法錯誤] 第{token.line}行 第{token.col}列：{msg}，"
            f"遇到了 {token.type.name}({token.value!r})")
        self.token = token


# ============================================================
# 關鍵字表（長優先）
# ============================================================

KEYWORDS = [
    ("大於等於",   TokenType.DAYÜDENGYU),
    ("小於等於",   TokenType.XIAOYÜDENGYU),
    ("不等於",     TokenType.BUDENGYU),
    ("整數列表",   TokenType.ZHENSHU_LIEBIAO),
    ("字串列表",   TokenType.ZIFUCHUAN_LIEBIAO),
    ("並存入",     TokenType.BINGCUNRU),
    ("若出錯",     TokenType.RUOCHUCUO),
    ("次方",       TokenType.CIFANG),
    ("長度",       TokenType.CHANGDU),
    ("顯示",       TokenType.XIANSHI),
    ("詢問",       TokenType.XUNWEN),
    ("如果",       TokenType.RUGUO),
    ("否則",       TokenType.FOUZE),
    ("定義",       TokenType.DINGY),
    ("回傳",       TokenType.HUITAN),
    ("跳出",       TokenType.TIAOCHU),
    ("繼續",       TokenType.JIXU),
    ("引入",       TokenType.YINRU),
    ("嘗試",       TokenType.SHICHANG),
    ("添加",       TokenType.TIANJIA),
    ("彈出",       TokenType.TANCHU),
    ("等於",       TokenType.DENGYU),
    ("整數",       TokenType.ZHENSHU),
    ("字串",       TokenType.ZIFUCHUAN),
    ("大於",       TokenType.DAYÜ),
    ("小於",       TokenType.XIAOYÜ),
    ("令",         TokenType.LING),
    ("為",         TokenType.WEI),
    ("則",         TokenType.ZE),
    ("當",         TokenType.DANG),
    ("就",         TokenType.JIU),
    ("從",         TokenType.CONG),
    ("到",         TokenType.DAO),
    ("以",         TokenType.YI),
    ("做",         TokenType.ZUO),
    ("加",         TokenType.JIA),
    ("減",         TokenType.JIAN),
    ("乘",         TokenType.CHENG),
    ("除",         TokenType.CHU),
    ("餘",         TokenType.YU_SHU),
    ("負",         TokenType.FU),
    ("且",         TokenType.QIE),
    ("或",         TokenType.HUO),
    ("非",         TokenType.FEI),
    ("於",         TokenType.YU),
    ("完",         TokenType.WANBI),
]

PUNCTUATION = {
    "：": TokenType.MAOHAO,
    "。": TokenType.WANHAO,
    "（": TokenType.ZUOKUO,
    "）": TokenType.YOUKUO,
    "［": TokenType.FANG_ZUO,
    "］": TokenType.FANG_YOU,
    "，": TokenType.DOUHAO,
    "[":  TokenType.FANG_ZUO,
    "]":  TokenType.FANG_YOU,
    ",":  TokenType.DOUHAO,
}


# ============================================================
# LEXER
# ============================================================

class Lexer:
    CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
    DIG = re.compile(r'[0-9]')

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def cur(self): return self.source[self.pos] if self.pos < len(self.source) else None
    def peek(self, n=1): p=self.pos+n; return self.source[p] if p<len(self.source) else None

    def advance(self, n=1):
        s = self.source[self.pos:self.pos+n]
        for c in s:
            if c == '\n': self.line += 1; self.col = 1
            else: self.col += 1
        self.pos += n
        return s

    def skip(self):
        while self.pos < len(self.source):
            c = self.cur()
            if c in ' \t\r\n\u3000': self.advance()
            elif c == '#':
                while self.pos < len(self.source) and self.cur() != '\n': self.advance()
            else: break

    def try_keyword(self):
        ln, col = self.line, self.col
        for kw, tt in KEYWORDS:
            e = self.pos + len(kw)
            if self.source[self.pos:e] == kw:
                after = self.source[e:e+1]
                if after and self.CJK.match(after) and tt != TokenType.WANBI:
                    continue
                self.advance(len(kw))
                return Token(tt, kw, ln, col)

    def try_punct(self):
        c = self.cur()
        if c and c in PUNCTUATION:
            ln, col = self.line, self.col
            self.advance()
            return Token(PUNCTUATION[c], c, ln, col)

    def try_string(self):
        if self.cur() != '「': return None
        ln, col = self.line, self.col
        self.advance()
        buf = []
        while self.pos < len(self.source):
            c = self.cur()
            if c == '」': self.advance(); return Token(TokenType.STR_LIT, ''.join(buf), ln, col)
            if c == '\n': raise LexerError("字串未結束", self.line, self.col)
            buf.append(c); self.advance()
        raise LexerError("字串未結束，缺少 」", ln, col)

    def try_int(self):
        c = self.cur()
        if not c or not self.DIG.match(c): return None
        ln, col = self.line, self.col
        buf = []
        while self.pos < len(self.source) and self.DIG.match(self.cur()):
            buf.append(self.cur()); self.advance()
        return Token(TokenType.INT_LIT, int(''.join(buf)), ln, col)

    def try_ident(self):
        c = self.cur()
        if not c or not self.CJK.match(c): return None
        ln, col = self.line, self.col
        buf = []
        while self.pos < len(self.source):
            c = self.cur()
            if self.CJK.match(c) or self.DIG.match(c): buf.append(c); self.advance()
            else: break
        return Token(TokenType.IDENT, ''.join(buf), ln, col)

    def tokenize(self):
        while True:
            self.skip()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, None, self.line, self.col)); break
            ln, col = self.line, self.col
            tok = self.try_keyword() or self.try_punct() or self.try_string() or self.try_int() or self.try_ident()
            if tok: self.tokens.append(tok)
            else: raise LexerError(f"無法識別：{self.cur()!r}", ln, col)
        return self.tokens


# ============================================================
# AST 節點
# ============================================================

@dataclass
class ASTNode: pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

# ── 語句 ──────────────────────────────────────────────────────
@dataclass
class DeclareStmt(ASTNode):
    name: str; type_annotation: str; expr: ASTNode; line: int

@dataclass
class AssignStmt(ASTNode):
    name: str; expr: ASTNode; line: int

@dataclass
class IndexAssignStmt(ASTNode):
    name: str; index: ASTNode; expr: ASTNode; line: int

@dataclass
class PrintStmt(ASTNode):
    expr: ASTNode; line: int

@dataclass
class AskStmt(ASTNode):
    """詢問 「提示」 並存入 變數。"""
    prompt: str; varname: str; line: int

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode; then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]]; line: int

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode; body: List[ASTNode]; line: int

@dataclass
class ForStmt(ASTNode):
    """從 start 到 end 以 varname 做：區塊"""
    start: ASTNode; end: ASTNode; varname: str; body: List[ASTNode]; line: int

@dataclass
class ReturnStmt(ASTNode):
    expr: ASTNode; line: int

@dataclass
class BreakStmt(ASTNode):
    line: int

@dataclass
class ContinueStmt(ASTNode):
    line: int

@dataclass
class AppendStmt(ASTNode):
    """添加 expr 於 listname。"""
    expr: ASTNode; listname: str; line: int

@dataclass
class PopStmt(ASTNode):
    """彈出 listname。 / 彈出 listname 並存入 varname。"""
    listname: str; varname: Optional[str]; line: int

@dataclass
class TryStmt(ASTNode):
    try_block: List[ASTNode]; except_block: List[ASTNode]; line: int

@dataclass
class FuncDefStmt(ASTNode):
    name: str; params: List[str]; body: List[ASTNode]; line: int

@dataclass
class ImportStmt(ASTNode):
    module: str; line: int

# ── 表達式 ────────────────────────────────────────────────────
@dataclass
class BinOp(ASTNode):
    op: str; left: ASTNode; right: ASTNode; line: int

@dataclass
class UnaryOp(ASTNode):
    op: str; operand: ASTNode; line: int

@dataclass
class IntLiteral(ASTNode):
    value: int; line: int

@dataclass
class StrLiteral(ASTNode):
    value: str; line: int

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode]; line: int

@dataclass
class IndexExpr(ASTNode):
    target: ASTNode; index: ASTNode; line: int

@dataclass
class Identifier(ASTNode):
    name: str; line: int

@dataclass
class CallExpr(ASTNode):
    """函數呼叫：識別字（引數, ...）"""
    name: str; args: List[ASTNode]; line: int

@dataclass
class BuiltinCall(ASTNode):
    """內建函數呼叫：長度（expr）"""
    func: str; args: List[ASTNode]; line: int


# ============================================================
# PARSER
# ============================================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.pos = 0

    def cur(self): return self.tokens[self.pos]
    def peek(self, n=1):
        p = self.pos+n
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]
    def advance(self):
        t = self.tokens[self.pos]
        if t.type != TokenType.EOF: self.pos += 1
        return t
    def expect(self, tt):
        t = self.cur()
        if t.type != tt: raise ParseError(f"預期 {tt.value!r}", t)
        return self.advance()
    def match(self, *types): return self.cur().type in types

    # ── 程式 ────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while not self.match(TokenType.EOF):
            if self.match(TokenType.DINGY):
                stmts.append(self.parse_funcdef())
            elif self.match(TokenType.YINRU):
                stmts.append(self.parse_import())
            else:
                stmts.append(self.parse_stmt())
        return Program(statements=stmts)

    def parse_stmt_list(self, in_block=False):
        stmts = []
        while True:
            t = self.cur()
            if t.type == TokenType.EOF: break
            if in_block:
                if t.type == TokenType.WANHAO and self.peek().type == TokenType.WANBI: break
                if t.type in (TokenType.FOUZE, TokenType.RUOCHUCUO): break
            stmts.append(self.parse_stmt())
        return stmts

    def parse_block(self):
        self.expect(TokenType.MAOHAO)
        stmts = self.parse_stmt_list(in_block=True)
        self.expect(TokenType.WANHAO)
        self.expect(TokenType.WANBI)
        return stmts

    # ── 函數定義 ─────────────────────────────────────────────

    def parse_funcdef(self):
        ln = self.cur().line
        self.expect(TokenType.DINGY)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ZUOKUO)
        params = []
        if not self.match(TokenType.YOUKUO):
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.DOUHAO):
                self.advance()
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.YOUKUO)
        self.expect(TokenType.WEI)
        body = self.parse_block()
        return FuncDefStmt(name=name, params=params, body=body, line=ln)

    def parse_import(self):
        ln = self.cur().line
        self.expect(TokenType.YINRU)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.WANHAO)
        return ImportStmt(module=name, line=ln)

    # ── 語句 ────────────────────────────────────────────────

    def parse_stmt(self):
        t = self.cur()
        if   t.type == TokenType.LING:     return self.parse_ling()
        elif t.type == TokenType.XIANSHI:  return self.parse_print()
        elif t.type == TokenType.XUNWEN:   return self.parse_ask()
        elif t.type == TokenType.RUGUO:    return self.parse_if()
        elif t.type == TokenType.DANG:     return self.parse_while()
        elif t.type == TokenType.CONG:     return self.parse_for()
        elif t.type == TokenType.HUITAN:   return self.parse_return()
        elif t.type == TokenType.TIAOCHU:  return self.parse_break()
        elif t.type == TokenType.JIXU:     return self.parse_continue()
        elif t.type == TokenType.TIANJIA:  return self.parse_append()
        elif t.type == TokenType.TANCHU:   return self.parse_pop()
        elif t.type == TokenType.SHICHANG: return self.parse_try()
        else: raise ParseError("預期語句開頭", t)

    def parse_ling(self):
        ln = self.cur().line
        self.expect(TokenType.LING)
        name = self.expect(TokenType.IDENT).value

        # 索引賦值：令 X［idx］ 等於 expr。
        if self.match(TokenType.FANG_ZUO):
            self.advance()
            idx = self.parse_expr()
            self.expect(TokenType.FANG_YOU)
            self.expect(TokenType.DENGYU)
            val = self.parse_expr()
            self.expect(TokenType.WANHAO)
            return IndexAssignStmt(name=name, index=idx, expr=val, line=ln)

        # 宣告：令 X 為 類型 等於 expr。
        if self.match(TokenType.WEI):
            self.advance()
            type_map = {
                TokenType.ZHENSHU:           'int',
                TokenType.ZIFUCHUAN:         'str',
                TokenType.ZHENSHU_LIEBIAO:   'int_list',
                TokenType.ZIFUCHUAN_LIEBIAO: 'str_list',
            }
            tt = self.cur()
            if tt.type not in type_map: raise ParseError("預期類型", tt)
            ann = type_map[tt.type]; self.advance()
            self.expect(TokenType.DENGYU)
            expr = self.parse_expr()
            self.expect(TokenType.WANHAO)
            return DeclareStmt(name=name, type_annotation=ann, expr=expr, line=ln)

        # 賦值：令 X 等於 expr。
        if self.match(TokenType.DENGYU):
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.WANHAO)
            return AssignStmt(name=name, expr=expr, line=ln)

        raise ParseError("「令」後預期「為」、「等於」或「［」", self.cur())

    def parse_print(self):
        ln = self.cur().line
        self.expect(TokenType.XIANSHI)
        expr = self.parse_expr()
        self.expect(TokenType.WANHAO)
        return PrintStmt(expr=expr, line=ln)

    def parse_ask(self):
        ln = self.cur().line
        self.expect(TokenType.XUNWEN)
        prompt_tok = self.expect(TokenType.STR_LIT)
        self.expect(TokenType.BINGCUNRU)
        varname = self.expect(TokenType.IDENT).value
        self.expect(TokenType.WANHAO)
        return AskStmt(prompt=prompt_tok.value, varname=varname, line=ln)

    def parse_if(self):
        ln = self.cur().line
        self.expect(TokenType.RUGUO)
        self.expect(TokenType.ZUOKUO)
        cond = self.parse_cond()
        self.expect(TokenType.YOUKUO)
        self.expect(TokenType.ZE)
        then = self.parse_if_block()
        else_ = None
        if self.match(TokenType.FOUZE):
            self.advance()
            else_ = self.parse_if_block()
        return IfStmt(condition=cond, then_block=then, else_block=else_, line=ln)

    def parse_if_block(self):
        self.expect(TokenType.MAOHAO)
        stmts = self.parse_stmt_list(in_block=True)
        self.expect(TokenType.WANHAO)
        self.expect(TokenType.WANBI)
        return stmts

    def parse_while(self):
        ln = self.cur().line
        self.expect(TokenType.DANG)
        self.expect(TokenType.ZUOKUO)
        cond = self.parse_cond()
        self.expect(TokenType.YOUKUO)
        self.expect(TokenType.JIU)
        body = self.parse_block()
        return WhileStmt(condition=cond, body=body, line=ln)

    def parse_for(self):
        """從 start 到 end 以 varname 做：區塊"""
        ln = self.cur().line
        self.expect(TokenType.CONG)
        start = self.parse_expr()
        self.expect(TokenType.DAO)
        end = self.parse_expr()
        self.expect(TokenType.YI)
        varname = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ZUO)
        body = self.parse_block()
        return ForStmt(start=start, end=end, varname=varname, body=body, line=ln)

    def parse_return(self):
        ln = self.cur().line
        self.expect(TokenType.HUITAN)
        expr = self.parse_expr()
        self.expect(TokenType.WANHAO)
        return ReturnStmt(expr=expr, line=ln)

    def parse_break(self):
        ln = self.cur().line
        self.expect(TokenType.TIAOCHU)
        self.expect(TokenType.WANHAO)
        return BreakStmt(line=ln)

    def parse_continue(self):
        ln = self.cur().line
        self.expect(TokenType.JIXU)
        self.expect(TokenType.WANHAO)
        return ContinueStmt(line=ln)

    def parse_append(self):
        """添加 expr 於 listname。"""
        ln = self.cur().line
        self.expect(TokenType.TIANJIA)
        expr = self.parse_expr()
        self.expect(TokenType.YU)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.WANHAO)
        return AppendStmt(expr=expr, listname=name, line=ln)

    def parse_pop(self):
        """彈出 listname。 / 彈出 listname 並存入 varname。"""
        ln = self.cur().line
        self.expect(TokenType.TANCHU)
        name = self.expect(TokenType.IDENT).value
        varname = None
        if self.match(TokenType.BINGCUNRU):
            self.advance()
            varname = self.expect(TokenType.IDENT).value
        self.expect(TokenType.WANHAO)
        return PopStmt(listname=name, varname=varname, line=ln)

    def parse_try(self):
        ln = self.cur().line
        self.expect(TokenType.SHICHANG)
        self.expect(TokenType.MAOHAO)
        try_stmts = self.parse_stmt_list(in_block=True)
        self.expect(TokenType.WANHAO)
        self.expect(TokenType.WANBI)
        self.expect(TokenType.RUOCHUCUO)
        self.expect(TokenType.MAOHAO)
        exc_stmts = self.parse_stmt_list(in_block=True)
        self.expect(TokenType.WANHAO)
        self.expect(TokenType.WANBI)
        return TryStmt(try_block=try_stmts, except_block=exc_stmts, line=ln)

    # ── 條件表達式 ───────────────────────────────────────────

    def parse_cond(self):
        if self.match(TokenType.FEI):
            ln = self.cur().line; self.advance()
            self.expect(TokenType.ZUOKUO)
            inner = self.parse_cond()
            self.expect(TokenType.YOUKUO)
            return UnaryOp(op='not', operand=inner, line=ln)
        left = self.parse_cmp()
        while self.match(TokenType.QIE, TokenType.HUO):
            op_tok = self.advance()
            op = '&&' if op_tok.type == TokenType.QIE else '||'
            right = self.parse_cmp()
            left = BinOp(op=op, left=left, right=right, line=op_tok.line)
        return left

    def parse_cmp(self):
        left = self.parse_expr()
        cmp = {
            TokenType.DENGYU: '==', TokenType.BUDENGYU: '!=',
            TokenType.DAYÜ: '>', TokenType.XIAOYÜ: '<',
            TokenType.DAYÜDENGYU: '>=', TokenType.XIAOYÜDENGYU: '<=',
        }
        if self.cur().type in cmp:
            op_tok = self.advance()
            right = self.parse_expr()
            return BinOp(op=cmp[op_tok.type], left=left, right=right, line=op_tok.line)
        return left

    # ── 算術表達式 ───────────────────────────────────────────

    def parse_expr(self): return self.parse_add_sub()

    def parse_add_sub(self):
        left = self.parse_mul_div()
        while self.match(TokenType.JIA, TokenType.JIAN):
            op = self.advance()
            right = self.parse_mul_div()
            left = BinOp(op='+' if op.type==TokenType.JIA else '-', left=left, right=right, line=op.line)
        return left

    def parse_mul_div(self):
        left = self.parse_power()
        while self.match(TokenType.CHENG, TokenType.CHU, TokenType.YU_SHU):
            op = self.advance()
            right = self.parse_power()
            sym = {'乘':'*','除':'/','餘':'%'}[op.value]
            left = BinOp(op=sym, left=left, right=right, line=op.line)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.match(TokenType.CIFANG):
            op = self.advance()
            right = self.parse_unary()
            return BinOp(op='**', left=left, right=right, line=op.line)
        return left

    def parse_unary(self):
        if self.match(TokenType.FU):
            ln = self.cur().line; self.advance()
            return UnaryOp(op='neg', operand=self.parse_postfix(), line=ln)
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while self.match(TokenType.FANG_ZUO):
            ln = self.cur().line; self.advance()
            idx = self.parse_expr()
            self.expect(TokenType.FANG_YOU)
            node = IndexExpr(target=node, index=idx, line=ln)
        return node

    def parse_primary(self):
        t = self.cur()
        if t.type == TokenType.INT_LIT:
            self.advance(); return IntLiteral(value=t.value, line=t.line)
        elif t.type == TokenType.STR_LIT:
            self.advance(); return StrLiteral(value=t.value, line=t.line)
        elif t.type == TokenType.FANG_ZUO:
            return self.parse_list_literal()
        elif t.type == TokenType.CHANGDU:
            # 長度（expr）
            ln = t.line; self.advance()
            self.expect(TokenType.ZUOKUO)
            arg = self.parse_expr()
            self.expect(TokenType.YOUKUO)
            return BuiltinCall(func='長度', args=[arg], line=ln)
        elif t.type == TokenType.IDENT:
            self.advance()
            # 函數呼叫：識別字（引數...）
            if self.match(TokenType.ZUOKUO):
                ln = t.line; self.advance()
                args = []
                if not self.match(TokenType.YOUKUO):
                    args.append(self.parse_expr())
                    while self.match(TokenType.DOUHAO):
                        self.advance(); args.append(self.parse_expr())
                self.expect(TokenType.YOUKUO)
                return CallExpr(name=t.value, args=args, line=ln)
            return Identifier(name=t.value, line=t.line)
        elif t.type == TokenType.ZUOKUO:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.YOUKUO)
            return expr
        else:
            raise ParseError("預期表達式", t)

    def parse_list_literal(self):
        ln = self.cur().line
        self.expect(TokenType.FANG_ZUO)
        elems = []
        if not self.match(TokenType.FANG_YOU):
            elems.append(self.parse_expr())
            while self.match(TokenType.DOUHAO):
                self.advance(); elems.append(self.parse_expr())
        self.expect(TokenType.FANG_YOU)
        return ListLiteral(elements=elems, line=ln)


# ============================================================
# AST 美化輸出
# ============================================================

def pretty_print_ast(node, indent=0):
    p = "  " * indent
    n = type(node).__name__
    if isinstance(node, Program):
        return p+"程式\n"+"\n".join(pretty_print_ast(s,indent+1) for s in node.statements)
    elif isinstance(node, FuncDefStmt):
        body = "\n".join(pretty_print_ast(s,indent+2) for s in node.body)
        return f"{p}函數定義[{node.name}({','.join(node.params)})]\n{body}"
    elif isinstance(node, (DeclareStmt,)):
        return f"{p}宣告[{node.name}:{node.type_annotation}]\n{pretty_print_ast(node.expr,indent+1)}"
    elif isinstance(node, AssignStmt):
        return f"{p}賦值[{node.name}]\n{pretty_print_ast(node.expr,indent+1)}"
    elif isinstance(node, PrintStmt):
        return f"{p}顯示\n{pretty_print_ast(node.expr,indent+1)}"
    elif isinstance(node, AskStmt):
        return f"{p}詢問[提示={node.prompt!r} → {node.varname}]"
    elif isinstance(node, ReturnStmt):
        return f"{p}回傳\n{pretty_print_ast(node.expr,indent+1)}"
    elif isinstance(node, BreakStmt):   return f"{p}跳出"
    elif isinstance(node, ContinueStmt):return f"{p}繼續"
    elif isinstance(node, AppendStmt):
        return f"{p}添加 → {node.listname}\n{pretty_print_ast(node.expr,indent+1)}"
    elif isinstance(node, PopStmt):
        return f"{p}彈出[{node.listname}{'→'+node.varname if node.varname else ''}]"
    elif isinstance(node, TryStmt):
        tb = "\n".join(pretty_print_ast(s,indent+2) for s in node.try_block)
        eb = "\n".join(pretty_print_ast(s,indent+2) for s in node.except_block)
        return f"{p}嘗試\n{tb}\n{p}  若出錯\n{eb}"
    elif isinstance(node, IntLiteral):  return f"{p}整數({node.value})"
    elif isinstance(node, StrLiteral):  return f"{p}字串({node.value!r})"
    elif isinstance(node, Identifier):  return f"{p}識別字({node.name})"
    elif isinstance(node, CallExpr):
        args = ", ".join(pretty_print_ast(a,0) for a in node.args)
        return f"{p}呼叫[{node.name}({args})]"
    elif isinstance(node, BuiltinCall):
        args = ", ".join(pretty_print_ast(a,0) for a in node.args)
        return f"{p}內建[{node.func}({args})]"
    elif isinstance(node, BinOp):
        return f"{p}二元({node.op})\n{pretty_print_ast(node.left,indent+1)}\n{pretty_print_ast(node.right,indent+1)}"
    elif isinstance(node, UnaryOp):
        return f"{p}一元({node.op})\n{pretty_print_ast(node.operand,indent+1)}"
    elif isinstance(node, ListLiteral):
        elems = "\n".join(f"{p}  [{i}]:{pretty_print_ast(e,0)}" for i,e in enumerate(node.elements))
        return f"{p}列表[{len(node.elements)}]\n{elems}"
    elif isinstance(node, IndexExpr):
        return f"{p}索引\n{pretty_print_ast(node.target,indent+1)}\n{pretty_print_ast(node.index,indent+1)}"
    elif isinstance(node, ForStmt):
        body = "\n".join(pretty_print_ast(s,indent+2) for s in node.body)
        return f"{p}從到[{node.varname}]\n{pretty_print_ast(node.start,indent+1)}\n{pretty_print_ast(node.end,indent+1)}\n{body}"
    else:
        return f"{p}{n}"