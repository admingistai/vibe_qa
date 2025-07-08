"""QA Tool Suite #1 - Automated Quality Assurance Utilities

This package provides three core QA utilities for Claude Code:
1. static_check - Static analysis and linting
2. log_scan - Log and warning inspection  
3. int_tests - Integration flow testing

All tools return standardized JSON results and log to qa_results.ndjson
"""

from .static_check import run_lint
from .log_scan import scan_logs
from .int_tests import run_flow

__version__ = "0.1"
__all__ = ["run_lint", "scan_logs", "run_flow"]