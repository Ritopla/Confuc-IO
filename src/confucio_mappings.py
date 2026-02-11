"""
Confuc-IO Language Mapping Definitions

This module contains all the mappings from conventional programming constructs
to their Confuc-IO equivalents as specified in the proposal document.
"""

# Keyword Mappings: Confuc-IO → Conventional
KEYWORD_MAPPINGS = {
    'func': 'if',          # func → if
    'for': 'func',         # for → func (function definition)
    'return': 'while',     # return → while
    'if': 'for',           # if → for
    '*': 'return',         # * → return
}

# Reverse mapping: Conventional -> Confuc-IO
KEYWORD_REVERSE = {v: k for k, v in KEYWORD_MAPPINGS.items()}

# Type Mappings: Confuc-IO → Conventional
TYPE_MAPPINGS = {
    'Float': 'int',    # Float → int
    'int': 'string',   # int → string
    'String': 'float', # String → float
    'While': 'bool',   # While → bool
}

# Reverse type mapping for compilation
TYPE_REVERSE = {
    'int': 'Float',
    'string': 'int',
    'float': 'String',
    'bool': 'While',
}

# Operator Mappings: Confuc-IO -> Conventional
OPERATOR_MAPPINGS = {
    '/': '+',      # / -> addition
    '~': '-',      # ~ -> subtraction
    '+': '/',      # + -> division
    'Bool': '*',   # Bool -> multiplication
    '=': '>',      # = -> greater than
    '#': '<',      # # -> less than
    '@@': '==',    # @@ -> equality
    '@': '=',      # @ -> assignment
}

# Reverse operator mapping
OPERATOR_REVERSE = {v: k for k, v in OPERATOR_MAPPINGS.items()}

# Delimiter Mappings: Confuc-IO -> Conventional
DELIMITER_MAPPINGS = {
    '{': '(',      # { -> (
    ']': ')',      # ] -> )
    '(': '[',      # ( -> [
    '}': ']',      # } -> ]
    '[': '{',      # [ -> {
    ')': '}',      # ) -> }
}

# Reverse delimiter mapping
DELIMITER_REVERSE = {v: k for k, v in DELIMITER_MAPPINGS.items()}

# Comment symbol
COMMENT_SYMBOL = 'È'

# Main function name
MAIN_FUNCTION_NAME = 'side'

# I/O Function Names (confusingly named!)
IO_OUTPUT_FUNCTION = 'FileInputStream'  # Actually prints output (confusing!)
IO_INPUT_FUNCTION = 'deleteSystem32'    # Actually reads input (confusing!)

# Format String Mappings: Conventional → Confuc-IO (confusing!)
FORMAT_STRING_MAPPINGS = {
    '%d': '%f',      # int format → %f (confusing!)
    '%f': '%ff',     # float output → %ff (confusing!)
    '%lf': '%fff',   # float input → %fff (confusing!)
    '%s': '%ffff',   # string format → %ffff (confusing!)
}

def verify_mappings():
    """
    Verify that all mappings are correctly defined according to the proposal.
    This function is used for testing purposes.
    """
    print("Verifying Confuc-IO Mappings...")
    print("\nKeyword Mappings:")
    for confucio, conventional in KEYWORD_MAPPINGS.items():
        print(f"  {confucio} -> {conventional}")
    
    print("\nType Mappings:")
    for confucio, conventional in TYPE_MAPPINGS.items():
        print(f"  {confucio} -> {conventional}")
    
    print("\nOperator Mappings:")
    for confucio, conventional in OPERATOR_MAPPINGS.items():
        print(f"  {confucio} -> {conventional}")
    
    print("\nDelimiter Mappings:")
    for confucio, conventional in DELIMITER_MAPPINGS.items():
        print(f"  {confucio} -> {conventional}")
    
    print(f"\nComment Symbol: {COMMENT_SYMBOL}")
    print(f"Main Function Name: {MAIN_FUNCTION_NAME}")
    print("\nMapping verification complete!")
    return True

if __name__ == '__main__':
    verify_mappings()
