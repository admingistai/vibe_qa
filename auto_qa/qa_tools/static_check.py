"""Static Analysis and Linting Tool

Executes linter commands and parses their output into normalized issues.
Supports JSON and text output formats from various linters.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


def _log_result(result: Dict[str, Any]) -> None:
    """Log result to qa_results.ndjson"""
    log_path = Path("logs/qa_results.ndjson")
    log_path.parent.mkdir(exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": "static_check",
        **result
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def _parse_eslint_json(output: str) -> List[Dict[str, Any]]:
    """Parse ESLint JSON output"""
    try:
        data = json.loads(output)
        issues = []
        for file_result in data:
            file_path = file_result.get("filePath", "")
            for message in file_result.get("messages", []):
                issues.append({
                    "type": "lint",
                    "location": f"{file_path}:{message.get('line', 0)}:{message.get('column', 0)}",
                    "message": message.get("message", ""),
                    "code": message.get("ruleId", ""),
                    "severity": message.get("severity", 1)
                })
        return issues
    except json.JSONDecodeError:
        return []


def _parse_pylint_json(output: str) -> List[Dict[str, Any]]:
    """Parse pylint JSON output"""
    try:
        data = json.loads(output)
        issues = []
        for item in data:
            issues.append({
                "type": "lint",
                "location": f"{item.get('path', '')}:{item.get('line', 0)}:{item.get('column', 0)}",
                "message": item.get("message", ""),
                "code": item.get("message-id", ""),
                "severity": 1 if item.get("type") == "error" else 0
            })
        return issues
    except json.JSONDecodeError:
        return []


def _parse_text_output(output: str) -> List[Dict[str, Any]]:
    """Parse generic text output using regex patterns"""
    issues = []
    
    # Common patterns for linters
    patterns = [
        # file:line:col: message
        re.compile(r"^([^:]+):(\d+):(\d+):\s*(.*?)$", re.MULTILINE),
        # file:line: message  
        re.compile(r"^([^:]+):(\d+):\s*(.*?)$", re.MULTILINE),
        # file(line,col): message
        re.compile(r"^([^(]+)\((\d+),(\d+)\):\s*(.*?)$", re.MULTILINE),
        # file(line): message
        re.compile(r"^([^(]+)\((\d+)\):\s*(.*?)$", re.MULTILINE),
        # Python syntax error: File "file", line X
        re.compile(r'File "([^"]+)", line (\d+)', re.MULTILINE),
    ]
    
    for pattern in patterns:
        for match in pattern.finditer(output):
            groups = match.groups()
            if len(groups) >= 2:
                file_path = groups[0]
                line = groups[1]
                
                # Handle Python syntax errors specially
                if 'File "' in pattern.pattern:
                    # Extract the error type from output (usually follows the match)
                    error_msg = "SyntaxError"
                    if "SyntaxError:" in output:
                        error_msg = output.split("SyntaxError:")[1].strip().split('\n')[0]
                    
                    issues.append({
                        "type": "lint",
                        "location": f"{file_path}:{line}:0",
                        "message": f"SyntaxError: {error_msg}",
                        "code": "syntax-error",
                        "severity": 1
                    })
                elif len(groups) >= 3:
                    col = groups[2] if len(groups) > 3 else "0"
                    message = groups[-1]
                    
                    issues.append({
                        "type": "lint",
                        "location": f"{file_path}:{line}:{col}",
                        "message": message.strip(),
                        "code": "",
                        "severity": 1 if any(word in message.lower() for word in ["error", "fail"]) else 0
                    })
    
    return issues


def run_lint(cmd: List[str]) -> Dict[str, Any]:
    """Execute linter command and parse output into normalized issues
    
    Args:
        cmd: List of command arguments (e.g., ['eslint', 'src', '-f', 'json'])
        
    Returns:
        Dict with 'success' bool and 'issues' list
    """
    result = {
        "success": False,
        "issues": []
    }
    
    try:
        # Execute the linter command
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Capture both stdout and stderr
        output = proc.stdout + proc.stderr
        
        # Try to parse as JSON first (common for modern linters)
        if "--format=json" in cmd or "--output-format=json" in cmd or ("-f" in cmd and "json" in cmd):
            # Try different JSON parsers based on likely tool
            if "eslint" in cmd[0].lower():
                result["issues"] = _parse_eslint_json(proc.stdout)
            elif "pylint" in cmd[0].lower():
                result["issues"] = _parse_pylint_json(proc.stdout)
            else:
                # Generic JSON attempt
                try:
                    data = json.loads(proc.stdout)
                    result["issues"] = [{"type": "lint", "location": "unknown", "message": str(data)}]
                except json.JSONDecodeError:
                    result["issues"] = _parse_text_output(output)
        else:
            # Parse as text output
            result["issues"] = _parse_text_output(output)
        
        # Success if command ran (exit code doesn't matter for linters)
        result["success"] = True
        
    except subprocess.TimeoutExpired:
        result["issues"] = [{
            "type": "lint",
            "location": "system",
            "message": f"Linter command timed out: {' '.join(cmd)}",
            "code": "timeout"
        }]
    except FileNotFoundError:
        result["issues"] = [{
            "type": "lint", 
            "location": "system",
            "message": f"Linter command not found: {cmd[0]}",
            "code": "not_found"
        }]
    except Exception as e:
        result["issues"] = [{
            "type": "lint",
            "location": "system", 
            "message": f"Error running linter: {str(e)}",
            "code": "error"
        }]
    
    # Log the result
    _log_result(result)
    
    return result