program    = { statement } ;

statement  = var_decl | assign_stmt | if_stmt | while_stmt | print_stmt ;

var_decl   = "令" identifier "=" expression ;

assign_stmt = identifier "=" expression ;

if_stmt    = "如果" expression "{" { statement } "}" [ "否則" "{" { statement } "}" ] ;

while_stmt = "當" expression "就" "{" { statement } "}" ;

print_stmt = "顯示" expression ;

expression = logic_expr ;

logic_expr = arithmetic { ("等於" | "大於" | "小於") arithmetic } ;

arithmetic = term { ("加" | "減") term } ;

term       = factor { ("乘" | "除") factor } ;

factor     = NUMBER | STRING | identifier | "(" expression ")" ;