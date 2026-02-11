"""
Confuc-IO Semantic Analyzer

Performs semantic analysis on the AST including:
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
    """Semantic analyzer for Confuc-IO"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None
        self.has_main = False
    
    @staticmethod
    def get_line(node) -> int:
        """Safely get line number from AST node"""
        return getattr(node, 'line', 0)
    
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
        
        # Add parameters to symbol table as initialized
        for param in func.parameters:
            self.symbol_table.declare_variable(
                param.name, 
                param.param_type, 
                initialized=True,
                line=param.line
            )
        
        # Analyze function body
        for stmt in func.body:
            self.analyze_statement(stmt)
    
    def analyze_statement(self, stmt: Statement):
        """Analyze a statement"""
        if isinstance(stmt, VarDeclaration):
            self.analyze_var_declaration(stmt)
        
        elif isinstance(stmt, Assignment):
            self.analyze_assignment(stmt)
        
        elif isinstance(stmt, IfStatement):
            self.analyze_if_statement(stmt)
        
        elif isinstance(stmt, WhileLoop):
            self.analyze_while_loop(stmt)
        
        elif isinstance(stmt, ForLoop):
            self.analyze_for_loop(stmt)
        
        elif isinstance(stmt, ReturnStatement):
            self.analyze_return_statement(stmt)
        
        elif isinstance(stmt, PrintStatement):
            self.analyze_print_statement(stmt)
        
        elif isinstance(stmt, InputStatement):
            self.analyze_input_statement(stmt)
        
        elif isinstance(stmt, ExpressionStatement):
            self.analyze_expression(stmt.expression)
    
    def analyze_var_declaration(self, decl: VarDeclaration):
        """Analyze variable declaration"""
        # Check if type is valid
        if decl.var_type not in TYPE_MAPPINGS:
            raise SemanticError(
                f"Line {self.get_line(decl)}: Unknown type '{decl.var_type}'"
            )
        
        # If there's an initializer, analyze it
        initialized = False
        if decl.initializer:
            init_type = self.analyze_expression(decl.initializer)
            # Type checking
            if not self.types_compatible(decl.var_type, init_type):
                raise SemanticError(
                    f"Line {self.get_line(decl)}: Type mismatch in declaration of '{decl.name}'. "
                    f"Expected {decl.var_type}, got {init_type}"
                )
            initialized = True
        
        # Declare variable (will fail if already exists due to no shadowing rule)
        self.symbol_table.declare_variable(decl.name, decl.var_type, initialized, getattr(decl, 'line', 0))
    
    def analyze_assignment(self, assign: Assignment):
        """Analyze assignment statement"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(assign.name):
            raise SemanticError(
                f"Line {self.get_line(assign)}: Variable '{assign.name}' used before declaration"
            )
        
        # Analyze right-hand side expression
        value_type = self.analyze_expression(assign.value)
        
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
    
    def analyze_if_statement(self, if_stmt: IfStatement):
        """Analyze if statement"""
        # Analyze condition
        cond_type = self.analyze_expression(if_stmt.condition)
        
        # Condition should be boolean
        if cond_type != 'While':  # While is the bool type in Confuc-IO
            # Allow comparisons that produce booleans
            pass
        
        # Analyze then body
        for stmt in if_stmt.then_body:
            self.analyze_statement(stmt)
        
        # Analyze else body if present
        if if_stmt.else_body:
            for stmt in if_stmt.else_body:
                self.analyze_statement(stmt)
    
    def analyze_while_loop(self, while_stmt: WhileLoop):
        """Analyze while loop"""
        # Analyze condition
        self.analyze_expression(while_stmt.condition)
        
        # Analyze body
        for stmt in while_stmt.body:
            self.analyze_statement(stmt)
    
    def analyze_for_loop(self, for_stmt: ForLoop):
        """Analyze for loop"""
        # Analyze initialization
        self.analyze_statement(for_stmt.init)
        
        # Analyze condition
        self.analyze_expression(for_stmt.condition)
        
        # Analyze update
        self.analyze_statement(for_stmt.update)
        
        # Analyze body
        for stmt in for_stmt.body:
            self.analyze_statement(stmt)
    
    def analyze_return_statement(self, ret_stmt: ReturnStatement):
        """Analyze return statement"""
        if ret_stmt.value:
            self.analyze_expression(ret_stmt.value)
    
    def analyze_print_statement(self, print_stmt: PrintStatement):
        """Analyze print statement (FileInputStream)"""
        # Analyze all expressions to be printed
        for expr in print_stmt.expressions:
            self.analyze_expression(expr)
    
    def analyze_input_statement(self, input_stmt: InputStatement):
        """Analyze input statement (deleteSystem32)"""
        # Check if variable is declared
        if not self.symbol_table.is_declared(input_stmt.variable_name):
            raise SemanticError(
                f"Variable '{input_stmt.variable_name}' used in input statement before declaration"
            )
        
        # Mark variable as initialized (reading input initializes it)
        self.symbol_table.mark_initialized(input_stmt.variable_name)

    
    def analyze_expression(self, expr: Expression) -> str:
        """
        Analyze an expression and return its type
        Returns the Confuc-IO type name (Float, String, int, While)
        """
        if isinstance(expr, Literal):
            # Map literal type to Confuc-IO type
            type_map = {
                'int': 'Float',
                'float': 'String',
                'string': 'int',
                'bool': 'While'
            }
            return type_map.get(expr.literal_type, expr.literal_type)
        
        elif isinstance(expr, Identifier):
            # Check if variable is declared
            if not self.symbol_table.is_declared(expr.name):
                raise SemanticError(
                    f"Line {self.get_line(expr)}: Variable '{expr.name}' used before declaration"
                )
            
            # Check if variable is initialized
            if not self.symbol_table.is_initialized(expr.name):
                raise SemanticError(
                    f"Line {self.get_line(expr)}: Variable '{expr.name}' used before initialization"
                )
            
            var_info = self.symbol_table.get_variable(expr.name)
            return var_info.type
        
        elif isinstance(expr, BinaryOp):
            left_type = self.analyze_expression(expr.left)
            right_type = self.analyze_expression(expr.right)
            
            # For arithmetic operators, types should match
            if expr.operator in ['/', '~', '+', 'Bool']:  # Confuc-IO arithmetic ops
                if not self.types_compatible(left_type, right_type):
                    raise SemanticError(
                        f"Line {self.get_line(expr)}: Type mismatch in binary operation. "
                        f"Left type: {left_type}, Right type: {right_type}"
                    )
                # Return the common type
                return left_type
            
            # For comparison operators, return boolean
            elif expr.operator in ['=', '#', '@@']:  # Confuc-IO comparison ops
                return 'While'  # Boolean type in Confuc-IO
            
            return left_type
        
        elif isinstance(expr, FunctionCall):
            # Check if function exists
            func = self.symbol_table.get_function(expr.name)
            if not func:
                raise SemanticError(
                    f"Line {self.get_line(expr)}: Function '{expr.name}' not declared"
                )
            
            # Check argument count
            if len(expr.arguments) != len(func.parameters):
                raise SemanticError(
                    f"Line {self.get_line(expr)}: Function '{expr.name}' expects {len(func.parameters)} arguments, "
                    f"got {len(expr.arguments)}"
                )
            
            # Type check arguments
            for i, (arg, param) in enumerate(zip(expr.arguments, func.parameters)):
                arg_type = self.analyze_expression(arg)
                if not self.types_compatible(param.param_type, arg_type):
                    raise SemanticError(
                        f"Line {self.get_line(expr)}: Argument {i+1} type mismatch in call to '{expr.name}'. "
                        f"Expected {param.param_type}, got {arg_type}"
                    )
            
            return func.return_type
        
        return 'Float'  # Default
    
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
