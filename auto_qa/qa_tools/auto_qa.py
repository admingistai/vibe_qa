#!/usr/bin/env python3
"""Auto-QA Coordinator Script

Automatically runs appropriate QA tools after Claude Code write operations.
Designed to be called by Claude Code hooks or manually.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

try:
    from .static_check import run_lint
    from .log_scan import scan_logs
    from .int_tests import run_flow
except ImportError:
    # Fallback for global installation
    import importlib.util
    import qa_tools.static_check as static_check
    import qa_tools.log_scan as log_scan
    import qa_tools.int_tests as int_tests
    run_lint = static_check.run_lint
    scan_logs = log_scan.scan_logs
    run_flow = int_tests.run_flow


def get_file_type(file_path: str) -> str:
    """Determine file type for QA tool selection"""
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    # Code files that benefit from static analysis
    code_extensions = {
        '.py': 'python',
        '.js': 'javascript', 
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala'
    }
    
    # Configuration files
    config_extensions = {
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.xml': 'xml',
        '.ini': 'ini'
    }
    
    # Test files
    test_patterns = ['test', 'spec', '__tests__']
    
    if suffix in code_extensions:
        return code_extensions[suffix]
    elif suffix in config_extensions:
        return config_extensions[suffix]
    elif any(pattern in path.name.lower() for pattern in test_patterns):
        return 'test'
    elif suffix in ['.log', '.out', '.err']:
        return 'log'
    else:
        return 'unknown'


def get_linter_command(file_type: str, file_path: str) -> Optional[List[str]]:
    """Get appropriate linter command for file type"""
    commands = {
        'python': ['python', '-m', 'py_compile', file_path],  # Basic syntax check
        'javascript': ['node', '--check', file_path],  # Basic syntax check
        'typescript': ['npx', 'tsc', '--noEmit', file_path],
        'json': ['python', '-m', 'json.tool', file_path],
        'yaml': ['python', '-c', f'import yaml; yaml.safe_load(open("{file_path}"))']
    }
    
    # Try to use more sophisticated linters if available
    sophisticated_commands = {
        'python': ['pylint', '--output-format=json', file_path],
        'javascript': ['eslint', '--format=json', file_path],
        'typescript': ['eslint', '--format=json', file_path]
    }
    
    # Check if sophisticated linter is available
    if file_type in sophisticated_commands:
        cmd = sophisticated_commands[file_type]
        try:
            subprocess.run([cmd[0], '--version'], capture_output=True, check=True)
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    return commands.get(file_type)


def run_static_analysis(file_path: str) -> Dict[str, Any]:
    """Run static analysis on a file"""
    file_type = get_file_type(file_path)
    linter_cmd = get_linter_command(file_type, file_path)
    
    if not linter_cmd:
        return {
            "success": True,
            "issues": [],
            "message": f"No linter available for {file_type} files"
        }
    
    return run_lint(linter_cmd)


def run_log_analysis(text: str) -> Dict[str, Any]:
    """Run log analysis on text content"""
    return scan_logs(text)


def analyze_recent_writes(max_age_minutes: int = 5) -> List[str]:
    """Find recently written files in current directory"""
    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_minutes * 60
    
    recent_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common build/cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'build', 'dist']]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_time = os.path.getmtime(file_path)
                if current_time - file_time < max_age_seconds:
                    recent_files.append(file_path)
            except OSError:
                continue
    
    return recent_files


def setup_logging():
    """Setup debug logging to track hook executions"""
    log_dir = Path.home() / '.claude' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'auto_qa_debug.log'
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """Main coordinator function"""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("Auto-QA Hook Triggered")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Command Line Args: {sys.argv}")
    logger.info(f"Environment: {os.environ.get('CLAUDE_CODE_TOOL', 'Not set')}")
    
    # Check for environment variables that might contain file info
    claude_file = os.environ.get('CLAUDE_FILE_PATH')
    claude_dir = os.environ.get('CLAUDE_WORKING_DIR')
    
    if claude_file:
        logger.info(f"CLAUDE_FILE_PATH: {claude_file}")
    if claude_dir:
        logger.info(f"CLAUDE_WORKING_DIR: {claude_dir}")
        # Change to the Claude working directory if provided
        try:
            os.chdir(claude_dir)
            logger.info(f"Changed to directory: {claude_dir}")
        except Exception as e:
            logger.error(f"Failed to change directory: {e}")
    
    print("🔍 Auto-QA: Analyzing recent changes...")
    
    # Determine what to analyze
    if len(sys.argv) > 1:
        # Specific file provided
        target_file = sys.argv[1]
        logger.info(f"Specific file provided: {target_file}")
        
        # If it's not an absolute path and we have a Claude dir, make it relative to that
        if not os.path.isabs(target_file) and claude_dir and not os.path.exists(target_file):
            potential_path = os.path.join(claude_dir, target_file)
            if os.path.exists(potential_path):
                target_file = potential_path
                logger.info(f"Resolved to: {target_file}")
        
        if not os.path.exists(target_file):
            logger.error(f"File not found: {target_file}")
            print(f"❌ File not found: {target_file}")
            sys.exit(1)
        files_to_check = [target_file]
    elif claude_file:
        # Use file from environment if provided
        logger.info(f"Using file from CLAUDE_FILE_PATH: {claude_file}")
        if os.path.exists(claude_file):
            files_to_check = [claude_file]
        else:
            logger.error(f"File from env not found: {claude_file}")
            files_to_check = []
    else:
        # Analyze recent writes in current directory
        logger.info("No specific file provided, analyzing recent writes...")
        files_to_check = analyze_recent_writes()
        logger.info(f"Found {len(files_to_check)} recent files to check")
    
    if not files_to_check:
        logger.info("No recent files to analyze")
        print("✅ No recent files to analyze")
        sys.exit(0)
    
    total_issues = 0
    critical_issues = 0
    
    for file_path in files_to_check:
        logger.info(f"Analyzing file: {file_path}")
        print(f"\n📄 Analyzing: {file_path}")
        
        try:
            # Run static analysis
            result = run_static_analysis(file_path)
            logger.debug(f"Static analysis result: {result}")
            
            if result["issues"]:
                print(f"  ⚠️  Found {len(result['issues'])} issues:")
                for issue in result["issues"][:5]:  # Show first 5 issues
                    severity = "🔴" if issue.get("severity", 0) > 0 else "🟡"
                    print(f"    {severity} {issue['location']}: {issue['message']}")
                    if issue.get("severity", 0) > 0:
                        critical_issues += 1
                    total_issues += 1
                
                if len(result["issues"]) > 5:
                    print(f"    ... and {len(result['issues']) - 5} more issues")
            else:
                print("  ✅ No static analysis issues found")
            
            # For log files, also run log analysis
            if get_file_type(file_path) == 'log':
                with open(file_path, 'r') as f:
                    log_content = f.read()
                log_result = run_log_analysis(log_content)
                
                if log_result["issues"]:
                    print(f"  ⚠️  Found {len(log_result['issues'])} log issues:")
                    for issue in log_result["issues"][:3]:
                        severity = "🔴" if issue.get("severity") == "high" else "🟡"
                        print(f"    {severity} {issue['location']}: {issue['message']}")
                        if issue.get("severity") == "high":
                            critical_issues += 1
                        total_issues += 1
                
        except Exception as e:
            logger.exception(f"Error analyzing {file_path}")
            print(f"  ❌ Error analyzing {file_path}: {str(e)}")
            critical_issues += 1
    
    # Summary
    logger.info(f"Auto-QA Summary - Files: {len(files_to_check)}, Total Issues: {total_issues}, Critical: {critical_issues}")
    print(f"\n📊 Auto-QA Summary:")
    print(f"  Files analyzed: {len(files_to_check)}")
    print(f"  Total issues: {total_issues}")
    print(f"  Critical issues: {critical_issues}")
    
    if critical_issues > 0:
        logger.warning(f"Exiting with critical issues: {critical_issues}")
        print(f"\n🚨 Found {critical_issues} critical issues that need attention!")
        print("💡 Claude should fix these issues before continuing.")
        sys.exit(1)
    elif total_issues > 0:
        logger.warning(f"Exiting with non-critical issues: {total_issues}")
        print(f"\n⚠️  Found {total_issues} issues that should be reviewed.")
        sys.exit(2)
    else:
        logger.info("All checks passed successfully")
        print("\n✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
