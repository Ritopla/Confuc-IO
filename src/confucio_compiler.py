"""
Confuc-IO Compiler

Main compiler orchestrator that coordinates all compilation phases:
Lexing → Parsing → Semantic Analysis → Code Generation → Optimization
"""

from pathlib import Path
from lark import Transformer
from confucio_parser import ConfucIOParser
from confucio_semantic import SemanticAnalyzer
from confucio_codegen import CodeGenerator
from confucio_ast import *


class ASTBuilder(Transformer):
    """Transform Lark parse tree to Confuc-IO AST"""
    
    def start(self, items):
        return Program(functions=items)
    
    def function_def(self, items):
        return_type = str(items[0])
        name = str(items[1])
        # Parameters would be extracted here
        # Body statements would be extracted from the rest
        return FunctionDef(
            return_type=return_type,
            name=name,
            parameters=[],
            body=[]
        )


class CompilerError(Exception):
    """Base class for compiler errors"""
    pass


class ConfucIOCompiler:
    """Main compiler for Confuc-IO language"""
    
    def __init__(self):
        self.parser = ConfucIOParser()
        self.semantic_analyzer = SemanticAnalyzer()
        self.code_generator = CodeGenerator()
        self.ast = None
        self.ir_code = None
    
    def compile(self, source_code: str, optimize_level: int = 0):
        """
        Compile Confuc-IO source code to LLVM IR
        
        Args:
            source_code: Confuc-IO source code string
            optimize_level: Optimization level (0-3)
        
        Returns:
            LLVM IR code as string
        """
        # Step 1: Parse
        parse_tree = self.parser.parse(source_code)
        
        # Step 2: Build AST (simplified for now)
        # In a full implementation, we'd use ASTBuilder transformer
        # For now, semantic analyzer works with manually built AST
        
        # Step 3: Semantic Analysis
        # self.semantic_analyzer.analyze(self.ast)
        
        # Step 4: Code Generation
        # self.ir_code = self.code_generator.generate(self.ast)
        
        # Step 5: Optimization
        # if optimize_level > 0:
        #     self.ir_code = self.code_generator.optimize(optimize_level)
        
        return parse_tree
    
    def compile_file(self, filename: str, optimize_level: int = 0):
        """Compile a Confuc-IO source file"""
        with open(filename, 'r', encoding='utf-8') as f:
            source_code = f.read()
        return self.compile(source_code, optimize_level)
    
    def get_ast(self):
        """Get the generated AST"""
        return self.ast
    
    def get_ir(self):
        """Get the generated LLVM IR"""
        return self.ir_code
    
    def save_ir(self, filename: str):
        """Save LLVM IR to file"""
        if not self.ir_code:
            raise CompilerError("No IR code generated yet")
        
        with open(filename, 'w') as f:
            f.write(self.ir_code)
    
    def generate_executable(self, output_filename: str):
        """
        Generate executable from LLVM IR
        (Requires LLVM toolchain to be installed)
        """
        import subprocess
        import tempfile
        
        if not self.ir_code:
            raise CompilerError("No IR code generated yet")
        
        # Save IR to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(self.ir_code)
            ir_file = f.name
        
        try:
            # Compile with llc to assembly
            asm_file = ir_file.replace('.ll', '.s')
            subprocess.run(['llc', '-filetype=asm', ir_file, '-o', asm_file], check=True)
            
            # Assemble and link with clang
            subprocess.run(['clang', asm_file, '-o', output_filename], check=True)
            
            print(f"✓ Executable generated: {output_filename}")
        except subprocess.CalledProcessError as e:
            raise CompilerError(f"Failed to generate executable: {e}")
        except FileNotFoundError:
            raise CompilerError(
                "LLVM toolchain (llc, clang) not found. "
                "Please install LLVM to generate executables."
            )


if __name__ == '__main__':
    # Test compiler
    test_code = """
    Float side {] [
        Float x @ 5
        Float y @ 3
        Float z @ x / y
        * 0
    )
    """
    
    compiler = ConfucIOCompiler()
    try:
        parse_tree = compiler.compile(test_code)
        print("✓ Compilation successful")
        print("\nParse tree:")
        print(parse_tree.pretty())
    except Exception as e:
        print(f"Compilation error: {e}")
