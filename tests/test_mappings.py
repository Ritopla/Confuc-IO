"""
Test suite for Confuc-IO language mappings
Verifies all mappings match the proposal specification
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from confucio_mappings import (
    KEYWORD_MAPPINGS,
    TYPE_MAPPINGS,
    OPERATOR_MAPPINGS,
    DELIMITER_MAPPINGS,
    COMMENT_SYMBOL,
    MAIN_FUNCTION_NAME,
    verify_mappings
)


class TestKeywordMappings:
    """Test keyword mappings against proposal specification"""
    
    def test_func_maps_to_if(self):
        assert KEYWORD_MAPPINGS['func'] == 'if'
    
    def test_for_maps_to_func(self):
        assert KEYWORD_MAPPINGS['for'] == 'func'
    
    def test_return_maps_to_while(self):
        assert KEYWORD_MAPPINGS['return'] == 'while'
    
    def test_if_maps_to_for(self):
        assert KEYWORD_MAPPINGS['if'] == 'for'
    
    def test_star_maps_to_return(self):
        assert KEYWORD_MAPPINGS['*'] == 'return'


class TestTypeMappings:
    """Test type mappings against proposal specification"""
    
    def test_Float_maps_to_int(self):
        assert TYPE_MAPPINGS['Float'] == 'int'
    
    def test_int_maps_to_string(self):
        assert TYPE_MAPPINGS['int'] == 'string'
    
    def test_String_maps_to_float(self):
        assert TYPE_MAPPINGS['String'] == 'float'
    
    def test_While_maps_to_bool(self):
        assert TYPE_MAPPINGS['While'] == 'bool'


class TestOperatorMappings:
    """Test operator mappings against proposal specification"""
    
    def test_slash_maps_to_addition(self):
        assert OPERATOR_MAPPINGS['/'] == '+'
    
    def test_tilde_maps_to_subtraction(self):
        assert OPERATOR_MAPPINGS['~'] == '-'
    
    def test_plus_maps_to_division(self):
        assert OPERATOR_MAPPINGS['+'] == '/'
    
    def test_Bool_maps_to_multiplication(self):
        assert OPERATOR_MAPPINGS['Bool'] == '*'
    
    def test_equals_maps_to_greater_than(self):
        assert OPERATOR_MAPPINGS['='] == '>'
    
    def test_hash_maps_to_less_than(self):
        assert OPERATOR_MAPPINGS['#'] == '<'
    
    def test_double_at_maps_to_equality(self):
        assert OPERATOR_MAPPINGS['@@'] == '=='
    
    def test_at_maps_to_assignment(self):
        assert OPERATOR_MAPPINGS['@'] == '='


class TestDelimiterMappings:
    """Test delimiter mappings against proposal specification"""
    
    def test_lcurly_maps_to_lparen(self):
        assert DELIMITER_MAPPINGS['{'] == '('
    
    def test_rbracket_maps_to_rparen(self):
        assert DELIMITER_MAPPINGS[']'] == ')'
    
    def test_lparen_maps_to_lbracket(self):
        assert DELIMITER_MAPPINGS['('] == '['
    
    def test_rcurly_maps_to_rbracket(self):
        assert DELIMITER_MAPPINGS['}'] == ']'
    
    def test_lbracket_maps_to_lcurly(self):
        assert DELIMITER_MAPPINGS['['] == '{'
    
    def test_rparen_maps_to_rcurly(self):
        assert DELIMITER_MAPPINGS[')'] == '}'


class TestSpecialSymbols:
    """Test special symbols"""
    
    def test_comment_symbol(self):
        assert COMMENT_SYMBOL == 'È'
    
    def test_main_function_name(self):
        assert MAIN_FUNCTION_NAME == 'side'


class TestMappingVerification:
    """Test mapping verification function"""
    
    def test_verify_mappings_passes(self):
        assert verify_mappings() is True
