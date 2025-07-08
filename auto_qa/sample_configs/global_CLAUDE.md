# Global Claude Code Configuration

## Auto-QA Workflow

### Post-Write Quality Assurance Protocol

After every file write, edit, or code generation operation, you MUST automatically:

1. **Run Static Analysis** - Check code for syntax errors, style issues, and potential bugs
2. **Scan for Issues** - Look for errors, warnings, and problems in any output
3. **Fix Issues Immediately** - If any issues are found, fix them before continuing
4. **Verify Fixes** - Re-run QA tools to ensure issues are resolved

### Auto-QA Tool Commands

**Manual QA Commands (if automatic QA fails):**
- **Static Check**: `python -m qa_tools.static_check ['command', 'args']`
- **Log Scan**: `python -m qa_tools.log_scan "log_text"`
- **Auto Coordinator**: `python -m qa_tools.auto_qa [file_path]`

**Integration Testing Commands:**

1. **File-Based Mode** (for complex multi-step flows):
   ```bash
   python -m qa_tools.int_tests "flow.yaml" "base_url"
   python -m qa_tools.int_tests --file "flow.yaml" --base-url "http://localhost:8000"
   ```

2. **Direct Mode** (for dynamic testing - PREFERRED for automation):
   ```bash
   # Simple endpoint test
   python -m qa_tools.int_tests --method GET --url /api/health --status 200 --base-url http://localhost:8000
   
   # POST with JSON body
   python -m qa_tools.int_tests --method POST --url /api/users --body '{"name":"test"}' --status 201 --base-url http://localhost:8000
   
   # With headers
   python -m qa_tools.int_tests --method GET --url /api/user/123 --headers '{"Authorization":"Bearer token"}' --base-url http://localhost:8000
   
   # Extract values for verification
   python -m qa_tools.int_tests --method GET --url /api/user/123 --extract '{"user_id":"id","email":"email"}' --json-output --base-url http://localhost:8000
   ```

### When to Use Integration Testing

**Use Direct Mode when:**
- Testing API endpoints after creating/modifying them
- Verifying API behavior matches documentation
- Running quick validation tests
- Checking specific endpoints mentioned in code or comments
- Testing authentication/authorization flows

**Use File-Based Mode when:**
- User provides a pre-written test flow file
- Testing complex multi-step workflows
- Need to maintain state across multiple requests
- Testing scenarios with variable extraction and reuse

### Issue Resolution Protocol

When QA tools find issues:

1. **Stop** - Do not continue with new tasks until issues are resolved
2. **Analyze** - Review the specific issues found and understand their impact
3. **Fix** - Make necessary corrections immediately using best practices
4. **Verify** - Re-run QA tools to confirm fixes work properly
5. **Continue** - Only proceed once all critical issues are resolved

### File Type Handling

- **Code Files** (.py, .js, .ts, .java, .cpp, .go, .rs, etc.) → Static analysis + syntax checking
- **Log Files** (.log, .out, .err) → Error/warning detection and analysis
- **Config Files** (.json, .yaml, .toml, .xml) → Format validation and syntax checking
- **Test Files** (*test*, *spec*, *__tests__*) → Run appropriate test suites when possible
- **Documentation** (.md, .rst, .txt) → Basic formatting and link validation

### Error Handling

If QA tools encounter errors:
- Report the specific error to the user with context
- Suggest manual resolution steps
- Do not proceed with additional operations until resolved
- Log all errors for debugging purposes

### Quality Standards

Maintain these standards in all code:
- **No syntax errors** - All code must be syntactically correct
- **No undefined variables** - All variables must be defined before use
- **Consistent style** - Follow project or language conventions
- **Security awareness** - Avoid common security vulnerabilities
- **Error handling** - Properly handle exceptions and edge cases

### Development Best Practices

Always follow these practices:
- Write clear, self-documenting code
- Use meaningful variable and function names
- Include appropriate comments for complex logic
- Handle errors gracefully
- Follow language-specific conventions
- Test code changes when possible

### Debugging and Troubleshooting

When issues arise:
1. Check the specific error messages from QA tools
2. Review the file context around the issue
3. Consider the broader impact of changes
4. Test fixes in isolation when possible
5. Document any workarounds or special cases

### Troubleshooting Auto-QA

If auto-QA is not running automatically in your Claude Code instance:

1. **Check Hook Configuration**
   - Verify hooks are configured in `~/.claude/settings.json`
   - Look for duplicate entries (should only have one entry per tool)
   - Run `/hooks` in Claude Code to see active hooks

2. **Check Debug Logs**
   - View auto-QA execution logs: `tail -f ~/.claude/logs/auto_qa_debug.log`
   - Look for "Auto-QA Hook Triggered" messages
   - Check which files are being analyzed

3. **Verify QA Tools Installation**
   ```bash
   # Test if QA tools are accessible
   python -m qa_tools.auto_qa --help
   
   # Test static analysis directly
   python -m qa_tools.static_check python -m py_compile test.py
   ```

4. **Install Better Linters**
   - For Python: `pip install pylint`
   - For JavaScript/TypeScript: `npm install -g eslint`
   - Auto-QA will use these if available for better analysis

5. **Manual Testing**
   - Create a test file with errors: `test_auto_qa_hooks.py`
   - Check if hooks fire when you save/edit files
   - Review `logs/qa_results.ndjson` for results

6. **Common Issues**
   - Duplicate hook entries can cause multiple executions
   - Missing linters result in basic syntax checks only
   - Claude Code may need restart after settings changes
   - Check permissions in `.claude/settings.local.json`

### Performance Considerations

- QA tools should not significantly slow down development
- Skip QA for very large files (>10MB) unless specifically requested
- Use appropriate timeout values for linting operations
- Cache QA results when possible to avoid redundant checks

### Integration with Development Workflow

- QA runs automatically after file operations
- Results are logged to `logs/qa_results.ndjson`
- Critical issues block further development
- Non-critical issues are reported but don't block progress
- Manual QA commands available for specific needs

### Proactive Integration Testing

**Automatically run integration tests when:**
1. Creating or modifying API endpoint handlers
2. Changing route configurations
3. Modifying authentication/authorization logic
4. After fixing API-related bugs
5. When API documentation mentions specific expected behaviors

**Example workflow:**
```bash
# After creating a new endpoint /api/products
python -m qa_tools.int_tests --method GET --url /api/products --status 200 --base-url http://localhost:8000

# After adding authentication
python -m qa_tools.int_tests --method GET --url /api/products --status 401 --base-url http://localhost:8000
python -m qa_tools.int_tests --method GET --url /api/products --headers '{"Authorization":"Bearer valid-token"}' --status 200 --base-url http://localhost:8000

# After implementing POST endpoint
python -m qa_tools.int_tests --method POST --url /api/products --body '{"name":"Test Product","price":9.99}' --status 201 --base-url http://localhost:8000
```