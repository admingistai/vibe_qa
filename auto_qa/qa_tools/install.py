#!/usr/bin/env python3
"""Global Installation Script for Claude Code Auto-QA

Automatically installs and configures the QA tools for global use with Claude Code.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any


def get_python_site_packages():
    """Get the site-packages directory for current Python installation"""
    try:
        import site
        return site.getsitepackages()[0]
    except Exception:
        # Fallback method
        result = subprocess.run([sys.executable, '-c', 'import site; print(site.getsitepackages()[0])'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None


def get_claude_config_dir():
    """Get Claude Code configuration directory"""
    home = Path.home()
    return home / '.claude'


def backup_existing_config(config_path: Path) -> bool:
    """Backup existing configuration file"""
    if config_path.exists():
        backup_path = config_path.with_suffix('.backup')
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backed up existing config to {backup_path}")
        return True
    return False


def merge_settings(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new settings with existing settings"""
    merged = existing.copy()
    
    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_settings(merged[key], value)
        elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
            # For lists, extend rather than replace
            merged[key].extend(value)
        else:
            merged[key] = value
    
    return merged


def install_qa_tools():
    """Install QA tools to Python site-packages"""
    print("🔧 Installing QA tools to Python site-packages...")
    
    # Get site-packages directory
    site_packages = get_python_site_packages()
    if not site_packages:
        print("❌ Could not determine Python site-packages directory")
        return False
    
    site_packages_path = Path(site_packages)
    if not site_packages_path.exists():
        print(f"❌ Site-packages directory not found: {site_packages_path}")
        return False
    
    # Current qa_tools directory
    current_dir = Path(__file__).parent
    qa_tools_source = current_dir
    qa_tools_dest = site_packages_path / 'qa_tools'
    
    try:
        # Remove existing installation
        if qa_tools_dest.exists():
            shutil.rmtree(qa_tools_dest)
            print("🗑️  Removed existing qa_tools installation")
        
        # Copy qa_tools to site-packages
        shutil.copytree(qa_tools_source, qa_tools_dest)
        print(f"✅ Installed qa_tools to {qa_tools_dest}")
        
        # Test the installation
        try:
            subprocess.run([sys.executable, '-c', 'import qa_tools; print("QA tools import successful")'], 
                          check=True, capture_output=True)
            print("✅ QA tools installation verified")
            return True
        except subprocess.CalledProcessError:
            print("❌ QA tools installation verification failed")
            return False
        
    except Exception as e:
        print(f"❌ Failed to install QA tools: {e}")
        return False


def setup_claude_settings():
    """Set up global Claude Code settings"""
    print("⚙️  Setting up Claude Code global settings...")
    
    claude_dir = get_claude_config_dir()
    claude_dir.mkdir(exist_ok=True)
    
    settings_path = claude_dir / 'settings.json'
    
    # New settings to add
    new_settings = {
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
    
    try:
        # Load existing settings
        existing_settings = {}
        if settings_path.exists():
            backup_existing_config(settings_path)
            with open(settings_path, 'r') as f:
                existing_settings = json.load(f)
        
        # Merge settings
        merged_settings = merge_settings(existing_settings, new_settings)
        
        # Write updated settings
        with open(settings_path, 'w') as f:
            json.dump(merged_settings, f, indent=2)
        
        print(f"✅ Updated Claude settings: {settings_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Claude settings: {e}")
        return False


def setup_claude_memory():
    """Set up global Claude Code memory"""
    print("🧠 Setting up Claude Code global memory...")
    
    claude_dir = get_claude_config_dir()
    memory_path = claude_dir / 'CLAUDE.md'
    
    memory_content = '''# Auto-QA Workflow

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
'''
    
    try:
        # Backup existing memory file
        if memory_path.exists():
            backup_existing_config(memory_path)
            # Append to existing memory rather than overwrite
            with open(memory_path, 'a') as f:
                f.write('\n\n' + memory_content)
            print(f"✅ Appended to existing Claude memory: {memory_path}")
        else:
            # Create new memory file
            with open(memory_path, 'w') as f:
                f.write(memory_content)
            print(f"✅ Created Claude memory file: {memory_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup Claude memory: {e}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    current_dir = Path(__file__).parent.parent
    requirements_path = current_dir / 'requirements.txt'
    
    if not requirements_path.exists():
        print("⚠️  requirements.txt not found, skipping dependency installation")
        return True
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def test_installation():
    """Test the complete installation"""
    print("🧪 Testing installation...")
    
    tests = [
        ("QA tools import", "python -c 'import qa_tools; print(\"OK\")'"),
        ("Auto-QA coordinator", "python -m qa_tools.auto_qa --help"),
        ("Static check", "python -c 'from qa_tools.static_check import run_lint; print(\"OK\")'"),
        ("Log scan", "python -c 'from qa_tools.log_scan import scan_logs; print(\"OK\")'"),
        ("Integration tests", "python -c 'from qa_tools.int_tests import run_flow; print(\"OK\")'"),
    ]
    
    all_passed = True
    for test_name, command in tests:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {test_name}")
            else:
                print(f"  ❌ {test_name}: {result.stderr}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main installation function"""
    print("🚀 Installing Claude Code Auto-QA System")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Install QA tools
    if not install_qa_tools():
        success = False
    
    # Setup Claude settings
    if not setup_claude_settings():
        success = False
    
    # Setup Claude memory DEPRECATED - set up manually
    #if not setup_claude_memory():
    #    success = False
    
    # Test installation
    if not test_installation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Restart Claude Code to load the new configuration")
        print("2. Test by editing a file and watching for automatic QA")
        print("3. Check logs/qa_results.ndjson for QA results")
        print("\nFor troubleshooting, see SETUP_GLOBAL_QA.md")
    else:
        print("❌ Installation failed. Please check the errors above.")
        print("See SETUP_GLOBAL_QA.md for manual setup instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
