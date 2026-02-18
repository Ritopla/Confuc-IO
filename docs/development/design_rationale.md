# Design Rationale

## Introduction

This document explains the key design decisions made during the development of the Confuc-IO compiler.

---

## Language Design

### Confusing Mappings

**Decision:** Use intentionally misleading names for keywords, types, operators, and delimiters.

**Rationale:**
- Forces developers to think beyond surface syntax
- Demonstrates that code meaning ≠ code appearance
- Makes the language memorable and interesting
- Teaches how compilers can handle any syntax

---

## Compiler Architecture

### Multi-Phase Pipeline

**Decision:** Separate parser, AST builder, semantic analyzer, and code generator.

**Rationale:**
- Each phase has one responsibility
- Can test each phase independently
- Changes isolated to specific phases
- Follows established compiler design patterns

### When Mappings Are Applied

**Decision:**
- **Delimiter mappings** → handled by the grammar (rule names like `delim_lparen` match `{`)
- **Keyword mappings** → partially in the grammar (rule names like `while_loop` use `KEYWORD_RETURN`), fully realized in the AST builder (creates `WhileLoop` node)
- **Operator symbol mappings** → the grammar names rules logically (`op_add` matches `/`), but the AST builder returns the raw Confuc-IO symbol (`'/'`). The final mapping (`'/'` → `add` instruction) happens in the code generator
- **Type mappings** → types stay as Confuc-IO names (`Float`, `int`, etc.) through the AST and semantic analysis. They are mapped to LLVM types only in the code generator

**Why operators are kept as Confuc-IO symbols in the AST:**
The AST builder's operator methods (e.g., `op_add`) return the raw Confuc-IO symbol (e.g., `'/'`) rather than the conventional meaning (`'+'`). This means the grammar's logical naming is only visible in the Parse Tree, not in the AST. The code generator then uses `OPERATOR_MAPPINGS` to translate them. This is a quirk of the implementation — the grammar maps operators to logical rule names, but the AST builder maps them back to raw symbols.

**Why types use Confuc-IO names throughout:**
The semantic analyzer works directly with Confuc-IO type names (`Float`, `int`, `String`, `While`). To make literal type checking work, it maps Python literal types to Confuc-IO names (e.g., a Python `int` literal → `Float` type). This way, declaring `Float x @ 5` checks out: the variable has type `Float`, and the literal `5` is mapped to type `Float`.

---

## Technology Choices

### Lark for Parsing

**Decision:** Use Lark parser generator with LALR(1).

**Rationale:**
- Declarative grammar files are readable
- Native Python library
- Automatic parse tree building
- Supports Transformers for AST building

### LLVM via llvmlite

**Decision:** Use LLVM IR as the compilation target, accessed through llvmlite.

**Rationale:**
- Industry standard backend (used by Clang, Rust, Swift)
- World-class optimization passes
- Built-in MCJIT engine for JIT execution
- llvmlite provides a clean Python API

---

## JIT Execution

### Default to JIT

**Decision:** Make JIT execution the default, with AOT as an option.

**Rationale:**
- Immediate execution feels interactive
- No external tool dependencies for basic usage
- AOT (`--output-executable`) is available when needed but requires `llc` and `clang`

### Automatic C Symbol Linkage

**Decision:** Rely on system linker for C stdlib symbols (`printf`, `scanf`, etc.).

**Rationale:** MCJIT automatically resolves these via the system's dynamic linker. No manual mapping code is needed.

---

## Type System

### Global Scope Only

**Decision:** Single global scope for all variables, no shadowing.

**Rationale:**
- Simpler implementation
- Focuses attention on the confusing syntax rather than scoping rules
- Sufficient for the language's educational goals

Function parameters are the one exception — they are temporarily added during function analysis and removed afterward.

### No Implicit Conversion

**Decision:** Require explicit types, no automatic int↔float conversion.

**Rationale:** Explicit is better than implicit. Prevents subtle bugs and keeps the type system simple.

---

## I/O Design

### Confusing I/O Names

- `FileInputStream` → prints output (sounds like input!)
- `deleteSystem32` → reads input (sounds destructive!)

### Real printf Formats

**Decision:** Use real printf format strings (`%d`, `%f`, `%s`) in generated LLVM IR, not confusing ones.

**Rationale:** Using `%f` for integers would be undefined behavior in C. The confusing format strings defined in `confucio_mappings.py` are conceptual/documentation-only and are never used in actual code generation.

---

## String Operations

### C stdlib for Strings

**Decision:** Use `strlen`, `malloc`, `strcpy`, `strcat`, `strcmp` for string operations.

**Rationale:** No need to reimplement standard functions. These are well-tested, optimized, and available on all platforms.

---

## CLI Design

### Parse Tree vs AST Output

**Decision:** Separate `--output-parse-tree` (saves `.pt`) from `--output-ast` (saves `.ast`).

**Rationale:** The Parse Tree (Lark's raw output) and the AST (transformed Python objects) are structurally different. The Parse Tree shows grammar rule names and all tokens; the AST shows only the meaningful program structure with Confuc-IO type and operator names preserved.
