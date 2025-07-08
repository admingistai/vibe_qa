# Claude Code Auto-QA Global Setup Guide

This guide sets up automatic quality assurance that runs after every Claude Code write operation across all your projects.

## 🎯 What This Does

- **Automatic Static Analysis**: Runs linters on code files after writes
- **Log Scanning**: Analyzes program output for errors and warnings  
- **Integration Testing**: Validates API flows when test files are present
- **Global Configuration**: Works in every Claude Code session without project setup
- **Auto-Fix Integration**: Claude automatically fixes issues it finds

## 📋 Prerequisites

- Python 3.11+ installed
- Claude Code installed and configured
- Basic command line access

## 🚀 Installation Steps

### Step 1: Install QA Tools Globally

```bash
# Navigate to your auto_qa directory
cd /path/to/your/auto_qa

# Install dependencies
pip install -r requirements.txt

# Run the global installer
python qa_tools/install.py
```

### Step 2: Configure Global Claude Settings

Create or edit your global Claude settings file:

**macOS/Linux:**
```bash
mkdir -p ~/.claude
touch ~/.claude/settings.json
```

**Windows:**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude"
New-Item -ItemType File -Force -Path "$env:USERPROFILE\.claude\settings.json"
```

Edit `~/.claude/settings.json` (or `%USERPROFILE%\.claude\settings.json` on Windows):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python -m qa_tools.auto_qa"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command", 
            "command": "python -m qa_tools.auto_qa"
          }
        ]
      },
      {
        "matcher": "MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python -m qa_tools.auto_qa"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(python -m qa_tools.*)",
      "Bash(pylint*)",
      "Bash(eslint*)",
      "Bash(npm run lint*)",
      "Bash(npm run test*)"
    ]
  }
}
```

### Step 3: Configure Global Memory Instructions

Create or edit your global Claude memory file:

```bash
# Create/edit global memory
touch ~/.claude/CLAUDE.md
```

Add to `~/.claude/CLAUDE.md`:

```markdown
# Auto-QA Workflow

## Post-Write Quality Assurance

After every file write, edit, or code generation operation, you MUST automatically:

1. **Run Static Analysis** - Check code for syntax errors, style issues, and potential bugs
2. **Scan for Issues** - Look for errors, warnings, and problems in any output
3. **Fix Issues Immediately** - If any issues are found, fix them before continuing
4. **Verify Fixes** - Re-run QA tools to ensure issues are resolved

## Auto-QA Tool Commands

### Manual QA Commands (if needed)
- **Static Check**: `python -m qa_tools.static_check ['command', 'args']`
- **Log Scan**: `python -m qa_tools.log_scan "log_text"`
- **Integration Tests**: `python -m qa_tools.int_tests "flow.yaml" "base_url"`
- **Auto Coordinator**: `python -m qa_tools.auto_qa [file_path]`

## Issue Resolution Protocol

When QA tools find issues:

1. **Stop** - Do not continue with new tasks
2. **Analyze** - Review the specific issues found
3. **Fix** - Make necessary corrections immediately
4. **Verify** - Re-run QA to confirm fixes work
5. **Continue** - Only proceed once all issues are resolved

## File Type Handling

- **Code Files** (.py, .js, .ts, etc.) → Static analysis + syntax checking
- **Log Files** (.log, .out, .err) → Error/warning detection
- **Config Files** (.json, .yaml, .toml) → Format validation
- **Test Files** → Run appropriate test suites when possible

## Error Handling

If QA tools encounter errors:
- Report the specific error to the user
- Suggest manual resolution steps
- Do not proceed with additional operations until resolved
```

### Step 4: Test the Installation

Create a test file to verify the setup:

```bash
# Create a test Python file with an intentional error
echo "def test_function()
    print('Hello World')" > test_qa.py

# Start Claude Code in the directory
claude-code
```

In Claude Code, ask it to:
```
Fix the syntax error in test_qa.py
```

You should see:
1. Claude fixes the syntax error
2. Auto-QA runs automatically after the fix
3. QA results appear in the terminal
4. If issues remain, Claude fixes them automatically

## 🔧 Advanced Configuration

### Custom Linter Commands

To use specific linters for your projects, add them to your global settings:

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
              "PYLINT_CMD": "pylint --output-format=json",
              "ESLINT_CMD": "eslint --format=json"
            }
          }
        ]
      }
    ]
  }
}
```

### Project-Specific Overrides

For specific projects, create `.claude/settings.json`:

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

### Integration Testing Setup

For API projects, create a `qa_flows/` directory with YAML test files:

```yaml
# qa_flows/api_test.yaml
name: "API Health Check"
steps:
  - name: "Health Check"
    method: "GET"
    url: "/health"
    expect:
      status: 200
```

## 📊 Monitoring and Logs

QA results are logged to `logs/qa_results.ndjson` in each project:

```bash
# View recent QA results
tail -f logs/qa_results.ndjson | jq '.'

# Count issues by type
grep -o '"type":"[^"]*"' logs/qa_results.ndjson | sort | uniq -c
```

## 🚨 Troubleshooting

### Hook Not Running
- Check `~/.claude/settings.json` syntax with `python -m json.tool ~/.claude/settings.json`
- Verify Python can find qa_tools: `python -c "import qa_tools; print('OK')"`
- Check Claude Code permissions allow the commands

### QA Tools Not Found
- Verify installation: `python -m qa_tools.auto_qa --version`
- Check Python path: `python -c "import sys; print(sys.path)"`
- Reinstall: `python qa_tools/install.py`

### Memory Instructions Ignored
- Verify `~/.claude/CLAUDE.md` exists and is readable
- Check for syntax errors in the markdown
- Restart Claude Code to reload memory

### Too Many False Positives
- Adjust sensitivity in `qa_tools/log_scan.py`
- Add file type exclusions in `qa_tools/auto_qa.py`
- Use project-specific settings to override global config

## 🎉 Success Indicators

When properly configured, you should see:
- ✅ QA analysis runs automatically after file writes
- ✅ Issues are reported with specific file locations
- ✅ Claude immediately fixes detected problems
- ✅ Clean output when no issues are found
- ✅ Logs are generated in `logs/qa_results.ndjson`

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Test individual QA tools manually
4. Review Claude Code hook documentation

The auto-QA system is designed to be robust and helpful. Once configured, it will consistently catch and help fix issues across all your Claude Code projects!