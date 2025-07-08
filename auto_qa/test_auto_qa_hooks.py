#!/usr/bin/env python3
"""Test script with intentional errors to verify auto-QA hooks

This script contains various intentional errors to test if the auto-QA
hooks are working correctly. When saved, it should trigger the hooks
and report the issues found.
"""

# Test 1: Undefined variable
def test_undefined_variable():
    print(undefined_var)  # This variable is not defined

# Test 2: Syntax error (uncomment to test)
# def test_syntax_error()
#     print("Missing colon")

# Test 3: Import error
from non_existent_module import something  # Module doesn't exist

# Test 4: Type error
def test_type_error():
    result = "string" + 5  # Cannot add string and int
    return result

# Test 5: Unused variable (style issue)
def test_unused_variable():
    unused_var = "This is never used"
    return "Something else"

# Test 6: Missing return type annotation (style)
def test_missing_annotation(x, y):
    return x + y

# Test 7: Security issue - hardcoded password
DATABASE_PASSWORD = "admin123"  # Never hardcode passwords!

# Test 8: Logic error
def divide_by_zero():
    return 10 / 0

if __name__ == "__main__":
    print("This test file contains intentional errors!")
    print("It should trigger auto-QA hooks when saved.")
    
    # Run some tests (will cause errors)
    test_undefined_variable()
    test_type_error()
    divide_by_zero()