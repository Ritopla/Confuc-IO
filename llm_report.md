# LLM Usage Report: Confuc-IO Compiler Project

## Models Used

### Primary Development: Claude Sonnet 4.5
**Role:** Code Generation and Debugging

Claude Sonnet 4.5 was the primary LLM used for:
- Writing core compiler components (parser, AST builder, semantic analyzer, code generator)
- Implementing LLVM IR code generation
- Debugging compilation errors and runtime issues
- Refactoring and optimizing code
- Implementing function parameters feature
- Creating comprehensive test suites

### Design Phase: Gemini 3 Pro
**Role:** Design Decisions and Architecture

Gemini 3 Pro was utilized for:
- High-level architectural decisions
- Language design discussions
- Mapping strategy planning
- Documentation structure and organization
- Project organization and workflow planning

---

## The Paradox: Teaching Confusion to a Conventional Mind

### The Core Challenge

Working on Confuc-IO presented a unique and significant challenge: **building a programming language that deliberately violates every convention that the LLMs were trained to respect**.

LLMs like Claude and Gemini have been trained on millions of lines of conventional code where:
- `+` means addition
- `if` means conditional branching
- `int` means integer
- `{` opens a code block
- Function names describe their purpose

Confuc-IO inverts all of this:
- `/` means addition
- `func` means if statement
- `Float` means integer
- `{` means opening parenthesis
- `deleteSystem32` means scanf (input)

### Specific Challenges Encountered

#### 1. **Natural Autocorrection Tendency**

The LLMs would frequently "correct" the confusing syntax back to conventional syntax:

**Example Problem:**
```python
# LLM would write:
if condition:
    x = a + b

# When it should write the AST for Confuc-IO source:
# func {condition] [
#     x @ a / b
```

**Impact:** Required constant vigilance and explicit reminders about the mapping inversions during every code generation session.

#### 2. **Documentation Confusion**

When writing documentation, the LLM would struggle with explaining something that reads backwards:

- "The `func` keyword maps to `if`" feels inherently wrong to a model trained on correct mappings
- Format strings like `%ff` for floats contradict all training data
- Had to repeatedly clarify which direction the mapping goes

**Solution:** Created explicit mapping reference tables and maintained them as canonical truth.

#### 3. **Code Review Blindness**

The most insidious issue: **LLMs would sometimes miss bugs in the confusing mappings because the "wrong" code looked "right" to their training**.

**Example:**
If code accidentally used `+` for addition (conventional mapping), the LLM might not flag it as an error because it looks correct in conventional terms, even though it's wrong for Confuc-IO.

#### 4. **Test Generation Difficulty**

Writing test cases required the LLM to:
1. Write confusing source code
2. Predict what it should actually do
3. Verify the conventional result

This triple-translation was error-prone:
```
Confuc-IO: x @ 5 / 3  
         ↓
Thinks: x = 5 + 3
         ↓  
Result should be: 8
```

The LLM would sometimes short-circuit and use conventional operators in the test expectations.

#### 5. **Mapping Direction Confusion**

The biggest recurring issue: **which direction do the mappings go?**

- Does `Float` in source code → `int` in AST (correct)
- Or does `int` in source code → `Float` in AST (wrong)

This required constant clarification in prompts:
- "Use Confuc-IO syntax" vs "Store as conventional types"
- "Source operator" vs "Mapped operator"
- "Parser sees" vs "Compiler generates"

### Effective Strategies Developed

#### 1. **Explicit Context Setting**
Every major coding session started with:
> "Remember: Confuc-IO has inverted mappings. `func` means if, `/` means +, `Float` means int."

#### 2. **Reference Table Maintenance**
Maintained `confucio_mappings.py` as the single source of truth and referenced it constantly.

#### 3. **Incremental Verification**
- Test each component in isolation
- Verify mappings at each stage (parse → AST → semantic → codegen)
- Unit tests for every mapping

#### 4. **Timing Awareness**
Critical insight: **understand WHEN mappings are applied**
- Types mapped during AST building
- Operators mapped during code generation
- This timing distinction helped avoid confusion

#### 5. **Example-Driven Development**
Always work with concrete examples:
```
Source: Float x @ 5 / 3
AST: VariableDeclaration(var_type='int', initializer=BinaryOp(operator='/', ...))
Generated IR: %result = add i32 5, 3
```

### Performance Observations

#### What Worked Well
- **Implementation of conventional compiler components** (parser architecture, LLVM integration)
- **Debugging conventional code** (Python syntax errors, type errors)
- **Test infrastructure** (pytest setup, automation)
- **Documentation writing** (once the mappings were clearly established)

#### What Required Extra Effort
- **Mapping logic** (40%+ more debugging iterations)
- **Code generation** (operator mapping application)
- **Test case writing** (predicting confusing behavior)
- **Quick fixes** (LLM would "fix" intentional confusion)

### Quantitative Impact

Estimated **20-30% development overhead** due to:
- Additional verification cycles
- Mapping confusion debugging
- Re-explaining context in each session
- "Undo autocorrection" rounds

### Lessons Learned

1. **Explicit is Better Than Implicit**
   - Never assume the LLM remembers the inverted context
   - State mappings explicitly in every relevant prompt

2. **Canonical Reference is Critical**
   - Single source of truth (mappings file) reduced errors significantly
   - Reference tables in documentation helped maintain consistency

3. **Testing Saves Time**
   - Comprehensive unit tests for mappings caught LLM errors early
   - Automated tests provided ground truth when LLM logic seemed wrong

4. **Separation of Concerns Helps**
   - Keeping mappings isolated in one module reduced cognitive load
   - Clear timing (when mappings apply) prevented confusion

5. **Human Verification Essential**
   - Cannot blindly trust LLM output on unconventional code
   - Every mapping-related change required human review

### Conclusion

Building Confuc-IO with LLMs was a fascinating exercise in **working against the grain of AI training data**. While modern LLMs are incredibly capable at generating conventional code, asking them to deliberately produce "wrong" code exposes interesting limitations:

- Strong bias toward correctness (a feature that became a bug)
- Pattern matching that can miss intentional inversions
- Difficulty maintaining unconventional context across conversations

Despite these challenges, the project succeeded by:
- Maintaining explicit context
- Building strong testing infrastructure  
- Using LLMs for what they do best (conventional software engineering)
- Adding human oversight for the unconventional aspects

**Final Verdict:** LLMs are excellent tools even for unconventional projects, but require careful prompt engineering and verification when working outside their training distribution. The 20-30% overhead is acceptable given the enormous productivity gains in conventional aspects of the compiler.

---

**Project Status:** Successfully completed with comprehensive test coverage (16/16 automated tests passing) and full documentation.

**LLM Contribution:** ~80% of code generated by Claude Sonnet 4.5, ~20% human correction/verification, 100% human-verified for correctness.
