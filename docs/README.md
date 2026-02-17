# Documentation Index

Welcome to the Confuc-IO Compiler documentation. This guide provides comprehensive information about the language, architecture, and development.

## Quick Links

### Language Specification
- **[Mapping Reference](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/mapping_reference.md)** - Complete reference of all Confuc-IO mappings

### Architecture
- **[Overview](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/overview.md)** - High-level compiler architecture
- **[Lexer & Parser](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/lexer_parser.md)** - Tokenization and parsing using Lark
- **[AST](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/ast.md)** - Abstract Syntax Tree design
- **[Semantic Analysis](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/semantic_analysis.md)** - Type checking and validation
- **[Code Generation](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/code_generation.md)** - LLVM IR generation
- **[JIT Execution](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/jit_execution.md)** - Runtime execution with MCJIT

### Development
- **[Design Rationale](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/development/design_rationale.md)** - Why we made specific design choices
- **[Testing Guide](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/development/testing_guide.md)** - How to test the compiler

## Documentation Structure

```
docs/
├── mapping_reference.md          # Language mappings reference
├── architecture/                 # Compiler internals
│   ├── overview.md
│   ├── lexer_parser.md
│   ├── ast.md
│   ├── semantic_analysis.md
│   ├── code_generation.md
│   └── jit_execution.md
└── development/                  # Development guides
    ├── design_rationale.md
    └── testing_guide.md
```

## Getting Started

1. **New to Confuc-IO?** Start with the [Mapping Reference](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/mapping_reference.md)
2. **Want to understand the compiler?** Read the [Architecture Overview](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/overview.md)
3. **Contributing to development?** Check the [Design Rationale](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/development/design_rationale.md) and [Testing Guide](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/development/testing_guide.md)
