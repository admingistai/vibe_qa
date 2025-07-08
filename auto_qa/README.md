# Claude Code Auto-QA System

Automated quality assurance tools that run after every Claude Code write operation to catch and fix bugs immediately.

## 🎯 Overview

This system provides **three standalone QA utilities** that Claude Code automatically runs after file operations:

1. **Static Analysis** (`static_check.py`) - Lints code files for syntax errors, style issues, and potential bugs
2. **Log Scanning** (`log_scan.py`) - Analyzes program output for errors, warnings, and stack traces
3. **Integration Testing** (`int_tests.py`) - Validates API flows using YAML/JSON test collections

## 🚀 Quick Start

### One-Command Installation
```bash
python qa_tools/install.py
```

### Manual Setup
See `SETUP_GLOBAL_QA.md` for detailed installation instructions.

### Test Installation
```bash
python test_installation.py
```

## 📁 Project Structure

```
auto_qa/
├── qa_tools/
│   ├── __init__.py           # Package initialization
│   ├── static_check.py       # Static analysis tool
│   ├── log_scan.py          # Log scanning tool
│   ├── int_tests.py         # Integration testing tool
│   ├── auto_qa.py           # Smart coordinator script
│   └── install.py           # Global installation script
├── sample_configs/
│   ├── global_settings.json  # Global Claude settings template
│   ├── global_CLAUDE.md     # Global memory template
│   └── project_settings.json # Project-specific settings template
├── logs/                    # QA results (created on first run)
├── requirements.txt         # Python dependencies
├── sample_flow.yaml         # Example integration test flow
├── test_installation.py     # Installation verification
├── SETUP_GLOBAL_QA.md      # Complete setup guide
└── README.md               # This file
```

## 🔧 How It Works

### Integration Testing Tool

The integration testing tool (`int_tests.py`) now supports two modes:

#### 1. File-Based Mode (Traditional)
Define test flows in YAML/JSON files with multiple steps, variable extraction, and complex validation:
```yaml
name: "User API Flow"
steps:
  - name: "Create User"
    method: POST
    url: /api/users
    body: {"email": "test@example.com"}
    expect:
      status: 201
    extract:
      user_id: "id"
  - name: "Get User"
    method: GET
    url: /api/users/{{user_id}}
    expect:
      status: 200
```

#### 2. Direct Mode (New)
Claude Code can now run integration tests directly via command-line arguments without creating files:
```bash
# Simple GET request
python -m qa_tools.int_tests --method GET --url /api/health --status 200 --base-url http://localhost:8000

# POST with JSON body
python -m qa_tools.int_tests --method POST --url /api/users \
  --body '{"name":"Test User","email":"test@example.com"}' \
  --status 201 --base-url http://localhost:8000

# With authentication headers
python -m qa_tools.int_tests --method GET --url /api/protected \
  --headers '{"Authorization":"Bearer token123"}' \
  --status 200 --base-url http://localhost:8000
```

This allows Claude Code to dynamically create and execute integration tests based on code changes, API documentation, or user requirements without manual file creation.

### Automatic Execution
1. **Hook Integration**: Claude Code hooks trigger after Write/Edit operations
2. **Smart Detection**: Coordinator script analyzes file types and recent changes
3. **Tool Selection**: Runs appropriate QA tools based on file content
4. **Issue Reporting**: Returns standardized JSON results with specific locations
5. **Auto-Fix**: Claude immediately addresses any issues found

### Manual Execution
```bash
# Run all QA tools on recent changes
python -m qa_tools.auto_qa

# Run specific tool
python -m qa_tools.static_check ['pylint', 'myfile.py']
python -m qa_tools.log_scan "ERROR: Something failed"

# Integration testing - File-based mode (traditional)
python -m qa_tools.int_tests "api_flow.yaml" "http://localhost:8000"
python -m qa_tools.int_tests --file "api_flow.yaml" --base-url "http://localhost:8000"

# Integration testing - Direct mode (new) 
python -m qa_tools.int_tests --method GET --url /api/health --status 200 --base-url http://localhost:8000
python -m qa_tools.int_tests --method POST --url /api/users --body '{"name":"test"}' --status 201 --base-url http://localhost:8000

# With headers and extraction
python -m qa_tools.int_tests --method GET --url /api/user/123 \
  --headers '{"Authorization":"Bearer token"}' \
  --extract '{"user_id":"id"}' \
  --base-url http://localhost:8000

# JSON output for scripting
python -m qa_tools.int_tests --method GET --url /api/status --json-output --base-url http://localhost:8000
```

## 🎛️ Configuration

### Global Settings (`~/.claude/settings.json`)
- PostToolUse hooks for automatic QA execution
- Permissions for QA tool commands
- Environment variables for customization

### Global Memory (`~/.claude/CLAUDE.md`)
- Instructions for Claude to run QA after writes
- Issue resolution protocols
- Quality standards and best practices

### Project Settings (`.claude/settings.json`)
- Project-specific overrides
- Custom linter commands
- Additional tool permissions

## 📊 Results and Logging

All QA results are logged to `logs/qa_results.ndjson` with:
- Timestamp and tool used
- Issues found with locations and messages
- Success/failure status
- Execution context

## 🛠️ Customization

### Adding New Linters
Modify `qa_tools/auto_qa.py` to add support for new linters:

```python
def get_linter_command(file_type: str, file_path: str):
    commands = {
        'python': ['your-custom-linter', file_path],
        # Add more...
    }
```

### Custom Log Patterns
Extend `qa_tools/log_scan.py` with new regex patterns:

```python
patterns = [
    {
        "name": "custom_error",
        "pattern": re.compile(r'YOUR_PATTERN'),
        "severity": "high"
    }
]
```

## 🔍 Troubleshooting

### If Auto-QA is Not Running Automatically

1. **Check Hook Configuration**
   ```bash
   # Verify hooks are configured
   cat ~/.claude/settings.json | grep -A 20 "hooks"
   
   # Should show PostToolUse hooks for Write, Edit, MultiEdit
   ```

2. **Check Debug Logs**
   ```bash
   # View auto-QA execution logs
   tail -f ~/.claude/logs/auto_qa_debug.log
   
   # Look for "Auto-QA Hook Triggered" messages
   ```

3. **Test QA Tools Manually**
   ```bash
   # Test static analysis
   python -m qa_tools.static_check python -m py_compile test.py
   
   # Test auto-QA coordinator
   python -m qa_tools.auto_qa
   ```

4. **Common Issues & Solutions**
   - **Syntax errors not detected**: Check if pylint is installed (`pip install pylint`)
   - **Multiple executions**: Remove duplicate hook entries in settings.json
   - **Permission errors**: Ensure Claude has permission to run Python commands
   - **Import errors**: Verify Python path with `python -c "import qa_tools"`

### Debug Commands
```bash
# Test individual QA tools
python -m qa_tools.static_check ['pylint', '--output-format=json', 'test.py']
python -m qa_tools.log_scan "ERROR: Something failed"

# Check Claude settings syntax
python -m json.tool ~/.claude/settings.json

# View recent QA results
tail -f logs/qa_results.ndjson | python -m json.tool

# Check if auto-QA is finding recent files
python -c "from qa_tools.auto_qa import analyze_recent_writes; print(analyze_recent_writes())"
```

### Installation Verification
```bash
# Run comprehensive installation test
python test_installation.py

# Check if hooks are firing
echo "def test(): pass" > test_hook.py
# Watch ~/.claude/logs/auto_qa_debug.log for activity
```

### Directory Issues
If auto-QA runs in the wrong directory (installation dir instead of project dir):
- See `FIX_DIRECTORY_ISSUE.md` for detailed solutions
- Use the wrapper script: `qa_tools/auto_qa_wrapper.py`
- Set `CLAUDE_WORKING_DIR` environment variable
- Pass file paths directly in hook configuration

## 📋 Requirements

- Python 3.11+
- Claude Code installed
- `requests` and `PyYAML` packages (auto-installed)

## 🎉 Success Indicators

When properly configured:
- ✅ QA runs automatically after file writes
- ✅ Issues are reported with specific locations
- ✅ Claude fixes problems immediately
- ✅ Clean output when no issues found
- ✅ Results logged for review

## 📞 Support

For setup help, see `SETUP_GLOBAL_QA.md`
For troubleshooting, run `python test_installation.py`

---

**Result**: Claude Code will automatically catch and fix bugs without user intervention! 🎯