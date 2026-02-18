# Code Generation

## Overview

The code generator is the final translation phase. It uses the same **reflection-based visitor pattern** as the semantic analyzer: for each AST node of type `Foo`, the method `visit_Foo` is dispatched via `getattr`. This is where all remaining mappings are applied.

**File:** `src/confucio_codegen.py`  
**Library:** llvmlite (Python bindings for LLVM)

## Visitor Pattern

Statement visitors (e.g., `visit_VarDeclaration`, `visit_WhileLoop`) generate LLVM IR instructions. Expression visitors (e.g., `visit_Literal`, `visit_BinaryOp`) return an `ir.Value`.

This is the same dispatch mechanism used in the semantic analyzer — the only difference is what `visit_*` methods return.

## Type Mapping

The code generator maps Confuc-IO type names to LLVM types:

```python
self.type_map = {
    'Float': ir.IntType(32),             # Float → i32 (integer)
    'int': ir.IntType(8).as_pointer(),   # int → i8* (string pointer)
    'String': ir.DoubleType(),           # String → double (float)
    'While': ir.IntType(1),             # While → i1 (boolean)
}
```

This mapping is used whenever a type name appears in the AST — variable declarations, function return types, parameters.

## Operator Mapping

Binary operators are mapped during code generation using the `OPERATOR_MAPPINGS` dictionary from `confucio_mappings.py`:

```python
def generate_binary_op(self, binop: BinaryOp):
    left = self.generate_expression(binop.left)
    right = self.generate_expression(binop.right)
    
    # Map Confuc-IO operator to conventional
    confucio_op = binop.operator          # e.g., "/"
    conventional_op = OPERATOR_MAPPINGS.get(confucio_op)  # e.g., "+"
    
    if conventional_op == '+':
        return self.builder.add(left, right)    # LLVM add instruction
    elif conventional_op == '-':
        return self.builder.sub(left, right)
    elif conventional_op == '*':
        return self.builder.mul(left, right)
    elif conventional_op == '/':
        return self.builder.sdiv(left, right)
    # ... comparisons, string operations
```

| Confuc-IO Operator | Conventional | LLVM Instruction |
|:-------------------|:-------------|:-----------------|
| `/` | `+` | `add` |
| `~` | `-` | `sub` |
| `Bool` | `*` | `mul` |
| `+` | `/` | `sdiv` |
| `=` | `>` | `icmp_signed >` |
| `#` | `<` | `icmp_signed <` |
| `@@` | `==` | `icmp_signed ==` |

## Function Name Mapping

The entry-point function `side` is renamed to `main` for LLVM:

```python
llvm_name = 'main' if func_def.name == 'side' else func_def.name
```

## Variable Storage

All variables are stack-allocated using `alloca`:

```python
var_alloca = self.builder.alloca(var_type, name=decl.name)
self.variables[decl.name] = var_alloca
```

Variables are loaded with `self.builder.load()` and stored with `self.builder.store()`.

## I/O

### Print (`FileInputStream`)

The `PrintStatement` node generates calls to C's `printf`:
- **String literals** are printed directly (no format string needed)
- **Variables** use the appropriate real format string (`%d` for integers, `%f` for floats, `%s` for strings)
- A newline is appended after each print statement

### Input (`deleteSystem32`)

The `InputStatement` node generates calls to C's `scanf`:
- **Integers (`Float` type):** Uses `%d` format
- **Floats (`String` type):** Uses `%lf` format
- **Strings (`int` type):** Allocates a 256-byte buffer with `malloc`, reads with `%255s`

## String Operations

### Concatenation

When the `+` operator (conventional, mapped from `/`) is applied to two string pointers (`i8*`), the generator calls `strlen` + `malloc` + `strcpy` + `strcat` to concatenate them.

### Comparison

When `==` (conventional, mapped from `@@`) is applied to two strings, the generator calls `strcmp` and compares the result with zero.

## Control Flow

### If Statements

Creates three basic blocks: `if.then`, `if.else`, `if.end`. The condition branches to `then` or `else`, and both merge at `end`.

### While Loops

Creates three basic blocks: `while.cond`, `while.body`, `while.end`. The condition block loops back from the body. If the condition is an `i32` (integer), it's compared to zero to produce a boolean.

### For Loops

Creates four basic blocks: initialization runs before branching to `for.cond`, body branches to `for.update`, update branches back to `for.cond`.

## C Standard Library

The following C functions are declared as LLVM externals and are resolved automatically by the MCJIT linker:

| Function | Purpose |
|:---------|:--------|
| `printf` | Output |
| `scanf` | Input |
| `malloc` | Memory allocation (for strings) |
| `strlen` | String length |
| `strcpy` | String copy |
| `strcat` | String concatenation |
| `strcmp` | String comparison (declared on demand) |

## Optimization

LLVM optimization passes can be applied after generation:

```bash
python3 cli.py program.cio -O1   # Basic optimization
python3 cli.py program.cio -O2   # Moderate
python3 cli.py program.cio -O3   # Aggressive
```

The `optimize()` method creates a pass manager, sets the optimization level, and runs it on the module.

## Generated IR Example

For the source `Float x @ 5 / 3` inside a `Float side` function:

```llvm
define i32 @main() {
entry:
  %x = alloca i32
  %addtmp = add i32 5, 3
  store i32 %addtmp, i32* %x
  ret i32 0
}
```

- `Float` → `i32`
- `side` → `main`
- `/` → `add`
- `5` and `3` are `i32` constants
