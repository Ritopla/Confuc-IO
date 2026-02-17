# Compiler Architecture Overview

## Introduction

The Confuc-IO compiler is a multi-phase compiler that translates Confuc-IO source code (with intentionally confusing mappings) into executable machine code. It uses LLVM as the backend and supports both JIT and AOT compilation.

## Pipeline

```
Source Code (.cio)
    ↓
┌───────────────┐
│ Lexer/Parser  │ → Tokens + Parse Tree (Lark)
└───────────────┘
    ↓
┌───────────────┐
│ AST Builder   │ → Abstract Syntax Tree
└───────────────┘
    ↓
┌───────────────┐
│ Semantic      │ → Validated AST
│ Analysis      │   (Type checking, scope validation)
└───────────────┘
    ↓
┌───────────────┐
│ Code          │ → LLVM IR
│ Generation    │   (Apply mappings, generate instructions)
└───────────────┘
    ↓
    ├─→ JIT Execution (MCJIT) → Direct execution
    └─→ AOT Compilation (llc + clang) → Executable binary
```

## Core Components

### 1. Lexer & Parser
**File:** `src/confucio_parser.py`  
**Grammar:** `grammar/confucio.lark`

- Uses Lark parser generator with LALR(1) algorithm
- Tokenizes Confuc-IO source code
- Builds parse tree from grammar
- Handles confusing delimiters and symbols

**Key Challenge:** Parsing confusing delimiters while maintaining correctness

### 2. AST Builder
**File:** `src/confucio_ast_builder.py`  
**Nodes:** `src/confucio_ast.py`

- Transforms Lark parse tree into custom AST
- Applies initial keyword/type mappings
- Creates structured representation of the program

**Key Challenge:** Designing AST nodes that represent both Confuc-IO syntax and conventional semantics

### 3. Semantic Analyzer
**File:** `src/confucio_semantic.py`

- Type checking with confusing type names
- Scope validation (single global scope)
- Variable initialization checks
- No shadowing enforcement

**Key Challenge:** Type checking where types have misleading names (Float = int, int = string, etc.)

### 4. Code Generator
**File:** `src/confucio_codegen.py`

- Generates LLVM IR from validated AST
- Applies operator mappings (/ = +, ~ = -, etc.)
- Handles I/O with C stdlib integration
- String operations (concatenation, comparison)

**Key Challenge:** Correctly mapping confusing operators to their actual operations

### 5. JIT Execution
**File:** `src/confucio_codegen.py` (execute method)

- Uses llvmlite MCJIT engine
- Links C standard library dynamically
- Executes main() immediately
- No external tools required

**Key Challenge:** Dynamic symbol resolution for C library functions

## Design Principles

### 1. Separation of Concerns
Each phase has a single responsibility:
- Lexer/Parser: Syntax
- AST Builder: Structure
- Semantic: Meaning
- CodeGen: Implementation

### 2. Mapping Application Timing
- **Keyword/Type mappings:** Applied during AST building
- **Operator mappings:** Applied during code generation
- **Delimiter mappings:** Handled by grammar

### 3. Error Handling
- Parse errors: Caught by Lark, reported with line/column
- Semantic errors: Custom exceptions with meaningful messages
- Code generation errors: Caught and reported before execution

## Data Flow Example

Consider: `Float x @ 5 / 3`

1. **Lexer:** `[TYPE_FLOAT, IDENTIFIER, OP_ASSIGN, INT_LIT, OP_ADD, INT_LIT]`
2. **Parser:** Parse tree with declaration and binary operation
3. **AST Builder:** `VariableDeclaration(type='int', name='x', init=BinaryOp('+', 5, 3))`
4. **Semantic:** Validates types, ensures `x` not already declared
5. **CodeGen:** 
   ```llvm
   %x = alloca i32
   %add = add i32 5, 3
   store i32 %add, i32* %x
   ```
6. **JIT:** Executes immediately

## File Organization

```
src/
├── confucio_compiler.py      # Main compiler interface
├── confucio_mappings.py      # Mapping definitions
├── confucio_parser.py        # Parser (uses Lark)
├── confucio_ast.py           # AST node definitions
├── confucio_ast_builder.py   # Parse tree → AST
├── confucio_semantic.py      # Semantic analysis
└── confucio_codegen.py       # LLVM IR generation + JIT
```

## Next Steps

- [Lexer & Parser Details](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/lexer_parser.md)
- [AST Design](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/ast.md)
- [Semantic Analysis](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/semantic_analysis.md)
- [Code Generation](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/code_generation.md)
- [JIT Execution](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/jit_execution.md)
