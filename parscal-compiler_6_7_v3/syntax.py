from ast import Node
from lexical import tokens
import ply.yacc as yacc
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('left', 'AND', 'OR'),
    ('left', 'EQUAL', 'UNEQUAL', 'LE', 'LT', 'GT', 'GE'),
    ('left', 'LP', 'RP'),
    # (%prec UMINUS覆盖了默认的优先级（MINUS的优先级），将UMINUS指代的优先级应用在该语法规则上)
    ('right', 'UMINUS', 'NOT')
)

start = 'program'


def p_program(p):
    '''
    program : program_head  routine  DOT
    '''
    p[0] = Node('program', p[1], p[2])


def p_program_head(p):
    '''
    program_head : PROGRAM  NAME  SEMI
    '''
    p[0] = p[2]


def p_routine(p):
    '''
    routine : routine_head  routine_body
    '''
    p[0] = Node('routine', p[1], p[2])


def p_sub_routine(p):
    '''
    sub_routine : routine
    '''
    p[0] = p[1]


def p_routine_head(p):
    '''
    routine_head : label_part  const_part  type_part  var_part  routine_part
    '''
    p[0] = Node('routine_head', p[1], p[2], p[3], p[4], p[5])


def p_label_part(p):
    '''
    label_part : empty
    '''
    pass


def p_empty(p):
    '''
    empty :
    '''
    pass

# const part


def p_const_part(p):
    '''
    const_part : CONST  const_expr_list
                | empty
    '''
    if len(p) == 3:
        p[0] = p[2]


def p_const_expr_list(p):
    '''
    const_expr_list : const_expr_list  const_expr
                    | const_expr
    '''
    if len(p) == 3:
        p[0] = Node('const_expr_list', p[1], p[2])
    elif len(p) == 2:
        p[0] = p[1]


def p_const_expr(p):
    '''
    const_expr : NAME  EQUAL  const_value  SEMI
    '''
    p[0] = Node('const_expr', p[1], p[3])


def p_const_value_1(p):
    '''
    const_value : INTEGER
    '''
    p[0] = Node('integer', p[1])


def p_const_value_2(p):
    '''
    const_value : REAL
    '''
    p[0] = Node('real', p[1])


def p_const_value_3(p):
    '''
    const_value : CHAR
    '''
    p[0] = Node('char', p[1])


def p_const_value_4(p):
    '''
    const_value : STRING
    '''
    p[0] = Node('string', p[1])


def p_const_value_5(p):
    '''
    const_value : SYS_CON
    '''
    p[0] = Node('sys_con', p[1])

# type part


def p_type_part(p):
    '''
    type_part : TYPE type_decl_list
                |  empty
    '''
    if len(p) == 3:
        p[0] = p[2]


def p_type_decl_list(p):
    '''
    type_decl_list : type_decl_list  type_definition
                    |  type_definition
    '''
    if len(p) == 3:
        p[0] = Node("type_decl_list", p[1], p[2])
    else:
        p[0] = p[1]


def p_type_definition(p):
    '''
    type_definition : NAME  EQUAL  type_decl  SEMI
    '''
    p[0] = Node("type_definition", p[1], p[3])


def p_type_decl(p):
    '''
    type_decl : simple_type_decl
            |  array_type_decl
            |  record_type_decl
    '''
    p[0] = p[1]


def p_simple_type_decl_1(p):
    '''
    simple_type_decl : SYS_TYPE
    '''
    p[0] = Node("sys_type", p[1])


def p_simple_type_decl_2(p):
    '''
    simple_type_decl : NAME
    '''
    p[0] = Node("alias", p[1])


def p_simple_type_decl_3(p):
    '''
    simple_type_decl : LP  name_list  RP
    '''
    p[0] = Node("enum", p[2])


def p_simple_type_decl_4(p):
    '''
    simple_type_decl : const_value  DOTDOT  const_value
    '''
    p[0] = Node("range",p[1], p[3])


def p_array_type_decl(p):
    '''
    array_type_decl : ARRAY  LB  simple_type_decl  RB  OF  type_decl
    '''
    p[0] = Node('array', p[3], p[6])


def p_record_type_decl(p):
    '''
    record_type_decl : RECORD  field_decl_list  END
    '''
    p[0] = Node('record', p[2])


def p_field_decl_list(p):
    '''
    field_decl_list : field_decl_list  field_decl
                    |  field_decl
    '''
    if len(p) == 3:
        p[0] = Node('field_decl_list', p[1], p[2])
    else:
        p[0] = p[1]


def p_field_decl(p):
    '''
    field_decl : name_list  COLON  type_decl  SEMI
    '''
    p[0] = Node('field_decl', p[1], p[3])


def p_name_list(p):
    '''
    name_list : name_list  COMMA  NAME
            |  NAME
    '''
    if len(p) == 4:
        p[0] = Node('name_list', p[1], p[3])
    else:
        p[0] = p[1]

# var part


def p_var_part(p):
    '''
    var_part : VAR  var_decl_list
            |  empty
    '''
    if len(p) == 3:
        p[0] = p[2]


def p_var_decl_list(p):
    '''
    var_decl_list : var_decl_list  var_decl
                |  var_decl
    '''
    if len(p) == 3:
        p[0] = Node('var_decl_list', p[1], p[2])
    else:
        p[0] = p[1]


def p_var_decl(p):
    '''
    var_decl : name_list  COLON  type_decl  SEMI
    '''
    p[0] = Node('var_decl', p[1], p[3])

# routine part


def p_routine_part(p):
    '''
    routine_part : routine_part  function_decl
                |  routine_part  procedure_decl
                |  function_decl
                |  procedure_decl
                |  empty
    '''
    if len(p) == 3:
        p[0] = Node('routine_part', p[1], p[2])
    elif p[1]:
        p[0] = p[1]


def p_function_decl(p):
    '''
    function_decl : function_head  SEMI  sub_routine  SEMI
    '''
    p[0] = Node('function_decl', p[1], p[3])


def p_function_head(p):
    '''
    function_head : FUNCTION  NAME  parameters  COLON  simple_type_decl
    '''
    p[0] = Node("function_head", p[2], p[3], p[5])


def p_procedure_decl(p):
    '''
    procedure_decl : procedure_head  SEMI  sub_routine  SEMI
    '''
    p[0] = Node("procedure_decl", p[1], p[3])


def p_procedure_head(p):
    '''
    procedure_head : PROCEDURE NAME parameters
    '''
    p[0] = Node("procedure_head", p[2], p[3])


def p_parameters(p):
    '''
    parameters : LP  para_decl_list  RP
                | empty
    '''
    if len(p) == 4:
        p[0] = p[2]


def p_para_decl_list(p):
    '''
    para_decl_list : para_decl_list  SEMI  para_type_list
                    | para_type_list
    '''
    if len(p) == 4:
        p[0] = Node("para_decl_list", p[1], p[3])
    else:
        p[0] = p[1]


def p_para_type_list_1(p):
    '''
    para_type_list : var_para_list COLON  simple_type_decl
    '''
    p[0] = Node("para_type_list", p[1], p[3])


def p_para_type_list_2(p):
    '''
    para_type_list : val_para_list  COLON  simple_type_decl
    '''
    p[0] = Node("para_type_list", p[1], p[3])


def p_var_para_list(p):
    '''
    var_para_list : VAR  name_list
    '''
    p[0] = p[2]


def p_val_para_list(p):
    '''
    val_para_list : name_list
    '''
    p[0] = p[1]

# routine body


def p_routine_body(p):
    '''
    routine_body : compound_stmt
    '''
    p[0] = p[1]


def p_compound_stmt(p):
    '''
    compound_stmt : BEGIN  stmt_list  END
    '''
    p[0] = p[2]


def p_stmt_list(p):
    '''
    stmt_list : stmt_list  stmt  SEMI
                |  empty
    '''
    if len(p) == 4:
        p[0] = Node("stmt_list", p[1], p[2])


def p_stmt(p):
    '''
    stmt : INTEGER  COLON  non_label_stmt
        |  non_label_stmt
    '''
    if len(p) == 4:
        p[0] = Node("stmt", p[1], p[3])
    else:
        p[0] = p[1]


def p_non_label_stmt(p):
    '''
    non_label_stmt : assign_stmt
                    | proc_stmt
                    | compound_stmt
                    | if_stmt
                    | repeat_stmt
                    | while_stmt
                    | for_stmt
                    | case_stmt
                    | goto_stmt
    '''
    p[0] = p[1]


def p_assign_stmt(p):
    '''
    assign_stmt : NAME  ASSIGN  expression
    '''
    p[0] = Node("assign_stmt", p[1], p[3])


def p_assign_stmt_array(p):
    '''
    assign_stmt : NAME LB expression RB ASSIGN expression
    '''
    p[0] = Node("assign_stmt_array", p[1], p[3], p[6])


def p_assign_stmt_record(p):
    '''
    assign_stmt : NAME  DOT  NAME  ASSIGN  expression
    '''
    p[0] = Node("assign_stmt_record", p[1], p[3], p[5])


def p_proc_stmt(p):
    '''
    proc_stmt : NAME
              | NAME  LP  args_list  RP
              | SYS_PROC
              | SYS_PROC  LP  expression_list  RP
              | READ  LP  factor  RP
    '''
    if len(p) == 2:
        p[0] = Node("proc_stmt", p[1])
    elif len(p) == 5:
        p[0] = Node("proc_stmt", p[1], p[3])
    else:
        p[0] = Node("proc_stmt", p[3])


def p_if_stmt(p):
    '''
    if_stmt : IF  expression  THEN  stmt  else_clause
    '''
    p[0] = Node("if_stmt", p[2], p[4], p[5])


def p_else_clause(p):
    '''
    else_clause : ELSE stmt
                | empty
    '''
    if len(p) == 3:
        p[0] = p[2]


def p_repeat_stmt(p):
    '''
    repeat_stmt : REPEAT  stmt_list  UNTIL  expression
    '''
    p[0] = Node("repeat_stmt", p[2], p[4])


def p_while_stmt(p):
    '''
    while_stmt : WHILE  expression  DO  stmt
    '''
    p[0] = Node("while_stmt", p[2], p[4])


def p_for_stmt(p):
    '''
    for_stmt : FOR  NAME  ASSIGN  expression  direction  expression  DO  stmt
    '''
    p[0] = Node("for_stmt", p[2], p[4], p[5], p[6], p[8])


def p_direction(p):
    '''
    direction : TO
            | DOWNTO
    '''
    p[0] = p[1]


def p_case_stmt(p):
    '''
    case_stmt : CASE expression OF case_expr_list  END
    '''
    p[0] = Node("case_stmt", p[2], p[4])


def p_case_expr_list(p):
    '''
    case_expr_list : case_expr_list  case_expr
                |  case_expr
    '''
    if len(p) == 3:
        p[0] = Node("case_expr_list", p[1], p[2])
    else:
        p[0] = p[1]


def p_case_expr(p):
    '''
    case_expr : const_value  COLON  stmt  SEMI
              | NAME  COLON  stmt  SEMI
    '''
    p[0] = Node("case_expr", p[1], p[3])


def p_goto_stmt(p):
    '''
    goto_stmt : GOTO  INTEGER
    '''
    p[0] = Node("goto_stmt", p[2])


def p_expression_list(p):
    '''
    expression_list : expression_list  COMMA  expression
                |  expression
    '''
    if len(p) == 4:
        p[0] = Node("expression_list", p[1], p[3])
    else:
        p[0] = p[1]


def p_expression(p):
    '''
    expression : expression  GE  expr
                |  expression  GT  expr
                |  expression  LE  expr
                |  expression  LT  expr
                |  expression  EQUAL  expr
                |  expression  UNEQUAL  expr
                |  expr
    '''
    if len(p) == 4:
        p[2] = Node(p[2], p[1], p[3])
        p[0] = Node("expression", p[2])
    elif len(p) == 2:
        p[0] = Node("expression", p[1])
    else:
        raise Exception


def p_expr(p):
    '''
    expr : expr  PLUS  term
        |  expr  MINUS  term
        |  expr  OR  term
        |  term
    '''
    if len(p) == 4:
        p[2] = Node(p[2], p[1], p[3])
        p[0] = Node("expr", p[2])
    elif len(p) == 2:
        p[0] = p[1]


def p_term(p):
    '''
    term : term  MUL  factor
        |  term  DIV  factor
        |  term  MOD  factor
        |  term  AND  factor
        |  factor
    '''
    if len(p) == 4:
        p[2] = Node(p[2], p[1], p[3])
        p[0] = Node("term", p[2])
    else:
        p[0] = p[1]


def p_factor_func(p):
    '''
    factor : SYS_FUNCT
            |  SYS_FUNCT  LP  args_list  RP
            |  NAME  LP  args_list  RP
    '''
    if len(p) == 5:
        p[0] = Node("factor_func", p[1], p[3])
    else:
        p[0] = Node("factor_func", p[1])


def p_factor_array(p):
    '''
    factor : NAME  LB  expression  RB
    '''
    p[0] = Node("factor_array", p[1], p[3])


def p_factor_1(p):
    '''
    factor : NAME
            |  const_value
            |  NOT  factor
            |  MINUS  factor %prec UMINUS
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("factor", p[1], p[2])


def p_factor_2(p):
    '''
    factor : LP  expression  RP
    '''
    p[0] = p[2]


def p_factor_3(p):
    '''
    factor : NAME DOT NAME
    '''
    p[0] = Node("factor_member", p[1], p[3])


def p_args_list(p):
    '''
    args_list : args_list  COMMA  expression
            |  expression
    '''
    if len(p) == 4:
        p[0] = Node("args_list", p[1], p[3])
    else:
        p[0] = p[1]


def p_error(p):
    print('Syntax Error occur around', 'line:', p.lineno)
    print('Syntax Error occur around', p.type, ':', p.value)
    exit()


parser = yacc.yacc()


def parse_grammar(s):
    result = parser.parse(s)
    return result


if __name__ == '__main__':

    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
        result = parser.parse(data, debug=1)
        print(result)
    else:
        data = ""
        while 1:
            try:
                data += input() + "\n"
            except:
                break
            if data == "q" or data == "quit":
                break
            if not data:
                continue

        result = parse_grammar(data)
        print(result)
