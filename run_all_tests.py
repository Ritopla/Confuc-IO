#!/usr/bin/env python3
"""
Confuc-IO Compiler Test Runner
Runs all tests from the testing guide automatically
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def run_test(name: str, command: str, should_fail: bool = False, cwd: str = ".") -> Tuple[bool, str]:
    """Run a single test command"""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}Test: {name}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"Command: {YELLOW}{command}{RESET}")
    print()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Check if test passed
        if should_fail:
            # For error tests, we expect non-zero exit code
            success = result.returncode != 0
            status = "PASS (error caught)" if success else "FAIL (should have errored)"
        else:
            # For success tests, we expect zero exit code
            success = result.returncode == 0
            status = "PASS" if success else "FAIL"
        
        # Print status
        color = GREEN if success else RED
        print(f"\n{color}{BOLD}Status: {status}{RESET}")
        
        return success, result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"{RED}{BOLD}Status: TIMEOUT{RESET}")
        return False, "Timeout"
    except Exception as e:
        print(f"{RED}{BOLD}Status: ERROR - {e}{RESET}")
        return False, str(e)

def main():
    """Run all tests from the testing guide"""
    print(f"{BOLD}{BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║        Confuc-IO Compiler - Automated Test Suite                 ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(RESET)
    
    tests = []
    passed = 0
    failed = 0
    
    # Part 1: Basic Compilation Tests
    print(f"\n{BOLD}━━━ PART 1: BASIC COMPILATION TESTS ━━━{RESET}")
    
    tests.append(("Unit Tests", "pytest tests/ -v", False))
    tests.append(("Parse Fibonacci", "python3 cli.py examples/fibonacci.cio", False))
    tests.append(("Parse with AST Output", "python3 cli.py examples/fibonacci.cio --output-ast", False))
    
    # Part 2: Code Generation Tests
    print(f"\n{BOLD}━━━ PART 2: CODE GENERATION TESTS ━━━{RESET}")
    
    tests.append(("Generate LLVM IR", "python3 cli.py examples/test_working.cio --output-llvm", False))
    tests.append(("Code Generation Unit Tests", "python3 tests/test_codegen.py", False))
    
    # Part 3: Error Handling Tests
    print(f"\n{BOLD}━━━ PART 3: ERROR HANDLING TESTS ━━━{RESET}")
    
    tests.append(("Missing Main Function", "python3 cli.py examples/errors/missing_main.cio", True))
    tests.append(("Undeclared Variable", "python3 cli.py examples/errors/undeclared_variable.cio", True))
    tests.append(("Variable Shadowing", "python3 cli.py examples/errors/shadowing.cio", True))
    tests.append(("Type Mismatch", "python3 cli.py examples/errors/type_mismatch.cio", True))
    
    # Run all tests
    for test_name, command, should_fail in tests:
        success, output = run_test(test_name, command, should_fail)
        if success:
            passed += 1
        else:
            failed += 1
    
    # Print summary
    print(f"\n{BOLD}{BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                      TEST SUMMARY                                 ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(RESET)
    
    total = passed + failed
    print(f"{BOLD}Total Tests:  {total}{RESET}")
    print(f"{GREEN}{BOLD}Passed:       {passed}{RESET}")
    print(f"{RED}{BOLD}Failed:       {failed}{RESET}")
    
    if failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! 🎉{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
