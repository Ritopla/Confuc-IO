# Confuc-IO Compiler

A compiler for Confuc-IO, an educational programming language with intentionally confusing syntax mappings.

## Quick Start

```bash
# Run a program (JIT execution)
python3 cli.py examples/hello_world.cio

# Generate LLVM IR
python3 cli.py examples/arithmetic.cio --output-llvm

# Compile to executable
python3 cli.py examples/fibonacci.cio --output-executable
```

## Features

- ✅ **Confusing Syntax:** Keywords, types, operators, and delimiters all intentionally misleading
- ✅ **JIT Execution:** Instant program execution using LLVM MCJIT
- ✅ **LLVM Backend:** Industry-standard code generation and optimization
- ✅ **I/O Support:** Input/output with confusingly named functions
- ✅ **String Manipulation:** Concatenation and comparison
- ✅ **Control Flow:** If statements, while loops, for loops

## Language Overview

### Confusing Mappings

| You Write | It Means | Example |
|:----------|:---------|:--------|
| `Float` | `int` | `Float x @ 5` |
| `int` | `string` | `int name @ "Alice"` |
| `/` | `+` | `x / y` is addition |
| `~` | `-` | `x ~ y` is subtraction |
| `{` | `(` | Function calls use `{]` |
| `]` | `)` | |
| `func` | `if` | `func {condition] [...]` |
| `for` | `func` | Functions use `for` keyword |
| `return` | `while` | `return {condition] [...]` |

See [docs/mapping_reference.md](docs/mapping_reference.md) for complete mappings.

### Hello World

```confucio
È This is a comment (È symbol)

Float side {] [
    FileInputStream{"Hello, World!"]
    * 0
)
```

- `Float side` is the main function (`Float` = int type, `side` = main name)
- `{]` and `[` `)` are confusing delimiters for `()` and `{}`
- `FileInputStream` is the print function (confusing name!)
- `* 0` is the return statement (`*` operator = `return` keyword)

## Installation

### Requirements

- Python 3.8+
- llvmlite

### Setup

```bash
# Clone repository
git clone <repo-url>
cd Confuc-IO

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# JIT execution (default

)
python3 cli.py <file.cio>

# Explicit JIT
python3 cli.py <file.cio> --run

# Generate LLVM IR
python3 cli.py <file.cio> --output-llvm

# Compile to executable (requires llc and clang)
python3 cli.py <file.cio> --output-executable

# Optimization levels
python3 cli.py <file.cio> -O0  # No optimization
python3 cli.py <file.cio> -O1  # Basic
python3 cli.py <file.cio> -O2  # Moderate (default)
python3 cli.py <file.cio> -O3  # Aggressive
```

### Examples

See [examples/](examples/) directory for sample programs:
- [hello_world.cio](examples/hello_world.cio) - Basic I/O
- [arithmetic.cio](examples/arithmetic.cio) - Confusing operators
- [fibonacci.cio](examples/fibonacci.cio) - Loops and control flow
- [strings.cio](examples/strings.cio) - String manipulation

## Project Structure

```
Confuc-IO/
├── cli.py                    # Main compiler CLI
├── src/                      # Compiler source code
│   ├── confucio_parser.py   # Lexer & parser
│   ├── confucio_ast.py      # AST definitions
│   ├── confucio_ast_builder.py  # AST construction
│   ├── confucio_semantic.py # Semantic analysis
│   ├── confucio_codegen.py  # LLVM code generation & JIT
│   └── confucio_mappings.py # Language mappings
├── grammar/                  # Language grammar
│   └── confucio.lark        # Lark parser grammar
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test input files
├── examples/                 # Example programs
├── docs/                     # Documentation
│   ├── mapping_reference.md # Complete mapping reference
│   └── architecture/        # Compiler architecture docs
└── scripts/                  # Utility scripts
```

## Documentation

### For Users
- **[Mapping Reference](docs/mapping_reference.md)** - Complete language reference
- **[Examples](examples/README.md)** - Example programs with explanations

### For Developers
- **[Architecture Overview](docs/architecture/overview.md)** - Compiler design
- **[Lexer & Parser](docs/architecture/lexer_parser.md)** - Parsing details
- **[AST Design](docs/architecture/ast.md)** - Abstract syntax tree
- **[Semantic Analysis](docs/architecture/semantic_analysis.md)** - Type checking
- **[Code Generation](docs/architecture/code_generation.md)** - LLVM IR generation
- **[JIT Execution](docs/architecture/jit_execution.md)** - Just-in-time compilation
- **[Design Rationale](docs/development/design_rationale.md)** - Why we made specific choices
- **[Testing Guide](docs/development/testing_guide.md)** - How to test the compiler

## Development

### Running Tests

```bash
# Run all tests
python3 scripts/run_all_tests.py

# Run specific test file
python3 -m pytest tests/unit/test_codegen.py

# Run with coverage
python3 -m pytest --cov=src tests/
```

### Adding Features

1. Update grammar in `grammar/confucio.lark`
2. Add AST nodes in `src/confucio_ast.py`
3. Update AST builder in `src/confucio_ast_builder.py`
4. Add semantic checks in `src/confucio_semantic.py`
5. Implement code generation in `src/confucio_codegen.py`
6. Add tests and documentation

## Architecture

The compiler uses a multi-phase pipeline:

```
Source (.cio) → Lexer/Parser → AST → Semantic Analysis → LLVM IR → JIT/AOT
```

- **Lexer/Parser:** Uses Lark with LALR(1) algorithm
- **AST Builder:** Transforms parse tree to abstract syntax tree
- **Semantic Analyzer:** Type checking and validation
- **Code Generator:** Produces LLVM IR with proper operator mappings
- **JIT Execution:** Uses LLVM MCJIT for instant execution

See [docs/architecture/overview.md](docs/architecture/overview.md) for details.

## Contributing

Contributions welcome! Please:
1. Read the [design rationale](docs/development/design_rationale.md)
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## License

[License information here]

## Credits

- Inspired by Grammo (reference implementation)
- Uses [Lark](https://github.com/lark-parser/lark) for parsing
- Uses [LLVM](https://llvm.org/) via [llvmlite](https://github.com/numba/llvmlite) for code generation

## Learn More

- **Language Specification:** [Confuc-IO Proposal PDF](Confuc-IO%20proposal.pdf)
- **Full Documentation:** [docs/](docs/)
- **Example Programs:** [examples/](examples/)
