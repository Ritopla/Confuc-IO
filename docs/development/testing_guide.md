# Confuc-IO Compiler Testing Guide

## Prerequisites

```bash
cd /Users/ritopla/Desktop/ILP/Confuc-IO
pip3 install -r requirements.txt
```

---

## Part 1: Basic Functionality

### Step 1: Verify Mappings

```bash
python3 cli.py --verify-mappings
```

This prints all keyword, type, operator, and delimiter mappings and confirms they are defined correctly.

### Step 2: Parse and Build AST

Test the full pipeline (parse + AST build + semantic analysis) on an example:

```bash
python3 cli.py examples/calculator.cio --output-ast --output-parse-tree
```

This produces two files:
- `examples/calculator.pt` — the Lark **Parse Tree** (grammar rule names + Confuc-IO tokens)
- `examples/calculator.ast` — the **AST** (clean program structure with Confuc-IO types and operators)

Inspect the Parse Tree:
```bash
cat examples/calculator.pt
```
You should see rule names like `while_loop`, `op_add`, `if_statement` with Confuc-IO token values like `return`, `/`, `func`.

Inspect the AST:
```bash
cat examples/calculator.ast
```
You should see node types like `While:`, `If:`, `Print:` with Confuc-IO symbols like `/`, `#`, `@@`.

### Step 3: Test Other Examples

```bash
python3 cli.py examples/hello_world.cio
python3 cli.py examples/arithmetic.cio
python3 cli.py examples/fibonacci.cio
python3 cli.py examples/strings.cio
```

Each should parse, build AST, pass semantic analysis, generate LLVM IR, and execute via JIT.

---

## Part 2: Compiler Options

### LLVM IR Output

```bash
python3 cli.py examples/fibonacci.cio --output-llvm
```

Produces `examples/fibonacci.ll` — the generated LLVM IR. Inspect it to verify:
- `Float` → `i32`, `int` → `i8*`, `String` → `double`, `While` → `i1`
- `/` → `add`, `~` → `sub`, `Bool` → `mul`, `+` → `sdiv`
- `side` → `main`

### Optimization Levels

```bash
python3 cli.py examples/fibonacci.cio -O0   # No optimization (default)
python3 cli.py examples/fibonacci.cio -O1   # Basic
python3 cli.py examples/fibonacci.cio -O2   # Moderate
python3 cli.py examples/fibonacci.cio -O3   # Aggressive
```

### Executable Output

```bash
python3 cli.py examples/fibonacci.cio --output-executable
```

Requires `llc` and `clang` to be installed (e.g., `brew install llvm` on macOS).

### Combining Flags

```bash
python3 cli.py examples/fibonacci.cio --output-ast --output-parse-tree --output-llvm -O2
```

When output flags are present, JIT is skipped unless `--run` is also specified.

---

## Part 3: Error Handling

The compiler catches errors at different phases:

### Parse Errors

Syntax errors are caught by Lark and reported with line/column information.

### Semantic Errors

```bash
# Missing main function (no "side" function)
python3 cli.py tests/fixtures/errors/missing_main.cio

# Undeclared variable
python3 cli.py tests/fixtures/errors/undeclared_variable.cio

# Variable shadowing (redeclaration)
python3 cli.py tests/fixtures/errors/shadowing.cio

# Type mismatch
python3 cli.py tests/fixtures/errors/type_mismatch.cio

# Uninitialized variable
python3 cli.py tests/fixtures/errors/uninitialized.cio
```

These should all pass parsing but fail at semantic analysis with clear error messages.

---

## Part 4: Automated Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Mapping tests
pytest tests/test_mappings.py -v

# Code generation tests
pytest tests/test_codegen.py -v
```

### Run Component Self-Tests

Each source file has a `__main__` block for quick testing:

```bash
cd src && python3 confucio_parser.py       # Parses a test program
cd src && python3 confucio_ast_builder.py   # Builds AST from test program
cd src && python3 confucio_semantic.py      # Runs semantic analysis on a test AST
cd src && python3 confucio_codegen.py       # Generates LLVM IR from a test AST
cd src && python3 confucio_mappings.py      # Prints all mappings
```

---

## Part 5: Testing the Code Generation Pipeline

### Verify Operator Mapping

Run the code generation tests to confirm operators are correctly translated:

```bash
python3 tests/test_codegen.py
```

Expected: all Confuc-IO operators map to the correct LLVM instructions:
- `/` → `add`, `~` → `sub`, `Bool` → `mul`, `+` → `sdiv`
- `=` → `icmp >`, `#` → `icmp <`, `@@` → `icmp ==`

### Inspect Generated IR

```bash
python3 cli.py examples/arithmetic.cio --output-llvm
cat examples/arithmetic.ll
```

Verify the LLVM IR uses real instructions (`add`, `sub`, `mul`, `sdiv`) and real types (`i32`, `double`, `i8*`).

---

## Quick Test Checklist

```bash
# 1. Verify mappings
python3 cli.py --verify-mappings

# 2. Parse + AST + run all examples
python3 cli.py examples/hello_world.cio
python3 cli.py examples/arithmetic.cio
python3 cli.py examples/fibonacci.cio
python3 cli.py examples/strings.cio
python3 cli.py examples/calculator.cio

# 3. Generate outputs
python3 cli.py examples/calculator.cio --output-ast --output-parse-tree --output-llvm

# 4. Run automated tests
pytest tests/ -v
```
