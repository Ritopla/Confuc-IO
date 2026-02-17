# Code Generation

## Overview

The code generator translates the validated AST into LLVM Intermediate Representation (IR), which can then be JIT-compiled or compiled to machine code.

## Technology: LLVM

**Library:** llvmlite (Python bindings for LLVM)  
**Output:** LLVM IR (text or binary format)  
**Target:** Platform-independent intermediate representation

### Why LLVM?

1. **Industry Standard:** Used by Clang, Rust, Swift, etc.
2. **Optimization:** Powerful optimization passes
3. **Multi-Platform:** Targets many architectures
4. **JIT Support:** Built-in MCJIT engine
5. **Python Integration:** llvmlite provides clean API

## Implementation

**File:** [confucio_codegen.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/src/confucio_codegen.py)

### Code Generator Class

```python
class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="confucio_module")
        self.builder = None
        self.locals = {}
        self.string_counter = 0
        
        # Declare C standard library functions
        self._declare_c_functions()
    
    def generate(self, ast: Program) -> str:
        # Generate LLVM IR for each statement
        # Return IR as string
```

## Operator Mapping Application

### When Operators Are Mapped

Operators are mapped **during code generation**, not in the AST:

```python
def generate_binary_op(self, binop: BinaryOp) -> ir.Value:
    left = self.generate_expression(binop.left)
    right = self.generate_expression(binop.right)
    
    # Map confusing operator to conventional
    conventional_op = OPERATOR_MAPPINGS.get(binop.operator, binop.operator)
    
    if conventional_op == '+':
        # Handle both numeric addition and string concatenation
        if isinstance(left.type, ir.PointerType):  # String
            return self._concatenate_strings(left, right)
        return self.builder.add(left, right, name="addtmp")
```

### Why Map Here?

**Reasons:**
1. **AST Purity:** AST remains source-faithful
2. **IR Correctness:** Generated IR uses real operations
3. **Debug Clarity:** Can trace back to source operators

## Type Mapping to LLVM Types

### Confuc-IO → Conventional → LLVM

| Confuc-IO | Conventional | LLVM Type |
|:----------|:-------------|:----------|
| `Float` | `int` | `i32` |
| `String` | `float` | `double` |
| `int` | `string` | `i8*` |
| `While` | `bool` | `i1` |

### Type Translation

```python
def get_llvm_type(self, conventional_type: str) -> ir.Type:
    type_map = {
        'int': ir.IntType(32),
        'float': ir.DoubleType(),
        'string': ir.IntType(8).as_pointer(),
        'bool': ir.IntType(1),
    }
    return type_map[conventional_type]
```

## Notable Implementation Details

### 1. Main Function

Confuc-IO's `side` becomes LLVM's `main`:

```python
def generate_function_declaration(self, func: FunctionDeclaration):
    # Create function with LLVM calling convention
    func_type = ir.FunctionType(ir.IntType(32), [])
    llvm_func = ir.Function(self.module, func_type, name="main")
```

### 2. Variable Storage

Variables stored on stack using `alloca`:

```python
def generate_variable_declaration(self, decl: VariableDeclaration):
    llvm_type = self.get_llvm_type(decl.var_type)
    ptr = self.builder.alloca(llvm_type, name=decl.identifier)
    self.locals[decl.identifier] = ptr
    
    if decl.initializer:
        value = self.generate_expression(decl.initializer)
        self.builder.store(value, ptr)
```

### 3. String Literals

Strings stored as global constants:

```python
def _get_string_constant(self, s: str) -> ir.Value:
    b = bytearray(s.encode("utf8"))
    b.append(0)  # Null terminator
    
    c = ir.Constant(ir.ArrayType(ir.IntType(8), len(b)), b)
    name = f"str_{self.string_counter}"
    self.string_counter += 1
    
    gvar = ir.GlobalVariable(self.module, c.type, name=name)
    gvar.global_constant = True
    gvar.initializer = c
    
    return self.builder.bitcast(gvar, ir.IntType(8).as_pointer())
```

### 4. String Operations

#### Concatenation

Uses C stdlib (`strlen`, `malloc`, `strcpy`, `strcat`):

```python
def _concatenate_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
    # Get lengths
    len_left = self.builder.call(self.strlen, [left])
    len_right = self.builder.call(self.strlen, [right])
    
    # Allocate memory
    total_len = self.builder.add(len_left, len_right)
    total_len_null = self.builder.add(total_len, ir.Constant(ir.IntType(64), 1))
    result = self.builder.call(self.malloc, [total_len_null])
    
    # Copy and concatenate
    self.builder.call(self.strcpy, [result, left])
    self.builder.call(self.strcat, [result, right])
    
    return result
```

#### Comparison

Uses C stdlib (`strcmp`):

```python
def _compare_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
    cmp_result = self.builder.call(self.strcmp, [left, right])
    zero = ir.Constant(ir.IntType(32), 0)
    return self.builder.icmp_signed('==', cmp_result, zero, name="streq")
```

### 5. I/O Operations

#### Print (FileInputStream)

String literals printed directly; variables use format strings:

```python
def generate_print_statement(self, stmt: PrintStatement):
    for expr in stmt.expressions:
        if isinstance(expr, Literal) and expr.literal_type == 'string':
            # String literal - print directly
            str_const = self._get_string_constant(expr.value)
            self.builder.call(self.printf, [str_const])
        else:
            # Variable - use format string
            value = self.generate_expression(expr)
            self._print_value(value, FORMAT_STRING_MAPPINGS)
    
    # Print newline
    newline = self._get_string_constant("\n")
    self.builder.call(self.printf, [newline])
```

**Important:** Uses REAL printf format strings (`%d`, `%f`, `%s`), not confusing ones!

#### Input (deleteSystem32)

```python
def generate_input_statement(self, stmt: InputStatement):
    var_ptr = self.locals[stmt.variable]
    var_type = var_ptr.type.pointee
    
    if var_type == ir.IntType(32):
        fmt = self._get_string_constant("%d")
        self.builder.call(self.scanf, [fmt, var_ptr])
    elif isinstance(var_type, ir.PointerType):
        # String input requires buffer
        # ... (implementation details)
```

## C Standard Library Integration

### Declared Functions

```python
def _declare_c_functions(self):
    # printf
    self.printf = ir.Function(
        self.module,
        ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True),
        name="printf"
    )
    
    # scanf, malloc, strlen, strcpy, strcat, strcmp
    # ...
```

### Symbol Resolution

MCJIT automatically resolves these symbols via the system linker - no manual mapping needed!

## Control Flow

### If Statements

```python
def generate_if_statement(self, stmt: IfStatement):
    condition = self.generate_expression(stmt.condition)
    
    then_block = self.builder.append_basic_block("then")
    merge_block = self.builder.append_basic_block("merge")
    
    if stmt.else_body:
        else_block = self.builder.append_basic_block("else")
        self.builder.cbranch(condition, then_block, else_block)
    else:
        self.builder.cbranch(condition, then_block, merge_block)
    
    # Generate blocks...
```

### While Loops

```python
def generate_while_statement(self, stmt: WhileStatement):
    loop_cond = self.builder.append_basic_block("loop.cond")
    loop_body = self.builder.append_basic_block("loop.body")
    loop_end = self.builder.append_basic_block("loop.end")
    
    self.builder.branch(loop_cond)
    
    # Condition block
    self.builder.position_at_end(loop_cond)
    cond = self.generate_expression(stmt.condition)
    self.builder.cbranch(cond, loop_body, loop_end)
    
    # Body block
    # ...
```

## Optimization

### LLVM Optimization Passes

```python
def optimize(self, level: int = 2) -> str:
    llvm_ir = str(self.module)
    mod = llvm_binding.parse_assembly(llvm_ir)
    mod.verify()
    
    # Create pass manager
    pmb = llvm_binding.create_pass_manager_builder()
    pmb.opt_level = level
    pm = llvm_binding.create_module_pass_manager()
    pmb.populate(pm)
    
    # Run optimization
    pm.run(mod)
    
    return str(mod)
```

### Optimization Levels

- **-O0:** No optimization (fastest compilation)
- **-O1:** Basic optimization
- **-O2:** Moderate optimization (default)
- **-O3:** Aggressive optimization

## Generated IR Example

### Confuc-IO Source
```confucio
Float x @ 5 / 3
FileInputStream{x]
```

### Generated LLVM IR
```llvm
define i32 @main() {
entry:
  %x = alloca i32
  %addtmp = add i32 5, 3
  store i32 %addtmp, i32* %x
  
  %x.1 = load i32, i32* %x
  %fmt = bitcast [3 x i8]* @str_0 to i8*
  %printf_result = call i32 (i8*, ...) @printf(i8* %fmt, i32 %x.1)
  
  %newline = bitcast [2 x i8]* @str_1 to i8*
  %printf_result2 = call i32 (i8*, ...) @printf(i8* %newline)
  
  ret i32 0
}

@str_0 = constant [3 x i8] c"%d\00"
@str_1 = constant [2 x i8] c"\0a\00"
```

## Testing

### Code Generation Tests

[tests/unit/test_codegen.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/tests/unit/test_codegen.py)

Verify correct IR generation for various constructs.

## Design Decisions

### Why Defer Operator Mapping?

Allows AST to be source-faithful while IR is semantically correct.

### Why Use C stdlib for String Operations?

1. **Simplicity:** Don't reimplement standard functions
2. **Correctness:** Well-tested implementations
3. **Performance:** Optimized native code

### Why Stack Allocation for Variables?

Standard approach for local variables; LLVM optimizer can promote to registers.

## Next Step

After IR generation, the code can be JIT-executed or compiled to a binary.

→ [Next: JIT Execution](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/jit_execution.md)
