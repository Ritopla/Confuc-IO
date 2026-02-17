# Semantic Analysis

## Overview

The semantic analyzer validates the AST for correctness beyond syntax, ensuring type safety, proper scoping, and variable initialization.

## Responsibilities

1. **Type Checking:** Verify type compatibility in operations and assignments
2. **Scope Validation:** Ensure variables are declared before use
3. **Initialization Checking:** Verify variables initialized before read
4. **No Shadowing:** Prevent variable redeclaration
5. **Main Function:** Ensure `main` (named `side` in Confuc-IO) exists

## Implementation

**File:** [confucio_semantic.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/src/confucio_semantic.py)

### Analyzer Class

```python
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}  # Global scope only
        self.initialized_vars = set()
    
    def analyze(self, ast: Program):
        # Check for main function
        # Analyze all statements
        for stmt in ast.statements:
            self.analyze_statement(stmt)
```

## Type System

### Types (Conventional Names)

After AST construction, types are:
- `int`: Integer numbers
- `float`: Floating-point numbers
- `string`: Text strings
- `bool`: Boolean values

### Type Compatibility Rules

#### Assignment
```python
def check_assignment(self, var_type: str, expr_type: str):
    if var_type != expr_type:
        raise SemanticError(f"Type mismatch: cannot assign {expr_type} to {var_type}")
```

#### Binary Operations

**Arithmetic** (`+`, `-`, `*`, `/`):
- Both operands must be `int` or `float`
- Result type matches operand type

**String Concatenation** (`+` when operands are strings):
- Both operands must be `string`
- Result type is `string`

**Comparison** (`>`, `<`, `==`, `!=`):
- Operands must have same type
- Result type is `bool`

**String Comparison** (`==` when operands are strings):
- Both operands must be `string`
- Result type is `bool`

### Type Inference

The analyzer infers expression types:

```python
def infer_type(self, expr: Expression) -> str:
    if isinstance(expr, Literal):
        return expr.literal_type
    elif isinstance(expr, Variable):
        return self.symbol_table[expr.name]
    elif isinstance(expr, BinaryOp):
        left_type = self.infer_type(expr.left)
        right_type = self.infer_type(expr.right)
        return self.check_binary_op(expr.operator, left_type, right_type)
```

## Scope Management

### Single Global Scope

Design decision: Confuc-IO uses only **global scope**
- All variables declared at module level
- Functions see all global variables
- Simpler implementation
- No closures or nested scopes

### Symbol Table

```python
self.symbol_table = {
    'variable_name': 'type',
    'x': 'int',
    'name': 'string',
    # ...
}
```

### Shadowing Prevention

```python
def analyze_variable_declaration(self, node: VariableDeclaration):
    if node.identifier in self.symbol_table:
        raise SemanticError(f"Variable '{node.identifier}' already declared")
    self.symbol_table[node.identifier] = node.var_type
```

## Initialization Tracking

### Problem

Prevent reading uninitialized variables:
```confucio
Float x
Float y @ x / 5  È Error: x not initialized
```

### Solution

Track initialized variables:
```python
self.initialized_vars = set()

def analyze_variable_declaration(self, node: VariableDeclaration):
    # Add to symbol table
    self.symbol_table[node.identifier] = node.var_type
    
    # Track initialization
    if node.initializer:
        self.initialized_vars.add(node.identifier)

def analyze_variable_use(self, var_name: str):
    if var_name not in self.initialized_vars:
        raise SemanticError(f"Variable '{var_name}' used before initialization")
```

## Error Reporting

### Error Types

**SemanticError**
```python
class SemanticError(Exception):
    """Raised when semantic analysis fails"""
    pass
```

### Error Messages

Clear, actionable messages:
```python
# Type mismatch
"Type mismatch in assignment: cannot assign float to int variable 'x'"

# Undeclared variable
"Undeclared variable: 'y'"

# Already declared
"Variable 'x' already declared"

# Uninitialized
"Variable 'x' used before initialization"

# Missing main
"Main function 'side' not found"
```

## Validation Examples

### Example 1: Type Checking

**Source:**
```confucio
Float x @ 5
String y @ x  È Error: cannot assign int to float
```

**Analysis:**
1. `x` declared with type `int` (Float→int mapping)
2. `x` initialized with literal `5` (type `int`) ✓
3. `y` declared with type `float` (String→float mapping)
4. Trying to assign `x` (type `int`) to `y` (type `float`) ✗
5. **Error:** Type mismatch

### Example 2: Uninitialized Variable

**Source:**
```confucio
Float x
Float y @ x / 5  È Error: x not initialized
```

**Analysis:**
1. `x` declared but not initialized
2. `y` initialized with `x / 5`
3. Reading `x` before initialization ✗
4. **Error:** Uninitialized variable

### Example 3: Redeclaration

**Source:**
```confucio
Float x @ 5
Float x @ 10  È Error: x already declared
```

**Analysis:**
1. `x` declared with type `int`
2. Attempting to redeclare `x` ✗
3. **Error:** Variable already declared

## Design Rationale

### Why Single-Pass?

**Reasons:**
1. **Simplicity:** Easier to implement and understand
2. **Performance:** Faster than multi-pass
3. **Sufficient:** Confuc-IO's simple scope model doesn't require multiple passes

### Why Global-Only Scope?

**Reasons:**
1. **Learning Focus:** Emphasizes confusing syntax over complex scoping
2. **Simplification:** Easier semantic analysis
3. **Specification:** Original language design choice

### Why Track Initialization?

**Reasons:**
1. **Safety:** Prevents undefined behavior
2. **Clarity:** Explicit initialization requirement
3. **Debugging:** Catches common errors early

## Testing

### Unit Tests

[tests/unit/test_semantic.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/tests/unit/) (if exists)

Test cases:
```python
def test_type_mismatch():
    source = "Float x @ 5\nString y @ x"
    with pytest.raises(SemanticError):
        compile_and_analyze(source)

def test_undeclared_variable():
    source = "Float x @ y / 5"
    with pytest.raises(SemanticError):
        compile_and_analyze(source)

def test_uninitialized():
    source = "Float x\nFloat y @ x"
    with pytest.raises(SemanticError):
        compile_and_analyze(source)
```

### Error Fixtures

[tests/fixtures/errors/](file:///Users/ritopla/Desktop/ILP/Confuc-IO/tests/fixtures/errors/)

Example error cases for validation.

## Limitations

### Current Limitations

1. **No Type Inference:** Must explicitly declare types
2. **No Implicit Conversion:** No automatic int↔float conversion
3. **No Function Scopes:** All variables global
4. **No Nested Declarations:** Cannot redeclare in nested blocks

### Future Enhancements

Potential improvements:
1. Function-local scopes
2. Type inference for literals
3. Implicit numeric conversions
4. Const/readonly variables

## Next Step

After validation, the code generator produces LLVM IR from the validated AST.

→ [Next: Code Generation](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/code_generation.md)
