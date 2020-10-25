"""
New Version changed in 6.4
修改内容:
1. 在const_expr_codegen钟加入了add_const函数内容
2. 实现const变量不能修改
3. 增添函数变量嵌套调用
4. 修改类型检查，根据pascal定义进行具体修改
5. array中的赋值问题修改(仍存在问题)
6. 实现部分系统函数
    writeln支持int、bool、及char
    succ及pred只支持int类型
"""
import llvmlite.ir as ir
import llvmlite.binding as llvm
import sys
from ast import Node
from lexical import tokens
import os
from syntax import*
from symbol_table import*
from ctypes import CFUNCTYPE, c_float, c_int, c_void_p, cast, c_int32,c_char,c_int8,c_char_p

SYS_FUN = {'writeln','read','chr','readln','odd','ord','abs','sqr','sqrt','succ','pred'}

def codegen_error(error):
    print('------------------------------------------')
    print('Compile_error:'+error)
    sys.exit()


def write(x):
    print(x)
    return

def writechar(x):
    print(x)
    return

def writefloat(x):
    print(x)
    return


c_do_write_type = CFUNCTYPE(c_void_p, c_int32)
c_do_write = c_do_write_type(write)
do_write_addr = cast(c_do_write, c_void_p).value

c_do_write_type_char = CFUNCTYPE(c_void_p, c_char)
c_do_write_char = c_do_write_type_char(writechar)
do_write_addr_char = cast(c_do_write_char, c_void_p).value


c_do_write_type_float = CFUNCTYPE(c_void_p, c_float)
c_do_write_float = c_do_write_type_float(writefloat)
do_write_addr_float = cast(c_do_write_float, c_void_p).value

def read(x):
    i = eval(input())
    x = i
    return x

def readchar(x):
    i = input()
    x = i.encode()
    return x

c_do_read_type = CFUNCTYPE(c_int32, c_int32)
c_do_read = c_do_read_type(read)
do_read_addr = cast(c_do_read, c_void_p).value

c_do_read_type_char = CFUNCTYPE(c_char, c_char)
c_do_read_char = c_do_read_type_char(readchar)
do_read_addr_char= cast(c_do_read_char, c_void_p).value

c_do_read_type_float= CFUNCTYPE(c_float, c_float)
c_do_read_float = c_do_read_type_float(read)
do_read_addr_float = cast(c_do_read_float, c_void_p).value

def do_chr(x):
    c = chr(x)
    q = c.encode()
    return q

c_do_chr_type = CFUNCTYPE(c_char, c_int32)
c_do_chr = c_do_chr_type(do_chr)
do_chr_addr = cast(c_do_chr, c_void_p).value

def do_abs(x):
    x = abs(x)
    return x

c_do_abs_type = CFUNCTYPE(c_int32, c_int32)
c_do_abs = c_do_abs_type(do_abs)
do_abs_addr = cast(c_do_abs, c_void_p).value  


c_do_abs_type_f = CFUNCTYPE(c_float, c_float)
c_do_abs_f = c_do_abs_type_f(do_abs)
do_abs_addr_f = cast(c_do_abs_f, c_void_p).value 

def do_sqrt(x):
    x = x**0.5
    return x

c_do_sqrt_type = CFUNCTYPE(c_float, c_int32)
c_do_sqrt = c_do_sqrt_type(do_sqrt)
do_sqrt_addr_i = cast(c_do_sqrt, c_void_p).value  


c_do_sqrt_type_f = CFUNCTYPE(c_float, c_float)
c_do_sqrt_f = c_do_sqrt_type_f(do_sqrt)
do_sqrt_addr_f = cast(c_do_sqrt_f, c_void_p).value 


class CodeGene(object):
    def __init__(self, code_name):
        self.module = ir.Module(code_name)
        self.builder = None
        self.sym_table = SymbleTable()
    scope_cnt = 0
    function_number = 0

    def code_generate(self, rt):
        return self._codegen(rt, self.builder)

    # 关键函数
    def _codegen(self, rt, builder):
        if rt is None:
            return
        # 叶子节点则直接返回
        if not isinstance(rt, Node):
            return rt
        # 调应ast节点type类型对应的树
        method = rt.type+'_codegen'
        print(method)
        return getattr(self, method)(rt, builder)

    def empty_codegen(self, node, builder):
        return None

    def listastnode_codegen(self, node, builder):
        res = None
        for v in node.args:
            tp = self._codegen(v, builder) if v else None
            res = tp if tp else res
        return res

    # 定义系统函数writeln
    def register_writeint(self):
        write_func_type = ir.FunctionType(ir.VoidType(), (ir.IntType(32),))
        write_func = ir.Function(self.module, write_func_type, 'writeint')
        builder = ir.IRBuilder(write_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_write_addr),
                             write_func_type.as_pointer(), name='f')
        x = write_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x])
        builder.ret_void()

        self.sym_table.add_fn('writeint', write_func, 0)
    
    def register_writechar(self):
        write_func_type = ir.FunctionType(ir.VoidType(), (ir.IntType(8),))
        write_func = ir.Function(self.module, write_func_type, 'writechar')
        builder = ir.IRBuilder(write_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_write_addr_char),
                             write_func_type.as_pointer(), name='f')
        x = write_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x])
        builder.ret_void()

        self.sym_table.add_fn('writechar', write_func, 0)
    
    def register_writefloat(self):
        write_func_type = ir.FunctionType(ir.VoidType(), (ir.FloatType(),))
        write_func = ir.Function(self.module, write_func_type, 'writefloat')
        builder = ir.IRBuilder(write_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_write_addr_float),
                             write_func_type.as_pointer(), name='f')
        x = write_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x])
        builder.ret_void()

        self.sym_table.add_fn('writefloat', write_func, 0)

    def register_readint(self):
        # 定义系统函数readln
        read_func_type = ir.FunctionType(ir.IntType(32), (ir.IntType(32),))
        read_func = ir.Function(self.module, read_func_type, 'readint')
        builder = ir.IRBuilder(read_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_read_addr),
                             read_func_type.as_pointer(), name='f')
        x = read_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x, ])
        builder.ret(call)
        self.sym_table.add_fn('readint', read_func, 0)
    
   
    def register_readchar(self):
        # 定义系统函数readln
        read_func_type = ir.FunctionType(ir.IntType(8), (ir.IntType(8),))
        read_func = ir.Function(self.module, read_func_type, 'readchar')
        builder = ir.IRBuilder(read_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_read_addr_char),
                             read_func_type.as_pointer(), name='f')
        x = read_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x, ])
        builder.ret(call)
        self.sym_table.add_fn('readchar', read_func, 0)
    
    def register_readfloat(self):
        # 定义系统函数readln
        read_func_type = ir.FunctionType(ir.FloatType(), (ir.FloatType(),))
        read_func = ir.Function(self.module, read_func_type, 'readfloat')
        builder = ir.IRBuilder(read_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_read_addr_float),
                             read_func_type.as_pointer(), name='f')
        x = read_func.args[0]
        x.name = 'x'
        call = builder.call(f, [x, ])
        builder.ret(call)
        self.sym_table.add_fn('readfloat', read_func, 0)
    
    
    def register_chr(self):
        chr_func_type = ir.FunctionType(ir.IntType(8),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'chr')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_chr_addr),
                             chr_func_type.as_pointer(), name='f')
        x = chr_func.args[0]
        x.name = 'x'
        call = builder.call(f,[x,])
        builder.ret(call)
        self.sym_table.add_fn('chr',chr_func,0)

    def register_odd(self):
        chr_func_type = ir.FunctionType(ir.IntType(1),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'odd')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.srem(x,ir.Constant(ir.IntType(32), 2))
        cmp_res = builder.icmp_signed(
            '==', res, ir.Constant(ir.IntType(32), 1))
        builder.ret(cmp_res)
        self.sym_table.add_fn('odd',chr_func,0)

    def register_ord(self):
        chr_func_type = ir.FunctionType(ir.IntType(1),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'ord')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.srem(x,ir.Constant(ir.IntType(32), 2))
        cmp_res = builder.icmp_signed(
            '==', res, ir.Constant(ir.IntType(32), 0))
        builder.ret(cmp_res)
        self.sym_table.add_fn('ord',chr_func,0)
    
    def register_abs(self):
        chr_func_type = ir.FunctionType(ir.IntType(32),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'abs_int')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_abs_addr),
                             chr_func_type.as_pointer(), name='f')
        x = chr_func.args[0]
        x.name = 'x'
        call = builder.call(f,[x,])
        builder.ret(call)
        self.sym_table.add_fn('abs_int',chr_func,0)

    def register_abs_f(self):
        chr_func_type = ir.FunctionType(ir.FloatType(),(ir.FloatType(),))
        chr_func = ir.Function(self.module,chr_func_type,'abs_float')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_abs_addr_f),
                             chr_func_type.as_pointer(), name='f')
        x = chr_func.args[0]
        x.name = 'x'
        call = builder.call(f,[x,])
        builder.ret(call)
        self.sym_table.add_fn('abs_float',chr_func,0)
    
    def register_sqr(self):
        chr_func_type = ir.FunctionType(ir.IntType(32),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'isqr')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.mul(x,x)
        builder.ret(res)
        self.sym_table.add_fn('isqr',chr_func,0)

    def register_fsqr(self):
        chr_func_type = ir.FunctionType(ir.FloatType(),(ir.FloatType(),))
        chr_func = ir.Function(self.module,chr_func_type,'fsqr')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.fmul(x,x)
        builder.ret(res)
        self.sym_table.add_fn('fsqr',chr_func,0)
    
    def register_sqrt(self):
        chr_func_type = ir.FunctionType(ir.FloatType(),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'isqrt')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_sqrt_addr_i),
                             chr_func_type.as_pointer(), name='f')
        x = chr_func.args[0]
        x.name = 'x'
        call = builder.call(f,[x,])
        builder.ret(call)
        self.sym_table.add_fn('isqrt',chr_func,0)
    
    def register_sqrtf(self):
        chr_func_type = ir.FunctionType(ir.FloatType(),(ir.FloatType(),))
        chr_func = ir.Function(self.module,chr_func_type,'fsqrt')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        f = builder.inttoptr(ir.Constant(ir.IntType(64), do_sqrt_addr_f),
                             chr_func_type.as_pointer(), name='f')
        x = chr_func.args[0]
        x.name = 'x'
        call = builder.call(f,[x,])
        builder.ret(call)
        self.sym_table.add_fn('fsqrt',chr_func,0)

    def register_pred(self):
        chr_func_type = ir.FunctionType(ir.IntType(32),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'pred')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.sub(x,ir.Constant(ir.IntType(32),1))
        builder.ret(res)
        self.sym_table.add_fn('pred',chr_func,0)
    
    def register_succ(self):
        chr_func_type = ir.FunctionType(ir.IntType(32),(ir.IntType(32),))
        chr_func = ir.Function(self.module,chr_func_type,'succ')
        builder = ir.IRBuilder(chr_func.append_basic_block('entry'))
        x = chr_func.args[0]
        x.name = 'x'
        res = builder.add(x,ir.Constant(ir.IntType(32),1))
        builder.ret(res)
        self.sym_table.add_fn('succ',chr_func,0)

    #注册系统函数
    def register_sysfun(self):
        self.register_writeint()
        self.register_writechar()
        self.register_writefloat()
        self.register_readint()
        self.register_readchar()
        self.register_readfloat()
        self.register_chr()
        self.register_odd()
        self.register_ord()
        self.register_abs()
        self.register_abs_f()
        self.register_sqrt()
        self.register_sqrtf()
        self.register_succ()
        self.register_pred()
        self.register_sqr()
        self.register_fsqr()

    # program型节点处理函数
    def program_codegen(self, node, builder):
        self.register_sysfun()
        global_func_type = ir.FunctionType(ir.IntType(32), ())
        self.global_func = ir.Function(self.module, global_func_type, 'main')
        self.global_block = self.global_func.append_basic_block('main')
        builder = ir.IRBuilder(self.global_block)
        # 进一步分析routine部分
        if node.args[1]:
            self._codegen(node.args[1], builder)
        builder.ret(ir.Constant(ir.IntType(32), 1))

    # 对每个子节点进行分析
    def routine_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    # 对每个子节点进行分析
    def routine_head_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        tp = self._codegen(node.args[2], builder) if node.args[2] else None
        res = tp if tp else res
        tp = self._codegen(node.args[3], builder) if node.args[3] else None
        res = tp if tp else res
        tp = self._codegen(node.args[4], builder) if node.args[4] else None
        res = tp if tp else res
        return res

    # use in const value
    def integer_codegen(self, node, builder):
        return ir.Constant(self._helper_get_type('int'), node.args[0])

    # use in const value
    def real_codegen(self, node, builder):
        return ir.Constant(self._helper_get_type('real'), node.args[0])

    # use in const value
    def char_codegen(self, node, builder):
        res = ord(eval(node.args[0]))
        return ir.Constant(self._helper_get_type('char'), res)

    # use in const value
    def string_codegen(self, node, builder):
        # Only use in Const value
        return ir.ArrayType(node.args[0], len(node.args[0]))

    # use in const value
    def sys_con_codegen(self, node, builder):
        if node.args[0] == 'true':
            return ir.Constant(ir.IntType(1), 1)
        elif node.args[0] == 'false':
            return ir.Constant(ir.IntType(1), 0)
        elif node.args[0] == 'maxint':
            return ir.Constant(ir.IntType(32), 32767)

    def const_expr_list_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    # Const变量定义
    def const_expr_codegen(self, node, builder):
        global_type = self.const_get_type(node)
        print(global_type)
        lhs_var = ir.GlobalVariable(self.module, global_type, node.args[0])
        # True代表该全局变量值不可更改
        lhs_var.global_constant = True
        # 初始化const值
        res = self._codegen(node.args[1], builder)
        lhs_var.initializer = res
        # 将Const常量加入常量表，并检查是否重复定义
        self.sym_table.add_const(node.args[0], lhs_var, global_type)
        self.sym_table.add_var(
            node.args[0], lhs_var, CodeGene.scope_cnt, global_type)
        return res

    def range_expr_codegen(self):
        # assume only use in array
        pass

    # 判断const变量类型，返回对应ir中的类型，由于语法分析显示其可能类型和var不同，于是单独成了一个函数
    def const_get_type(self, node):
        if node.args[1].type == 'integer':
            return ir.IntType(32)
        elif node.args[1].type == 'real':
            return ir.FloatType()
        elif node.args[1].type == 'char':
            return ir.IntType(8)
        elif node.args[1].type == 'string':
            return ir.ArrayType(ir.IntType(8), len(node.args[1].args[0]))
        elif node.args[1].type == 'sys_con':
            if node.args[1].args[0] in ('true', 'false'):
                return ir.IntType(1)
            else:
                return ir.IntType(32)

    # 申请var型变量
    def new_var_codegen(self, var, builder, var_type):

        with builder.goto_entry_block():
            tp = var_type if isinstance(
                var_type, ir.Type) else self._helper_get_type(var_type)
            addr = ir.GlobalVariable(self.module,tp,var+str(CodeGene.function_number))
            if isinstance(var_type,ir.Aggregate):
                ##数组型变量初始化
                n = tp.count
                intial = [0 for i in range(0,n)]
                addr.initializer=ir.Constant(tp,intial)
            else:
                addr.initializer=ir.Constant(tp,0)

            self.sym_table.add_var(var, addr, CodeGene.scope_cnt, tp)
        return addr

    # var型变量的类型，返回对应ir中的类型
    def _helper_get_type(self, t):
        if t in ('int', 'integer'):
            return ir.IntType(32)
        elif t == 'real':
            return ir.FloatType()
        elif t == 'char':
            return ir.IntType(8)
        elif t in ('boolean', 'bool'):
            return ir.IntType(1)
        elif t == 'void':
            return ir.VoidType()
        else:
            raise codegen_error('invalid type name')

    # 分析type语句
    def type_decl_list_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    # type定义，并在符号表中增添
    def type_definition_codegen(self, node, builder):
        var_name = node.args[0]
        var_type = self._codegen(node.args[1], builder)
        self.sym_table.add_type(var_name, var_type, CodeGene.scope_cnt)

    def sys_type_codegen(self, node, builder):
        return self._helper_get_type(node.args[0])

    def alias_codegen(self, node, builder):
        real_type = self.sym_table.fetch_type(node.args[0])
        return real_type

    def array_codegen(self, node, builder):
        array_range = node.args[0]
        if array_range.type != 'range':
            self.codegen_error("Illegal symbol")
        lb = array_range.args[0].args[0]
        rb = array_range.args[1].args[0]
        array_len = rb-lb+1
        ele_type = self._codegen(node.args[1], builder)
        res = ir.ArrayType(ele_type, array_len)
        setattr(res, '_lb', lb)
        setattr(res, '_rb', rb)
        return res

    def record_codegen(self, node, builder):
        pass

    # 变量定义并列语句分析
    def var_decl_list_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    # var变量定义分析
    def var_decl_codegen(self, node, builder):
        res = None
        var_type = self._codegen(node.args[1], builder)
        for var in self.list_codegen(node.args[0], 'name_list'):
            tp = self.new_var_codegen(var, builder, var_type)
            res = tp if tp else res
        return res

    def routine_part_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    def list_codegen(self, node, list_name):
        res = []
        p = node
        while(isinstance(p, Node)):
            print('test')
            res.append(p.args[1])
            p = p.args[0]
        res.append(p)
        return res

    # 赋值语句分析
    def assign_stmt_codegen(self, node, builder):
        res = None
        res = self._codegen(node.args[1], builder) if node.args[1] else None
        if type(res) == str:
            addr = self.sym_table.fetch_var_addr(res)
            res = builder.load(addr)
        if node.args[0] in self.sym_table.const_table:
            raise semantic_error("Const {} can not be changed!".format(node.args[0]))
        var = self.sym_table.fetch_var_addr_type(node.args[0])
        var_type = var[1]
        var_addr = var[0]
        self.do_assign_codegen(var_addr, res, builder)
        return res

    def type_to_id(self, res, res_type):
        if res_type == None:
            pass
        else:
            pass

    # 赋值操作，将rhs_val赋值给addr
    def do_assign_codegen(self, addr, rhs_val, builder):
        return builder.store(rhs_val, addr)

    def function_decl_codegen(self, node, builder):
        return self.__codegen_FunctionDecl(node, builder, 'fun')

    def procedure_decl_codegen(self, node, builder):
        return self.__codegen_FunctionDecl(node, builder, 'pro')

    def function_head_codegen(self, node, builder, fn_params_type, fn_params_name, fn_return_type_l, gen_type):
        fn_name = node.args[0]
        if gen_type == 'fun':
            fn_return_type = self._codegen((node.args[2]), builder)
        if gen_type == 'pro':
            fn_return_type = ir.VoidType()
        res = []
        mid = None
        para_names = []
        types = None
        if node.args[1]:
            if node.args[1].type == 'para_type_list':
                res .append(node.args[1])
            else:
                res = self._codegen(node.args[1], builder)
        print(fn_params_name)
        for i in res:
            para_names = self.list_codegen(i.args[0], 'name_list')
            fn_params_name += para_names
            types = self._codegen(i.args[1], builder)
            fn_params_type += [types]*len(para_names)

        print(fn_return_type)
        fn_params_name.reverse()
        fn_params_type.reverse()
        print(fn_params_name)
        print(fn_params_type)
        fn_type = ir.FunctionType(fn_return_type, fn_params_type)
        func = ir.Function(self.module, fn_type, fn_name)
        fn_return_type_l.append(fn_return_type)
        return func

    #参数定义函数
    def para_decl_list_codegen(self, node, builder):
        p = node
        para_decl = []
        while (p.type == 'para_decl_list'):
            print('1')
            para_decl.append(p.args[1])
            p = p.args[0]
        para_decl.append(p)
        print(para_decl)
        return para_decl

    def __codegen_FunctionDecl(self, node, builder, gen_type):
        CodeGene.scope_cnt += 1
        CodeGene.function_number +=1
        fn_params_name, fn_params_type = [], []
        fn_return_type_l = []
        proto = self.function_head_codegen(
            node.args[0], builder, fn_params_type, fn_params_name, fn_return_type_l, gen_type)
        fn_name = node.args[0].args[0]
        self.sym_table.add_fn(fn_name, proto, CodeGene.scope_cnt)
        bb_entry = proto.append_basic_block('entry')
        newBuilder = ir.IRBuilder(bb_entry)
        for i, arg in enumerate(proto.args):
            arg.name = fn_params_name[i]
            addr = self.new_var_codegen(
                arg.name, newBuilder, fn_params_type[i])
            newBuilder.store(arg, addr)
        fn_return_type = fn_return_type_l[0]
        print(fn_return_type)
        if gen_type != 'pro':
            print(fn_name)
            return_addr = self.new_var_codegen(
                fn_name, newBuilder, fn_return_type)
        res = self._codegen(node.args[1], newBuilder)
        if gen_type == 'fun':
            return_val = newBuilder.load(return_addr, fn_name)
            newBuilder.ret(return_val)
        else:
            newBuilder.ret_void()
        self.sym_table.remove_scope(CodeGene.scope_cnt)
        CodeGene.scope_cnt -= 1
        return None

    def stmt_list_codegen(self, node, builder):
        res = None
        tp = self._codegen(node.args[0], builder) if node.args[0] else None
        res = tp if tp else res
        tp = self._codegen(node.args[1], builder) if node.args[1] else None
        res = tp if tp else res
        return res

    def stmt_codegen(self, node, builder):
        block = builder.function.append_basic_block(
            'integer_symbo_block'+str(node.args[0]))
        builder.branch(block)
        builder.position_at_start(block)
        body_val = self._codegen(node.args[1], builder)
        self.sym_table.add_sym_block(node.args[0], block, CodeGene.scope_cnt)

    def assign_stmt_record_codegen(self, node, builder):
        res = None
        res = self._codegen(node.args[2], builder) if node.args[2] else None
        var_addr = self.sym_table.fetch_var_addr(node.args[0])
        self.do_assign_codegen(var_addr, res, builder)
        return res
    def expression_codegen(self, node, builder):
        res = None
        subnode = node.args[0]
        if isinstance(subnode, Node) and subnode.type in ('=', '>=', '>', '<=', '<', '<>'):
            les = self._codegen(
                node.args[0].args[0], builder) if node.args[0].args[0] else None
            res = self._codegen(
                node.args[0].args[1], builder) if node.args[0].args[1] else None
            if type(les) == str:
                addr = self.sym_table.fetch_var_addr(les)
                les = builder.load(addr)
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
            if subnode.type in ('>=', '>', '<=', '<', '=', '<>'):
                op = subnode.type
                if op == '=':
                    op = '=='
                if op == '<>':
                    op = '!='
                if res.type== ir.FloatType() or les.type== ir.FloatType():
                    return builder.fcmp_ordered(op, les, res)
                else:
                    return builder.icmp_signed(op, les, res)
        elif isinstance(subnode, Node):
            res = self._codegen(
                node.args[0], builder) if node.args[0] else None
        elif type(type(subnode) == str):
            addr = self.sym_table.fetch_var_addr(subnode)
            res = builder.load(addr)
        return res

    def expr_codegen(self, node, builder):
        res = None
        les = None
        if node.args[0] == 'term':
            res = self._codegen(
                node.args[0], builder) if node.args[0] else None
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
        else:
            les = self._codegen(
                node.args[0].args[0], builder) if node.args[0].args[0] else None
            res = self._codegen(
                node.args[0].args[1], builder) if node.args[0].args[1] else None
            # 叶子节点若是变量名，需要加载变量的值
            if type(les) == str:
                addr = self.sym_table.fetch_var_addr(les)
                les = builder.load(addr)
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
            if node.args[0].type == '+':
                if res.type== ir.FloatType() or les.type== ir.FloatType():
                    return builder.fadd(les, res, name='float_add')
                elif res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.add(les, res, name='integer_add')
                else:
                    raise codegen_error('add operation only use in integer and float')
            elif node.args[0].type == '-':
                if res.type== ir.FloatType() or les.type== ir.FloatType():
                    return builder.fsub(les, res, name='float_sub')
                elif res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.sub(les, res, name='integer_sub')
                else: 
                    raise codegen_error('sub operation only use in integer and float')
            elif node.args[0].type == 'or':
                if res.type== ir.IntType(1) or les.type== ir.IntType(1):
                    return builder.or_(les, res, name='bool_or')
                else:
                    raise codegen_error('or operation : bool or bool ')
            else:
                codegen_error("Illegal Symbol")
        return res

    def term_codegen(self, node, builder):
        res = None
        les = None
        if node.args[0].type == 'factor':
            res = self._codegen(
                node.args[0], builder) if node.args[0] else None
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
        else:
            les = self._codegen(
                node.args[0].args[0], builder) if node.args[0].args[0] else None
            res = self._codegen(
                node.args[0].args[1], builder) if node.args[0].args[1] else None
            if type(les) == str:
                addr = self.sym_table.fetch_var_addr(les)
                les = builder.load(addr)
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
            if node.args[0].type in ('*', 'mul'):
                if res.type== ir.FloatType() or les.type == ir.FloatType():
                    return builder.fmul(les, res, name='float_mul')
                elif res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.mul(les, res, name='integer_mul')
                else: 
                    raise codegen_error('mul operation only use in integer and float')
            elif node.args[0].type in ('/'):
                if res.type== ir.FloatType() or les.type== ir.FloatType():
                    return builder.fdiv(les, res, name='floag_div')
                elif res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.sdiv(les, res, name='integer_div')
                else: 
                    raise codegen_error('/ operation only use in integer and float')
            elif node.args[0].type in ('div'):
                if res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.sdiv(les, res, name='integer_div')
                else:
                    raise codegen_error('div operation only use in integer and float')
            elif node.args[0].type in ('MOD', 'mod'):
                if res.type== ir.FloatType() or les.type== ir.FloatType():
                    return builder.frem(les, res, name='float_mod')
                elif res.type== ir.IntType(32) or les.type== ir.IntType(32):
                    return builder.srem(les, res, name='integer_mod')
                else: 
                    raise codegen_error('mod operation only use in integer and float')
            elif node.args[0].type == 'and':
                if res.type== ir.IntType(1) or les.type== ir.IntType(1):
                    return builder.and_(les, res, name='integer_and')
                else: 
                    raise codegen_error('and operation only use : bool and bool')
            else:
                codegen_error("Illegal symbol")
        return res

    def factor_codegen(self, node, builder):
        res = None
        if node.args[0] == 'not':
            res = self._codegen(
                node.args[1], builder) if node.args[1] else None
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
            if res.type== ir.IntType(1):
                return builder.not_(res, name='integer_not')
            else:
                return codegen_error('not operation only use in bool')
        elif node.args[0] == '-':
            res = self._codegen(
                node.args[1], builder) if node.args[1] else None
            if type(res) == str:
                addr = self.sym_table.fetch_var_addr(res)
                res = builder.load(addr)
            if res.type== ir.IntType(32):
                return builder.neg(res, name='')
            else:
                return codegen_error('minus operation only use in integer')
        else:
            return None

    def sysfun_codegen(self,node,builder):
        if node.args[0] == 'writeln':
            call_args = self.args(node.args[1], builder)
            if call_args[0].type==ir.IntType(32):
                
                callee = self.sym_table.fetch_fn_block('writeint')
                return builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.IntType(8):
                
                callee = self.sym_table.fetch_fn_block('writechar')
                return builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.FloatType():
                
                callee = self.sym_table.fetch_fn_block('writefloat')
                return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'read' or node.args[0] == 'readln':
            call_args = self.args(node.args[1], builder)
            print(call_args[0])
            if call_args[0].type==ir.IntType(32):
                
                callee = self.sym_table.fetch_fn_block('readint')
                res = builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.IntType(8):
                
                callee = self.sym_table.fetch_fn_block('readchar')
                res = builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.FloatType():
                
                callee = self.sym_table.fetch_fn_block('readfloat')
                res = builder.call(callee, call_args, 'call'+node.args[0])
            if type(node.args[1])==str:
                addr = self.sym_table.fetch_var_addr(node.args[1])
            else:
                addr = self.sym_table.fetch_var_addr(node.args[1].args[0])
            builder.store(res, addr)
            return res
        elif node.args[0] == 'chr':
            call_args = self.args(node.args[1], builder)
            callee = self.sym_table.fetch_fn_block('chr')
            return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'odd':
            call_args = self.args(node.args[1], builder)
            callee = self.sym_table.fetch_fn_block('odd')
            return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'ord':
            call_args = self.args(node.args[1], builder)
            callee = self.sym_table.fetch_fn_block('ord')
            return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'abs':
            print(node.args[1])
            call_args = self.args(node.args[1], builder)
            print(call_args[0].type)
            if call_args[0].type==ir.IntType(32):
                callee = self.sym_table.fetch_fn_block('abs_int')
                return builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.FloatType():
                callee = self.sym_table.fetch_fn_block('abs_float')
                return builder.call(callee, call_args, 'call'+node.args[0])
            else:
                raise codegen_error("abs args type error")
        elif node.args[0] == 'succ':
            call_args = self.args(node.args[1], builder)
            callee = self.sym_table.fetch_fn_block('succ')
            return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'pred':
            call_args = self.args(node.args[1], builder)
            callee = self.sym_table.fetch_fn_block('pred')
            return builder.call(callee, call_args, 'call'+node.args[0])
        elif node.args[0] == 'sqr':
            print(node.args[1])
            call_args = self.args(node.args[1], builder)
            print(call_args[0].type)
            if call_args[0].type==ir.IntType(32):
                callee = self.sym_table.fetch_fn_block('isqr')
                return builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.FloatType():
                callee = self.sym_table.fetch_fn_block('fsqr')
                return builder.call(callee, call_args, 'call'+node.args[0])
            else:
                raise codegen_error("abs args type error")
        elif node.args[0] == 'sqrt':
            print(node.args[1])
            call_args = self.args(node.args[1], builder)
            print(call_args[0].type)
            if call_args[0].type==ir.IntType(32):
                callee = self.sym_table.fetch_fn_block('isqrt')
                return builder.call(callee, call_args, 'call'+node.args[0])
            elif call_args[0].type==ir.FloatType():
                callee = self.sym_table.fetch_fn_block('fsqrt')
                return builder.call(callee, call_args, 'call'+node.args[0])
            else:
                raise codegen_error("abs args type error")
    def factor_func_codegen(self, node, builder):
        if len(node.args) == 1:
            callee = self.sym_table.fetch_fn_block(node.args[0])
            call_args = []
            return builder.call(callee, call_args, 'call'+node.args[0])
        else:
            if node.args[0] in SYS_FUN:
                return self.sysfun_codegen(node,builder)
            else:
                callee = self.sym_table.fetch_fn_block(node.args[0])
                call_args = self.args(node.args[1], builder)
                return builder.call(callee, call_args, 'call'+node.args[0])

    def factor_array_codegen(self, node, builder):
        var_addr, var_type = self.sym_table.fetch_var_addr_type(node.args[0])
        index = []
        i = node.args[1]
        if isinstance(i, Node):
            val = self._codegen(i, builder)
        elif type(i) == str:
            addr = self.sym_table.fetch_var_addr(i)
            val = builder.load(addr)
        else:
            val = ir.Constant(ir.IntType(32), i.value)
        index.append(val)
        indices = index
        indices.append(ir.Constant(var_addr.type.pointee.element, 0))
        addr = builder.gep(var_addr, indices)
        res = builder.load(addr, "arraymember")
        return res

    def args_list_codegen(self, node, builder):
        res = []
        mid = None
        for i in node.args:
            mid = self._codegen(i, builder)
            if(type(mid) == list):
                res += mid
            else:
                res.append(mid)
        return res

    def array_address_codegen(self, node, builder):
        var_addr, var_type = self.sym_table.fetch_var_addr_type(node.args[0])
        index = []
        i = node.args[1]
        if isinstance(i, Node):
            val = self._codegen(i, builder)
        elif type(i) == str:
            addr = self.sym_table.fetch_var_addr(i)
            val = builder.load(addr)
        else:
            val = ir.Constant(ir.IntType(32), i.value)
        index.append(val)
        indices = index
        indices.append(ir.Constant(var_addr.type.pointee.element, 0))
        return builder.gep(var_addr, indices)

    def assign_stmt_array_codegen(self, node, builder):
        les = None
        res = None
        les = self.array_address_codegen(node, builder)
        res = self._codegen(node.args[2], builder)
        if type(res) == str:
            addr = self.sym_table.fetch_var_addr(res)
            res = builder.load(addr)
        self.do_assign_codegen(les, res, builder)
        return res

    def assign_stmt_record(self, node, builder):
        # TODO
        pass

    def proc_stmt_codegen(self, node, builder):
        if len(node.args) == 1:
            # 无参数函数
            callee = self.sym_table.fetch_fn_block(node.args[0])
            call_args = []
            return builder.call(callee, call_args, 'call'+node.args[0])
        else:
            # 有参数函数
            if node.args[0] in SYS_FUN:
                return self.sysfun_codegen(node,builder)
            else:
                callee = self.sym_table.fetch_fn_block(node.args[0])
                call_args = self.args(node.args[1], builder)
                res = builder.call(callee, call_args, 'call'+node.args[0])
                return res

    def args(self, node, builder):
        res = []
        mid = None
        if type(node) == str:
            addr = self.sym_table.fetch_var_addr(node)
            s = builder.load(addr)
            res.append(s)
        else:
            mid = self._codegen(node, builder)
            if(type(mid) == list):
                res += mid
            else:
                res.append(mid)
        return res

    def goto_stmt_codegen(self, node, builder):
        target = self.sym_table.fetch_sym_block(node.args[0])
        goto_bb = builder.function.append_basic_block('goto')
        after_bb = builder.function.append_basic_block('after_goto')
        builder.branch(goto_bb)
        builder.position_at_start(goto_bb)
        builder.branch(target)
        builder.position_at_start(after_bb)

    def repeat_stmt_codegen(self, node, builder):
        loop_bb = builder.function.append_basic_block('loop')
        after_bb = builder.function.append_basic_block('after_loop')
        builder.branch(loop_bb)
        builder.position_at_start(loop_bb)
        body_val = self._codegen(node.args[0], builder)
        end_expr_val = self._codegen(node.args[1], builder)
        cmp_res = builder.icmp_signed(
            '==', end_expr_val, ir.Constant(ir.IntType(1), 0))
        builder.cbranch(cmp_res, loop_bb, after_bb)
        builder.position_at_start(after_bb)

    def if_stmt_codegen(self, node, builder):
        cond_val = self._codegen(node.args[0], builder)
        cmp_res = builder.icmp_signed(
            '!=', cond_val, ir.Constant(ir.IntType(1), 0))
        then_bb = builder.function.append_basic_block('then_block')
        else_bb = builder.function.append_basic_block('else_block')
        end_bb = builder.function.append_basic_block('end_block')
        builder.cbranch(cmp_res, then_bb, else_bb)
        builder.position_at_start(then_bb)
        then_val = self._codegen(node.args[1], builder)
        builder.branch(end_bb)
        then_bb = builder.block
        builder.position_at_start(else_bb)
        else_val = self._codegen(node.args[2], builder)
        else_bb = builder.block
        builder.branch(end_bb)
        builder.position_at_start(end_bb)

    #
    def while_stmt_codegen(self, node, builder):
        end_expr_val = self._codegen(node.args[0], builder)
        cmp_res = builder.icmp_signed(
            '!=', end_expr_val, ir.Constant(ir.IntType(1), 0))
        loop_bb = builder.function.append_basic_block('loop')
        after_bb = builder.function.append_basic_block('after_loop')
        builder.cbranch(cmp_res, loop_bb, after_bb)
        builder.position_at_start(loop_bb)
        body_val = self._codegen(node.args[1], builder)
        end_expr_val = self._codegen(node.args[0], builder)
        cmp_res = builder.icmp_signed(
            '!=', end_expr_val, ir.Constant(ir.IntType(1), 0))
        builder.cbranch(cmp_res, loop_bb, after_bb)
        builder.position_at_start(after_bb)

    def for_stmt_codegen(self, node, builder):
        var_addr = self.sym_table.fetch_var_addr(node.args[0])
        start_val = self._codegen(node.args[1], builder)
        cur_val = start_val
        self.do_assign_codegen(var_addr, start_val, builder)
        end_val = self._codegen(node.args[3], builder)
        if node.args[2] == 'to':
            cmp_res = builder.icmp_signed('<=', cur_val, end_val)
        elif node.args[2] == 'downto':
            cmp_res = builder.icmp_signed('>=', cur_val, end_val)
        else:
            codegen_error('symbol error in for!')
        loop_bb = builder.append_basic_block('loop')
        after_bb = builder.append_basic_block('after_bb')
        builder.cbranch(cmp_res, loop_bb, after_bb)
        builder.position_at_start(loop_bb)
        res = self._codegen(node.args[4], builder)
        step = ir.Constant(self._helper_get_type('int'), 1)
        cur_val = builder.load(var_addr)
        if node.args[2] == 'to':
            cur_val = builder.add(cur_val, step)
            cmp_res = builder.icmp_signed('<=', cur_val, end_val)
        elif node.args[2] == 'downto':
            cur_val = builder.sub(cur_val, step)
            cmp_res = builder.icmp_signed('>=', cur_val, end_val)
        cur_val = builder.store(cur_val, var_addr)
        builder.cbranch(cmp_res, loop_bb, after_bb)
        builder.position_at_start(after_bb)
        return res

    def case_stmt_codegen(self, node, builder):
        res = None
        start_bb = builder.append_basic_block('before_switch')
        ex_value = self._codegen(node.args[0], builder)
        builder.branch(start_bb)
        stmt = self._codegen(node.args[1], builder)
        end_bb = builder.append_basic_block('end_switch')
        builder.position_at_start(start_bb)
        mycase = builder.switch(ex_value, end_bb)
        for i in stmt:
            mycase.add_case(i[0], i[1])
        for i in stmt:
            builder.position_at_end(i[1])
            builder.branch(end_bb)
        builder.position_at_start(end_bb)
        return res

    def case_expr_list_codegen(self, node, builder):
        res = None
        blocks = []
        p = node
        while(p.type == 'case_expr_list'):
            blocks.append(self._codegen(p.args[1], builder))
            p = p.args[0]
        blocks.append(self._codegen(p, builder))
        print(blocks)
        return blocks

    def case_expr_codegen(self, node, builder):
        value = self._codegen(node.args[0], builder)
        case_bb = builder.append_basic_block('case_block')
        builder.position_at_start(case_bb)
        res = self._codegen(node.args[1], builder)
        return (value, case_bb)

    def expression_list_codegen(self, node, builder):
        res = []
        mid = None
        for i in node.args:
            mid = self._codegen(i, builder)
            if(type(mid) == list):
                res += mid
            else:
                res.append(mid)
        return res


if __name__ == '__main__':

    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
        result = parser.parse(data, debug=1)
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
    codegen = CodeGene('main')
    codegen.code_generate(result)
    print(codegen.module)
