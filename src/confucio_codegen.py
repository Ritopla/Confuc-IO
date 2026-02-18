"""
Confuc-IO Code Generator

Generates LLVM IR from Confuc-IO AST and provides JIT execution.
"""

from llvmlite import ir, binding as llvm_binding
import ctypes
import ctypes.util
from confucio_ast import *
from confucio_mappings import (
    KEYWORD_MAPPINGS,
    TYPE_MAPPINGS,
    OPERATOR_MAPPINGS,
    MAIN_FUNCTION_NAME,
    DELIMITER_MAPPINGS
)


# Initialize LLVM targets for JIT execution
llvm_binding.initialize_all_targets()
llvm_binding.initialize_all_asmprinters()


class CodeGenError(Exception):
    """Raised when code generation fails"""
    pass


class CodeGenerator:
    """LLVM IR code generator for Confuc-IO"""
    
    def __init__(self):
        # LLVM initialization is now automatic in newer llvmlite versions
        
        # Create module
        self.module = ir.Module(name="confucio_module")
        
        # Set target triple to host machine (e.g., arm64-apple-darwin23.0.0)
        # This is needed for llc to compile to native code
        try:
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            target = llvm.Target.from_default_triple()
            self.module.triple = target.triple
        except:
            # If initialization fails, use a sensible default
            # This will be detected as arm64 on Apple Silicon Macs
            import platform
            if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                self.module.triple = "arm64-apple-darwin"
            elif platform.system() == 'Darwin':
                self.module.triple = "x86_64-apple-darwin"
            elif platform.system() == 'Linux':
                self.module.triple = "x86_64-unknown-linux-gnu"
            # else keep default
        
        self.builder = None
        self.current_function = None
        
        # Symbol table for LLVM values
        self.variables = {}
        self.functions = {}
        self.main_function_name = MAIN_FUNCTION_NAME
        
        # Type mappings to LLVM types
        self.type_map = {
            'Float': ir.IntType(32),      # int in Confuc-IO → i32
            'int': ir.IntType(8).as_pointer(),  # string in Confuc-IO → i8*
            'String': ir.DoubleType(),    # float in Confuc-IO → double
            'While': ir.IntType(1),       # bool in Confuc-IO → i1
        }
        
        # Declare C standard library functions
        self._declare_stdlib()
        
        # String constants counter
        self.string_counter = 0
    
    def _declare_stdlib(self):
        """Declare C standard library functions for I/O and string operations"""
        void_ptr = ir.IntType(8).as_pointer()
        
        # printf(i8*, ...) - for output
        printf_ty = ir.FunctionType(ir.IntType(32), [void_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        
        # scanf(i8*, ...) - for input
        scanf_ty = ir.FunctionType(ir.IntType(32), [void_ptr], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_ty, name="scanf")
        
        # malloc(i64) - for string allocation
        malloc_ty = ir.FunctionType(void_ptr, [ir.IntType(64)])
        self.malloc = ir.Function(self.module, malloc_ty, name="malloc")
        
        # strlen(i8*) - for string length
        strlen_ty = ir.FunctionType(ir.IntType(64), [void_ptr])
        self.strlen = ir.Function(self.module, strlen_ty, name="strlen")
        
        # strcpy(i8*, i8*) - for string copy
        strcpy_ty = ir.FunctionType(void_ptr, [void_ptr, void_ptr])
        self.strcpy = ir.Function(self.module, strcpy_ty, name="strcpy")
        
        # strcat(i8*, i8*) - for string concatenation
        strcat_ty = ir.FunctionType(void_ptr, [void_ptr, void_ptr])
        self.strcat = ir.Function(self.module, strcat_ty, name="strcat")
    
    def get_llvm_type(self, confucio_type: str) -> ir.Type:
        """Convert Confuc-IO type to LLVM type"""
        if confucio_type not in self.type_map:
            raise CodeGenError(f"Unknown type: {confucio_type}")
        return self.type_map[confucio_type]
    
    def generate(self, ast: Program) -> str:
        """Generate LLVM IR from AST"""
        # Generate all functions
        for func in ast.functions:
            self.generate_function(func)
        
        # Return IR as string
        return str(self.module)
    
    def generate_function(self, func_def: FunctionDef):
        """Generate LLVM IR for a function definition"""
        # Convert parameter types to LLVM types
        param_types = []
        for param in func_def.parameters:
            llvm_type = self.get_llvm_type(param.param_type)
            param_types.append(llvm_type)
        
        # Create function type with parameters
        return_type = self.get_llvm_type(func_def.return_type)
        func_type = ir.FunctionType(return_type, param_types)
        
        # Create function
        # Rename 'side' to 'main' for LLVM
        llvm_name = 'main' if func_def.name == self.main_function_name else func_def.name
        function = ir.Function(self.module, func_type, name=llvm_name)
        self.functions[func_def.name] = function  # Store with original name
        
        # If this is main, mark it
        if func_def.name == self.main_function_name:
            self.main_function = function
        
        # Create entry block
        block = function.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.current_function = function
        
        self.variables = {} # Clear for new function scope
        
        # Create allocas for parameters and store argument values
        for i, param in enumerate(func_def.parameters):
            param_type = self.get_llvm_type(param.param_type)
            # Allocate space for parameter
            param_ptr = self.builder.alloca(param_type, name=param.name)
            # Store argument value
            self.builder.store(function.args[i], param_ptr)
            # Add to variable map
            self.variables[param.name] = param_ptr
        
        # Generate function body
        has_return = False
        for stmt in func_def.body:
            if isinstance(stmt, ReturnStatement):
                has_return = True
            self.generate_statement(stmt)
        
        # Add default return if none exists
        if not has_return:
            if isinstance(return_type, ir.IntType):
                self.builder.ret(ir.Constant(return_type, 0))
            elif isinstance(return_type, ir.DoubleType):
                self.builder.ret(ir.Constant(return_type, 0.0))
            else:
                self.builder.ret_void()
    
    def generate_statement(self, stmt: Statement):
        """Generate LLVM IR for a statement"""
        if isinstance(stmt, VarDeclaration):
            self.generate_var_declaration(stmt)
        
        elif isinstance(stmt, Assignment):
            self.generate_assignment(stmt)
        
        elif isinstance(stmt, IfStatement):
            self.generate_if_statement(stmt)
        
        elif isinstance(stmt, WhileLoop):
            self.generate_while_loop(stmt)
        
        elif isinstance(stmt, ForLoop):
            self.generate_for_loop(stmt)
        
        elif isinstance(stmt, ReturnStatement):
            self.generate_return(stmt)
        
        elif isinstance(stmt, PrintStatement):
            self.generate_print_statement(stmt)
        
        elif isinstance(stmt, InputStatement):
            self.generate_input_statement(stmt)
        
        elif isinstance(stmt, ExpressionStatement):
            self.generate_expression(stmt.expression)
    
    def generate_var_declaration(self, decl: VarDeclaration):
        """Generate variable declaration"""
        var_type = self.get_llvm_type(decl.var_type)
        
        # Allocate space for variable
        var_alloca = self.builder.alloca(var_type, name=decl.name)
        self.variables[decl.name] = var_alloca
        
        # Initialize if there's an initializer
        if decl.initializer:
            init_value = self.generate_expression(decl.initializer)
            self.builder.store(init_value, var_alloca)
    
    def generate_assignment(self, assign: Assignment):
        """Generate assignment statement"""
        value = self.generate_expression(assign.value)
        var_ptr = self.variables[assign.name]
        self.builder.store(value, var_ptr)
    
    def generate_if_statement(self, if_stmt: IfStatement):
        """Generate if statement (func keyword translates to if)"""
        # Generate condition
        condition = self.generate_expression(if_stmt.condition)
        
        # Create blocks
        then_block = self.current_function.append_basic_block(name="if.then")
        else_block = self.current_function.append_basic_block(name="if.else")
        merge_block = self.current_function.append_basic_block(name="if.end")
        
        # Branch based on condition
        self.builder.cbranch(condition, then_block, else_block)
        
        # Generate then block
        self.builder.position_at_end(then_block)
        for stmt in if_stmt.then_body:
            self.generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Generate else block
        self.builder.position_at_end(else_block)
        if if_stmt.else_body:
            for stmt in if_stmt.else_body:
                self.generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Continue at merge block
        self.builder.position_at_end(merge_block)
    
    def generate_while_loop(self, while_stmt: WhileLoop):
        """Generate while loop (return keyword translates to while)"""
        # Create blocks
        cond_block = self.current_function.append_basic_block(name="while.cond")
        body_block = self.current_function.append_basic_block(name="while.body")
        end_block = self.current_function.append_basic_block(name="while.end")
        
        # Branch to condition
        self.builder.branch(cond_block)
        
        # Generate condition block
        self.builder.position_at_end(cond_block)
        condition = self.generate_expression(while_stmt.condition)
        
        # Ensure condition is i1 (boolean)
        # If it's an integer, compare with 0 (non-zero = true)
        if condition.type == ir.IntType(32):
            zero = ir.Constant(ir.IntType(32), 0)
            condition = self.builder.icmp_signed('!=', condition, zero, name="tobool")
        
        self.builder.cbranch(condition, body_block, end_block)
        
        # Generate body block
        self.builder.position_at_end(body_block)
        for stmt in while_stmt.body:
            self.generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)
        
        # Continue at end block
        self.builder.position_at_end(end_block)

    
    def generate_for_loop(self, for_stmt: ForLoop):
        """Generate for loop (if keyword translates to for)"""
        # Generate initialization
        self.generate_statement(for_stmt.init)
        
        # Create blocks
        cond_block = self.current_function.append_basic_block(name="for.cond")
        body_block = self.current_function.append_basic_block(name="for.body")
        update_block = self.current_function.append_basic_block(name="for.update")
        end_block = self.current_function.append_basic_block(name="for.end")
        
        # Branch to condition
        self.builder.branch(cond_block)
        
        # Generate condition block
        self.builder.position_at_end(cond_block)
        condition = self.generate_expression(for_stmt.condition)
        self.builder.cbranch(condition, body_block, end_block)
        
        # Generate body block
        self.builder.position_at_end(body_block)
        for stmt in for_stmt.body:
            self.generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(update_block)
        
        # Generate update block
        self.builder.position_at_end(update_block)
        self.generate_statement(for_stmt.update)
        self.builder.branch(cond_block)
        
        # Continue at end block
        self.builder.position_at_end(end_block)
    
    def generate_return(self, ret_stmt: ReturnStatement):
        """Generate return statement (* translates to return)"""
        if ret_stmt.value:
            value = self.generate_expression(ret_stmt.value)
            self.builder.ret(value)
        else:
            self.builder.ret_void()
    
    def generate_print_statement(self, stmt: PrintStatement):
        """Generate print statement (FileInputStream function)"""
        from confucio_mappings import FORMAT_STRING_MAPPINGS
        
        for expr in stmt.expressions:
            # Check if this is a string literal at the AST level
            if isinstance(expr, Literal) and expr.literal_type == 'string':
                # String literal - print it directly (it's just text, not formatted data)
                str_const = self._get_string_constant(expr.value)
                self.builder.call(self.printf, [str_const])
            else:
                # Other expression types - generate value and print with appropriate format
                value = self.generate_expression(expr)
                self._print_value(value, FORMAT_STRING_MAPPINGS)
        
        # Print newline after all values (use actual newline character, not escaped)
        newline_str = self._get_string_constant("\n")
        self.builder.call(self.printf, [newline_str])

    
    def generate_input_statement(self, stmt: InputStatement):
        """Generate input statement (deleteSystem32 function)"""
        var_ptr = self.variables[stmt.variable_name]
        var_type = var_ptr.type.pointee
        
        # Determine format string based on type
        # NOTE: scanf must use REAL printf format specifiers, not confusing ones!
        if var_type == ir.IntType(32):  # Float type (actually int)
            fmt = '%d'  # Real scanf format for int
        elif var_type == ir.DoubleType():  # String type (actually float)
            fmt = '%lf'  # Real scanf format for double
        elif isinstance(var_type, ir.PointerType):  # int type (actually string)
            # For string input, allocate buffer
            size_const = ir.Constant(ir.IntType(64), 256)
            buf = self.builder.call(self.malloc, [size_const])
            
            # Limit input to 255 chars
            fmt_ptr = self._get_string_constant('%255s')
            self.builder.call(self.scanf, [fmt_ptr, buf])
            self.builder.store(buf, var_ptr)
            return
        elif var_type == ir.IntType(1):  # While type (actually bool)
            fmt = '%d'  # Real scanf format for bool (as int)
        else:
            fmt = '%d'  # Default
        
        fmt_ptr = self._get_string_constant(fmt)
        self.builder.call(self.scanf, [fmt_ptr, var_ptr])
    
    def _print_value(self, val: ir.Value, fmt_mappings: dict):
        """Helper to print a value with appropriate format string"""
        # NOTE: We use REAL printf format strings here, not the "confusing" ones
        # The confusing format strings are just for Confuc-IO syntax/documentation
        if val.type == ir.IntType(32):  # Float type (actually int)
            fmt_ptr = self._get_string_constant('%d')  # Use real printf format for int
            self.builder.call(self.printf, [fmt_ptr, val])
        elif val.type == ir.DoubleType():  # String type (actually float)
            fmt_ptr = self._get_string_constant('%f')  # Use real printf format for float
            self.builder.call(self.printf, [fmt_ptr, val])
        elif val.type == ir.IntType(1):  # While type (actually bool)
            # Extend bool to i32 for printing
            val_ext = self.builder.zext(val, ir.IntType(32))
            fmt_ptr = self._get_string_constant('%d')  # Use real printf format
            self.builder.call(self.printf, [fmt_ptr, val_ext])
        elif isinstance(val.type, ir.PointerType):  # int type (actually string variable)
            # String variable - use real printf format for strings
            fmt_ptr = self._get_string_constant('%s')
            self.builder.call(self.printf, [fmt_ptr, val])
        else:
            # Default: print as int
            fmt_ptr = self._get_string_constant('%d')
            self.builder.call(self.printf, [fmt_ptr, val])
    
    def _get_string_constant(self, s: str) -> ir.Value:
        """Create a global string constant and return pointer to it"""
        # Convert string to bytes with null terminator
        b = bytearray(s.encode("utf8"))
        b.append(0)
        c = ir.Constant(ir.ArrayType(ir.IntType(8), len(b)), b)
        
        # Create unique global variable name
        name = f"str_{self.string_counter}"
        self.string_counter += 1
        
        # Create global variable
        gvar = ir.GlobalVariable(self.module, c.type, name=name)
        gvar.global_constant = True
        gvar.initializer = c
        
        # Return pointer to first element
        return self.builder.bitcast(gvar, ir.IntType(8).as_pointer())

    
    def generate_expression(self, expr: Expression) -> ir.Value:
        """Generate LLVM IR for an expression"""
        if isinstance(expr, Literal):
            return self.generate_literal(expr)
        
        elif isinstance(expr, Identifier):
            return self.generate_identifier(expr)
        
        elif isinstance(expr, BinaryOp):
            return self.generate_binary_op(expr)
        
        elif isinstance(expr, FunctionCall):
            return self.generate_function_call(expr)
        
        raise CodeGenError(f"Unsupported expression type: {type(expr)}")
    
    def generate_literal(self, lit: Literal) -> ir.Value:
        """Generate literal value"""
        if lit.literal_type == 'int':
            return ir.Constant(ir.IntType(32), int(lit.value))
        elif lit.literal_type == 'float':
            return ir.Constant(ir.DoubleType(), float(lit.value))
        elif lit.literal_type == 'bool':
            return ir.Constant(ir.IntType(1), int(lit.value))
        elif lit.literal_type == 'string':
            # String literals are stored as global constants
            return self._get_string_constant(lit.value)
        else:
            raise CodeGenError(f"Unsupported literal type: {lit.literal_type}")
    
    def generate_identifier(self, ident: Identifier) -> ir.Value:
        """Generate identifier reference (load from memory)"""
        var_ptr = self.variables[ident.name]
        return self.builder.load(var_ptr, name=ident.name)
    
    def generate_binary_op(self, binop: BinaryOp) -> ir.Value:
        """
        Generate binary operation
        APPLIES MAPPING: Confuc-IO operator → conventional operation
        """
        left = self.generate_expression(binop.left)
        right = self.generate_expression(binop.right)
        
        # Map Confuc-IO operator to conventional meaning
        confucio_op = binop.operator
        conventional_op = OPERATOR_MAPPINGS.get(confucio_op, confucio_op)
        
        # Special case: String concatenation with + operator
        if conventional_op == '+':
            # Check if operands are strings (i8*)
            if isinstance(left.type, ir.PointerType) and isinstance(right.type, ir.PointerType):
                return self._concatenate_strings(left, right)
            # Otherwise numeric addition
            return self.builder.add(left, right, name="addtmp")
        
        # Generate appropriate LLVM instruction based on conventional meaning
        elif conventional_op == '-':
            return self.builder.sub(left, right, name="subtmp")
        elif conventional_op == '*':
            return self.builder.mul(left, right, name="multmp")
        elif conventional_op == '/':
            return self.builder.sdiv(left, right, name="divtmp")
        elif conventional_op == '>':
            return self.builder.icmp_signed('>', left, right, name="gttmp")
        elif conventional_op == '<':
            return self.builder.icmp_signed('<', left, right, name="lttmp")
        elif conventional_op == '==':
            # For strings, use strcmp (returns 0 if equal)
            if isinstance(left.type, ir.PointerType) and isinstance(right.type, ir.PointerType):
                return self._compare_strings(left, right)
            # Otherwise numeric comparison
            return self.builder.icmp_signed('==', left, right, name="eqtmp")
        else:
            raise CodeGenError(f"Unsupported operator: {conventional_op}")
    
    def _concatenate_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
        """Concatenate two strings using C stdlib functions"""
        # Get length of both strings
        len_left = self.builder.call(self.strlen, [left])
        len_right = self.builder.call(self.strlen, [right])
        
        # Calculate total length (left + right + 1 for null terminator)
        total_len = self.builder.add(len_left, len_right, name="total_len")
        one = ir.Constant(ir.IntType(64), 1)
        total_len_with_null = self.builder.add(total_len, one, name="total_len_null")
        
        # Allocate memory for result
        result_ptr = self.builder.call(self.malloc, [total_len_with_null])
        
        # Copy first string
        self.builder.call(self.strcpy, [result_ptr, left])
        
        # Concatenate second string
        self.builder.call(self.strcat, [result_ptr, right])
        
        return result_ptr
    
    def _compare_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
        """Compare two strings using strcmp (returns 0 if equal)"""
        # Declare strcmp if not already declared
        if not hasattr(self, 'strcmp'):
            void_ptr = ir.IntType(8).as_pointer()
            strcmp_ty = ir.FunctionType(ir.IntType(32), [void_ptr, void_ptr])
            self.strcmp = ir.Function(self.module, strcmp_ty, name="strcmp")
        
        # Call strcmp
        cmp_result = self.builder.call(self.strcmp, [left, right])
        
        # strcmp returns 0 if equal, so compare result with 0
        zero = ir.Constant(ir.IntType(32), 0)
        return self.builder.icmp_signed('==', cmp_result, zero, name="streqtmp")
    
    def generate_function_call(self, call: FunctionCall) -> ir.Value:
        """Generate function call"""
        func = self.functions.get(call.function_name)
        if not func:
            raise CodeGenError(f"Function '{call.function_name}' not found")
        
        # Generate arguments
        args = [self.generate_expression(arg) for arg in call.arguments]
        
        # Call function
        return self.builder.call(func, args, name="calltmp")
    
    def optimize(self, level: int = 2) -> str:
        """
        Optimize the generated LLVM IR
        
        Args:
            level: Optimization level (0-3)
        
        Returns:
            Optimized LLVM IR as string
        """
        # Parse the IR
        llvm_ir = str(self.module)
        mod = llvm_binding.parse_assembly(llvm_ir)
        mod.verify()
        
        # Create pass manager builder
        pmb = llvm_binding.create_pass_manager_builder()
        pmb.opt_level = level
        
        # Create module pass manager
        pm = llvm_binding.create_module_pass_manager()
        pmb.populate(pm)
        
        # Run optimization
        pm.run(mod)
        
        return str(mod)
    
    def execute(self) -> int:
        """
        Execute the compiled program using JIT (MCJIT)
        
        Returns:
            Exit code from main() function
        """
        # Parse LLVM IR
        llvm_ir = str(self.module)
        mod = llvm_binding.parse_assembly(llvm_ir)
        mod.verify()
        
        # Create target machine
        target = llvm_binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        
        # Create execution engine (MCJIT)
        # MCJIT should automatically resolve C stdlib symbols via the system linker
        backing_mod = llvm_binding.parse_assembly("")
        engine = llvm_binding.create_mcjit_compiler(backing_mod, target_machine)
        
        # Add module and finalize
        engine.add_module(mod)
        engine.finalize_object()
        engine.run_static_constructors()
        
        # Get main() function pointer
        main_ptr = engine.get_function_address("main")
        if main_ptr == 0:
            raise CodeGenError("Could not find main() function")
        
        # Create C function type and call it
        cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)
        result = cfunc()
        
        return result

    
    def generate_executable(self, output_path: str):
        """
        Generate executable from LLVM IR
        
        Note: This requires LLVM tools (llc, clang) to be installed.
        As an alternative, users can manually run:
          1. Save LLVM IR: python3 cli.py program.cio --output-llvm
          2. Compile to object: llc -filetype=obj program.ll -o program.o
          3. Link: clang program.o -o program
        """
        import subprocess
        import tempfile
        import os
        import shutil
        
        # Get LLVM IR
        llvm_ir = str(self.module)
        
        # Write IR to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(llvm_ir)
            ll_file = f.name
        
        # Find llc - try PATH first, then Homebrew location
        llc_cmd = shutil.which('llc')
        if not llc_cmd:
            # Try Homebrew LLVM location on macOS
            homebrew_llc = '/opt/homebrew/opt/llvm/bin/llc'
            if os.path.exists(homebrew_llc):
                llc_cmd = homebrew_llc
            else:
                raise CodeGenError(
                    f"llc not found. Please install LLVM:\\n"
                    f"  macOS: brew install llvm\\n"
                    f"  Then add to PATH: export PATH=\"/opt/homebrew/opt/llvm/bin:$PATH\""
                )
        
        clang_cmd = shutil.which('clang') or 'clang'
        
        try:
            # Try to compile with llc (LLVM compiler)
            obj_file = ll_file.replace('.ll', '.o')
            
            # Step 1: Compile LLVM IR to object file
            result = subprocess.run(
                [llc_cmd, '-filetype=obj', ll_file, '-o', obj_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise CodeGenError(
                    f"llc compilation failed: {result.stderr}\n\n"
                    f"Make sure LLVM is installed. On macOS: brew install llvm"
                )
            
            # Step 2: Link object file to executable
            result = subprocess.run(
                [clang_cmd, obj_file, '-o', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise CodeGenError(
                    f"Linking failed: {result.stderr}\n\n"
                    f"Make sure clang is installed."
                )
            
            print(f"✓ Executable generated: {output_path}")
            
        except FileNotFoundError as e:
            raise CodeGenError(
                f"Required tool not found: {e}\n\n"
                f"To generate executables, you need:\n"
                f"  - llc (LLVM compiler): brew install llvm\n"
                f"  - clang (linker): xcode-select --install\n\n"
                f"Alternatively, compile manually:\n"
                f"  1. python3 cli.py {output_path}.cio --output-llvm\n"
                f"  2. llc -filetype=obj {output_path}.ll -o {output_path}.o\n"
                f"  3. clang {output_path}.o -o {output_path}"
            )
        finally:
            # Clean up temporary files
            for temp_file in [ll_file, obj_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)


if __name__ == '__main__':
    # Test code generator
    from confucio_ast import *
    
    # Create simple program
    program = Program(
        functions=[
            FunctionDef(
                return_type='Float',
                name='side',
                parameters=[],
                body=[
                    VarDeclaration(
                        var_type='Float',
                        name='x',
                        initializer=Literal(value=5, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='y',
                        initializer=Literal(value=3, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='z',
                        initializer=BinaryOp(
                            operator='/',  # / in Confuc-IO = addition
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    ReturnStatement(value=Identifier(name='z'))
                ]
            )
        ]
    )
    
    codegen = CodeGenerator()
    try:
        ir_code = codegen.generate(program)
        print("Generated LLVM IR:")
        print(ir_code)
    except CodeGenError as e:
        print(f"Code generation error: {e}")
