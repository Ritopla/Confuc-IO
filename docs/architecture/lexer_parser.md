# Lexer and Parser

## Overview

The lexer and parser form the first phase of the Confuc-IO compiler, responsible for converting source code text into a structured parse tree.

## Technology Choice

**Tool:** [Lark Parser Generator](https://lark-parser.readthedocs.io/)  
**Algorithm:** LALR(1)  
**Grammar File:** `grammar/confucio.lark`

### Why Lark?

1. **Declarative Grammar:** Easy to read and maintain
2. **Python Integration:** Native Python library
3. **Good Error Messages:** Helpful for debugging
4. **Tree Construction:** Automatic parse tree building
5. **Flexibility:** Supports custom transformers

## Grammar Structure

The grammar is defined in EBNF (Extended Backus-Naur Form) syntax:

```lark
// Top level
start: statement*

// Statements
statement: variable_declaration
         | assignment
         | print_statement
         | input_statement
         | if_statement
         | while_statement
         | for_statement
         | return_statement
         | function_declaration

// Expressions
expression: binary_operation
          | literal
          | variable
          | ...
```

## Handling Confusing Delimiters

### The Challenge

Confuc-IO uses confusing delimiters:
- `{` means `(`
- `]` means `)`
- `(` means `[`
- `}` means `]`
- `[` means `{`
- `)` means `}`

### Solution: Terminal Mapping

We define terminals that match the confusing syntax:

```lark
// Delimiter terminals (confusing versions)
LPAREN: "{"          // Actually means (
RPAREN: "]"          // Actually means )
LBRACKET: "("        // Actually means [
RBRACKET: "}"        // Actually means ]
LBRACE: "["          // Actually means {
RBRACE: ")"          // Actually means }
```

Then use them in rules where their conventional meaning is needed:

```lark
function_declaration: TYPE_FLOAT MAIN_FUNCTION LPAREN RPAREN LBRACE statement* RBRACE
//                                             {      ]       [      ...      )
```

This allows the grammar to look conventional while accepting confusing syntax.

## Lexical Analysis (Tokenization)

### Token Categories

1. **Keywords:** `func`, `for`, `return`, `if`, etc.
2. **Types:** `Float`, `int`, `String`, `While`
3. **Operators:** `/`, `~`, `+`, `Bool`, `@`, etc.
4. **Delimiters:** `{`, `]`, `(`, `)`, etc.
5. **Literals:** Numbers, strings
6. **Identifiers:** Variable/function names
7. **Comments:** Lines starting with `È`

### Priority System

Lark processes terminals in order of specificity:
1. Keywords (most specific)
2. Language operators
3. Identifiers (catch-all for names)

Example:
```lark
// Keywords must come before identifiers
TYPE_FLOAT: "Float"
TYPE_INT: "int"
// ...
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
```

## Syntactic Analysis (Parsing)

### Parse Tree Construction

Lark automatically builds a parse tree with:
- **Nodes:** Rule names (e.g., `variable_declaration`)
- **Leaves:** Terminal tokens (e.g., `TYPE_FLOAT`, `IDENTIFIER`)

Example parse tree for `Float x @ 5`:
```
variable_declaration
├── TYPE_FLOAT: "Float"
├── IDENTIFIER: "x"
├── OP_ASSIGN: "@"
└── literal
    └── INT_LIT: "5"
```

### Associativity & Precedence

Binary operators use precedence levels:

```lark
?expression: comparison

?comparison: additive (("@@" | "!@") additive)?

?additive: multiplicative (("/" | "~") multiplicative)*

?multiplicative: primary (("Bool" | "+") primary)*

?primary: literal | variable | "(" expression ")"
```

- **Lowest precedence:** Comparison (`@@`, `!@`)
- **Medium:** Additive (`/`, `~`)
- **High:** Multiplicative (`Bool`, `+`)
- **Highest:** Primary (literals, variables, parentheses)

## Error Handling

### Syntax Errors

Lark provides detailed error messages:
```
Unexpected token Token('SEMICOLON', ';') at line 5, column 10.
Expected one of:
    * TYPE_FLOAT
    * TYPE_INT
    * ...
```

### Location Tracking

Every token includes:
- **Line number**
- **Column number**
- **Character position**

This enables precise error reporting.

## Implementation Details

### Parser Class

[confucio_parser.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/src/confucio_parser.py)

```python
class ConfucIOParser:
    def __init__(self):
        grammar_path = Path(__file__).parent.parent / 'grammar' / 'confucio.lark'
        self.parser = Lark.open(
            grammar_path,
            parser='lalr',
            start='start',
            propagate_positions=True
        )
    
    def parse(self, source_code: str):
        return self.parser.parse(source_code)
```

### Key Features

1. **Position Propagation:** `propagate_positions=True` tracks source locations
2. **LALR Parser:** Fast, efficient for most grammars
3. **Start Symbol:** `start` rule defines entry point

## Design Decisions

### Why Not Write a Custom Lexer/Parser?

**Reasons for using Lark:**
1. **Time Efficiency:** Grammar-based approach is faster to develop
2. **Maintainability:** Easier to modify grammar than custom code
3. **Correctness:** Parser generators are well-tested
4. **Features:** Built-in error recovery and tree construction

### Why LALR vs LL or LR?

**LALR chosen because:**
1. **Performance:** Faster than full LR
2. **Memory:** Smaller parse tables than LR
3. **Coverage:** Handles most programming language grammars
4. **Lark Support:** Well-supported in Lark

## Common Issues & Solutions

### Issue 1: Delimiter Confusion

**Problem:** Mixing up which delimiter to use  
**Solution:** Always use the confusing delimiter in the source; grammar handles the mapping

### Issue 2: Operator Ambiguity

**Problem:** Operator precedence unclear  
**Solution:** Explicit precedence levels in grammar

### Issue 3: Comment Parsing

**Problem:** Comments breaking tokenization  
**Solution:** Comments handled as ignored tokens with `%ignore` directive

## Testing

### Unit Tests

[tests/unit/test_parser.py](file:///Users/ritopla/Desktop/ILP/Confuc-IO/tests/unit/) (if exists)

Tests include:
- Valid syntax parsing
- Error detection
- Token extraction
- Tree structure validation

### Test Fixtures

[tests/fixtures/basic/](file:///Users/ritopla/Desktop/ILP/Confuc-IO/tests/fixtures/basic/)

Simple programs to verify parsing correctness.

## Next Step

After parsing, the parse tree is transformed into an AST by the AST Builder.

→ [Next: AST Design](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/architecture/ast.md)
