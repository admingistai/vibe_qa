# Fixing Auto-QA Directory Issues

If auto-QA is running in the wrong directory (e.g., in the auto_qa installation directory instead of your project directory), here's how to fix it.

## The Problem

When Claude Code triggers hooks, it runs them from the current working directory. However, the auto-QA script may not properly detect which files were just edited if:

1. The hook doesn't pass the file path as an argument
2. The working directory isn't properly communicated
3. The auto-QA is looking for files in its installation directory

## Solution 1: Use the Wrapper Script (Recommended)

Update your `~/.claude/settings.json` to use the wrapper script:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/auto_qa/qa_tools/auto_qa_wrapper.py"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/auto_qa/qa_tools/auto_qa_wrapper.py"
          }
        ]
      },
      {
        "matcher": "MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/auto_qa/qa_tools/auto_qa_wrapper.py"
          }
        ]
      }
    ]
  }
}
```

## Solution 2: Pass File Path Directly

If Claude Code supports placeholders in hooks, you can pass the edited file directly:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python -m qa_tools.auto_qa {{file_path}}"
          }
        ]
      }
    ]
  }
}
```

**Note**: Check Claude Code documentation for the exact placeholder syntax.

## Solution 3: Environment-Based Configuration

Set environment variables in the hook configuration:

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
              "CLAUDE_WORKING_DIR": "{{working_dir}}",
              "CLAUDE_FILE_PATH": "{{file_path}}"
            }
          }
        ]
      }
    ]
  }
}
```

## Solution 4: Project-Specific Override

For specific projects, create `.claude/settings.json` in the project root:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/project && python -m qa_tools.auto_qa"
          }
        ]
      }
    ]
  }
}
```

## Testing the Fix

1. **Check Debug Logs**:
   ```bash
   tail -f ~/.claude/logs/auto_qa_debug.log
   ```
   Look for:
   - "Working Directory:" - should show your project directory
   - "CLAUDE_WORKING_DIR:" - if using environment variables
   - File paths being analyzed

2. **Create a Test File**:
   ```bash
   # In your project directory
   echo "def test(): pass" > test_qa_dir.py
   ```

3. **Edit in Claude Code**:
   Ask Claude to add a comment to the file and watch the logs.

## How Auto-QA Finds Files

The updated auto-QA script now:

1. Checks for `CLAUDE_WORKING_DIR` environment variable
2. Changes to that directory if provided
3. Looks for files passed as command-line arguments
4. Falls back to analyzing recently modified files in the current directory

## Debugging Commands

```bash
# Test auto-QA with specific file
python -m qa_tools.auto_qa /full/path/to/your/file.py

# Test with environment variable
CLAUDE_WORKING_DIR=/your/project python -m qa_tools.auto_qa

# Test wrapper script
python /path/to/auto_qa/qa_tools/auto_qa_wrapper.py test.py
```

## Expected Behavior

When working correctly, you should see:

```
🔍 Auto-QA: Analyzing recent changes...

📄 Analyzing: ./your-edited-file.js
  ✅ No static analysis issues found
```

The file path should be relative to your project directory, not the auto_qa installation directory.

## Alternative: Manual QA Command

If automatic hooks aren't working properly, you can always run QA manually after edits:

```bash
# In your project directory
python -m qa_tools.auto_qa

# Or analyze specific file
python -m qa_tools.auto_qa path/to/edited/file.py
```

## Long-term Solution

The auto-QA system has been updated to better handle directory issues. Make sure you have the latest version that includes:

- Environment variable support (`CLAUDE_WORKING_DIR`, `CLAUDE_FILE_PATH`)
- Better path resolution for relative file paths
- Improved debug logging for troubleshooting

With these changes, auto-QA should work correctly regardless of where it's installed or called from.