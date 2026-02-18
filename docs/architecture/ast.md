# Abstract Syntax Tree (AST)

## Overview

The AST is the compiler's structured representation of the program after parsing. It strips away all syntax-level details (delimiters, keywords, grammar rule structure) and keeps only the meaningful program structure.

**Files:**
- `src/confucio_ast.py` — AST node definitions (Python dataclasses)
- `src/confucio_ast_builder.py` — Lark Transformer that builds the AST from the Parse Tree

## How the AST Builder Works

The AST Builder is a Lark `Transformer`. Each method corresponds to a grammar rule name and receives the already-transformed children:

```python
class ConfucIOASTBuilder(Transformer):
    def while_loop(self, items):
        # "while_loop" rule → WhileLoop AST node
        return WhileLoop(condition=..., body=...)
    
    def op_add(self, items):
        # Returns the Confuc-IO symbol "/" as a string
        return '/'
```

### What Gets Mapped

**Statement types** are mapped to conventional AST node classes:
- `while_loop` rule → `WhileLoop` node
- `if_statement` rule → `IfStatement` node
- `for_loop` rule → `ForLoop` node
- `return_statement` rule → `ReturnStatement` node

This is a natural consequence of the grammar: the grammar rule is named `while_loop`, so the transformer method is `while_loop`, and it creates a `WhileLoop` object.

### What Does NOT Get Mapped

**Types** stay as Confuc-IO names:
```python
VarDeclaration(var_type='Float', name='x', initializer=...)
# "Float" is kept — it is NOT mapped to "int" here
```

**Operators** stay as Confuc-IO symbols:
```python
BinaryOp(operator='/', left=..., right=...)
# "/" is kept — it is NOT mapped to "+" here
```

**Delimiters** are discarded (returned as `None` by the transformer).

## AST Node Types

### Program Structure

| Node | Fields | Description |
|:-----|:-------|:------------|
| `Program` | `functions: List[FunctionDef]` | Root node |
| `FunctionDef` | `return_type, name, parameters, body` | Function definition |
| `Parameter` | `param_type, name` | Function parameter |

### Statements

| Node | Fields | Description |
|:-----|:-------|:------------|
| `VarDeclaration` | `var_type, name, initializer` | Variable declaration |
| `Assignment` | `name, value` | Assignment |
| `IfStatement` | `condition, then_body, else_body` | If statement (from `func` keyword) |
| `WhileLoop` | `condition, body` | While loop (from `return` keyword) |
| `ForLoop` | `init, condition, update, body` | For loop (from `if` keyword) |
| `ReturnStatement` | `value` | Return (from `*` keyword) |
| `PrintStatement` | `expressions` | Print (from `FileInputStream`) |
| `InputStatement` | `variable_name` | Input (from `deleteSystem32`) |
| `ExpressionStatement` | `expression` | Expression used as statement |

### Expressions

| Node | Fields | Description |
|:-----|:-------|:------------|
| `BinaryOp` | `operator, left, right` | Binary operation (operator is Confuc-IO symbol) |
| `UnaryOp` | `operator, operand` | Unary operation |
| `Literal` | `value, literal_type` | Literal value (`literal_type` is `'int'`, `'float'`, `'string'`, `'bool'`) |
| `Identifier` | `name` | Variable reference |
| `FunctionCall` | `function_name, arguments` | Function call |

## Example

For the source `Float x @ 5 / 3`:

**Parse Tree:**
```
var_declaration
  type  Float
  x
  op_assign
  additive
    5
    op_add
    3
```

**AST (after transformation):**
```
VarDecl: Float x = (5 / 3)
```

In this AST:
- `var_type` is `'Float'` (Confuc-IO name, not `'int'`)
- The operator is `'/'` (Confuc-IO symbol, not `'+'`)
- `literal_type` for `5` and `3` is `'int'` (Python's type, not the Confuc-IO type name)

You can save the AST with `--output-ast` (saved as `.ast` file).

## Design Notes

- The AST is built from Python **dataclasses** — simple, immutable data containers
- All nodes inherit from `ASTNode`; statements from `Statement`; expressions from `Expression`
- The `Literal` node's `literal_type` field uses Python type names (`'int'`, `'string'`) to describe the value, while `VarDeclaration.var_type` uses Confuc-IO type names (`'Float'`, `'int'`)
- This asymmetry is resolved in the semantic analysis phase, where literal types are mapped to Confuc-IO type names for comparison
