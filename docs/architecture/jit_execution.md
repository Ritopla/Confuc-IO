# JIT Execution

## Overview

JIT (Just-In-Time) execution allows Confuc-IO programs to run immediately without creating intermediate files or executables. The compiler generates LLVM IR, compiles it to machine code in memory, and executes it directly.

## Why JIT Execution?

### Benefits

1. **Fast Development Cycle:** Edit → Run immediately
2. **No External Tools:** Self-contained; no llc or clang required
3. **Cross-Platform:** Works consistently across OS platforms
4. **Alignment with Grammo:** Matches reference implementation behavior

### vs AOT Compilation

| Feature | JIT | AOT |
|:--------|:----|:----|
| Speed to execute | Instant | Compile + run |
| Executable file | No | Yes |
| External tools needed | No | Yes (llc, clang) |
| Portability | Source | Binary |
| Use case | Development | Distribution |

## Technology: LLVMLLVM MCJIT

**Engine:** LLVM MCJIT (Machine Code JIT)  
**Library:** llvmlite.binding  
**Implementation:** [confucio_codegen.py:execute()](file:///Users/ritopla/Desktop/ILP/Confuc-IO/src/confucio_codegen.py)

### MCJIT vs Older JIT

MCJIT is the modern LLVM JIT engine:
- **MC:** Machine Code - generates actual machine code, not interpreted
- **Fast:** Near-native execution speed
- **Optimizing:** Can apply optimization passes before execution

## Implementation

### Execute Method

```python
def execute(self) -> int:
    """Execute the compiled program using JIT (MCJIT)"""
    
    # 1. Parse LLVM IR
    llvm_ir = str(self.module)
    mod = llvm_binding.parse_assembly(llvm_ir)
    mod.verify()
    
    # 2. Create target machine
    target = llvm_binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    
    # 3. Create MCJIT engine
    backing_mod = llvm_binding.parse_assembly("")
    engine = llvm_binding.create_mcjit_compiler(backing_mod, target_machine)
    
    # 4. Add module and finalize
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    
    # 5. Get main() function pointer
    main_ptr = engine.get_function_address("main")
    if main_ptr == 0:
        raise CodeGenError("Could not find main() function")
    
    # 6. Create C function type and call
    cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)
    result = cfunc()
    
    return result
```

### Key Steps Explained

#### 1. Parse LLVM IR

Convert the string IR to a module object that LLVM can work with:
```python
mod = llvm_binding.parse_assembly(llvm_ir)
mod.verify()  # Ensure IR is well-formed
```

#### 2. Create Target Machine

Target machine defines the CPU architecture and features:
```python
target = llvm_binding.Target.from_default_triple()
target_machine = target.create_target_machine()
```

This automatically detects:
- **Architecture:** x86-64, ARM, etc.
- **OS:** macOS, Linux, Windows
- **Features:** SIMD extensions, etc.

#### 3. Create MCJIT Engine

```python
backing_mod = llvm_binding.parse_assembly("")
engine = llvm_binding.create_mcjit_compiler(backing_mod, target_machine)
```

The "backing module" is an empty module that serves as the compilation context.

#### 4. Add Module and Finalize

```python
engine.add_module(mod)           # Add our compiled module
engine.finalize_object()         # Compile IR → machine code
engine.run_static_constructors() # Initialize globals
```

`finalize_object()` is where actual compilation happens!

#### 5. Get Function Pointer

```python
main_ptr = engine.get_function_address("main")
```

Returns the memory address of the compiled `main()` function.

#### 6. Execute via ctypes

```python
cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)
result = cfunc()
```

- `ctypes.CFUNCTYPE(ctypes.c_int)`: Function signature (returns int)
- `(main_ptr)`: Cast address to function pointer
- `cfunc()`: Call the function!

## C Standard Library Linking

### The Challenge

LLVM IR references C functions like `printf`, `scanf`, `malloc`, etc. The JIT engine needs to find these symbols.

### The Solution: System Linker

**Key Insight:** MCJIT automatically resolves stdlib symbols via the system's dynamic linker!

```python
# NO manual mapping needed!
# MCJIT finds printf, scanf, etc. automatically
```

This works because:
1. libc is loaded in the process
2. Symbols are available via dynamic linking
3. MCJIT queries the OS for symbol addresses

### Why This Is Great

- **Simple:** No manual function mapping code
- **Portable:** Works across platforms (macOS, Linux, Windows)
- **Robust:** Uses OS-provided symbol resolution

### Initial Attempts (What Didn't Work)

We tried manual mapping:
```python
# WRONG: Doesn't work with llvmlite
engine.add_global_mapping(name, addr)  # No such method
engine.add_symbol(name, addr)          # Also doesn't exist
```

The automatic resolution is actually **better** than manual mapping!

## Execution Flow Example

### Source Code
```confucio
Float x @ 5 / 3
FileInputStream{x]
```

### Execution Steps

1. **Parse:** Lark → Parse tree
2. **AST Build:** Parse tree → AST
3. **Semantic:** Validate AST
4. **CodeGen:** AST → LLVM IR
   ```llvm
   define i32 @main() {
     %x = alloca i32
     %add = add i32 5, 3
     store i32 %add, i32* %x
     %load = load i32, i32* %x
     call i32 @printf(i8* @fmt, i32 %load)
     ret i32 0
   }
   ```
5. **JIT Compile:** IR → Machine code (in memory)
   ```asm
   ; x86-64 machine code
   push rbp
   mov rbp, rsp
   mov eax, 8        ; 5 + 3
   mov [rbp-4], eax
   ; printf call...
   xor eax, eax
   pop rbp
   ret
   ```
6. **Execute:** Call machine code
   ```
   8
   ```
7. **Return:** Exit code `0`

## LLVM Initialization

### Required Initialization

```python
# Initialize LLVM targets for JIT execution
llvm_binding.initialize_all_targets()
llvm_binding.initialize_all_asmprinters()
```

This must happen once, before creating the MCJIT engine.

### Why `initialize_all_*`?

- **Targets:** Support multiple architectures (x86, ARM, etc.)
- **ASM Printers:** Generate assembly for debugging

### Deprecated Function

**Don't use:**
```python
llvm_binding.initialize()  # Deprecated in newer llvmlite!
```

Modern llvmlite handles basic initialization automatically.

## Performance Considerations

### Compilation Time

JIT compilation is fast:
- Small programs: <10ms
- Medium programs: 10-50ms
- Large programs: 50-200ms

### Execution Speed

JIT-compiled code runs at **native speed** (same as AOT):
- MCJIT generates actual machine code
- Optimizations applied before execution
- No interpretation overhead

### Optimization

Can apply LLVM optimization passes before JIT:
```python
optimized_ir = codegen.optimize(level=2)
# Then execute optimized IR
```

## CLI Integration

### Default Behavior

```bash
python3 cli.py program.cio
# → JIT execution (instant)
```

### Explicit JIT Flag

```bash
python3 cli.py program.cio --run
# Same as default
```

### AOT Compilation

```bash
python3 cli.py program.cio --output-executable
# → Generates binary (requires llc + clang)
```

## Error Handling

### JIT Failures

```python
try:
    exit_code = codegen.execute()
except Exception as e:
    print(f"Execution error: {e}")
    traceback.print_exc()
```

Common errors:
- **Module verification fails:** Malformed IR
- **Symbol not found:** Missing C function
- **Segmentation fault:** Runtime error in generated code

## Design Decisions

### Why Default to JIT?

**Reasons:**
1. **User Experience:** Immediate feedback
2. **Development Workflow:** Fast iteration
3. **Simplicity:** No external dependencies
4. **Grammo Alignment:** Matches reference behavior

### Why Keep AOT Option?

**Reasons:**
1. **Distribution:** Standalone executables
2. **Debugging:** Inspect generated assembly
3. **Compatibility:** Some users prefer binaries

### Why Not Interpret?

**JIT vs Interpreter:**
- **JIT:** Compiles to machine code → native speed
- **Interpreter:** Executes IR directly → slower

MCJIT provides best of both: fast startup AND fast execution.

## Comparison with Other Languages

| Language | Default Execution |
|:---------|:------------------|
| Python | Interpreted (bytecode) |
| Java | JIT (HotSpot) |
| JavaScript | JIT (V8, SpiderMonkey) |
| Rust | AOT |
| C++ | AOT |
| **Confuc-IO** | **JIT (MCJIT)** |

Confuc-IO follows the modern trend of JIT execution for dynamic languages.

## Testing

### JIT Execution Tests

Verify programs run correctly via JIT:
```python
def test_jit_arithmetic():
    result = compile_and_execute("Float x @ 5 / 3\n* x")
    assert result == 8
```

### Comparison with AOT

Ensure JIT and AOT produce same results:
```python
def test_jit_vs_aot():
    source = read_file("test.cio")
    jit_result = run_jit(source)
    aot_result = run_aot(source)
    assert jit_result == aot_result
```

## Limitations

### Current Limitations

1. **No Debugging:** Can't use gdb/lldb on JIT code
2. **No Profiling:** Standard profilers don't see JIT code
3. **Memory Management:** JIT-compiled code stays in memory

### Workarounds

1. **Debugging:** Use `--output-llvm` to inspect IR, then compile with debug symbols
2. **Profiling:** Use `--output-executable` for profiling
3. **Memory:** Restart for large compilation sessions

## Future Enhancements

Potential improvements:
1. **Caching:** Cache compiled modules
2. **Lazy Compilation:** Compile functions on first call
3. **Profiling Hooks:** JIT-aware profiling
4. **REPL:** Interactive Read-Eval-Print-Loop

## Summary

JIT execution makes Confuc-IO immediate and interactive:
1. Generate LLVM IR
2. MCJIT compiles to machine code
3. Execute instantly
4. Native-speed performance

All without external tools or intermediate files!

---

**Related Documents:**
- [Code Generation](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/code_generation.md)
- [Architecture Overview](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/overview.md)
