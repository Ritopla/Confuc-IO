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
        result = f"{prefix}FunctionDef: {node.return_type} {node.name}(...)\n"
        for stmt in node.body:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, VarDeclaration):
        result = f"{prefix}VarDecl: {node.var_type} {node.name}"
        if node.initializer:
            result += f" = {ast_to_string(node.initializer, 0).strip()}"
        return result + "\n"
    
    elif isinstance(node, Assignment):
        result = f"{prefix}Assignment: {node.name} = {ast_to_string(node.value, 0).strip()}\n"
        return result
    
    elif isinstance(node, IfStatement):
        result = f"{prefix}If: {ast_to_string(node.condition, 0).strip()}\n"
        for stmt in node.then_body:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, WhileLoop):
        result = f"{prefix}While: {ast_to_string(node.condition, 0).strip()}\n"
        for stmt in node.body:
            result += ast_to_string(stmt, indent + 1)
        return result
    
    elif isinstance(node, ReturnStatement):
        result = f"{prefix}Return"
        if node.value:
            result += f": {ast_to_string(node.value, 0).strip()}"
        return result + "\n"
    
    elif isinstance(node, BinaryOp):
        return f"({ast_to_string(node.left, 0).strip()} {node.operator} {ast_to_string(node.right, 0).strip()})"
    
    elif isinstance(node, Literal):
        return f"{node.value}"
    
    elif isinstance(node, Identifier):
        return f"{node.name}"
    
    else:
        return f"{prefix}{node.__class__.__name__}\n"
