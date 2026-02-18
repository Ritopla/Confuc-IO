# JIT Execution

## Overview

JIT (Just-In-Time) execution lets you run Confuc-IO programs immediately without generating intermediate files. The compiler produces LLVM IR, compiles it to machine code in memory, and executes it — all in one step.

**File:** `src/confucio_codegen.py` (the `execute()` method)

## How It Works

The `execute()` method in `CodeGenerator`:

1. **Parses** the LLVM IR string into a module object
2. **Verifies** the module is well-formed
3. **Creates** a target machine for the host CPU
4. **Creates** an MCJIT engine and adds the module
5. **Finalizes** the object (compiles IR → machine code)
6. **Gets** the address of the `main` function
7. **Calls** it via Python's `ctypes`

```python
cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)
result = cfunc()
```

The return value is the program's exit code.

## C Library Linking

MCJIT automatically resolves C standard library symbols (`printf`, `scanf`, `malloc`, etc.) through the system's dynamic linker. No manual symbol mapping is needed — the functions are available because libc is loaded in the process.

## AOT Compilation

As an alternative, the `generate_executable()` method produces a standalone binary:

1. Writes LLVM IR to a temporary `.ll` file
2. Runs `llc` to compile IR → object file (`.o`)
3. Runs `clang` to link → executable

This requires LLVM tools to be installed (`brew install llvm` on macOS).

## CLI Usage

```bash
# JIT execution (default)
python3 cli.py program.cio

# Explicit JIT
python3 cli.py program.cio --run

# AOT compilation
python3 cli.py program.cio --output-executable
```

If no output flag is specified, JIT is the default. If any output flag is given (`--output-llvm`, `--output-ast`, `--output-parse-tree`, `--output-executable`), JIT is skipped unless `--run` is also present.
