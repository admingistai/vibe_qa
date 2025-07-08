#!/usr/bin/env python3
"""Another test file to verify auto-QA hooks with pylint"""

# This should trigger pylint warnings
def bad_function_name():  # Function name doesn't follow snake_case convention
    UnusedVariable = "This variable name doesn't follow convention"
    x = 1
    y = 2
    # Missing return statement
    
import os  # Import should be at the top

# Global variable without proper naming
myVariable = "bad naming"

# Function with too many arguments
def function_with_many_args(a, b, c, d, e, f, g, h):
    return a + b

# Missing docstring
def no_docstring():
    pass

print("Testing auto-QA hooks with pylint!")