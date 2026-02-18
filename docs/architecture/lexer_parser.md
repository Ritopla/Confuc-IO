# Lexer and Parser

## Overview

The parser is the first phase of the compiler. It reads Confuc-IO source code and produces a **Parse Tree** — a structured representation that reflects the grammar rules.

**Files:**
- `src/confucio_parser.py` — Python wrapper around Lark
- `grammar/confucio.lark` — The grammar definition

## How It Works

The `ConfucIOParser` class loads the Lark grammar and exposes two methods:

```python
parser = ConfucIOParser()
tree = parser.parse(source_code)       # Parse a string
tree = parser.parse_file("program.cio") # Parse a file
```

Lark handles both lexing (tokenization) and parsing in one step using the LALR(1) algorithm.

## The Grammar

The grammar in `confucio.lark` is written in EBNF and defines how Confuc-IO source code is structured. It is also where the first layer of mapping happens.

### How the Grammar Handles Mappings

The grammar defines **rules with logical names** that match **Confuc-IO symbols**:

```lark
// Operators: the rule name describes what the operator DOES
op_add: "/"        // The "/" symbol means addition
op_sub: "~"        // The "~" symbol means subtraction
op_mul: "Bool"     // The word "Bool" means multiplication
op_div: "+"        // The "+" symbol means division

// Delimiters: the rule name describes the CONVENTIONAL role
delim_lparen: "{"  // The "{" symbol means "("
delim_rparen: "]"  // The "]" symbol means ")"
delim_lbrace: "["  // The "[" symbol means "{"
delim_rbrace: ")"  // The ")" symbol means "}"
```

Keywords work similarly — the rule name describes the conventional meaning:

```lark
// "func" in source code is used for if-statements
if_statement: KEYWORD_FUNC delim_lparen expression delim_rparen ...

// "return" in source code is used for while-loops
while_loop: KEYWORD_RETURN delim_lparen expression delim_rparen ...

// "if" in source code is used for for-loops
for_loop: KEYWORD_IF delim_lparen ...
```

### Types

Types are **not mapped** in the grammar. They are stored as-is:

```lark
TYPE_FLOAT: "Float"     // Stays "Float" in the Parse Tree
TYPE_INT: "int"         // Stays "int"
TYPE_STRING: "String"   // Stays "String"
TYPE_WHILE: "While"     // Stays "While"
```

### Expression Precedence

Operator precedence is defined by nesting rules:

```lark
expression → comparison → additive → multiplicative → primary
```

- **Lowest:** Comparison (`@@`, `=`, `#`)
- **Medium:** Additive (`/`, `~`) — these are add/subtract
- **Highest:** Multiplicative (`Bool`, `+`) — these are multiply/divide

### Inline Rules

Rules prefixed with `?` are **inline rules** — Lark removes them from the tree when they have a single child. For example:

```lark
?expression: comparison
?primary: INTEGER | IDENTIFIER | ...
```

This keeps the tree clean by avoiding unnecessary wrapper nodes.

## The Parse Tree

The output is a Lark `Tree` object. Each node has:
- A **rule name** (e.g., `while_loop`, `op_add`, `var_declaration`)
- **Children** that are either sub-trees (other rules) or `Token` objects (terminal values)

### Example

For the source code `Float x @ 5 / 3`:

```
var_declaration
  type  Float
  x
  op_assign
  additive
    5
    op_add
    3
```

Notice:
- The rule name `op_add` tells you this is addition
- The leaf value `/` is the actual Confuc-IO symbol (visible if you print the token)
- The type `Float` is stored as-is (not mapped)

You can save the Parse Tree with `--output-parse-tree` (saved as `.pt` file).

## What the Parser Does NOT Do

- It does **not** map types (`Float` stays `Float`)
- It does **not** create the AST (that's the next phase)
- It does **not** check semantics (no type checking, no scope validation)

The Parse Tree is a direct structural representation of the grammar rules applied to the source code.
