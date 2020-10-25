"""
New Version changed in 6.4
修改内容：
1. 添加了常量表，在code_gen的const_expr_codegen处加入self.sym_table.add_const(node.args[0], lhs_var, global_type)这行
2. 对常量、作用域内的变量/函数/类型定义进行重复检查
"""
import sys


def codegen_error(error):
    print(error)
    sys.exit()


def semantic_error(error):
    print("SEMANTIC ERROR:", error)
    sys.exit()


class SymbleTable(object):
    def __init__(self):
        self.const_table = {}
        self.var_table = {}
        self.fn_table = {}
        self.scope_var = {}
        self.scope_fn = {}
        self.type_table = {}
        self.scope_type = {}
        self.symbol_block_table = {}

    def add_const(self, const_name, addr, const_type=None):
        o = self.const_table.get(const_name, None)
        # 检查常量变量内是否重复定义
        if o:
            raise semantic_error(
                "Const {} is defined duplicatedly!".format(const_name))
        else:
            self.const_table.setdefault(
                const_name, []).append((addr, const_type))

    def add_var(self, var_name, addr, scope_id, var_type=None):
        o = self.scope_var.get(scope_id, None)
        # 检查作用域内变量是否重复定义
        if o and var_name in o:
            raise semantic_error(
                "{} is defined duplicatedly in the scope!".format(var_name))
        else:
            self.scope_var.setdefault(scope_id, []).append(var_name)
            self.var_table.setdefault(var_name, []).append((addr, var_type))

    def add_fn(self, fn_name, fn_block, scope_id):
        o = self.scope_fn.get(scope_id, None)
        # 检查作用域内函数是否重复定义
        if o and fn_name in o:
            raise semantic_error(
                "{} is defined duplicatedly in the scope!".format(fn_name))
        else:
            self.fn_table.setdefault(fn_name, []).append(fn_block)
            self.scope_fn.setdefault(scope_id, []).append(fn_name)

    def add_type(self, name, type_def, scope_id):
        o = self.scope_type.get(scope_id, None)
        # 检查作用域内类型是否重复定义
        if o and name in o:
            raise semantic_error(
                "{} is defined duplicatedly in the scope!".format(name))
        else:
            self.type_table.setdefault(name, []).append(type_def)
            self.scope_type.setdefault(scope_id, []).append(name)

    def add_sym_block(self, integer, integer_block, scope_id):
        self.symbol_block_table.setdefault(integer, []).append(integer_block)

    def fetch_sym_block(self, integer):
        o = self.symbol_block_table.get(integer, None)
        if o:
            return o[-1]
        else:
            raise codegen_error(
                'Can not find goto_integer {0}'.format(integer))

    def fetch_var_addr(self, var_name):
        o = self.var_table.get(var_name, None)
        if o:
            return o[-1][0]
        else:
            raise codegen_error('Can not find symble {0}'.format(var_name))

    def fetch_var_addr_type(self, var_name):
        o = self.var_table.get(var_name, None)
        if o:
            return o[-1]
        else:
            raise codegen_error('Can not find symble {0}'.format(var_name))

    def fetch_fn_block(self, fn_name):
        o = self.fn_table.get(fn_name, None)
        if o:
            return o[-1]
        else:
            raise codegen_error('Can not find function {0}'.format(fn_name))

    def fetch_type(self, type_name):
        o = self.type_table.get(type_name, None)
        if o:
            return o[-1]
        else:
            raise codegen_error('Can not find type {0}'.format(type_name))

    def remove_scope(self, scope_id):
        for name in self.scope_var.get(scope_id, []):
            o = self.var_table.get(name, None)
            if o:
                del o[-1]
            else:
                raise codegen_error(
                    'Remove var {0} that not exsists!'.format(name))
        if self.scope_fn.get(scope_id, None) != None:
            del self.scope_var[scope_id]
        scope_id += 1
        for name in self.scope_fn.get(scope_id, []):
            o = self.fn_table.get(name, None)
            if o:
                del o[-1]
            else:
                raise codegen_error(
                    'Remove var {0} that not exsists!'.format(name))
        if self.scope_fn.get(scope_id, None) != None:
            del self.scope_fn[scope_id]
