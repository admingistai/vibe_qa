"""Log and Warning Inspection Tool

Analyzes stdout/stderr text buffers to identify errors, warnings, 
stack traces, and HTTP error codes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def _log_result(result: Dict[str, Any]) -> None:
    """Log result to qa_results.ndjson"""
    log_path = Path("logs/qa_results.ndjson")
    log_path.parent.mkdir(exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": "log_scan",
        **result
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def _extract_context(lines: List[str], line_idx: int, context_size: int = 2) -> str:
    """Extract context lines around a problematic line"""
    start = max(0, line_idx - context_size)
    end = min(len(lines), line_idx + context_size + 1)
    
    context_lines = []
    for i in range(start, end):
        marker = ">>> " if i == line_idx else "    "
        context_lines.append(f"{marker}{lines[i]}")
    
    return "\n".join(context_lines)


def scan_logs(text: str) -> Dict[str, Any]:
    """Scan log text for errors, warnings, stack traces, and HTTP errors
    
    Args:
        text: Complete stdout/stderr buffer text to analyze
        
    Returns:
        Dict with 'success' bool and 'issues' list
    """
    result = {
        "success": True,
        "issues": []
    }
    
    if not text or not text.strip():
        _log_result(result)
        return result
    
    lines = text.split('\n')
    
    # Define patterns for different types of issues
    patterns = [
        # Error patterns
        {
            "name": "error",
            "pattern": re.compile(r'\b(ERROR|FATAL|CRITICAL|EXCEPTION|FAILED?)\b', re.IGNORECASE),
            "severity": "high"
        },
        # Warning patterns  
        {
            "name": "warning",
            "pattern": re.compile(r'\b(WARN|WARNING|CAUTION)\b', re.IGNORECASE),
            "severity": "medium"
        },
        # Stack trace patterns
        {
            "name": "stack_trace",
            "pattern": re.compile(r'^\s*at\s+.*\(.*:\d+:\d+\)|^\s*File\s+".*", line\s+\d+|Traceback \(most recent call last\)', re.IGNORECASE),
            "severity": "high"
        },
        # HTTP error codes
        {
            "name": "http_error",
            "pattern": re.compile(r'\b(4\d{2}|5\d{2})\b|\b(400|401|403|404|500|502|503|504)\b'),
            "severity": "medium"
        },
        # Database errors
        {
            "name": "db_error",
            "pattern": re.compile(r'\b(SQL|Database|Connection)\s*(Error|Exception|Failed)', re.IGNORECASE),
            "severity": "high"
        },
        # Network/timeout errors
        {
            "name": "network_error",
            "pattern": re.compile(r'\b(timeout|connection\s+refused|network\s+error|dns\s+error)\b', re.IGNORECASE),
            "severity": "medium"
        },
        # Memory/resource errors
        {
            "name": "resource_error",
            "pattern": re.compile(r'\b(out\s+of\s+memory|memory\s+error|disk\s+full|resource\s+exhausted)\b', re.IGNORECASE),
            "severity": "high"
        },
        # Security-related issues
        {
            "name": "security_issue",
            "pattern": re.compile(r'\b(unauthorized|forbidden|access\s+denied|authentication\s+failed|permission\s+denied)\b', re.IGNORECASE),
            "severity": "high"
        }
    ]
    
    # Scan each line for patterns
    for line_idx, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        for pattern_info in patterns:
            if pattern_info["pattern"].search(line):
                # Extract context around the problematic line
                context = _extract_context(lines, line_idx)
                
                # Determine location info
                location = f"line {line_idx + 1}"
                
                # Try to extract more specific location info if available
                file_match = re.search(r'([^/\s]+\.(py|js|ts|java|cpp|c|rb|go|php|rs))', line)
                if file_match:
                    location = f"{file_match.group(1)}:{line_idx + 1}"
                
                result["issues"].append({
                    "type": "log",
                    "location": location,
                    "message": line_stripped,
                    "category": pattern_info["name"],
                    "severity": pattern_info["severity"],
                    "context": context
                })
    
    # Additional checks for multi-line patterns
    text_lower = text.lower()
    
    # Check for stack traces spanning multiple lines
    stack_trace_starts = []
    for i, line in enumerate(lines):
        if re.search(r'traceback|exception|error:', line, re.IGNORECASE):
            stack_trace_starts.append(i)
    
    # Look for common multi-line error patterns
    if "traceback (most recent call last)" in text_lower:
        start_idx = text_lower.find("traceback (most recent call last)")
        start_line = text[:start_idx].count('\n')
        
        result["issues"].append({
            "type": "log",
            "location": f"line {start_line + 1}",
            "message": "Python traceback detected",
            "category": "stack_trace",
            "severity": "high",
            "context": _extract_context(lines, start_line, 5)
        })
    
    # Check for build/compilation failures
    if any(term in text_lower for term in ["build failed", "compilation error", "make: ***"]):
        result["issues"].append({
            "type": "log",
            "location": "build",
            "message": "Build or compilation failure detected",
            "category": "build_error",
            "severity": "high",
            "context": text[:500] + "..." if len(text) > 500 else text
        })
    
    # Success is false if any high severity issues found
    high_severity_count = sum(1 for issue in result["issues"] if issue.get("severity") == "high")
    if high_severity_count > 0:
        result["success"] = False
    
    # Log the result
    _log_result(result)
    
    return result