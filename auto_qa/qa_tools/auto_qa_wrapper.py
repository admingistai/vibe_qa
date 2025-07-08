#!/usr/bin/env python3
"""
Wrapper script for auto-QA that handles working directory issues.
This script ensures auto-QA runs in the correct directory regardless of where it's called from.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where the wrapper is being called from (Claude's working directory)
    calling_dir = os.getcwd()
    
    # Get the directory where the auto-QA tools are installed
    script_dir = Path(__file__).parent.absolute()
    
    # Prepare environment variables for the auto-QA script
    env = os.environ.copy()
    env['CLAUDE_WORKING_DIR'] = calling_dir
    
    # Build the command to run auto_qa.py
    cmd = [sys.executable, '-m', 'qa_tools.auto_qa'] + sys.argv[1:]
    
    # Run auto_qa.py with the proper environment
    try:
        result = subprocess.run(cmd, env=env, cwd=calling_dir)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Error running auto-QA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()