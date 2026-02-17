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

def run_test(name: str, command: str, should_fail: bool = False, cwd: str = ".", use_venv: bool = True) -> Tuple[bool, str]:
    """Run a single test command"""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}Test: {name}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"Command: {YELLOW}{command}{RESET}")
    print()
    
    # Activate virtual environment if needed
    if use_venv:
        command = f"source .venv/bin/activate && {command}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            executable='/bin/bash'  # Use bash to support source command
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
    
    # Part 1: Unit Tests
    print(f"\n{BOLD}━━━ PART 1: UNIT TESTS ━━━{RESET}")
    
    tests.append(("Mapping Tests", "PYTHONPATH=src pytest tests/unit/test_mappings.py -v", False))
    tests.append(("Code Generation Tests", "PYTHONPATH=src pytest tests/unit/test_codegen.py -v", False))
    
    # Part 2: Example Programs
    print(f"\n{BOLD}━━━ PART 2: EXAMPLE PROGRAMS ━━━{RESET}")
    
    tests.append(("Hello World", "python3 cli.py examples/hello_world.cio", False))
    tests.append(("Arithmetic", "python3 cli.py examples/arithmetic.cio", False))
    tests.append(("Fibonacci", "python3 cli.py examples/fibonacci.cio", False))
    tests.append(("Strings", "python3 cli.py examples/strings.cio", False))
    tests.append(("Calculator (AST)", "python3 cli.py examples/calculator.cio --output-ast", False))
    tests.append(("Test Params", "python3 cli.py examples/test_params.cio", False))
    
    # Part 3: Basic Fixtures
    print(f"\n{BOLD}━━━ PART 3: BASIC FIXTURES ━━━{RESET}")
    
    tests.append(("Basic Arithmetic", "python3 cli.py tests/fixtures/basic/arithmetic.cio", False))
    tests.append(("Basic Fibonacci", "python3 cli.py tests/fixtures/basic/fibonacci.cio", False))
    
    # Part 4: Control Flow Fixtures
    print(f"\n{BOLD}━━━ PART 4: CONTROL FLOW ━━━{RESET}")
    
    tests.append(("While Loop Simple", "python3 cli.py tests/fixtures/control_flow/test_while_simple.cio", False))
    
    # Part 5: String Fixtures
    print(f"\n{BOLD}━━━ PART 5: STRING OPERATIONS ━━━{RESET}")
    
    tests.append(("String Simple", "python3 cli.py tests/fixtures/strings/test_string_simple.cio", False))
    tests.append(("String Concatenation", "python3 cli.py tests/fixtures/strings/test_string_concat.cio", False))
    
    # Part 6: I/O Print Tests (non-interactive)
    print(f"\n{BOLD}━━━ PART 6: I/O PRINT TESTS ━━━{RESET}")
    
    tests.append(("I/O Print", "python3 cli.py tests/fixtures/io/test_io_print.cio", False))
    # Skipping test_io.cio - requires user input
    
    # Part 7: Code Generation
    print(f"\n{BOLD}━━━ PART 7: CODE GENERATION ━━━{RESET}")
    
    tests.append(("Generate LLVM IR", "python3 cli.py examples/calculator.cio --output-llvm", False))
    tests.append(("Generate AST", "python3 cli.py examples/fibonacci.cio --output-ast", False))
    
    # Note: Skipping scanf tests (require user input) and error tests (expected to fail)
    
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
