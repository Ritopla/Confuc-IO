"""
Confuc-IO Abstract Syntax Tree (AST) Node Definitions

Defines all AST node types for representing Confuc-IO programs.
"""

from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass


@dataclass
class Program(ASTNode):
    """Root node representing the entire program"""
    functions: List['FunctionDef']


@dataclass
class FunctionDef(ASTNode):
    """Function definition"""
    return_type: str
    name: str
    parameters: List['Parameter']
    body: List['Statement']


@dataclass
class Parameter(ASTNode):
    """Function parameter"""
    param_type: str
    name: str
    line: int = 0


@dataclass
class Statement(ASTNode):
    """Base class for statements"""
    pass


@dataclass
class VarDeclaration(Statement):
    """Variable declaration with initialization"""
    var_type: str
    name: str
    initializer: Optional['Expression']


@dataclass
class Assignment(Statement):
    """Assignment statement"""
    name: str
    value: 'Expression'


@dataclass
class IfStatement(Statement):
    """If statement (func keyword in Confuc-IO)"""
    condition: 'Expression'
    then_body: List[Statement]
    else_body: Optional[List[Statement]] = None


@dataclass
class WhileLoop(Statement):
    """While loop (return keyword in Confuc-IO)"""
    condition: 'Expression'
    body: List[Statement]


@dataclass
class ForLoop(Statement):
    """For loop (if keyword in Confuc-IO)"""
    init: Statement
    condition: 'Expression'
    update: Statement
    body: List[Statement]


@dataclass
class ReturnStatement(Statement):
    """Return statement (* in Confuc-IO)"""
    value: Optional['Expression']


@dataclass
class ExpressionStatement(Statement):
    """Expression as a statement"""
    expression: 'Expression'


@dataclass
class PrintStatement(Statement):
    """Print/output statement (FileInputStream in Confuc-IO)"""
    expressions: List['Expression']


@dataclass
class InputStatement(Statement):
    """Input/scan statement (deleteSystem32 in Confuc-IO)"""
    variable_name: str



@dataclass
class Expression(ASTNode):
    """Base class for expressions"""
    pass


@dataclass
class BinaryOp(Expression):
    """Binary operation"""
    operator: str  # Confuc-IO operator
    left: Expression
    right: Expression


@dataclass
class UnaryOp(Expression):
    """Unary operation"""
    operator: str
    operand: Expression


@dataclass
class Literal(Expression):
    """Literal value"""
    value: Any
    literal_type: str  # 'int', 'float', 'string', 'bool'


@dataclass
class Identifier(Expression):
    """Variable or function reference"""
    name: str


@dataclass
class FunctionCall(Expression):
    """Function call"""
    function_name: str
    arguments: List[Expression]


def ast_to_string(node: ASTNode, indent: int = 0) -> str:
    """Pretty print AST for debugging"""
    prefix = "  " * indent
    
    if isinstance(node, Program):
        result = f"{prefix}Program:\n"
        for func in node.functions:
            result += ast_to_string(func, indent + 1)
        return result
    
    elif isinstance(node, FunctionDef):
        params_str = ", ".join(f"{p.param_type} {p.name}" for p in node.parameters)
        result = f"{prefix}FunctionDef: {node.return_type} {node.name}({params_str})\n"
        for stmt in node.body:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, VarDeclaration):
        result = f"{prefix}VarDecl: {node.var_type} {node.name}"
        if node.initializer:
            result += f" = {ast_to_string(node.initializer, 0).strip()}"
        return result + "\n"
    
    elif isinstance(node, Assignment):
        return f"{prefix}Assignment: {node.name} = {ast_to_string(node.value, 0).strip()}\n"
    
    elif isinstance(node, IfStatement):
        result = f"{prefix}If: {ast_to_string(node.condition, 0).strip()}\n"
        for stmt in node.then_body:
            result += ast_to_string(stmt, indent + 1)
        if node.else_body:
            result += f"{prefix}Else:\n"
            for stmt in node.else_body:
                result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, WhileLoop):
        result = f"{prefix}While: {ast_to_string(node.condition, 0).strip()}\n"
        for stmt in node.body:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, ForLoop):
        result = f"{prefix}For:\n"
        result += f"{prefix}  Init: {ast_to_string(node.init, 0).strip()}\n"
        result += f"{prefix}  Cond: {ast_to_string(node.condition, 0).strip()}\n"
        result += f"{prefix}  Update: {ast_to_string(node.update, 0).strip()}\n"
        result += f"{prefix}  Body:\n"
        for stmt in node.body:
            result += ast_to_string(stmt, indent + 2)
        return result
    
    elif isinstance(node, ReturnStatement):
        result = f"{prefix}Return"
        if node.value:
            result += f": {ast_to_string(node.value, 0).strip()}"
        return result + "\n"
    
    elif isinstance(node, PrintStatement):
        exprs_str = ", ".join(ast_to_string(e, 0).strip() for e in node.expressions)
        return f"{prefix}Print: [{exprs_str}]\n"
    
    elif isinstance(node, InputStatement):
        return f"{prefix}Input: {node.variable_name}\n"
    
    elif isinstance(node, ExpressionStatement):
        return f"{prefix}ExprStmt: {ast_to_string(node.expression, 0).strip()}\n"
    
    elif isinstance(node, BinaryOp):
        return f"({ast_to_string(node.left, 0).strip()} {node.operator} {ast_to_string(node.right, 0).strip()})"
    
    elif isinstance(node, UnaryOp):
        return f"({node.operator}{ast_to_string(node.operand, 0).strip()})"
    
    elif isinstance(node, Literal):
        if node.literal_type == 'string':
            return f'"{node.value}"'
        return f"{node.value}"
    
    elif isinstance(node, Identifier):
        return f"{node.name}"
    
    elif isinstance(node, FunctionCall):
        args_str = ", ".join(ast_to_string(a, 0).strip() for a in node.arguments)
        return f"{node.function_name}({args_str})"
    
    else:
        return f"{prefix}{node.__class__.__name__}\n"
