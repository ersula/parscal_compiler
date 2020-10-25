import ply.lex as lex
import sys

simpletokens = {
    "(": 'LP',
    ")": 'RP',
    "[": 'LB',
    "]": 'RB',
    ".": 'DOT',
    ":": 'COMMA',
    ",": 'COLON',

    "*": 'MUL',
    "/": 'DIV',
    "+":'PLUS',
    "-": 'MINUS',
    "<>": 'UNEQUAL',

    ">=": 'GE',
    ">": 'GT',
    "<=": 'LE',
    "<": 'LT',
    "=": 'EQUAL',
    ":=": 'ASSIGN',

    'int': "INTEGER",
    'real':"REAL",
    'char':"CHAR",
    'string': "STRING",
    'real' : 'REAL',

    '..': 'DOTDOT',
    ';': 'SEMI',

    #only used for parser, not actually exist
    'number': 'NUMBER',
    'name': 'NAME',
    'id': 'ID'
}

reserved = {
    "array": "ARRAY",
    "begin": "BEGIN",
    "case": "CASE",
    "const": "CONST",
    "div": "DIV",
    "do": "DO",
    "downto": "DOWNTO",
    "else": "ELSE",
    "end": "END",
    "for": "FOR",
    "function": "FUNCTION",
    "goto": "GOTO",
    "if": "IF",
    "mod": "MOD",
    'and': "AND",
    "not": "NOT",
    "of": "OF",
    "or": "OR",
    "packed": "PACKED",
    "procedure": "PROCEDURE",
    "program": "PROGRAM",
    "record": "RECORD",
    "repeat": "REPEAT",
    "then": "THEN",
    "to": "TO",
    "type": "TYPE",
    "until": "UNTIL",
    "var": "VAR",
    "while": "WHILE",
    "read": "READ",

    #sys_proc
    "write": "SYS_PROC",
    "writeln": "SYS_PROC",


    #sys_type
    "boolean": "SYS_TYPE",
    "char": "SYS_TYPE",
    "integer": "SYS_TYPE",
    "real": "SYS_TYPE",

    #sys_con
    "true": "SYS_CON",
    "false": "SYS_CON",
    "maxint": "SYS_CON",

    #sys_funct
    "abs": "SYS_FUNCT",
    "chr": "SYS_FUNCT",
    "odd": "SYS_FUNCT",
    "ord": "SYS_FUNCT",
    "pred": "SYS_FUNCT",
    "sqr": "SYS_FUNCT",
    "sqrt": "SYS_FUNCT",
    "succ": "SYS_FUNCT"
}


tokens = list(simpletokens.values()) + list(reserved.values())


class lexer:
    tokens = tokens


    t_LP = r'\('
    t_RP = r'\)'
    t_LB = r'\['
    t_RB = r'\]'
    t_DOT = r'\.'
    t_COMMA = r'\,'
    t_COLON = r'\:'
    t_MUL = r'\*'
    t_DIV = r'\/'
    t_UNEQUAL = r'\<\>'

    t_PLUS = r'\+'
    t_MINUS = r'\-'
    t_GE = r'\>\='
    t_GT = r'\>'
    t_LE = r'\<\='
    t_LT = r'\<'
    t_EQUAL = r'\='
    t_ASSIGN = r'\:\='
    t_MOD = 'MOD'
    t_DOTDOT = r'\.\.'
    t_SEMI = r'\;'
    t_ignore = ' \t'

    t_CHAR = r'(\'([^\\\'\.]?)\')|(\"([^\\\"\.]?)\")'

    def t_NAME(self, t):
        r'[A-Za-z](_?[A-Za-z0-9])*'
        t.type = reserved.get(t.value.lower(), 'NAME')
        return t

    def t_ID(self, t):
        r'[A-Za-z](_?[A-Za-z0-9])*'  # (\.[A-Za-z](_?[A-Za-z0-9])*)?'
        t.type = reserved.get(t.value.lower(), 'ID')
        return t

    def t_REAL(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r'[-]?[0-9]*[0-9]+'
        t.value = int(t.value)
        return t

    def t_error(self, t):
        print("[  Illegal character  ] '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def build(self, **kwargs):
        self.lexer = lex.lex(debug=0,module=self, **kwargs)

    def test(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print(tok)


lexer = lexer()
lexer.build()

if sys.version_info[0] >= 3:
    raw_input = input

if __name__ == '__main__':

    mylexer = lexer

    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
    else:
        data = ""
        while 1:
            try:
                data += raw_input() + "\n"
            except:
                break

    mylexer.test(data)
