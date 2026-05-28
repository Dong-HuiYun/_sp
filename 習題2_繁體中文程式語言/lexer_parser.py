"""
繁體中文程式語言 - Lexer (詞法分析器) 與 Parser (語法分析器)
============================================================

EBNF 語法規則
=============

程式         ::= 語句列表
語句列表      ::= 語句 { 語句 }
語句         ::= 宣告語句
               | 列表宣告語句
               | 賦值語句
               | 索引賦值語句
               | 顯示語句
               | 判斷語句
               | 循環語句

宣告語句      ::= 「令」 識別字 「為」 純量類型 「等於」 表達式 「。」
列表宣告語句  ::= 「令」 識別字 「為」 列表類型 「等於」 列表字面值 「。」
賦值語句      ::= 「令」 識別字 「等於」 表達式 「。」
索引賦值語句  ::= 「令」 識別字 「［」 表達式 「］」 「等於」 表達式 「。」
顯示語句      ::= 「顯示」 表達式 「。」
判斷語句      ::= 「如果」 「（」 條件表達式 「）」 「則」 區塊
                  [ 「否則」 區塊 ]
循環語句      ::= 「當」 「（」 條件表達式 「）」 「就」 區塊

區塊         ::= 「：」 語句列表 「。完」
               | 「：」 語句 （隱含單一語句區塊）

純量類型      ::= 「整數」 | 「字串」
列表類型      ::= 「整數列表」 | 「字串列表」

列表字面值    ::= 「［」 [ 表達式 { 「，」 表達式 } ] 「］」

表達式       ::= 加減表達式
加減表達式    ::= 乘除表達式 { ( 「加」 | 「減」 ) 乘除表達式 }
乘除表達式    ::= 一元表達式 { ( 「乘」 | 「除」 ) 一元表達式 }
一元表達式    ::= [ 「負」 ] 後綴表達式
後綴表達式    ::= 基本表達式 { 「［」 表達式 「］」 }
基本表達式    ::= 整數字面值
               | 字串字面值
               | 列表字面值
               | 識別字
               | 「（」 表達式 「）」

條件表達式    ::= 表達式 比較運算子 表達式
               | 表達式 「且」 表達式
               | 表達式 「或」 表達式
               | 「非」 「（」 條件表達式 「）」

比較運算子    ::= 「等於」 | 「不等於」 | 「大於」 | 「小於」
               | 「大於等於」 | 「小於等於」

識別字        ::= 中文字 { 中文字 | 數字 }
整數字面值    ::= 數字 { 數字 }
字串字面值    ::= 「「」 { 任意字元 } 「」」
列表字面值    ::= 「［」 [ 表達式 { 「，」 表達式 } ] 「］」

"""

import re
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Any


# ============================================================
# Token 類型定義
# ============================================================

class TokenType(Enum):
    # 關鍵字
    LING            = "令"       # 變數宣告/賦值
    WEI             = "為"       # 類型指定
    DENGYU          = "等於"     # 等於（賦值與比較）
    BUDENGYU        = "不等於"   # 不等於
    XIANSHI         = "顯示"     # 輸出
    RUGUO           = "如果"     # if
    ZE              = "則"       # then
    FOUZE           = "否則"     # else
    DANG            = "當"       # while
    JIU             = "就"       # do
    JIA             = "加"       # +
    JIAN            = "減"       # -
    CHENG           = "乘"       # *
    CHU             = "除"       # /
    FU              = "負"       # unary minus
    QIE             = "且"       # and
    HUO             = "或"       # or
    FEI             = "非"       # not
    DAYÜ            = "大於"     # >
    XIAOYÜ          = "小於"     # <
    DAYÜDENGYU      = "大於等於" # >=
    XIAOYÜDENGYU    = "小於等於" # <=
    ZHENSHU         = "整數"     # int type
    ZIFUCHUAN       = "字串"     # string type
    ZHENSHU_LIEBIAO = "整數列表" # int list type
    ZIFUCHUAN_LIEBIAO = "字串列表" # string list type

    # 標點符號
    MAOHAO      = "："       # colon (block start)
    WANHAO      = "。"       # period (statement end)
    WANBI       = "完"       # end of block marker (。完)
    ZUOKUO      = "（"       # left paren
    YOUKUO      = "）"       # right paren
    FANG_ZUO    = "［"       # left bracket  ［
    FANG_YOU    = "］"       # right bracket ］
    DOUHAO     = "，"        # comma         ，

    # 字面值與識別字
    INT_LIT     = "整數字面值"
    STR_LIT     = "字串字面值"
    IDENT       = "識別字"

    # 特殊
    EOF         = "EOF"
    NEWLINE     = "換行"


# ============================================================
# Token 資料結構
# ============================================================

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.col})"


# ============================================================
# 詞法分析錯誤
# ============================================================

class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[詞法錯誤] 第{line}行 第{col}列：{msg}")
        self.line = line
        self.col = col


# ============================================================
# LEXER 詞法分析器
# ============================================================

# 關鍵字對照表（順序很重要，長的優先匹配）
KEYWORDS = [
    ("大於等於",   TokenType.DAYÜDENGYU),
    ("小於等於",   TokenType.XIAOYÜDENGYU),
    ("不等於",     TokenType.BUDENGYU),
    ("整數列表",   TokenType.ZHENSHU_LIEBIAO),   # 必須在「整數」前面
    ("字串列表",   TokenType.ZIFUCHUAN_LIEBIAO), # 必須在「字串」前面
    ("顯示",       TokenType.XIANSHI),
    ("如果",       TokenType.RUGUO),
    ("否則",       TokenType.FOUZE),
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
    ("加",         TokenType.JIA),
    ("減",         TokenType.JIAN),
    ("乘",         TokenType.CHENG),
    ("除",         TokenType.CHU),
    ("負",         TokenType.FU),
    ("且",         TokenType.QIE),
    ("或",         TokenType.HUO),
    ("非",         TokenType.FEI),
    ("完",         TokenType.WANBI),
]

PUNCTUATION = {
    "：": TokenType.MAOHAO,
    "。": TokenType.WANHAO,
    "（": TokenType.ZUOKUO,
    "）": TokenType.YOUKUO,
    "［": TokenType.FANG_ZUO,   # 全形左中括號
    "］": TokenType.FANG_YOU,   # 全形右中括號
    "，": TokenType.DOUHAO,     # 全形逗號
    # 也支援半形方括號與逗號，方便鍵盤輸入
    "[":  TokenType.FANG_ZUO,
    "]":  TokenType.FANG_YOU,
    ",":  TokenType.DOUHAO,
}


class Lexer:
    """
    詞法分析器：將原始碼字串轉換為 Token 串列。

    掃描策略：
    1. 跳過空白與注釋（# 開頭到行尾）
    2. 嘗試匹配關鍵字（長優先）
    3. 嘗試匹配標點符號
    4. 嘗試匹配字串字面值（「...」）
    5. 嘗試匹配整數字面值
    6. 嘗試匹配識別字（中文字符）
    7. 其他字元報錯
    """

    # 中文字元 Unicode 範圍（CJK 統一表意文字）
    # 排除數字與ASCII，識別字只能由中文組成
    CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df]')
    DIGIT_PATTERN = re.compile(r'[0-9]')

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek(self, offset: int = 1) -> Optional[str]:
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return None

    def advance(self, n: int = 1) -> str:
        chars = self.source[self.pos:self.pos + n]
        for ch in chars:
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        self.pos += n
        return chars

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.current_char()
            if ch in (' ', '\t', '\r', '\n', '\u3000'):  # \u3000 = 全形空格
                self.advance()
            elif ch == '#':
                # 單行注釋
                while self.pos < len(self.source) and self.current_char() != '\n':
                    self.advance()
            else:
                break

    def try_match_keyword(self) -> Optional[Token]:
        """嘗試在目前位置匹配關鍵字（長優先）"""
        line, col = self.line, self.col
        for kw, tt in KEYWORDS:
            end = self.pos + len(kw)
            if self.source[self.pos:end] == kw:
                # 確認不是更長識別字的一部分（後面不能緊跟中文）
                after = self.source[end:end+1]
                if after and self.CJK_PATTERN.match(after):
                    # 若後面還有中文，則這不是獨立關鍵字
                    # 特例：「完」不需要後面沒中文（因為通常前面有「。」）
                    if tt != TokenType.WANBI:
                        continue
                self.advance(len(kw))
                return Token(tt, kw, line, col)
        return None

    def try_match_punctuation(self) -> Optional[Token]:
        ch = self.current_char()
        if ch and ch in PUNCTUATION:
            line, col = self.line, self.col
            self.advance()
            return Token(PUNCTUATION[ch], ch, line, col)
        return None

    def try_match_string_literal(self) -> Optional[Token]:
        """匹配字串字面值：「...」（使用全形書名號）"""
        ch = self.current_char()
        if ch != '「':
            return None
        line, col = self.line, self.col
        self.advance()  # 跳過 「
        buf = []
        while self.pos < len(self.source):
            c = self.current_char()
            if c == '」':
                self.advance()  # 跳過 」
                return Token(TokenType.STR_LIT, ''.join(buf), line, col)
            elif c == '\n':
                raise LexerError("字串字面值中不允許換行", self.line, self.col)
            else:
                buf.append(c)
                self.advance()
        raise LexerError("字串字面值未結束，缺少 」", line, col)

    def try_match_integer(self) -> Optional[Token]:
        ch = self.current_char()
        if not ch or not self.DIGIT_PATTERN.match(ch):
            return None
        line, col = self.line, self.col
        buf = []
        while self.pos < len(self.source) and self.DIGIT_PATTERN.match(self.current_char()):
            buf.append(self.current_char())
            self.advance()
        return Token(TokenType.INT_LIT, int(''.join(buf)), line, col)

    def try_match_identifier(self) -> Optional[Token]:
        ch = self.current_char()
        if not ch or not self.CJK_PATTERN.match(ch):
            return None
        line, col = self.line, self.col
        buf = []
        while self.pos < len(self.source):
            c = self.current_char()
            if self.CJK_PATTERN.match(c) or self.DIGIT_PATTERN.match(c):
                buf.append(c)
                self.advance()
            else:
                break
        name = ''.join(buf)
        return Token(TokenType.IDENT, name, line, col)

    def tokenize(self) -> List[Token]:
        """主掃描迴圈，回傳完整 Token 串列"""
        while True:
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
                break

            line, col = self.line, self.col
            tok = (
                self.try_match_keyword()       or
                self.try_match_punctuation()   or
                self.try_match_string_literal()or
                self.try_match_integer()       or
                self.try_match_identifier()
            )
            if tok:
                self.tokens.append(tok)
            else:
                ch = self.current_char()
                raise LexerError(f"無法識別的字元：{ch!r}", line, col)

        return self.tokens


# ============================================================
# AST 節點定義
# ============================================================

@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    """程式根節點"""
    statements: List[ASTNode]


@dataclass
class DeclareStmt(ASTNode):
    """
    宣告語句：令 <名稱> 為 <類型> 等於 <表達式>
    type_annotation: 'int' | 'str' | 'int_list' | 'str_list'
    """
    name: str
    type_annotation: str
    expr: ASTNode
    line: int


@dataclass
class AssignStmt(ASTNode):
    """
    賦值語句：令 <名稱> 等於 <表達式>
    """
    name: str
    expr: ASTNode
    line: int


@dataclass
class IndexAssignStmt(ASTNode):
    """
    索引賦值語句：令 <名稱>［<索引>］ 等於 <表達式>
    例：令 數組［1］ 等於 50。
    """
    name: str
    index: ASTNode
    expr: ASTNode
    line: int


@dataclass
class PrintStmt(ASTNode):
    """顯示語句：顯示 <表達式>"""
    expr: ASTNode
    line: int


@dataclass
class IfStmt(ASTNode):
    """
    判斷語句：如果（條件）則：區塊。完  [否則：區塊。完]
    """
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]]
    line: int


@dataclass
class WhileStmt(ASTNode):
    """
    循環語句：當（條件）就：區塊。完
    """
    condition: ASTNode
    body: List[ASTNode]
    line: int


@dataclass
class BinOp(ASTNode):
    """二元運算：left op right"""
    op: str      # '+', '-', '*', '/', '==', '!=', '>', '<', '>=', '<=', '&&', '||'
    left: ASTNode
    right: ASTNode
    line: int


@dataclass
class UnaryOp(ASTNode):
    """一元運算：op expr"""
    op: str      # 'neg', 'not'
    operand: ASTNode
    line: int


@dataclass
class IntLiteral(ASTNode):
    value: int
    line: int


@dataclass
class StrLiteral(ASTNode):
    value: str
    line: int


@dataclass
class ListLiteral(ASTNode):
    """
    列表字面值：［expr, expr, ...］
    elements: 元素表達式串列
    """
    elements: List[ASTNode]
    line: int


@dataclass
class IndexExpr(ASTNode):
    """
    索引存取表達式：expr［index_expr］
    例：數組［0］ 或 數組［索引 加 1］
    """
    target: ASTNode   # 被索引的物件（通常是 Identifier）
    index: ASTNode    # 索引表達式
    line: int


@dataclass
class Identifier(ASTNode):
    name: str
    line: int


# ============================================================
# 語法分析錯誤
# ============================================================

class ParseError(Exception):
    def __init__(self, msg, token: Token):
        super().__init__(
            f"[語法錯誤] 第{token.line}行 第{token.col}列：{msg}，"
            f"遇到了 {token.type.name}({token.value!r})"
        )
        self.token = token


# ============================================================
# PARSER 語法分析器（遞迴下降）
# ============================================================

class Parser:
    """
    語法分析器：將 Token 串列轉換為 AST。

    使用遞迴下降（Recursive Descent）策略，
    每個文法規則對應一個 parse_* 方法。
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── 輔助方法 ──────────────────────────────────────────

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]  # EOF

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def expect(self, tt: TokenType) -> Token:
        tok = self.current()
        if tok.type != tt:
            raise ParseError(f"預期 {tt.value!r}", tok)
        return self.advance()

    def match(self, *types: TokenType) -> bool:
        return self.current().type in types

    # ── 程式入口 ──────────────────────────────────────────

    def parse(self) -> Program:
        stmts = self.parse_statement_list()
        self.expect(TokenType.EOF)
        return Program(statements=stmts)

    def parse_statement_list(self, in_block: bool = False) -> List[ASTNode]:
        """
        語句列表 ::= 語句 { 語句 }
        in_block=True：遇到「。完」或「否則」時停止（供區塊內部使用）
        in_block=False：遇到 EOF 停止（頂層使用）
        """
        stmts = []
        while True:
            tok = self.current()
            if tok.type == TokenType.EOF:
                break
            if in_block:
                # 「。完」是區塊結束標記，停止收集語句
                if tok.type == TokenType.WANHAO and self.peek().type == TokenType.WANBI:
                    break
                # 「否則」表示 then 區塊結束，交給上層 parse_if 處理
                if tok.type == TokenType.FOUZE:
                    break
            stmts.append(self.parse_statement())
        return stmts

    # ── 語句解析 ──────────────────────────────────────────

    def parse_statement(self) -> ASTNode:
        """
        語句 ::= 宣告語句 | 賦值語句 | 索引賦值語句 | 顯示語句 | 判斷語句 | 循環語句
        """
        tok = self.current()

        if tok.type == TokenType.LING:
            return self.parse_declare_or_assign()
        elif tok.type == TokenType.XIANSHI:
            return self.parse_print()
        elif tok.type == TokenType.RUGUO:
            return self.parse_if()
        elif tok.type == TokenType.DANG:
            return self.parse_while()
        else:
            raise ParseError("預期語句開頭（令、顯示、如果、當）", tok)

    def parse_declare_or_assign(self) -> ASTNode:
        """
        宣告語句 ::= 「令」 識別字 「為」 類型 「等於」 表達式 「。」
        賦值語句 ::= 「令」 識別字 「等於」 表達式 「。」
        索引賦值 ::= 「令」 識別字 「［」 表達式 「］」 「等於」 表達式 「。」

        向前看第2、3個 Token 來區分：
          令 X 為 ...       → 宣告（純量 或 列表）
          令 X 等於 ...     → 賦值
          令 X ［ ...       → 索引賦值
        """
        line = self.current().line
        self.expect(TokenType.LING)
        name_tok = self.expect(TokenType.IDENT)
        name = name_tok.value

        # ── 索引賦值：令 X［expr］ 等於 expr。 ──────────────
        if self.match(TokenType.FANG_ZUO):
            self.advance()                      # 吃掉「［」
            index_expr = self.parse_expression()
            self.expect(TokenType.FANG_YOU)     # 「］」
            self.expect(TokenType.DENGYU)       # 「等於」
            val_expr = self.parse_expression()
            self.expect(TokenType.WANHAO)
            return IndexAssignStmt(name=name, index=index_expr, expr=val_expr, line=line)

        # ── 宣告：令 X 為 類型 等於 expr。 ─────────────────
        if self.match(TokenType.WEI):
            self.advance()  # 吃掉「為」
            type_tok = self.current()
            type_ann_map = {
                TokenType.ZHENSHU:           'int',
                TokenType.ZIFUCHUAN:         'str',
                TokenType.ZHENSHU_LIEBIAO:   'int_list',
                TokenType.ZIFUCHUAN_LIEBIAO: 'str_list',
            }
            if type_tok.type not in type_ann_map:
                raise ParseError("預期類型（整數、字串、整數列表、字串列表）", type_tok)
            type_ann = type_ann_map[type_tok.type]
            self.advance()
            self.expect(TokenType.DENGYU)
            expr = self.parse_expression()
            self.expect(TokenType.WANHAO)
            return DeclareStmt(name=name, type_annotation=type_ann, expr=expr, line=line)

        # ── 賦值：令 X 等於 expr。 ─────────────────────────
        if self.match(TokenType.DENGYU):
            self.advance()  # 吃掉「等於」
            expr = self.parse_expression()
            self.expect(TokenType.WANHAO)
            return AssignStmt(name=name, expr=expr, line=line)

        raise ParseError("「令」之後預期「為」（宣告）、「等於」（賦值）或「［」（索引賦值）",
                         self.current())

    def parse_print(self) -> PrintStmt:
        """顯示語句 ::= 「顯示」 表達式 「。」"""
        line = self.current().line
        self.expect(TokenType.XIANSHI)
        expr = self.parse_expression()
        self.expect(TokenType.WANHAO)
        return PrintStmt(expr=expr, line=line)

    def parse_if(self) -> IfStmt:
        """
        判斷語句 ::= 「如果」 「（」 條件表達式 「）」 「則」
                      「：」 語句列表 「。」 「完」
                     [ 「否則」 「：」 語句列表 「。」 「完」 ]

        注意：如果後面有「否則」，then 區塊的 「。完」後面緊接 「否則」；
              如果沒有「否則」，則整個 if 語句結束於 「。完」。
        """
        line = self.current().line
        self.expect(TokenType.RUGUO)
        self.expect(TokenType.ZUOKUO)
        cond = self.parse_condition()
        self.expect(TokenType.YOUKUO)
        self.expect(TokenType.ZE)
        # 解析 then 區塊（：語句列表。完）
        then_block = self.parse_if_block()

        else_block = None
        if self.match(TokenType.FOUZE):
            self.advance()  # 吃掉「否則」
            else_block = self.parse_if_block()

        return IfStmt(condition=cond, then_block=then_block, else_block=else_block, line=line)

    def parse_if_block(self) -> List[ASTNode]:
        """
        解析區塊（：語句列表。完）
        利用 in_block=True，自動在「。完」或「否則」前停止
        """
        self.expect(TokenType.MAOHAO)
        stmts = self.parse_statement_list(in_block=True)
        self.expect(TokenType.WANHAO)   # 「。」
        self.expect(TokenType.WANBI)    # 「完」
        return stmts

    def parse_while(self) -> WhileStmt:
        """
        循環語句 ::= 「當」 「（」 條件表達式 「）」 「就」
                      「：」 語句列表 「。」 「完」
        """
        line = self.current().line
        self.expect(TokenType.DANG)
        self.expect(TokenType.ZUOKUO)
        cond = self.parse_condition()
        self.expect(TokenType.YOUKUO)
        self.expect(TokenType.JIU)
        body = self.parse_block()
        return WhileStmt(condition=cond, body=body, line=line)

    def parse_block(self) -> List[ASTNode]:
        """
        區塊 ::= 「：」 語句列表 「。」 「完」
        """
        self.expect(TokenType.MAOHAO)
        stmts = self.parse_statement_list(in_block=True)
        self.expect(TokenType.WANHAO)   # 「。」
        self.expect(TokenType.WANBI)    # 「完」
        return stmts

    # ── 條件表達式 ────────────────────────────────────────

    def parse_condition(self) -> ASTNode:
        """
        條件表達式 ::= 比較表達式 { (「且」|「或」) 比較表達式 }
                     | 「非」 「（」 條件表達式 「）」
        """
        if self.match(TokenType.FEI):
            line = self.current().line
            self.advance()
            self.expect(TokenType.ZUOKUO)
            inner = self.parse_condition()
            self.expect(TokenType.YOUKUO)
            return UnaryOp(op='not', operand=inner, line=line)

        left = self.parse_comparison()

        while self.match(TokenType.QIE, TokenType.HUO):
            op_tok = self.advance()
            op = '&&' if op_tok.type == TokenType.QIE else '||'
            right = self.parse_comparison()
            left = BinOp(op=op, left=left, right=right, line=op_tok.line)

        return left

    def parse_comparison(self) -> ASTNode:
        """
        比較表達式 ::= 表達式 [ 比較運算子 表達式 ]
        比較運算子 ::= 「等於」|「不等於」|「大於」|「小於」|「大於等於」|「小於等於」
        """
        left = self.parse_expression()

        cmp_map = {
            TokenType.DENGYU:       '==',
            TokenType.BUDENGYU:     '!=',
            TokenType.DAYÜ:         '>',
            TokenType.XIAOYÜ:       '<',
            TokenType.DAYÜDENGYU:   '>=',
            TokenType.XIAOYÜDENGYU: '<=',
        }

        if self.current().type in cmp_map:
            op_tok = self.advance()
            op = cmp_map[op_tok.type]
            right = self.parse_expression()
            return BinOp(op=op, left=left, right=right, line=op_tok.line)

        return left

    # ── 算術表達式 ────────────────────────────────────────

    def parse_expression(self) -> ASTNode:
        """表達式 ::= 加減表達式"""
        return self.parse_add_sub()

    def parse_add_sub(self) -> ASTNode:
        """加減表達式 ::= 乘除表達式 { (「加」|「減」) 乘除表達式 }"""
        left = self.parse_mul_div()
        while self.match(TokenType.JIA, TokenType.JIAN):
            op_tok = self.advance()
            op = '+' if op_tok.type == TokenType.JIA else '-'
            right = self.parse_mul_div()
            left = BinOp(op=op, left=left, right=right, line=op_tok.line)
        return left

    def parse_mul_div(self) -> ASTNode:
        """乘除表達式 ::= 一元表達式 { (「乘」|「除」) 一元表達式 }"""
        left = self.parse_unary()
        while self.match(TokenType.CHENG, TokenType.CHU):
            op_tok = self.advance()
            op = '*' if op_tok.type == TokenType.CHENG else '/'
            right = self.parse_unary()
            left = BinOp(op=op, left=left, right=right, line=op_tok.line)
        return left

    def parse_unary(self) -> ASTNode:
        """一元表達式 ::= [ 「負」 ] 後綴表達式"""
        if self.match(TokenType.FU):
            line = self.current().line
            self.advance()
            operand = self.parse_postfix()
            return UnaryOp(op='neg', operand=operand, line=line)
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        """
        後綴表達式 ::= 基本表達式 { 「［」 表達式 「］」 }
        支援鏈式索引：數組［0］［1］ 等
        """
        node = self.parse_primary()
        while self.match(TokenType.FANG_ZUO):
            line = self.current().line
            self.advance()               # 吃掉「［」
            index = self.parse_expression()
            self.expect(TokenType.FANG_YOU)  # 「］」
            node = IndexExpr(target=node, index=index, line=line)
        return node

    def parse_primary(self) -> ASTNode:
        """
        基本表達式 ::= 整數字面值
                     | 字串字面值
                     | 列表字面值
                     | 識別字
                     | 「（」 表達式 「）」
        """
        tok = self.current()

        if tok.type == TokenType.INT_LIT:
            self.advance()
            return IntLiteral(value=tok.value, line=tok.line)

        elif tok.type == TokenType.STR_LIT:
            self.advance()
            return StrLiteral(value=tok.value, line=tok.line)

        elif tok.type == TokenType.FANG_ZUO:
            # 列表字面值：［ expr，expr，... ］
            return self.parse_list_literal()

        elif tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(name=tok.value, line=tok.line)

        elif tok.type == TokenType.ZUOKUO:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.YOUKUO)
            return expr

        else:
            raise ParseError("預期表達式（數字、字串、列表、識別字 或 括號）", tok)

    def parse_list_literal(self) -> ListLiteral:
        """
        列表字面值 ::= 「［」 [ 表達式 { 「，」 表達式 } ] 「］」
        """
        line = self.current().line
        self.expect(TokenType.FANG_ZUO)  # 「［」
        elements = []
        if not self.match(TokenType.FANG_YOU):
            elements.append(self.parse_expression())
            while self.match(TokenType.DOUHAO):
                self.advance()           # 吃掉「，」
                elements.append(self.parse_expression())
        self.expect(TokenType.FANG_YOU)  # 「］」
        return ListLiteral(elements=elements, line=line)


# ============================================================
# AST 美化輸出
# ============================================================

def pretty_print_ast(node: ASTNode, indent: int = 0) -> str:
    prefix = "  " * indent
    if isinstance(node, Program):
        lines = [f"{prefix}程式"]
        for s in node.statements:
            lines.append(pretty_print_ast(s, indent + 1))
        return "\n".join(lines)
    elif isinstance(node, DeclareStmt):
        return (f"{prefix}宣告 [{node.name} : {node.type_annotation}]\n"
                + pretty_print_ast(node.expr, indent + 1))
    elif isinstance(node, AssignStmt):
        return (f"{prefix}賦值 [{node.name}]\n"
                + pretty_print_ast(node.expr, indent + 1))
    elif isinstance(node, IndexAssignStmt):
        return (f"{prefix}索引賦值 [{node.name}]\n"
                + f"{prefix}  索引：\n" + pretty_print_ast(node.index, indent + 2) + "\n"
                + f"{prefix}  值：\n"   + pretty_print_ast(node.expr,  indent + 2))
    elif isinstance(node, PrintStmt):
        return f"{prefix}顯示\n" + pretty_print_ast(node.expr, indent + 1)
    elif isinstance(node, IfStmt):
        lines = [f"{prefix}如果"]
        lines.append(f"{prefix}  條件：")
        lines.append(pretty_print_ast(node.condition, indent + 2))
        lines.append(f"{prefix}  則：")
        for s in node.then_block:
            lines.append(pretty_print_ast(s, indent + 2))
        if node.else_block:
            lines.append(f"{prefix}  否則：")
            for s in node.else_block:
                lines.append(pretty_print_ast(s, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, WhileStmt):
        lines = [f"{prefix}當"]
        lines.append(f"{prefix}  條件：")
        lines.append(pretty_print_ast(node.condition, indent + 2))
        lines.append(f"{prefix}  就：")
        for s in node.body:
            lines.append(pretty_print_ast(s, indent + 2))
        return "\n".join(lines)
    elif isinstance(node, BinOp):
        return (f"{prefix}二元運算({node.op})\n"
                + pretty_print_ast(node.left, indent + 1) + "\n"
                + pretty_print_ast(node.right, indent + 1))
    elif isinstance(node, UnaryOp):
        return (f"{prefix}一元運算({node.op})\n"
                + pretty_print_ast(node.operand, indent + 1))
    elif isinstance(node, IntLiteral):
        return f"{prefix}整數({node.value})"
    elif isinstance(node, StrLiteral):
        return f"{prefix}字串({node.value!r})"
    elif isinstance(node, ListLiteral):
        lines = [f"{prefix}列表[{len(node.elements)}個元素]"]
        for i, el in enumerate(node.elements):
            lines.append(f"{prefix}  [{i}]: " + pretty_print_ast(el, 0))
        return "\n".join(lines)
    elif isinstance(node, IndexExpr):
        return (f"{prefix}索引存取\n"
                + f"{prefix}  物件：\n" + pretty_print_ast(node.target, indent + 2) + "\n"
                + f"{prefix}  索引：\n" + pretty_print_ast(node.index,  indent + 2))
    elif isinstance(node, Identifier):
        return f"{prefix}識別字({node.name})"
    else:
        return f"{prefix}未知節點({type(node).__name__})"


# ============================================================
# 測試入口
# ============================================================

SAMPLE_CODE = """
# 繁體中文程式語言 — 範例程式

# 變數宣告
令 計數 為 整數 等於 1。
令 訊息 為 字串 等於 「哈囉，世界」。

# 顯示字串
顯示 訊息。

# 算術運算
令 結果 為 整數 等於 計數 加 5 乘 2。
顯示 結果。

# 條件判斷（如果/否則，各自有獨立的 。完）
如果（結果 大於 10）則：
  顯示 「結果大於十」。
。完否則：
  顯示 「結果不超過十」。
。完

# 循環
當（計數 小於等於 3）就：
  顯示 計數。
  令 計數 等於 計數 加 1。
。完
"""


def run_demo(source: str = SAMPLE_CODE):
    print("=" * 60)
    print("【繁體中文程式語言】詞法 + 語法分析示範")
    print("=" * 60)

    print("\n── 原始碼 ──────────────────────────────────")
    print(source.strip())

    # 詞法分析
    print("\n── Token 串列 ──────────────────────────────")
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    for tok in tokens:
        if tok.type != TokenType.EOF:
            print(f"  {tok}")

    # 語法分析
    print("\n── 抽象語法樹 (AST) ────────────────────────")
    parser = Parser(tokens)
    ast = parser.parse()
    print(pretty_print_ast(ast))
    print("\n分析完成！✓")
    return ast


if __name__ == "__main__":
    run_demo()