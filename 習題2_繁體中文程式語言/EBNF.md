### 繁體中文程式語言 EBNF 語法定義

#### 1. 程式與頂層結構 (Program & Top-level)
```ebnf
Program        ::= { TopLevelStmt }
TopLevelStmt   ::= FunctionDef | ImportStmt | Statement

FunctionDef    ::= "定義" Identifier "（" [ ParamList ] "）" "為" Block
ParamList      ::= Identifier { "，" Identifier }
ImportStmt     ::= "引入" Identifier "。"
```

#### 2. 語句 (Statements)
```ebnf
Statement      ::= DeclareStmt | AssignStmt | IndexAssignStmt 
                 | PrintStmt | AskStmt | IfStmt | WhileStmt | ForStmt 
                 | ReturnStmt | BreakStmt | ContinueStmt 
                 | AppendStmt | PopStmt | TryStmt

DeclareStmt     ::= "令" Identifier "為" Type "等於" Expression "。"
AssignStmt      ::= "令" Identifier "等於" Expression "。"
IndexAssignStmt ::= "令" Identifier "［" Expression "］" "等於" Expression "。"

PrintStmt       ::= "顯示" Expression "。"
AskStmt         ::= "詢問" StringLiteral "並存入" Identifier "。"

IfStmt          ::= "如果" "（" Condition "）" "則" Block [ "否則" Block ]
WhileStmt       ::= "當" "（" Condition "）" "就" Block
ForStmt         ::= "從" Expression "到" Expression "以" Identifier "做" Block

ReturnStmt      ::= "回傳" Expression "。"
BreakStmt       ::= "跳出" "。"
ContinueStmt    ::= "繼續" "。"

AppendStmt      ::= "添加" Expression "於" Identifier "。"
PopStmt         ::= "彈出" Identifier [ "並存入" Identifier ] "。"

TryStmt         ::= "嘗試" Block "若出錯" Block

Block           ::= "：" { Statement } "。完"
```

#### 3. 類型與字面值 (Types & Literals)
```ebnf
Type            ::= "整數" | "字串" | "整數列表" | "字串列表"
ListLiteral     ::= "［" [ Expression { "，" Expression } ] "］"
```

#### 4. 表達式與運算順序 (Expressions & Precedence)
```ebnf
Condition       ::= CompareExpr { ( "且" | "或" ) CompareExpr }
                  | "非" "（" Condition "）"

CompareExpr     ::= Expression [ CompareOp Expression ]
CompareOp       ::= "等於" | "不等於" | "大於" | "小於" | "大於等於" | "小於等於"

Expression      ::= AddSubExpr
AddSubExpr      ::= MulDivModExpr { ( "加" | "減" ) MulDivModExpr }
MulDivModExpr   ::= PowerExpr { ( "乘" | "除" | "餘" ) PowerExpr }
PowerExpr       ::= UnaryExpr [ "次方" UnaryExpr ]

UnaryExpr       ::= [ "負" ] PostfixExpr
PostfixExpr     ::= PrimaryExpr { "［" Expression "］" }

PrimaryExpr     ::= Identifier [ "（" [ ArgumentList ] "）" ]
                  | IntegerLiteral
                  | StringLiteral
                  | ListLiteral
                  | "長度" "（" Expression "）"
                  | "（" Expression "）"

ArgumentList    ::= Expression { "，" Expression }
```

#### 5. 詞法定義 (Lexical Tokens)
```ebnf
Identifier      ::= ChineseChar { ChineseChar | Digit }
IntegerLiteral  ::= Digit { Digit }
StringLiteral   ::= "「" { AnyCharacter } "」"
ChineseChar     ::= <任何中文字符 / CJK 統一表意文字>
Digit           ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```