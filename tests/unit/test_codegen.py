"""
Integration test for LLVM IR code generation
Demonstrates the complete operator mapping translation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from confucio_ast import *
from confucio_codegen import CodeGenerator, CodeGenError
from confucio_mappings import OPERATOR_MAPPINGS


def test_operator_mapping_in_codegen():
    """Test that Confuc-IO operators are correctly mapped in LLVM IR"""
    
    print("=== Testing Operator Mapping in Code Generation ===\n")
    
    # Test case: x / y where / in Confuc-IO means addition
    program = Program(
        functions=[
            FunctionDef(
                return_type='Float',
                name='side',
                parameters=[],
                body=[
                    VarDeclaration(
                        var_type='Float',
                        name='x',
                        initializer=Literal(value=10, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='y',
                        initializer=Literal(value=5, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='sum',
                        initializer=BinaryOp(
                            operator='/',  # Confuc-IO: / means +
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='diff',
                        initializer=BinaryOp(
                            operator='~',  # Confuc-IO: ~ means -
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    ReturnStatement(value=Identifier(name='sum'))
                ]
            )
        ]
    )
    
    codegen = CodeGenerator()
    ir_code = codegen.generate(program)
    
    print("Generated LLVM IR:\n")
    print(ir_code)
    print("\n" + "="*60 + "\n")
    
    # Verify mappings
    print("Mapping Verification:")
    print(f"  Confuc-IO '/' → Conventional '+' → LLVM 'add'")
    assert 'add i32' in ir_code, "Expected 'add' instruction for / operator"
    print(f"    ✓ Found 'add' instruction in IR")
    
    print(f"  Confuc-IO '~' → Conventional '-' → LLVM 'sub'")
    assert 'sub i32' in ir_code, "Expected 'sub' instruction for ~ operator"
    print(f"    ✓ Found 'sub' instruction in IR")
    
    print("\n✓ All operator mappings correctly applied in LLVM IR generation!")


def test_all_arithmetic_operators():
    """Test all arithmetic operator mappings"""
    
    print("\n=== Testing All Arithmetic Operators ===\n")
    
    # Create program using all arithmetic operators
    program = Program(
        functions=[
            FunctionDef(
                return_type='Float',
                name='side',
                parameters=[],
                body=[
                    VarDeclaration(
                        var_type='Float',
                        name='a',
                        initializer=Literal(value=10, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='b',
                        initializer=Literal(value=2, literal_type='int')
                    ),
                    # Test: / → +
                    VarDeclaration(
                        var_type='Float',
                        name='add_result',
                        initializer=BinaryOp(
                            operator='/',
                            left=Identifier(name='a'),
                            right=Identifier(name='b')
                        )
                    ),
                    # Test: ~ → -
                    VarDeclaration(
                        var_type='Float',
                        name='sub_result',
                        initializer=BinaryOp(
                            operator='~',
                            left=Identifier(name='a'),
                            right=Identifier(name='b')
                        )
                    ),
                    # Test: Bool → *
                    VarDeclaration(
                        var_type='Float',
                        name='mul_result',
                        initializer=BinaryOp(
                            operator='Bool',
                            left=Identifier(name='a'),
                            right=Identifier(name='b')
                        )
                    ),
                    # Test: + → /
                    VarDeclaration(
                        var_type='Float',
                        name='div_result',
                        initializer=BinaryOp(
                            operator='+',
                            left=Identifier(name='a'),
                            right=Identifier(name='b')
                        )
                    ),
                    ReturnStatement(value=Literal(value=0, literal_type='int'))
                ]
            )
        ]
    )
    
    codegen = CodeGenerator()
    ir_code = codegen.generate(program)
    
    # Verify each operator mapping
    mappings_to_test = [
        ('/', '+', 'add'),
        ('~', '-', 'sub'),
       ('Bool', '*', 'mul'),
        ('+', '/', 'sdiv'),
    ]
    
    print("Operator Mapping Verification:\n")
    for confucio_op, conventional_op, llvm_inst in mappings_to_test:
        expected = f"{llvm_inst} i32"
        assert expected in ir_code, f"Expected '{expected}' for {confucio_op} operator"
        print(f"  ✓ {confucio_op:6} (Confuc-IO) → {conventional_op:2} (conventional) → {llvm_inst:4} (LLVM)")
    
    print("\n✓ All arithmetic operator mappings verified!")


def test_comparison_operators():
    """Test comparison operator mappings"""
    
    print("\n=== Testing Comparison Operators ===\n")
    
    program = Program(
        functions=[
            FunctionDef(
                return_type='Float',
                name='side',
                parameters=[],
                body=[
                    VarDeclaration(
                        var_type='Float',
                        name='x',
                        initializer=Literal(value=5, literal_type='int')
                    ),
                    VarDeclaration(
                        var_type='Float',
                        name='y',
                        initializer=Literal(value=3, literal_type='int')
                    ),
                    # Test: = → >
                    VarDeclaration(
                        var_type='While',
                        name='gt_result',
                        initializer=BinaryOp(
                            operator='=',
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    # Test: # → <
                    VarDeclaration(
                        var_type='While',
                        name='lt_result',
                        initializer=BinaryOp(
                            operator='#',
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    # Test: @@ → ==
                    VarDeclaration(
                        var_type='While',
                        name='eq_result',
                        initializer=BinaryOp(
                            operator='@@',
                            left=Identifier(name='x'),
                            right=Identifier(name='y')
                        )
                    ),
                    ReturnStatement(value=Literal(value=0, literal_type='int'))
                ]
            )
        ]
    )
    
    codegen = CodeGenerator()
    ir_code = codegen.generate(program)
    
    # Verify comparison operators
    comparisons = [
        ('=', '>', 'gttmp'),
        ('#', '<', 'lttmp'),
        ('@@', '==', 'eqtmp'),
    ]
    
    print("Comparison Operator Mapping Verification:\n")
    for confucio_op, conventional_op, llvm_name in comparisons:
        assert llvm_name in ir_code, f"Expected '{llvm_name}' for {confucio_op} operator"
        print(f"  ✓ {confucio_op:3} (Confuc-IO) → {conventional_op:2} (conventional) → icmp in LLVM")
    
    print("\n✓ All comparison operator mappings verified!")


if __name__ == '__main__':
    try:
        test_operator_mapping_in_codegen()
        test_all_arithmetic_operators()
        test_comparison_operators()
        
        print("\n" + "="*60)
        print("✓ ALL CODE GENERATION TESTS PASSED!")
        print("="*60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
