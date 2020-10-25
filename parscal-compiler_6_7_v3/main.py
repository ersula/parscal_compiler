#IR to ASM
import llvmlite.ir as ir
import llvmlite.binding as llvm
import sys
from ast import Node
from lexical import tokens
import os
from syntax import *
from symbol_table import*
from code_gen import*
from ctypes import CFUNCTYPE,c_double,c_int,c_void_p,cast,c_int32
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

import argparse
par = argparse.ArgumentParser(description="Parscal_Test")
par.add_argument("--input_file", type=str, default="test.pas", help="parscal_file_name")
par.add_argument("--print_ir", type=int, default=0, help='print ir or not')
par.add_argument("--print_final", type=int, default=0, help='print final of not')
par.add_argument("--optimize", type=int, default=0, help='optimize or not')
opt = par.parse_args()


def create_execution_engine():
    """
    Create an ExecutionEngine suitable for JIT code generation on
    the host CPU.  The engine is reusable for an arbitrary number of
    modules.
    """
    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return (engine,target_machine)


def compile_ir(engine, llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    # Now add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod



f = open(opt.input_file, "r")
data = f.read()
f.close()
result = parser.parse(data)


result = parse_grammar(data)
codegen=CodeGene('main')
codegen.code_generate(result)
llvm_ir=str(codegen.module)


(engine,target) = create_execution_engine()
mod = compile_ir(engine, llvm_ir)

if opt.optimize == 1:
    pm_builder = llvm.create_pass_manager_builder()
    pm_builder.opt_level = 2
    pm = llvm.create_module_pass_manager()
    pm_builder.populate(pm)
    pm.add_constant_merge_pass()
    pm.add_dead_arg_elimination_pass()
    pm.add_dead_code_elimination_pass()
    pm.add_function_inlining_pass(3)
    pm.add_global_optimizer_pass()
    change_m = pm.run(mod)


if opt.print_ir == 1:
    print(llvm_ir)

# Look up the function pointer (a Python int)
func_ptr = engine.get_function_address("main")

# Run the function via ctypes
cfunc = CFUNCTYPE(c_void_p)(func_ptr)
res = cfunc()
with open('target.txt','w') as f:
    f.write(llvm_ir)
with open('asm.txt','w') as a:
    a.write(target.emit_assembly(mod))

if opt.print_final == 1:
    print(target.emit_assembly(mod))