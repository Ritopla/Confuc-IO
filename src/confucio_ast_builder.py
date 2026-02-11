"""
Confuc-IO AST Builder

Transforms Lark parse tree into Confuc-IO AST nodes.
This bridges the parser output with semantic analysis and code generation.
"""

from lark import Transformer, Token, Tree
from confucio_ast import *


class ASTBuilderError(Exception):
    """Raised when AST building fails"""
    pass


class ConfucIOASTBuilder(Transformer):
    """
    Lark Transformer that converts parse tree to Confuc-IO AST.
    
    Each method corresponds to a grammar rule and returns an AST node.
    """
    
    # Top-level program
    def start(self, items):
        """start: function_def+"""
        functions = [item for item in items if isinstance(item, FunctionDef)]
        return Program(functions=functions)
    
    # Function definition
    def function_def(self, items):
        """function_def: type IDENTIFIER delim_lparen parameters? delim_rparen delim_lbrace statement* delim_rbrace"""
        return_type = str(items[0])
        
        # Name might be an Identifier node or string
        name_item = items[1]
        name = name_item.name if isinstance(name_item, Identifier) else str(name_item)
        
        # Find parameters (optional)
        parameters = []
        statements = []
        
        for item in items[2:]:
            if isinstance(item, list):
                # Could be parameters or statements
                if item and isinstance(item[0], Parameter):
                    parameters = item
                else:
                    statements.extend(item)
            elif isinstance(item, Statement):
                statements.append(item)
        
        return FunctionDef(
            return_type=return_type,
            name=name,
            parameters=parameters,
            body=statements
        )
    
    def parameters(self, items):
        """parameters: parameter (COMMA parameter)*"""
        return items
    
    def parameter(self, items):
        """parameter: type IDENTIFIER"""
        param_type = str(items[0])
        name = str(items[1])
        return Parameter(param_type=param_type, name=name)
    
    # Statements
    def statement(self, items):
        """statement: var_declaration | assignment | if_statement | while_loop | for_loop | return_statement | expression_statement"""
        return items[0]
    
    def var_declaration(self, items):
        """var_declaration: type IDENTIFIER (op_assign expression)?"""
        var_type = str(items[0])
        # Name might be an Identifier node or string
        name_item = items[1]
        name = name_item.name if isinstance(name_item, Identifier) else str(name_item)
        
        # If there's an initializer, it's after the operator
        # items = [type, name, operator_str, expression] or [type, name]
        # The operator returns '@' string, the expression returns an Expression node
        initializer = None
        for item in items[2:]:
            # Look for Expression nodes (Literal, Identifier, BinaryOp, etc.)
            if isinstance(item, Expression):
                initializer = item
                break
        
        return VarDeclaration(var_type=var_type, name=name, initializer=initializer)
    
    def assignment(self, items):
        """assignment: IDENTIFIER op_assign expression"""
        # Name might be an Identifier node or string
        name_item = items[0]
        name = name_item.name if isinstance(name_item, Identifier) else str(name_item)
        
        # Value is after the operator
        # items = [name, operator, expression]
        value = None
        for item in items[1:]:
            # Look for Expression nodes
            if isinstance(item, Expression):
                value = item
                break
        
        return Assignment(name=name, value=value)
    
    def if_statement(self, items):
        """if_statement: KEYWORD_FUNC delim_lparen expression delim_rparen delim_lbrace statement* delim_rbrace (ELSE delim_lbrace statement* delim_rbrace)?"""
        # Items contains: [expression, statement*, ...]
        # Extract the condition expression (should be first Expression node)
        condition = None
        statements = []
        
        for item in items:
            if condition is None and isinstance(item, Expression):
                condition = item
            elif isinstance(item, Statement):
                statements.append(item)
        
        # Split statements into then_body and else_body
        # For now, all statements go to then_body (else not fully implemented)
        then_body = statements
        else_body = []
        
        return IfStatement(condition=condition, then_body=then_body, else_body=else_body)
    
    def while_loop(self, items):
        """while_loop: KEYWORD_RETURN delim_lparen expression delim_rparen delim_lbrace statement* delim_rbrace"""
        # Items contains: [expression, statement*, ...]
        # Extract condition (first Expression) and body (all Statements)
        condition = None
        body = []
        
        for item in items:
            if condition is None and isinstance(item, Expression):
                condition = item
            elif isinstance(item, Statement):
                body.append(item)
        
        return WhileLoop(condition=condition, body=body)
    
    def for_loop(self, items):
        """for_loop: KEYWORD_IF delim_lparen statement SEMICOLON expression SEMICOLON statement delim_rparen delim_lbrace statement* delim_rbrace"""
        # Items contains: [init_statement, expression, update_statement, body_statements*]
        # Extract in order: init (Statement), condition (Expression), update (Statement), body (Statements)
        init = None
        condition = None
        update = None
        body = []
        
        statements_found = 0
        for item in items:
            if isinstance(item, Statement):
                if init is None:
                    init = item
                    statements_found += 1
                elif update is None and statements_found == 1:
                    update = item
                    statements_found += 1
                else:
                    body.append(item)
            elif isinstance(item, Expression) and condition is None:
                condition = item
        
        return ForLoop(init=init, condition=condition, update=update, body=body)
    
    def return_statement(self, items):
        """return_statement: KEYWORD_STAR expression?"""
        # Items might be [keyword_token, expression] or just [keyword_token]
        # Filter out strings and None
        value = None
        for item in items:
            if item is not None and not isinstance(item, str) and not isinstance(item, Token):
                value = item
                break
        return ReturnStatement(value=value)
    
    def print_statement(self, items):
        """print_statement: FileInputStream delim_lparen expression (COMMA expression)* delim_rparen"""
        # Extract all Expression nodes from items
        expressions = [item for item in items if isinstance(item, Expression)]
        return PrintStatement(expressions=expressions)
    
    def input_statement(self, items):
        """input_statement: deleteSystem32 delim_lparen IDENTIFIER delim_rparen"""
        # Extract identifier (could be an Identifier node or Token)
        for item in items:
            if isinstance(item, Identifier):
                return InputStatement(variable_name=item.name)
            elif isinstance(item, Token) and item.type == 'IDENTIFIER':
                return InputStatement(variable_name=item.value)
        # Fallback: use string representation
        var_name = str(items[0]) if items else 'unknown'
        return InputStatement(variable_name=var_name)

    
    def expression_statement(self, items):
        """expression_statement: expression"""
        return ExpressionStatement(expression=items[0])
    
    # Expressions
    def expression(self, items):
        """expression: logical_or"""
        return items[0]
    
    def logical_or(self, items):
        """logical_or: logical_and (OP_OR logical_and)*"""
        if len(items) == 1:
            return items[0]
        # Build binary operation tree
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryOp(operator='||', left=result, right=items[i])
        return result
    
    def logical_and(self, items):
        """logical_and: equality (OP_AND equality)*"""
        if len(items) == 1:
            return items[0]
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryOp(operator='&&', left=result, right=items[i])
        return result
    
    def equality(self, items):
        """equality: comparison (op_equality comparison)*"""
        if len(items) == 1:
            return items[0]
        # items should be [expr, op, expr, op, expr, ...]
        if len(items) == 2:
            return BinaryOp(operator=str(items[0]), left=items[0], right=items[1])
        # For simplicity, just handle first comparison
        return items[0]
    
    def comparison(self, items):
        """comparison: additive (op_comparison additive)*"""
        if len(items) == 1:
            return items[0]
        
        # Build left-associative binary operations
        result = items[0]
        i = 1
        while i < len(items):
            if i + 1 < len(items):
                operator = str(items[i]) if isinstance(items[i], str) else None
                if operator:
                    result = BinaryOp(operator=operator, left=result, right=items[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        return result
    
    def additive(self, items):
        """additive: multiplicative (op_add multiplicative)*"""
        # Filter out None and Token objects
        filtered = [item for item in items if item is not None and not isinstance(item, Token)]
        if len(filtered) == 1:
            return filtered[0]
        
        # Items are [left_expr, operator_str, right_expr]
        # Build left-associative: ((a + b) + c)
        result = filtered[0]
        i = 1
        while i + 1 < len(filtered):
            operator = filtered[i] if isinstance(filtered[i], str) else '/'
            right = filtered[i + 1]
            result = BinaryOp(operator=operator, left=result, right=right)
            i += 2
        return result
    
    def multiplicative(self, items):
        """multiplicative: unary (op_multiply unary)*"""
        # Filter out None and Token objects
        filtered = [item for item in items if item is not None and not isinstance(item, Token)]
        if len(filtered) == 1:
            return filtered[0]
        
        result = filtered[0]
        i = 1
        while i + 1 < len(filtered):
            operator = filtered[i] if isinstance(filtered[i], str) else '+'
            right = filtered[i + 1]
            result = BinaryOp(operator=operator, left=result, right=right)
            i += 2
        return result
    
    def unary(self, items):
        """unary: (OP_NOT | OP_TILDE) unary | primary"""
        if len(items) == 1:
            return items[0]
        # Unary operation
        operator = str(items[0])
        operand = items[1]
        return UnaryOp(operator=operator, operand=operand)
    
    def primary(self, items):
        """primary: literal | IDENTIFIER | function_call | delim_lparen expression delim_rparen"""
        # Filter out None values (from delimiters)
        filtered = [item for item in items if item is not None]
        return filtered[0] if filtered else items[0]
    
    def function_call(self, items):
        """function_call: IDENTIFIER delim_lparen arguments? delim_rparen"""
        # First item is the identifier (already an Identifier AST node)
        name_node = items[0]
        name = name_node.name if isinstance(name_node, Identifier)  else str(name_node)
        
        # Find arguments (filter out None from delimiters)
        arguments = []
        for item in items[1:]:
            if isinstance(item, list):
                arguments = item
                break
        
        return FunctionCall(name=name, arguments=arguments)
    
    def arguments(self, items):
        """arguments: expression (COMMA expression)*"""
        return items
    
    def literal(self, items):
        """literal: NUMBER | FLOAT | STRING | BOOL"""
        # Now literals are already created by terminal handlers
        return items[0]
    
    # Types
    def type(self, items):
        """type: TYPE_FLOAT | TYPE_INT | TYPE_STRING | TYPE_WHILE"""
        if isinstance(items[0], Token):
            return items[0].value
        return str(items[0])
    
    # Operators - these are terminal tokens, handle them directly
    def op_assign(self, items):
        """op_assign: OP_AT"""
        return '@'
    
    def op_equality(self, items):
        """op_equality: OP_DOUBLE_AT | OP_NOT_EQUAL"""
        return '@@' if not items else str(items[0])
    
    def op_comparison(self, items):
        """op_comparison: OP_EQUALS | OP_HASH | OP_LESS_EQUAL | OP_GREATER_EQUAL"""
        return '=' if not items else str(items[0])
    
    def op_add(self, items):
        """op_add: OP_SLASH | OP_TILDE"""
        # These are tokens that match directly
        return '/'  # Default, will be overridden by actual token
    
    def op_multiply(self, items):
        """op_multiply: OP_PLUS | OP_BOOL"""
        return '+' if not items else str(items[0])
    
    # Delimiters - we ignore these in the AST
    def delim_lparen(self, items):
        return None
    
    def delim_rparen(self, items):
        return None
    
    def delim_lbrace(self, items):
        return None
    
    def delim_rbrace(self, items):
        return None
    
    # Terminals - convert tokens to strings/values
    def IDENTIFIER(self, token):
        """Convert identifier token to string"""
        return Identifier(name=token.value)
    
    def INTEGER(self, token):
        """Convert integer token to Literal node"""
        return Literal(value=int(token.value), literal_type='int')
    
    def FLOAT_LITERAL(self, token):
        """Convert float token to Literal node"""
        return Literal(value=float(token.value), literal_type='float')
    
    def STRING_LITERAL(self, token):
        """Convert string token to Literal node"""
        # Remove quotes
        string_value = token.value[1:-1] if token.value.startswith('"') else token.value
        return Literal(value=string_value, literal_type='string')
    
    def BOOL(self, token):
        """Convert bool token to Literal node"""
        return Literal(value=token.value.lower() == 'true', literal_type='bool')
    
    # Handle operator tokens directly
    def OP_SLASH(self, token):
        return '/'
    
    def OP_TILDE(self, token):
        return '~'
    
    def OP_PLUS(self, token):
        return '+'
    
    def OP_BOOL(self, token):
        return 'Bool'
    
    def OP_EQUALS(self, token):
        return '='
    
    def OP_HASH(self, token):
        return '#'
    
    def OP_DOUBLE_AT(self, token):
        return '@@'
    
    def OP_AT(self, token):
        return '@'


def build_ast(parse_tree):
    """
    Build Confuc-IO AST from Lark parse tree
    
    Args:
        parse_tree: Lark Tree object from parser
        
    Returns:
        Program AST node
    """
    builder = ConfucIOASTBuilder()
    try:
        ast = builder.transform(parse_tree)
        return ast
    except Exception as e:
        raise ASTBuilderError(f"Failed to build AST: {e}") from e


if __name__ == '__main__':
    # Test AST builder
    from confucio_parser import ConfucIOParser
    
    test_code = """
    Float side {] [
        Float x @ 5
        Float y @ 3
        Float z @ x / y
        * z
    )
    """
    
    parser = ConfucIOParser()
    parse_tree = parser.parse(test_code)
    
    print("Parse tree:")
    print(parse_tree.pretty())
    print("\n" + "="*60 + "\n")
    
    ast = build_ast(parse_tree)
    
    print("Built AST:")
    print(f"Program with {len(ast.functions)} function(s)")
    for func in ast.functions:
        print(f"\nFunction: {func.name}")
        print(f"  Return type: {func.return_type}")
        print(f"  Parameters: {len(func.parameters)}")
        print(f"  Statements: {len(func.body)}")
        for stmt in func.body:
            print(f"    - {type(stmt).__name__}")
