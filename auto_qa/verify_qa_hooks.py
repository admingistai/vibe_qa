#!/usr/bin/env python3
"""Verify QA Hooks Configuration

This script helps verify that auto-QA hooks are properly configured
and working in your Claude Code environment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def check_settings_file():
    """Check if Claude settings.json exists and has hooks configured"""
    settings_path = Path.home() / '.claude' / 'settings.json'
    
    print("🔍 Checking Claude Code settings...")
    
    if not settings_path.exists():
        print("❌ Settings file not found at ~/.claude/settings.json")
        return False
    
    try:
        with open(settings_path) as f:
            settings = json.load(f)
        
        hooks = settings.get('hooks', {}).get('PostToolUse', [])
        
        if not hooks:
            print("❌ No PostToolUse hooks configured")
            return False
        
        # Check for auto_qa hooks
        auto_qa_hooks = []
        for hook in hooks:
            if hook.get('matcher') in ['Write', 'Edit', 'MultiEdit']:
                hook_cmds = hook.get('hooks', [])
                for cmd in hook_cmds:
                    if 'qa_tools.auto_qa' in cmd.get('command', ''):
                        auto_qa_hooks.append(f"{hook['matcher']}: {cmd['command']}")
        
        if auto_qa_hooks:
            print(f"✅ Found {len(auto_qa_hooks)} auto-QA hooks:")
            for hook in auto_qa_hooks:
                print(f"   - {hook}")
            
            # Check for duplicates
            if len(auto_qa_hooks) > 3:
                print("⚠️  Warning: Duplicate hooks detected. Should only have 3 (Write, Edit, MultiEdit)")
        else:
            print("❌ No auto-QA hooks found in PostToolUse")
            return False
            
    except Exception as e:
        print(f"❌ Error reading settings: {e}")
        return False
    
    return True

def check_qa_tools():
    """Check if QA tools are accessible"""
    print("\n🔍 Checking QA tools availability...")
    
    tools_ok = True
    
    # Check auto_qa
    try:
        result = subprocess.run(['python', '-m', 'qa_tools.auto_qa', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ qa_tools.auto_qa is accessible")
        else:
            print("❌ qa_tools.auto_qa failed to run")
            tools_ok = False
    except Exception as e:
        print(f"❌ Error running qa_tools.auto_qa: {e}")
        tools_ok = False
    
    # Check static_check
    try:
        result = subprocess.run(['python', '-m', 'qa_tools.static_check', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ qa_tools.static_check is accessible")
        else:
            print("❌ qa_tools.static_check failed to run")
            tools_ok = False
    except Exception as e:
        print(f"❌ Error running qa_tools.static_check: {e}")
        tools_ok = False
    
    return tools_ok

def check_linters():
    """Check which linters are available"""
    print("\n🔍 Checking available linters...")
    
    linters = {
        'pylint': ['pylint', '--version'],
        'eslint': ['eslint', '--version'],
        'ruff': ['ruff', '--version'],
        'mypy': ['mypy', '--version']
    }
    
    available = []
    for name, cmd in linters.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                available.append(name)
                print(f"✅ {name} is installed")
            else:
                print(f"❌ {name} not found")
        except FileNotFoundError:
            print(f"❌ {name} not found")
    
    if not available:
        print("\n⚠️  No advanced linters found. Auto-QA will use basic syntax checking only.")
        print("   Install linters for better analysis:")
        print("   - Python: pip install pylint")
        print("   - JavaScript: npm install -g eslint")
    
    return available

def check_debug_logs():
    """Check if debug logs show recent activity"""
    print("\n🔍 Checking debug logs...")
    
    log_path = Path.home() / '.claude' / 'logs' / 'auto_qa_debug.log'
    
    if not log_path.exists():
        print("❌ Debug log not found at ~/.claude/logs/auto_qa_debug.log")
        print("   This means hooks haven't run yet")
        return False
    
    # Check last modification time
    mod_time = datetime.fromtimestamp(log_path.stat().st_mtime)
    age = datetime.now() - mod_time
    
    if age < timedelta(minutes=5):
        print(f"✅ Debug log shows recent activity ({age.seconds} seconds ago)")
        
        # Show last few hook triggers
        try:
            with open(log_path) as f:
                lines = f.readlines()
            
            triggers = [l for l in lines[-50:] if 'Hook Triggered' in l]
            if triggers:
                print(f"   Last hook trigger: {triggers[-1].strip()}")
        except:
            pass
    else:
        print(f"⚠️  Debug log hasn't been updated in {age.days} days, {age.seconds//3600} hours")
        print("   Hooks may not be running")
    
    return True

def test_hook_execution():
    """Create a test file to trigger hooks"""
    print("\n🧪 Testing hook execution...")
    
    test_file = Path("test_qa_hook_trigger.py")
    
    print(f"Creating test file: {test_file}")
    with open(test_file, 'w') as f:
        f.write("# Test file for QA hooks\nprint('Testing')\n")
    
    print("✅ Test file created")
    print("\n⚠️  Note: Hooks only trigger when Claude Code performs file operations")
    print("   This manual test won't trigger hooks - use Claude Code to edit files")
    
    # Clean up
    test_file.unlink()
    print("🧹 Test file cleaned up")
    
    return True

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Claude Code Auto-QA Hook Verification")
    print("=" * 60)
    
    all_ok = True
    
    # Run checks
    all_ok &= check_settings_file()
    all_ok &= check_qa_tools()
    check_linters()  # Informational only
    check_debug_logs()  # Informational only
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ Basic configuration looks good!")
        print("\nTo test if hooks are working:")
        print("1. Ask Claude Code to create or edit a Python file")
        print("2. Check ~/.claude/logs/auto_qa_debug.log for activity")
        print("3. Look for QA output in Claude Code's response")
    else:
        print("❌ Some issues found - please fix them and try again")
        print("\nFor more help, see the troubleshooting section in CLAUDE.md")
    
    print("=" * 60)

if __name__ == "__main__":
    main()