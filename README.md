# Confuc-IO Compiler

A compiler for the Confuc-IO programming language with intentionally counterintuitive semantics.

## Installation

```bash
pip3 install -r requirements.txt
```

## Mappings

### Keywords
- `func` → if
- `for` → func (function definition)
- `return` → while
- `if` → for
- `*` → return

### Types
- `Float` → int
- `int` → string  
- `String` → float
- `While` → bool

### Operators
- `/` → + (addition)
- `~` → - (subtraction)
- `+` → / (division)
- `Bool` → * (multiplication)
- `=` → > (greater than)
- `#` → < (less than)
- `@@` → == (equality)
- `@` → = (assignment)

### Delimiters
- `{` → `(`
- `]` → `)`
- `(` → `[`
- `}` → `]`
- `[` → `{`
- `)` → `}`

### Special
- `È` → comment symbol
- `side` → main function name

## Usage

```bash
# Compile a Confuc-IO program
python3 cli.py examples/example_basic.cio

# Generate AST
python3 cli.py examples/example_basic.cio --output-ast

# Generate LLVM IR
python3 cli.py examples/example_basic.cio --output-llvm

# Compile to executable
python3 cli.py examples/example_basic.cio --output-executable

# With optimization
python3 cli.py examples/example_basic.cio -O2 --output-executable
```

## Example

```confuc-io
È Confuc-IO program
Float side {] [
    Float x @ 5      È int x = 5
    Float y @ 3      È int y = 3  
    Float z @ x / y  È int z = x + y
    * 0              È return 0
)
```

## Language Features

- **Single global scope** - no variable shadowing allowed
- **Main function** must be named `side`
- **Type checking** with mapped type names
- **Semantic validation** including initialization checks

## Testing

```bash
pytest tests/
```
