#!/usr/bin/env python3
"""
Confuc-IO Compiler CLI

Command-line interface for the Confuc-IO compiler.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from confucio_mappings import verify_mappings
from confucio_parser import ConfucIOParser
from confucio_semantic import SemanticAnalyzer, SemanticError


def main():
    parser = argparse.ArgumentParser(
        description='Confuc-IO Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s program.cio                    # Run program with JIT (default)
  %(prog)s program.cio --run              # Explicitly run with JIT
  %(prog)s program.cio --output-llvm      # Generate LLVM IR file
  %(prog)s program.cio --output-executable # Generate standalone binary
  %(prog)s program.cio --output-ast       # Generate AST
'''
    )
    
    parser.add_argument('input', nargs='?', help='Input Confuc-IO source file (.cio)')
    parser.add_argument('--run', action='store_true',
                       help='Execute program using JIT (default if no output specified)')
    parser.add_argument('--output-ast', action='store_true',
                       help='Generate and save AST')
    parser.add_argument('--output-llvm', action='store_true',
                       help='Generate and save LLVM IR')
    parser.add_argument('--output-executable', action='store_true',
                       help='Generate executable binary (AOT compilation)')
    parser.add_argument('-O0', dest='opt_level', action='store_const', const=0,
                       help='No optimization (default)')
    parser.add_argument('-O1', dest='opt_level', action='store_const', const=1,
                       help='Basic optimization')
    parser.add_argument('-O2', dest='opt_level', action='store_const', const=2,
                       help='Moderate optimization')
    parser.add_argument('-O3', dest='opt_level', action='store_const', const=3,
                       help='Aggressive optimization')
    parser.add_argument('--verify-mappings', action='store_true',
                       help='Verify language mappings and exit')
    
    args = parser.parse_args()
    
    # Set default optimization level
    if args.opt_level is None:
        args.opt_level = 0
    
    # Verify mappings if requested
    if args.verify_mappings:
        print("Verifying Confuc-IO language mappings...")
        if verify_mappings():
            print("✓ All mappings are valid!")
            return 0
        else:
            print("✗ Mapping verification failed!")
            return 1
    
    # Check input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return 1
    
    try:
        # Step 1: Parse
        print(f"Parsing {input_path.name}...")
        confucio_parser = ConfucIOParser()
        parse_tree = confucio_parser.parse_file(str(input_path))
        print("✓ Parsing successful")
        
        if args.output_ast:
            ast_file = input_path.with_suffix('.ast')
            with open(ast_file, 'w') as f:
                f.write(parse_tree.pretty())
            print(f"✓ AST saved to {ast_file}")
        
        # Step 2: Build AST
        from confucio_ast_builder import build_ast, ASTBuilderError
        
        try:
            print("\nBuilding AST...")
            ast = build_ast(parse_tree)
            print("✓ AST built successfully")
        except ASTBuilderError as e:
            print(f"✗ AST building failed: {e}")
            return 1
        
        # Step 3: Semantic Analysis
        from confucio_semantic import SemanticAnalyzer, SemanticError
        
        print("Running semantic analysis...")
        analyzer = SemanticAnalyzer()
        try:
            analyzer.analyze(ast)
            print("✓ Semantic analysis passed")
        except SemanticError as e:
            print(f"✗ Semantic error: {e}", file=sys.stderr)
            return 1
        
        # Step 4: Code Generation and/or Execution
        from confucio_codegen import CodeGenerator, CodeGenError
        
        print("\nGenerating LLVM IR...")
        codegen = CodeGenerator()
        try:
            llvm_ir = codegen.generate(ast)
            print("✓ LLVM IR generated successfully")
            
            # Apply optimization if requested
            if args.opt_level > 0:
                print(f"Applying optimization level: -O{args.opt_level}")
                llvm_ir = codegen.optimize(args.opt_level)
                print("✓ Optimization complete")
            
            # Save LLVM IR if requested
            if args.output_llvm:
                llvm_file = input_path.with_suffix('.ll')
                with open(llvm_file, 'w') as f:
                    f.write(llvm_ir)
                print(f"✓ LLVM IR saved to {llvm_file}")
            
            # Generate executable if requested (AOT compilation)
            if args.output_executable:
                exe_file = input_path.with_suffix('')
                print(f"\nGenerating executable: {exe_file}")
                try:
                    codegen.generate_executable(exe_file)
                except CodeGenError as e:
                    print(f"✗ {e}", file=sys.stderr)
                    return 1
            
            # Execute with JIT if --run or no output flags
            should_run = args.run or not (args.output_llvm or args.output_executable or args.output_ast)
            
            if should_run:
                print("\nExecuting program via JIT...")
                print("-" * 60)
                try:
                    exit_code = codegen.execute()
                    print("-" * 60)
                    print(f"✓ Program exited with code: {exit_code}")
                except Exception as e:
                    print("-" * 60)
                    print(f"✗ Execution error: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()
                    return 1
        
        except CodeGenError as e:
            print(f"✗ Code generation error: {e}", file=sys.stderr)
            return 1
        
        return 0
        
    except SemanticError as e:
        print(f"Semantic error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
