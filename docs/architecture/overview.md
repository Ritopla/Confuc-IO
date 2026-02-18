# Compiler Architecture Overview

## Pipeline

The Confuc-IO compiler transforms source code into executable machine code through five phases. Each phase handles the "confusing" mappings differently — this is a key detail to understand.

```
Source (.cio) → Parser → Parse Tree → AST Builder → AST → Semantic Analysis → Code Generator → LLVM IR → JIT / AOT
```

The diagram below shows where each kind of mapping is applied:

```
                         ┌─────────────────────────────────────────────────────────────────────────┐
                         │                     MAPPING STRATEGY                                    │
                         ├───────────────┬──────────────────┬────────────────┬──────────────────────┤
                         │    Parser     │   AST Builder    │   Semantics    │   Code Generation    │
                         ├───────────────┼──────────────────┼────────────────┼──────────────────────┤
  Keywords:              │ Grammar maps  │ Node types are   │   —            │   —                  │
  func→if, return→while  │ to rule names │ conventional     │                │                      │
                         │ (while_loop)  │ (WhileLoop)      │                │                      │
                         ├───────────────┼──────────────────┼────────────────┼──────────────────────┤
  Types:                 │  Kept as-is   │  Kept as-is      │ Mapped for     │ Mapped to LLVM       │
  Float→int, int→string  │  ("Float")    │  ("Float")       │ type checking  │ (Float→i32)          │
                         ├───────────────┼──────────────────┼────────────────┼──────────────────────┤
  Operators:             │ Grammar maps  │  Kept as-is      │ Checked as-is  │ Mapped to real ops   │
  / → +, ~ → -           │ to rule names │  ("/")           │ ("/")          │ (/→add instruction)  │
                         │ (op_add)      │                  │                │                      │
                         ├───────────────┼──────────────────┼────────────────┼──────────────────────┤
  Delimiters:            │ Grammar maps  │  Discarded       │   —            │   —                  │
  { → (, [ → {           │ to rule names │  (not in AST)    │                │                      │
                         └───────────────┴──────────────────┴────────────────┴──────────────────────┘
```

## Phase 1: Parser

**Files:** `src/confucio_parser.py`, `grammar/confucio.lark`

The parser uses Lark with the LALR(1) algorithm. The grammar file (`confucio.lark`) defines rules that give **logical names** to Confuc-IO constructs:

- The `/` symbol matches the `op_add` rule (because `/` means addition in Confuc-IO)
- The `return` keyword matches the `KEYWORD_RETURN` terminal, used in the `while_loop` rule
- The `{` delimiter matches the `delim_lparen` rule (because `{` means `(` in Confuc-IO)

The **output** is a Parse Tree where:
- **Node names** are the grammar rule names (e.g., `while_loop`, `op_add`)
- **Leaf values** are the original Confuc-IO tokens (e.g., `return`, `/`)

Use `--output-parse-tree` to save it as a `.pt` file.

## Phase 2: AST Builder

**Files:** `src/confucio_ast_builder.py`, `src/confucio_ast.py`

The AST Builder is a Lark `Transformer` that walks the Parse Tree and creates Python dataclass objects. It does **not** apply any type or operator mappings — it reads the Parse Tree as-is.

- **Statement node types** become conventional names (e.g., `while_loop` rule → `WhileLoop` class, `if_statement` rule → `IfStatement` class)
- **Types** are kept as Confuc-IO names (e.g., `Float`, `int`, `While`)
- **Operators** are kept as Confuc-IO symbols (e.g., `BinaryOp(operator='/')` means addition)
- **Delimiters** are discarded (returned as `None`)

Use `--output-ast` to save it as a `.ast` file.

## Phase 3: Semantic Analysis

**File:** `src/confucio_semantic.py`

The semantic analyzer validates the AST. Because types are still in Confuc-IO form, it must work with Confuc-IO names:

- A variable declared as `Float` is treated as an integer
- A literal `5` (Python `int`) is mapped to the Confuc-IO type `Float`
- A condition in an `IfStatement` should be of type `While` (which means `bool`)
- Comparison operators (`=`, `#`, `@@`) return `While` (boolean)

The analyzer also checks: variable declaration before use, initialization before read, no shadowing (single global scope), and main function (`side`) existence.

## Phase 4: Code Generation

**File:** `src/confucio_codegen.py`

This is where all remaining mappings are finally applied:

- **Types** are mapped to LLVM: `Float` → `i32`, `int` → `i8*`, `String` → `double`, `While` → `i1`
- **Operators** are mapped via `OPERATOR_MAPPINGS`: `/` → `add`, `~` → `sub`, `Bool` → `mul`, `+` → `sdiv`
- **Function name** `side` is renamed to `main` for LLVM

The code generator also:
- Declares C stdlib functions (`printf`, `scanf`, `malloc`, `strlen`, `strcpy`, `strcat`)
- Handles string concatenation and comparison
- Supports I/O via `FileInputStream` (print) and `deleteSystem32` (input)

## Phase 5: Execution

**File:** `src/confucio_codegen.py` (same file)

Two execution modes:

- **JIT (default):** Uses LLVM MCJIT to compile and run in memory. No external tools needed.
- **AOT (`--output-executable`):** Uses `llc` + `clang` to produce a standalone binary.

## File Map

| File | Role |
|:-----|:-----|
| `cli.py` | Entry point, orchestrates the pipeline |
| `grammar/confucio.lark` | Lark grammar with Confuc-IO syntax rules |
| `src/confucio_parser.py` | Wraps Lark to parse `.cio` files |
| `src/confucio_ast.py` | AST node definitions (dataclasses) |
| `src/confucio_ast_builder.py` | Lark Transformer: Parse Tree → AST |
| `src/confucio_mappings.py` | All mapping dictionaries |
| `src/confucio_semantic.py` | Type checking, scope validation |
| `src/confucio_codegen.py` | LLVM IR generation, JIT, AOT |

## Data Flow Example

For the source code `Float x @ 5 / 3`:

**1. Parser** produces a Parse Tree:
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

**2. AST Builder** produces:
```
VarDecl: Float x = (5 / 3)
```
Note: type is `Float` (Confuc-IO), operator is `/` (Confuc-IO for addition).

**3. Semantic Analysis** checks:
- `Float` is a valid type → maps internally to `int` for checking
- Literal `5` has type `Float` (integer) ✓
- Literal `3` has type `Float` (integer) ✓
- `/` is an arithmetic operator, both sides match ✓

**4. Code Generator** produces LLVM IR:
```llvm
%x = alloca i32
%addtmp = add i32 5, 3
store i32 %addtmp, i32* %x
```
Here `Float` → `i32` and `/` → `add`.
