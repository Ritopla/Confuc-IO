"""
Confuc-IO Semantic Analyzer

Performs semantic analysis on the AST using a reflection-based visitor pattern.
Each AST node type is handled by a visit_<ClassName> method, dispatched via getattr.

Checks include:
- Identifier declaration checking
- No shadowing enforcement (single global scope)
- Variable initialization verification before use
- Type checking with mapped types
- Symbol table management
"""

from typing import Dict, Set, Optional, List
from confucio_ast import *
from confucio_mappings import MAIN_FUNCTION_NAME, TYPE_MAPPINGS


class SemanticError(Exception):
    """Raised when semantic analysis fails"""
    pass


class SymbolInfo:
    """Information about a symbol in the symbol table"""
    def __init__(self, name: str, symbol_type: str, is_initialized: bool = False, line: int = 0):
        self.name = name
        self.type = symbol_type
        self.is_initialized = is_initialized
        self.line = line  # Line where declared
    
    def __repr__(self):
        init_status = "initialized" if self.is_initialized else "uninitialized"
        return f"Symbol({self.name}, {self.type}, {init_status}, line {self.line})"


class SymbolTable:
    """
    Symbol table for Confuc-IO
    Enforces single global scope with no shadowing
    """
    def __init__(self):
        self.symbols: Dict[str, SymbolInfo] = {}
        self.functions: Dict[str, FunctionDef] = {}
    
    def declare_variable(self, name: str, var_type: str, initialized: bool, line: int):
        """Declare a variable - fails if already exists (no shadowing)"""
        if name in self.symbols:
            raise SemanticError(
                f"Line {line}: Variable '{name}' already declared at line {self.symbols[name].line}. "
                f"Shadowing is not allowed in Confuc-IO (single global scope)."
            )
        
        self.symbols[name] = SymbolInfo(name, var_type, initialized, line)
    
    def get_variable(self, name: str) -> Optional[SymbolInfo]:
        """Get variable info"""
        return self.symbols.get(name)
    
    def mark_initialized(self, name: str):
        """Mark a variable as initialized"""
        if name in self.symbols:
            self.symbols[name].is_initialized = True
    
    def is_declared(self, name: str) -> bool:
        """Check if variable is declared"""
        return name in self.symbols
    
    def is_initialized(self, name: str) -> bool:
        """Check if variable is initialized"""
        if name not in self.symbols:
            return False
        return self.symbols[name].is_initialized
    
    def declare_function(self, name: str, func_def: FunctionDef):
        """Declare a function"""
        if name in self.functions:
            raise SemanticError(
                f"Line {func_def.line}: Function '{name}' already declared. "
                f"No shadowing allowed."
            )
        self.functions[name] = func_def
    
    def get_function(self, name: str) -> Optional[FunctionDef]:
        """Get function definition"""
        return self.functions.get(name)


class SemanticAnalyzer:
    """
    Semantic analyzer for Confuc-IO.
    
    Uses a reflection-based visitor pattern: for each AST node of type Foo,
    the method visit_Foo is looked up via getattr and called.
    """
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None
        self.has_main = False
    
    @staticmethod
    def get_line(node) -> int:
        """Safely get line number from AST node"""
        return getattr(node, 'line', 0)
    
    def visit(self, node):
        """
        Dispatch to the appropriate visit_<ClassName> method via reflection.
        
        For statement nodes, returns None.
        For expression nodes, returns the Confuc-IO type name (str).
        """
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise SemanticError(f"No visitor method for AST node type: {type(node).__name__}")
        return visitor(node)
    
    def analyze(self, ast: Program):
        """Perform semantic analysis on the program"""
        # First pass: collect all function declarations
        for func in ast.functions:
            self.symbol_table.declare_function(func.name, func)
            
            # Check if this is the main function
            if func.name == MAIN_FUNCTION_NAME:
                self.has_main = True
                # Verify main function signature
                if func.parameters:
                    raise SemanticError(
                        f"Line {self.get_line(func)}: Main function '{MAIN_FUNCTION_NAME}' must have no parameters"
                    )
        
        # Verify main function exists
        if not self.has_main:
            raise SemanticError(
                f"Program must have a main function named '{MAIN_FUNCTION_NAME}'"
            )
        
        # Second pass: analyze function bodies
        for func in ast.functions:
            self.analyze_function(func)
    
    def analyze_function(self, func: FunctionDef):
        """Analyze a function definition"""
        self.current_function = func
        
        # Save current variables (parameters should be function-local)
        saved_variables = self.symbol_table.symbols.copy()
        
        # Add parameters to symbol table as initialized
        for param in func.parameters:
            self.symbol_table.declare_variable(
                param.name, 
                param.param_type, 
                initialized=True,
                line=param.line
            )
        
        # Analyze function body using visitor dispatch
        for stmt in func.body:
            self.visit(stmt)
        
        # Restore variables (remove parameters from global scope)
        self.symbol_table.symbols = saved_variables
    
    # ── Statement visitors ──────────────────────────────────────────
    
    def visit_VarDeclaration(self, decl: VarDeclaration):
        """Visit variable declaration"""
        # Check if type is valid
        if decl.var_type not in TYPE_MAPPINGS:
            raise SemanticError(
                f"Line {self.get_line(decl)}: Unknown type '{decl.var_type}'"
            )
        
        # If there's an initializer, analyze it
        initialized = False
        if decl.initializer:
            init_type = self.visit(decl.initializer)
            # Type checking
            if not self.types_compatible(decl.var_type, init_type):
                raise SemanticError(
                    f"Line {self.get_line(decl)}: Type mismatch in declaration of '{decl.name}'. "
                    f"Expected {decl.var_type}, got {init_type}"
                )
            initialized = True
        
        # Declare variable (will fail if already exists due to no shadowing rule)
        self.symbol_table.declare_variable(decl.name, decl.var_type, initialized, getattr(decl, 'line', 0))
    
    def visit_Assignment(self, assign: Assignment):
        """Visit assignment statement"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(assign.name):
            raise SemanticError(
                f"Line {self.get_line(assign)}: Variable '{assign.name}' used before declaration"
            )
        
        # Analyze right-hand side expression
        value_type = self.visit(assign.value)
        
        # Get variable type
        var_info = self.symbol_table.get_variable(assign.name)
        
        # Type checking
        if not self.types_compatible(var_info.type, value_type):
            raise SemanticError(
                f"Line {self.get_line(assign)}: Type mismatch in assignment to '{assign.name}'. "
                f"Expected {var_info.type}, got {value_type}"
            )
        
        # Mark as initialized
        self.symbol_table.mark_initialized(assign.name)
    
    def visit_IfStatement(self, if_stmt: IfStatement):
        """Visit if statement"""
        # Analyze condition
        cond_type = self.visit(if_stmt.condition)
        
        # Condition should be boolean
        if cond_type != 'While':  # While is the bool type in Confuc-IO
            # Allow comparisons that produce booleans
            pass
        
        # Analyze then body
        for stmt in if_stmt.then_body:
            self.visit(stmt)
        
        # Analyze else body if present
        if if_stmt.else_body:
            for stmt in if_stmt.else_body:
                self.visit(stmt)
    
    def visit_WhileLoop(self, while_stmt: WhileLoop):
        """Visit while loop"""
        # Analyze condition
        self.visit(while_stmt.condition)
        
        # Analyze body
        for stmt in while_stmt.body:
            self.visit(stmt)
    
    def visit_ForLoop(self, for_stmt: ForLoop):
        """Visit for loop"""
        # Analyze initialization
        self.visit(for_stmt.init)
        
        # Analyze condition
        self.visit(for_stmt.condition)
        
        # Analyze update
        self.visit(for_stmt.update)
        
        # Analyze body
        for stmt in for_stmt.body:
            self.visit(stmt)
    
    def visit_ReturnStatement(self, ret_stmt: ReturnStatement):
        """Visit return statement"""
        if ret_stmt.value:
            self.visit(ret_stmt.value)
    
    def visit_PrintStatement(self, print_stmt: PrintStatement):
        """Visit print statement (FileInputStream)"""
        # Analyze all expressions to be printed
        for expr in print_stmt.expressions:
            self.visit(expr)
    
    def visit_InputStatement(self, input_stmt: InputStatement):
        """Visit input statement (deleteSystem32)"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(input_stmt.variable_name):
            raise SemanticError(
                f"Variable '{input_stmt.variable_name}' used in input statement before declaration"
            )
        
        # Mark variable as initialized (reading input initializes it)
        self.symbol_table.mark_initialized(input_stmt.variable_name)

    def visit_ExpressionStatement(self, stmt: ExpressionStatement):
        """Visit expression used as statement"""
        self.visit(stmt.expression)
    
    # ── Expression visitors ─────────────────────────────────────────
    
    def visit_Literal(self, lit: Literal) -> str:
        """Visit literal — returns Confuc-IO type name"""
        # Map literal type to Confuc-IO type
        type_map = {
            'int': 'Float',
            'float': 'String',
            'string': 'int',
            'bool': 'While'
        }
        return type_map.get(lit.literal_type, lit.literal_type)
    
    def visit_Identifier(self, ident: Identifier) -> str:
        """Visit identifier — returns Confuc-IO type name"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(ident.name):
            raise SemanticError(
                f"Line {self.get_line(ident)}: Variable '{ident.name}' used before declaration"
            )
        
        # Check if variable is initialized
        if not self.symbol_table.is_initialized(ident.name):
            raise SemanticError(
                f"Line {self.get_line(ident)}: Variable '{ident.name}' used before initialization"
            )
        
        var_info = self.symbol_table.get_variable(ident.name)
        return var_info.type
    
    def visit_BinaryOp(self, binop: BinaryOp) -> str:
        """Visit binary operation — returns Confuc-IO type name"""
        left_type = self.visit(binop.left)
        right_type = self.visit(binop.right)
        
        # For arithmetic operators, types should match
        if binop.operator in ['/', '~', '+', 'Bool']:  # Confuc-IO arithmetic ops
            if not self.types_compatible(left_type, right_type):
                raise SemanticError(
                    f"Line {self.get_line(binop)}: Type mismatch in binary operation. "
                    f"Left type: {left_type}, Right type: {right_type}"
                )
            # Return the common type
            return left_type
        
        # For comparison operators, return boolean
        elif binop.operator in ['=', '#', '@@']:  # Confuc-IO comparison ops
            return 'While'  # Boolean type in Confuc-IO
        
        return left_type
    
    def visit_FunctionCall(self, call: FunctionCall) -> str:
        """Visit function call — returns Confuc-IO type name"""
        # Check if function exists
        func = self.symbol_table.get_function(call.function_name)
        if func is None:
            raise SemanticError(
                f"Line {self.get_line(call)}: Undefined function '{call.function_name}'"
            )
        
        # Check argument count
        if len(call.arguments) != len(func.parameters):
            raise SemanticError(
                f"Line {self.get_line(call)}: Function '{call.function_name}' expects {len(func.parameters)} arguments, "
                f"got {len(call.arguments)}"
            )
        
        # Type check arguments
        for i, (arg, param) in enumerate(zip(call.arguments, func.parameters)):
            arg_type = self.visit(arg)
            if not self.types_compatible(param.param_type, arg_type):
                raise SemanticError(
                    f"Line {self.get_line(call)}: Argument {i+1} type mismatch in call to '{call.function_name}'. "
                    f"Expected {param.param_type}, got {arg_type}"
                )
        
        return func.return_type
    
    # ── Helpers ─────────────────────────────────────────────────────
    
    def types_compatible(self, expected: str, actual: str) -> bool:
        """Check if two types are compatible"""
        # Exact match
        if expected == actual:
            return True
        
        # In Confuc-IO, Float can accept int or string
        # But we'll be strict for now
        return False
    
    def print_symbol_table(self):
        """Print the symbol table for debugging"""
        print("\n=== Symbol Table ===")
        print("\nVariables:")
        for name, info in self.symbol_table.symbols.items():
            print(f"  {info}")
        print("\nFunctions:")
        for name, func in self.symbol_table.functions.items():
            print(f"  {name}: {func.return_type}")


if __name__ == '__main__':
    # Test semantic analyzer
    from confucio_ast import *
    
    # Create a simple program AST
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
                    Assignment(
                        name='x',
                        value=Literal(value=10, literal_type='int')
                    ),
                    ReturnStatement(value=Identifier(name='x'))
                ]
            )
        ]
    )
    
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(program)
        print("✓ Semantic analysis passed!")
        analyzer.print_symbol_table()
    except SemanticError as e:
        print(f"✗ Semantic error: {e}")
