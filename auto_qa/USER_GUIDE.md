# Auto-QA User Guide

A comprehensive guide for using the Claude Code Auto-QA system in your daily development workflow.

## 📖 Table of Contents

1. [What is Auto-QA?](#what-is-auto-qa)
2. [Daily Usage](#daily-usage)
3. [Understanding QA Results](#understanding-qa-results)
4. [Manual QA Commands](#manual-qa-commands)
5. [Integration Testing](#integration-testing)
6. [Customization](#customization)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## 🎯 What is Auto-QA?

Auto-QA is a quality assurance system that automatically runs after every file operation in Claude Code. It provides:

- **Automatic Static Analysis**: Catches syntax errors, style issues, and potential bugs
- **Log Analysis**: Scans program output for errors and warnings
- **Integration Testing**: Validates API endpoints and flows
- **Real-time Feedback**: Issues are reported immediately and fixed by Claude

## 🔄 Daily Usage

### Automatic Operation

Once installed, auto-QA runs seamlessly in the background:

1. **Write or Edit Files**: Use Claude Code normally
2. **QA Runs Automatically**: After each file operation, QA tools analyze your code
3. **Issues Reported**: Any problems are displayed immediately
4. **Claude Fixes Issues**: Critical problems are resolved automatically

### What You'll See

When auto-QA runs, you'll see output like:

```
🔍 Auto-QA: Analyzing recent changes...

📄 Analyzing: ./src/utils.py
  ✅ No static analysis issues found

📄 Analyzing: ./app.py
  ⚠️  Found 2 issues:
    🔴 app.py:15:0: Undefined variable 'databse' (did you mean 'database'?)
    🟡 app.py:23:4: Line too long (85/80)

✅ Auto-QA completed: 2 issues found, 1 critical
```

### Silent Operation

When no issues are found, auto-QA runs silently:

```
🔍 Auto-QA: Analyzing recent changes...
✅ All checks passed successfully
```

## 📊 Understanding QA Results

### Issue Types

Auto-QA categorizes issues by type:

- **🔴 Critical (Severity 1)**: Syntax errors, undefined variables, broken imports
- **🟡 Warning (Severity 0)**: Style issues, unused variables, line length

### Result Format

Each issue includes:
- **Location**: `filename:line:column`
- **Message**: Description of the problem
- **Code**: Error/warning code (e.g., `E0001`, `W0612`)
- **Severity**: 0 (warning) or 1 (error)

### Example Issues

```
🔴 myfile.py:10:5: SyntaxError: invalid syntax
🟡 myfile.py:25:0: Line too long (105/100)
🔴 myfile.py:30:8: NameError: name 'undefined_var' is not defined
🟡 myfile.py:45:4: Unused variable 'temp'
```

## 🔧 Manual QA Commands

### Static Analysis

```bash
# Analyze specific file
python -m qa_tools.static_check python -m py_compile myfile.py

# Use advanced linter
python -m qa_tools.static_check ['pylint', '--output-format=json', 'myfile.py']

# Analyze JavaScript
python -m qa_tools.static_check ['node', '--check', 'script.js']
```

### Log Analysis

```bash
# Analyze log content
python -m qa_tools.log_scan "ERROR: Database connection failed"

# Analyze log file
cat application.log | python -m qa_tools.log_scan
```

### Auto-QA Coordinator

```bash
# Run full QA on recent changes
python -m qa_tools.auto_qa

# Analyze specific file
python -m qa_tools.auto_qa myfile.py

# Check specific directory
cd /path/to/project && python -m qa_tools.auto_qa
```

## 🌐 Integration Testing

### Direct Mode (Recommended)

Test API endpoints directly without creating files:

```bash
# Simple GET request
python -m qa_tools.int_tests --method GET --url /api/health --status 200 --base-url http://localhost:8000

# POST with JSON body
python -m qa_tools.int_tests --method POST --url /api/users \
  --body '{"name":"John","email":"john@example.com"}' \
  --status 201 --base-url http://localhost:8000

# Authentication test
python -m qa_tools.int_tests --method GET --url /api/protected \
  --headers '{"Authorization":"Bearer token123"}' \
  --status 200 --base-url http://localhost:8000

# Extract values from response
python -m qa_tools.int_tests --method GET --url /api/user/123 \
  --extract '{"user_id":"id","email":"email"}' \
  --json-output --base-url http://localhost:8000
```

### File-Based Mode

For complex multi-step workflows:

```yaml
# tests/user_flow.yaml
name: "User Registration Flow"
base_url: "http://localhost:8000"
steps:
  - name: "Create User"
    method: POST
    url: /api/users
    body:
      name: "Test User"
      email: "test@example.com"
    expect:
      status: 201
    extract:
      user_id: "id"
      
  - name: "Verify User"
    method: GET
    url: /api/users/{{user_id}}
    expect:
      status: 200
      body:
        email: "test@example.com"
```

```bash
# Run file-based test
python -m qa_tools.int_tests tests/user_flow.yaml
```

## ⚙️ Customization

### Project-Specific Settings

Create `.claude/settings.json` in your project:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint"
          },
          {
            "type": "command",
            "command": "python -m qa_tools.auto_qa"
          }
        ]
      }
    ]
  }
}
```

### Custom Linter Commands

Set environment variables in hook configuration:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python -m qa_tools.auto_qa",
            "env": {
              "PYLINT_CMD": "pylint --disable=C0103",
              "ESLINT_CMD": "eslint --fix"
            }
          }
        ]
      }
    ]
  }
}
```

### Exclude Files

Modify `qa_tools/auto_qa.py` to skip certain files:

```python
def should_analyze_file(file_path):
    """Check if file should be analyzed"""
    exclude_patterns = [
        "node_modules/",
        ".git/",
        "__pycache__/",
        "*.min.js",
        "*.generated.py"
    ]
    
    for pattern in exclude_patterns:
        if pattern in file_path:
            return False
    return True
```

## 🎯 Best Practices

### Development Workflow

1. **Trust the Process**: Let auto-QA run automatically
2. **Address Critical Issues**: Fix red (severity 1) issues immediately
3. **Review Warnings**: Consider yellow (severity 0) issues for code quality
4. **Test Integration**: Use direct mode for quick API validation

### Code Quality

1. **Keep It Clean**: Auto-QA helps maintain consistent code style
2. **Fix Early**: Address issues as they appear, don't accumulate technical debt
3. **Learn from Patterns**: Common issues indicate areas for improvement

### Performance Tips

1. **Small Commits**: Auto-QA analyzes recent changes (5-minute window)
2. **Targeted Testing**: Use specific file analysis for large projects
3. **Batch Operations**: Multiple file edits trigger single QA run

## 🔍 Troubleshooting

### QA Not Running

**Check hooks configuration:**
```bash
cat ~/.claude/settings.json | grep -A 10 "hooks"
```

**Verify installation:**
```bash
python -c "import qa_tools; print('✅ QA tools installed')"
```

**Check debug logs:**
```bash
tail -f ~/.claude/logs/auto_qa_debug.log
```

### Issues Not Detected

**Test manual analysis:**
```bash
# Create test file with error
echo "def broken(): return 'missing quote" > test.py

# Test detection
python -m qa_tools.static_check ['pylint', '--output-format=json', 'test.py']
```

**Check linter installation:**
```bash
# Install better linters
pip install pylint
npm install -g eslint
```

### Performance Issues

**Reduce analysis scope:**
```bash
# Analyze only specific file types
python -m qa_tools.auto_qa --include "*.py"

# Skip large files
python -m qa_tools.auto_qa --max-size 1MB
```

### False Positives

**Adjust sensitivity in `qa_tools/log_scan.py`:**
```python
# Reduce sensitivity for certain patterns
patterns = [
    {
        "name": "error",
        "pattern": re.compile(r'\berror\b', re.IGNORECASE),
        "severity": "medium"  # Changed from "high"
    }
]
```

## 📋 Monitoring

### View QA Results

```bash
# Recent results
tail -20 logs/qa_results.ndjson | jq '.'

# Count issues by type
jq -r '.issues[].type' logs/qa_results.ndjson | sort | uniq -c

# Find critical issues
jq 'select(.issues[].severity == 1)' logs/qa_results.ndjson
```

### Debug Information

```bash
# Check recent file analysis
python -c "from qa_tools.auto_qa import analyze_recent_writes; print(analyze_recent_writes())"

# Test specific QA tool
python -m qa_tools.static_check ['python', '-m', 'py_compile', 'myfile.py']

# Verify hook execution
grep "Auto-QA Hook Triggered" ~/.claude/logs/auto_qa_debug.log
```

## 🚀 Advanced Usage

### Custom Integration Tests

Create dynamic tests based on your API documentation:

```python
# In Claude Code, ask:
# "Create integration tests for the user management API"
# Claude will generate appropriate test commands
```

### Automated Workflows

Combine auto-QA with CI/CD:

```yaml
# .github/workflows/qa.yml
name: QA Check
on: [push, pull_request]
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run QA
        run: python -m qa_tools.auto_qa
```

### Team Configuration

Share QA settings across team:

```bash
# Add to project repository
git add .claude/settings.json
git commit -m "Add team QA configuration"
```

---

## 🎉 Success Metrics

When using auto-QA effectively, you should see:
- ✅ Fewer bugs in production
- ✅ Consistent code style across projects
- ✅ Faster development cycles
- ✅ Improved code quality metrics
- ✅ Reduced time spent on manual code review

The auto-QA system is designed to be your development partner, catching issues early and maintaining code quality automatically. Trust the process and let it help you write better code!