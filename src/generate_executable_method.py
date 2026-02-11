    def generate_executable(self, output_path: str):
        """
        Generate executable from LLVM IR
        
        Note: This requires LLVM tools (llc, clang) to be installed.
        As an alternative, users can manually run:
          1. Save LLVM IR: python3 cli.py program.cio --output-llvm
          2. Compile to object: llc -filetype=obj program.ll -o program.o
          3. Link: clang program.o -o program
        """
        import subprocess
        import tempfile
        import os
        
        # Get LLVM IR
        llvm_ir = str(self.module)
        
        # Write IR to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(llvm_ir)
            ll_file = f.name
        
        try:
            # Try to compile with llc (LLVM compiler)
            obj_file = ll_file.replace('.ll', '.o')
            
            # Step 1: Compile LLVM IR to object file
            result = subprocess.run(
                ['llc', '-filetype=obj', ll_file, '-o', obj_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise CodeGenError(
                    f"llc compilation failed: {result.stderr}\n\n"
                    f"Make sure LLVM is installed. On macOS: brew install llvm"
                )
            
            # Step 2: Link object file to executable
            result = subprocess.run(
                ['clang', obj_file, '-o', output_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise CodeGenError(
                    f"Linking failed: {result.stderr}\n\n"
                    f"Make sure clang is installed."
                )
            
            print(f"✓ Executable generated: {output_path}")
            
        finally:
            # Clean up temporary files
            for temp_file in [ll_file, obj_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
