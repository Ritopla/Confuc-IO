# Abstract Syntax Tree (AST)

## Overview

The AST is an intermediate representation that captures the semantic structure of a Confuc-IO program, independent of the concrete syntax.

## Purpose

The AST serves as:
1. **Abstraction:** Removes parsing details, focuses on meaning
2. **Interface:** Clean boundary between frontend (parsing) and backend (code generation)
3. **Analysis Target:** Used by semantic analyzer for type checking
4. **IR Foundation:** Directly translates to LLVM IR

## Node Design

### Base Class

All AST nodes inherit from a base `ASTNode` class:

```python
class ASTNode:
    """Base class for all AST nodes"""
    pass
```

### Node Categories

#### 1. Program Structure

**Program**
```python
class Program(ASTNode):
    statements: List[Statement]
```
- Top-level container
- List of all statements

#### 2. Declarations

**VariableDeclaration**
```python
class VariableDeclaration(ASTNode):
    var_type: str          # 'int', 'float', 'string', 'bool'
    identifier: str        # Variable name
    initializer: Expression | None
```

**FunctionDeclaration**
```python
class FunctionDeclaration(ASTNode):
    return_type: str
    name: str
    parameters: List[Parameter]
    body: List[Statement]
```

#### 3. Statements

**Assignment**
```python
class Assignment(ASTNode):
    identifier: str
    value: Expression
```

**PrintStatement**
```python
class PrintStatement(ASTNode):
    expressions: List[Expression]
```

**InputStatement**
```python
class InputStatement(ASTNode):
    variable: str
```

**IfStatement**
```python
class IfStatement(ASTNode):
    condition: Expression
    then_body: List[Statement]
    else_body: List[Statement] | None
```

**WhileStatement**
```python
class WhileStatement(ASTNode):
    condition: Expression
    body: List[Statement]
```

**ForStatement**
```python
class ForStatement(ASTNode):
    init: VariableDeclaration | None
    condition: Expression | None
    increment: Assignment | None
    body: List[Statement]
```

**ReturnStatement**
```python
class ReturnStatement(ASTNode):
    value: Expression | None
```

#### 4. Expressions

**BinaryOp**
```python
class BinaryOp(ASTNode):
    operator: str        # '+', '-', '*', '/', '==', '>', '<', etc.
    left: Expression
    right: Expression
```

**UnaryOp**
```python
class UnaryOp(ASTNode):
    operator: str        # '-', '!'
    operand: Expression
```

**Variable**
```python
class Variable(ASTNode):
    name: str
```

**Literal**
```python
class Literal(ASTNode):
    literal_type: str    # 'int', 'float', 'string', 'bool'
    value: Any
```

## Transformation Process

### Parse Tree → AST

The AST Builder ([confucio_ast_builder.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/src/confucio_ast_builder.py)) uses Lark's `Transformer` class:

```python
class ASTBuilder(Transformer):
    def variable_declaration(self, items):
        type_token, identifier, initializer = items
        # Map confusing type to conventional type
        conventional_type = TYPE_MAPPINGS.get(type_token.value, type_token.value)
        return VariableDeclaration(
            var_type=conventional_type,
            identifier=str(identifier),
            initializer=initializer
        )
```

### Mapping Application

**Type Mappings** are applied during AST construction:

```python
TYPE_MAPPINGS = {
    'Float': 'int',      # Float in code → int in AST
    'int': 'string',     # int in code → string in AST
    'String': 'float',   # String in code → float in AST
    'While': 'bool',     # While in code → bool in AST
}
```

**Operator Mappings** are deferred to code generation.

### Why Apply Type Mappings Early?

**Reasons:**
1. **Semantic Analysis:** Type checker works with conventional types
2. **Simplicity:** Rest of compiler uses normal type names
3. **Separation:** Confusing syntax vs. actual semantics

## Design Rationale

### Immutability

AST nodes are designed to be **immutable** where possible:
- Easier to reason about
- Safer for concurrent processing
- Simpler semantic analysis

### Simplicity

AST is intentionally simple:
- No method complexity
- Data-only structures
- Easy to traverse

### Conventional Representation

After AST construction, the tree uses **conventional names**:
- Types: `int`, `float`, `string`, `bool`
- Operators: `+`, `-`, `*`, `/`, `==`, etc.

This means:
- `Float x @ 5` becomes `VariableDeclaration(var_type='int', name='x', init=Literal('int', 5))`
- Semantic analyzer sees `int`, not `Float`

## Traversal Patterns

### Visitor Pattern

The semantic analyzer uses visitor pattern:

```python
class SemanticAnalyzer:
    def analyze(self, node: ASTNode):
        method_name = f'analyze_{node.__class__.__name__}'
        method = getattr(self, method_name, self.generic_analyze)
        return method(node)
    
    def analyze_VariableDeclaration(self, node: VariableDeclaration):
        # Type-specific analysis
        ...
```

### Recursive Descent

Code generator uses recursive descent:

```python
def generate_statement(self, stmt: Statement):
    if isinstance(stmt, VariableDeclaration):
        return self.generate_variable_declaration(stmt)
    elif isinstance(stmt, Assignment):
        return self.generate_assignment(stmt)
    # ...
```

## Example AST

### Source Code
```confucio
Float x @ 5 / 3
```

### Parse Tree
```
variable_declaration
├── TYPE_FLOAT: "Float"
├── IDENTIFIER: "x"
├── OP_ASSIGN: "@"
└── binary_operation
    ├── literal [INT_LIT: "5"]
    ├── OP_ADD: "/"
    └── literal [INT_LIT: "3"]
```

### AST
```python
VariableDeclaration(
    var_type='int',           # Float mapped to int
    identifier='x',
    initializer=BinaryOp(
        operator='+',         # / not yet mapped (done in codegen)
        left=Literal('int', 5),
        right=Literal('int', 3)
    )
)
```

Note: Operator `/` is stored as-is in AST, mapped to `+` during code generation.

## Benefits of This Design

### 1. Clean Separation
- **Syntax → AST:** Removes parsing artifacts
- **AST → IR:** Focuses on semantics

### 2. Type Safety
- Conventional types enable standard type checking
- No confusion in semantic analysis

### 3. Maintainability
- Simple data structures
- Easy to extend with new nodes

### 4. Tooling Support
- Easy to serialize/visualize
- Straightforward debugging

## Testing

### AST Construction Tests

Verify correct transformation:
```python
def test_variable_declaration():
    source = "Float x @ 5"
    ast = parser.parse_and_build(source)
    assert isinstance(ast, Program)
    assert ast.statements[0].var_type == 'int'  # Mapped!
```

### Node Structure Tests

Verify node relationships:
```python
def test_binary_op_structure():
    source = "Float x @ 5 / 3"
    decl = parse_and_build(source).statements[0]
    assert isinstance(decl.initializer, BinaryOp)
    assert decl.initializer.operator == '+'  # Depends on when mapping occurs
```

## Common Pitfalls

### Pitfall 1: Premature Operator Mapping

**Wrong:**
```python
# In AST builder
operator = OPERATOR_MAPPINGS.get(op_token.value, op_token.value)
return BinaryOp(operator=operator, ...)  # Too early!
```

**Right:**
```python
# Keep original operator in AST
return BinaryOp(operator=op_token.value, ...)
# Map during code generation
```

### Pitfall 2: Mutable Nodes

**Wrong:**
```python
class IfStatement(ASTNode):
    def add_else(self, else_body):
        self.else_body = else_body  # Mutating!
```

**Right:**
```python
class IfStatement(ASTNode):
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body  # Immutable
```

## Next Step

After AST construction, the semantic analyzer validates the tree.

→ [Next: Semantic Analysis](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/semantic_analysis.md)
