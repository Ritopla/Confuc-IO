"""
Confuc-IO Lexer

Tokenizes Confuc-IO source code using the language mappings.
Handles keywords, types, operators, delimiters, and comments.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional
from confucio_mappings import (
    KEYWORD_MAPPINGS,
    TYPE_MAPPINGS,
    OPERATOR_MAPPINGS,
    DELIMITER_MAPPINGS,
    COMMENT_SYMBOL,
    MAIN_FUNCTION_NAME
)


class TokenType(Enum):
    """Token types for Confuc-IO language"""
    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    
    # Keywords
    KEYWORD = auto()
    
    # Types
    TYPE = auto()
    
    # Operators
    OPERATOR = auto()
    
    # Delimiters
    DELIMITER = auto()
    
    # Special
    COMMENT = auto()
    NEWLINE = auto()
    WHITESPACE = auto()
    EOF = auto()


@dataclass
class Token:
    """Represents a single token in the source code"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class Lexer:
    """Lexical analyzer for Confuc-IO source code"""
    
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """Get the current character without advancing"""
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek ahead at a character"""
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Advance to the next character and return current"""
        if self.position >= len(self.source):
            return None
        
        char = self.source[self.position]
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Skip comment lines starting with È"""
        if self.current_char() == COMMENT_SYMBOL:
            # Skip until end of line
            while self.current_char() and self.current_char() != '\n':
                self.advance()
    
    def read_number(self) -> Token:
        """Read a numeric literal (integer or float)"""
        start_line = self.line
        start_column = self.column
        num_str = ''
        has_dot = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break  # Second dot, stop
                has_dot = True
            num_str += self.current_char()
            self.advance()
        
        token_type = TokenType.FLOAT_LITERAL if has_dot else TokenType.INTEGER
        return Token(token_type, num_str, start_line, start_column)
    
    def read_string(self) -> Token:
        """Read a string literal enclosed in quotes"""
        start_line = self.line
        start_column = self.column
        quote_char = self.current_char()  # Can be ' or "
        self.advance()  # Skip opening quote
        
        string_value = ''
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                # Handle escape sequences
                escape_char = self.current_char()
                if escape_char == 'n':
                    string_value += '\n'
                elif escape_char == 't':
                    string_value += '\t'
                elif escape_char == '\\':
                    string_value += '\\'
                elif escape_char == quote_char:
                    string_value += quote_char
                else:
                    string_value += escape_char
                self.advance()
            else:
                string_value += self.current_char()
                self.advance()
        
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING_LITERAL, string_value, start_line, start_column)
    
    def read_identifier(self) -> Token:
        """Read an identifier or keyword"""
        start_line = self.line
        start_column = self.column
        identifier = ''
        
        # First character must be letter or underscore
        if self.current_char() and (self.current_char().isalpha() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()
        
        # Subsequent characters can be letters, digits, or underscores
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()
        
        # Determine if it's a keyword, type, or identifier
        if identifier in KEYWORD_MAPPINGS:
            return Token(TokenType.KEYWORD, identifier, start_line, start_column)
        elif identifier in TYPE_MAPPINGS:
            return Token(TokenType.TYPE, identifier, start_line, start_column)
        else:
            return Token(TokenType.IDENTIFIER, identifier, start_line, start_column)
    
    def read_operator(self) -> Optional[Token]:
        """Read an operator"""
        start_line = self.line
        start_column = self.column
        
        # Check for multi-character operators first
        two_char = self.current_char() + (self.peek_char() or '')
        if two_char in OPERATOR_MAPPINGS:
            self.advance()
            self.advance()
            return Token(TokenType.OPERATOR, two_char, start_line, start_column)
        
        # Check for single-character operators
        if self.current_char() in OPERATOR_MAPPINGS:
            op = self.current_char()
            self.advance()
            return Token(TokenType.OPERATOR, op, start_line, start_column)
        
        # Special case for 'Bool' keyword used as multiplication operator
        if self.current_char() == 'B':
            # Look ahead for 'Bool'
            if (self.peek_char(1) == 'o' and 
                self.peek_char(2) == 'o' and 
                self.peek_char(3) == 'l'):
                # Check if it's followed by non-identifier character
                next_char = self.peek_char(4)
                if not next_char or not (next_char.isalnum() or next_char == '_'):
                    op = 'Bool'
                    for _ in range(4):
                        self.advance()
                    return Token(TokenType.OPERATOR, op, start_line, start_column)
        
        return None
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code"""
        while self.position < len(self.source):
            self.skip_whitespace()
            
            if self.current_char() is None:
                break
            
            # Check for comment
            if self.current_char() == COMMENT_SYMBOL:
                self.skip_comment()
                continue
            
            # Check for newline
            if self.current_char() == '\n':
                self.advance()
                continue
            
            # Check for string literal
            if self.current_char() in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # Check for number
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Check for delimiter
            if self.current_char() in DELIMITER_MAPPINGS:
                token = Token(TokenType.DELIMITER, self.current_char(), self.line, self.column)
                self.tokens.append(token)
                self.advance()
                continue
            
            # Check for special character operators and keywords (like *)
            if self.current_char() == '*':
                # * maps to return keyword
                token = Token(TokenType.KEYWORD, '*', self.line, self.column)
                self.tokens.append(token)
                self.advance()
                continue
            
            # Try to read operator
            op_token = self.read_operator()
            if op_token:
                self.tokens.append(op_token)
                continue
            
            # Try to read identifier/keyword/type
            if self.current_char().isalpha() or self.current_char() == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Unknown character
            print(f"Warning: Unknown character '{self.current_char()}' at {self.line}:{self.column}")
            self.advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens


def tokenize_file(filename: str) -> List[Token]:
    """Tokenize a Confuc-IO source file"""
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    
    lexer = Lexer(source)
    return lexer.tokenize()


if __name__ == '__main__':
    # Test the lexer with a simple example
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
    
    lexer = Lexer(test_code)
    tokens = lexer.tokenize()
    
    print("Tokens:")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"  {token}")
