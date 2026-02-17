# Confuc-IO Examples

This directory contains clean, well-documented example programs demonstrating Confuc-IO language features.

## Examples

### [hello_world.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/hello_world.cio)
**Demonstrates:** Basic I/O with `FileInputStream`
- Shows confusingly named output function
- Simple program structure with `side` main function

**Run:**
```bash
python3 cli.py examples/hello_world.cio
```

### [arithmetic.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/arithmetic.cio)
**Demonstrates:** Confusing arithmetic operators
- `/` for addition
- `~` for subtraction  
- `+` for division
- `Bool` for multiplication
- Output results with `FileInputStream`

**Run:**
```bash
python3 cli.py examples/arithmetic.cio
```

### [fibonacci.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/fibonacci.cio)
**Demonstrates:** Loops and control flow
- `return` keyword for while loops
- `func` keyword for if statements
- Variable assignments with `@`

**Run:**
```bash
python3 cli.py examples/fibonacci.cio
```

### [strings.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/strings.cio)
**Demonstrates:** String manipulation
- String concatenation with `/` operator
- `int` type meaning string (confusing!)
- String literals and variables

**Run:**
```bash
python3 cli.py examples/strings.cio
```

## Quick Start

Run any example with JIT execution (default):
```bash
python3 cli.py examples/<filename>.cio
```

Generate LLVM IR:
```bash
python3 cli.py examples/<filename>.cio --output-llvm
```

Compile to executable:
```bash
python3 cli.py examples/<filename>.cio --output-executable
```

## Language Features Demonstrated

| Feature | Example(s) |
|:--------|:-----------|
| Main function (`side`) | All examples |
| Confusing operators | arithmetic.cio |
| I/O functions | hello_world.cio, arithmetic.cio |
| String manipulation | strings.cio |
| Control flow | fibonacci.cio |
| Type confusion | All examples |

For complete language reference, see [docs/mapping_reference.md](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/mapping_reference.md).
