# Changelog

All notable changes to the Claude Code Auto-QA system will be documented in this file.

## [1.2.0] - 2025-07-08

### 🐛 Critical Bug Fixes

#### Fixed Syntax Error Detection
- **Issue**: Python syntax errors were not being detected by auto-QA hooks
- **Root Cause**: JSON detection logic in `static_check.py` didn't recognize pylint's `--output-format=json` flag
- **Fix**: Updated JSON detection pattern to include `--output-format=json` alongside existing patterns
- **Impact**: Auto-QA now correctly detects and reports Python syntax errors in real-time

#### Fixed Python Syntax Error Parsing
- **Issue**: Python `py_compile` syntax errors weren't being parsed correctly
- **Root Cause**: Error format `File "filename", line X` didn't match existing regex patterns
- **Fix**: Added specific regex pattern for Python syntax errors: `File "([^"]+)", line (\d+)`
- **Impact**: Both basic py_compile and advanced pylint syntax errors are now caught

#### Fixed Hook Execution Reliability
- **Issue**: Auto-QA hooks were configured but not always executing
- **Root Cause**: Multiple issues including duplicate entries and permission problems
- **Fix**: Simplified hook configuration and added debug logging
- **Impact**: Hooks now execute consistently after Write, Edit, and MultiEdit operations

### 🚀 Improvements

#### Enhanced Debug Logging
- Added comprehensive debug logging to `~/.claude/logs/auto_qa_debug.log`
- Logs include hook triggers, file analysis, and execution results
- Helps troubleshoot integration issues

#### Better Error Reporting
- Improved error message format with file:line:column locations
- Added severity levels (0 = warning, 1 = error)
- More descriptive error messages for syntax issues

#### Improved Documentation
- Updated README.md with comprehensive troubleshooting section
- Enhanced SETUP_GLOBAL_QA.md with step-by-step debugging
- Added common issues and solutions based on real debugging experience

### 🔧 Technical Changes

#### Static Analysis Improvements
- Fixed JSON parsing for pylint output format
- Added Python syntax error pattern matching
- Improved error message extraction and formatting

#### Hook Configuration
- Simplified hook setup in global settings
- Added proper permissions for qa_tools commands
- Removed redundant hook configurations

#### File Processing
- Better file type detection for Python files
- Improved recent file analysis (5-minute window)
- Enhanced error handling for file operations

### 📋 Testing

#### Added Comprehensive Testing
- Created test cases for syntax error detection
- Added hook execution verification
- Included installation validation scripts

#### Debugging Tools
- Added manual testing commands for each QA tool
- Created debug scripts for hook verification
- Included file analysis testing utilities

## [1.1.0] - Previous Version

### Features
- Initial auto-QA implementation
- Basic static analysis integration
- Log scanning capabilities
- Integration testing framework
- Global Claude Code hooks

### Issues (Fixed in 1.2.0)
- Syntax errors not detected in Python files
- Inconsistent hook execution
- Limited debugging capabilities
- Incomplete error reporting

## [1.0.0] - Initial Release

### Features
- Three standalone QA tools (static_check, log_scan, int_tests)
- Claude Code hook integration
- Global installation script
- Basic configuration templates
- Project-specific overrides

---

## 🔍 Debugging the Bug Fix Process

For reference, here's how we diagnosed and fixed the main issues:

### 1. Syntax Error Detection Issue

**Symptoms**: 
- Auto-QA hooks were running but not finding syntax errors
- Manual testing showed errors were detectable
- Debug logs showed "No issues found" for files with clear syntax errors

**Diagnosis Process**:
1. Verified hook configuration was correct
2. Tested individual QA tools manually - they worked
3. Tested auto_qa.py directly - it failed to find issues
4. Traced execution through static_check.py
5. Found JSON detection logic was faulty

**Fix**:
```python
# Before (broken)
if "--format=json" in cmd or "-f" in cmd and "json" in cmd:

# After (fixed)
if "--format=json" in cmd or "--output-format=json" in cmd or ("-f" in cmd and "json" in cmd):
```

### 2. Python Syntax Error Parsing

**Symptoms**:
- py_compile errors weren't being parsed
- Error format didn't match existing patterns
- Syntax errors were detected but not reported

**Diagnosis**:
- Compared py_compile output format with existing regex patterns
- Found Python uses `File "filename", line X` format
- Existing patterns expected `filename:line:column` format

**Fix**:
```python
# Added new pattern for Python syntax errors
re.compile(r'File "([^"]+)", line (\d+)', re.MULTILINE)
```

### 3. Hook Execution Reliability

**Symptoms**:
- Hooks sometimes didn't run
- Multiple executions on some operations
- Inconsistent behavior across different file types

**Diagnosis**:
- Checked hook configuration syntax
- Verified debug logging was working
- Found duplicate hook entries in some configurations

**Fix**:
- Simplified hook configuration
- Added debug logging to track execution
- Improved error handling in hook commands

This changelog documents the evolution of the auto-QA system from a basic tool to a reliable, production-ready quality assurance system for Claude Code.