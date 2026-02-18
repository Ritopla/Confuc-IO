# Semantic Analysis

## Overview

The semantic analyzer validates the AST before code generation. It uses a **reflection-based visitor pattern**: for each AST node of type `Foo`, the method `visit_Foo` is looked up via `getattr` and called automatically.

**File:** `src/confucio_semantic.py`

## Visitor Pattern

The central dispatch method uses Python reflection to find and call the appropriate visitor:

```python
def visit(self, node):
    method_name = f'visit_{type(node).__name__}'
    visitor = getattr(self, method_name, None)
    if visitor is None:
        raise SemanticError(f"No visitor method for: {type(node).__name__}")
    return visitor(node)
```

Statement visitors (e.g., `visit_VarDeclaration`, `visit_WhileLoop`) return `None`. Expression visitors (e.g., `visit_Literal`, `visit_BinaryOp`) return the Confuc-IO type name as a string.

## The Type Challenge

Because the AST stores types as Confuc-IO names (`Float`, `int`, `String`, `While`), the semantic analyzer must work with these names directly. It maps literal types to Confuc-IO names internally for comparison.

### How Literal Types Are Mapped

The AST stores literal values with Python type names (`literal_type='int'`). The semantic analyzer maps these to Confuc-IO type names so they can be compared with variable types:

```python
# In analyze_expression(), when encountering a Literal:
type_map = {
    'int': 'Float',      # Python int literal → Confuc-IO "Float" type
    'float': 'String',   # Python float literal → Confuc-IO "String" type
    'string': 'int',     # Python string literal → Confuc-IO "int" type
    'bool': 'While',     # Python bool literal → Confuc-IO "While" type
}
```

This means: a literal `5` (which has `literal_type='int'`) is reported as type `Float`, which is correct because `Float` is the Confuc-IO name for integers.

### How Conditions Are Checked

For `IfStatement` and `WhileLoop`, the condition should produce a boolean. In Confuc-IO, the boolean type is called `While`. So the analyzer checks:

```python
# In analyze_if_statement():
cond_type = self.analyze_expression(if_stmt.condition)
if cond_type != 'While':  # "While" is the bool type
    pass  # Allow comparisons that implicitly produce booleans
```

### How Operators Are Checked

Operators are still in Confuc-IO form. The analyzer checks them as-is:

- Arithmetic operators: `/`, `~`, `+`, `Bool` — both sides must have the same type
- Comparison operators: `=`, `#`, `@@` — return `While` (boolean)

## What Gets Checked

### 1. Type Validity

Variable types must be one of the keys in `TYPE_MAPPINGS` (`Float`, `int`, `String`, `While`):

```python
if decl.var_type not in TYPE_MAPPINGS:
    raise SemanticError(f"Unknown type '{decl.var_type}'")
```

### 2. Type Compatibility

Assignments and initializations must have matching types:

```python
Float x @ 5         # Float var, int literal → literal maps to Float ✓
Float x @ "hello"   # Float var, string literal → literal maps to int ✗
```

### 3. Variable Declaration

Variables must be declared before use. No shadowing is allowed — a variable name can only be declared once in the entire program (single global scope):

```python
if name in self.symbols:
    raise SemanticError(f"Variable '{name}' already declared")
```

### 4. Variable Initialization

Variables must be initialized before being read:

```python
if not self.symbol_table.is_initialized(expr.name):
    raise SemanticError(f"Variable '{expr.name}' used before initialization")
```

### 5. Main Function

The program must contain a function named `side` (the Confuc-IO name for `main`):

```python
if not self.has_main:
    raise SemanticError(f"Program must have a main function named 'side'")
```

### 6. Function Calls

Function calls are checked for: function existence, argument count, and argument types.

## Symbol Table

The `SymbolTable` class tracks:
- **Variables:** name, type (Confuc-IO name), initialization status
- **Functions:** name, `FunctionDef` AST node

Function parameters are added to the symbol table as initialized variables when analyzing a function body, and removed afterward (they are function-local).

## Scope Model

Confuc-IO uses a **single global scope** with no shadowing. This means:
- All variables are visible everywhere after declaration
- No two variables can share the same name
- Function parameters are the one exception (they are temporarily added during function analysis)
