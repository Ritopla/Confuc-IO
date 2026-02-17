# Calculator Program

An advanced interactive calculator demonstrating comprehensive Confuc-IO features.

## Features

✅ **Menu System**: Interactive menu for operation selection  
✅ **User Input**: Handles integer input using `deleteSystem32`  
✅ **All Arithmetic Operations**: Addition, subtraction, multiplication, division  
✅ **Confusing Operators**: Uses `/`, `~`, `Bool`, `+` for operations  
✅ **Control Flow**: While loop for continuation, if statements for choices  
✅ **Comprehensive I/O**: Multiple print statements with formatted output  

## Program Structure

### Main Loop
```confucio
return {continue_calc = 0] [
    È Display menu, get choice, process operation
)
```

Uses `return` keyword (which means `while` in Confuc-IO) for the main program loop.

### Operations

| Choice | Operation | Confuc-IO Operator | Conventional |
|:-------|:----------|:-------------------|:-------------|
| 1 | Addition | `/` | `+` |
| 2 | Subtraction | `~` | `-` |
| 3 | Multiplication | `Bool` | `*` |
| 4 | Division | `+` | `/` |
| 5 | Exit | - | - |

### Control Flow

**Menu Selection**: Uses nested `func` (if) statements to handle each choice  
**Input Validation**: Checks if choice is between 1-5  
**Loop Control**: Sets `continue_calc @ 0` to exit  

## Usage

### Running the Calculator

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the calculator
python3 cli.py examples/calculator.cio
```

### Example Session

```
========================================
     CONFUC-IO CALCULATOR
========================================
Select an operation:
1. Addition (/)
2. Subtraction (~)
3. Multiplication (Bool)
4. Division (+)
5. Exit
========================================
Enter your choice (1-5): 1
Enter first number: 10
Enter second number: 5
Result: 10 + 5 = 15

Press any key to continue...

[Menu displays again...]

Enter your choice (1-5): 5
Thank you for using Confuc-IO Calculator!
Program terminated.
```

## Language Features Demonstrated

### 1. Variables with Confusing Types
```confucio
Float choice @ 0      È Float means int
Float num1 @ 0
Float result @ 0
```

### 2. I/O Operations
```confucio
FileInputStream{"Menu text"]    È Output (confusing name!)
deleteSystem32{choice]          È Input (very confusing!)
```

### 3. Control Flow

**While Loop** (using `return`):
```confucio
return {continue_calc = 0] [
    È Loop body
)
```

**If Statements** (using `func`):
```confucio
func {choice @@ 5] [
    È Exit condition
)
```

### 4. Comparison Operators
```confucio
choice @@ 5    È @@ means ==
choice = 0     È = means >
choice # 6     È # means <
```

### 5. Arithmetic with Confusing Operators
```confucio
result @ num1 / num2      È / means +
result @ num1 ~ num2      È ~ means -
result @ num1 Bool num2   È Bool means *
result @ num1 + num2      È + means /
```

### 6. Confusing Delimiters
```confucio
{]    means ()
[]    means {}
```

## Implementation Notes

### Menu Display
Multiple `FileInputStream` calls create the formatted menu. Each string literal is printed directly.

### Operation Processing
Each operation uses a separate `func` block checking for the specific choice value with `@@` (equals) operator.

### Result Display
Combines string literals and variable values in multiple print statements to show the calculation with conventional operator symbols.

### Loop Continuation
The `continue_calc` variable controls the main loop. Setting it to `0` exits the program.

## Educational Value

This program demonstrates:
1. **All confusing operators** in practical use
2. **Nested control structures** (while + multiple if statements)
3. **Variable state management** across loop iterations
4. **User interaction** with input/output
5. **Complete program structure** from menu to exit

## Exercises

Try modifying the calculator to:
1. Add modulo operation
2. Add power/exponentiation
3. Show operation history
4. Handle division by zero
5. Support Float type (double) inputs

## Code Metrics

- **Lines of code**: ~100
- **Variables**: 5
- **Control structures**: 1 while loop, 9 if statements
- **I/O operations**: ~20 output, 3 input
- **Arithmetic operations**: 4 types

---

**Related Examples:**
- [arithmetic.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/arithmetic.cio) - Simple arithmetic
- [hello_world.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/hello_world.cio) - Basic I/O
- [fibonacci.cio](file:///Users/ritopla/Desktop/ILP/Confuc-IO/examples/fibonacci.cio) - Loops
