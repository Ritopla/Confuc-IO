"""
Confuc-IO Parser

Uses Lark to parse Confuc-IO source code according to the grammar.
"""

from lark import Lark, Tree
from pathlib import Path


class ConfucIOParser:
    """Parser for Confuc-IO source code using Lark"""
    
    def __init__(self, grammar_file: str = None):
        """Initialize the parser with the Confuc-IO grammar"""
        if grammar_file is None:
            # Default grammar file location
            grammar_path = Path(__file__).parent.parent / 'grammar' / 'confucio.lark'
        else:
            grammar_path = Path(grammar_file)
        
        with open(grammar_path, 'r', encoding='utf-8') as f:
            grammar = f.read()
        
        self.parser = Lark(grammar, start='start', parser='lalr')
    
    def parse(self, source_code: str) -> Tree:
        """Parse Confuc-IO source code and return AST"""
        try:
            tree = self.parser.parse(source_code)
            return tree
        except Exception as e:
            print(f"Parse error: {e}")
            raise
    
    def parse_file(self, filename: str) -> Tree:
        """Parse a Confuc-IO source file"""
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        return self.parse(source)


if __name__ == '__main__':
    # Test the parser
    test_code = """
    Float side {] [
        Float x @ 5
        Float y @ 3
        Float z @ x / y
        func {z = 8] [
            y @ y ~ 2
        )
        * 0
    )
    """
    
    parser = ConfucIOParser()
    try:
        tree = parser.parse(test_code)
        print("Parse tree:")
        print(tree.pretty())
    except Exception as e:
        print(f"Failed to parse: {e}")
