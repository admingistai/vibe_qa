#!/usr/bin/env python3
"""Test script to verify Auto-QA installation works correctly"""

import sys
import tempfile
import os
from pathlib import Path

def test_basic_import():
    """Test basic import of qa_tools"""
    try:
        import qa_tools
        print("✅ qa_tools import successful")
        return True
    except ImportError as e:
        print(f"❌ qa_tools import failed: {e}")
        return False

def test_static_check():
    """Test static_check functionality"""
    try:
        from qa_tools.static_check import run_lint
        
        # Create a temporary Python file with a syntax error
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    print('Hello'")  # Missing closing parenthesis
            temp_file = f.name
        
        try:
            # Test basic compile check
            result = run_lint(['python', '-m', 'py_compile', temp_file])
            if result['issues']:
                print("✅ static_check detected syntax error correctly")
                return True
            else:
                print("⚠️  static_check should have detected syntax error")
                return False
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ static_check test failed: {e}")
        return False

def test_log_scan():
    """Test log_scan functionality"""
    try:
        from qa_tools.log_scan import scan_logs
        
        test_log = """
        INFO: Starting application
        ERROR: Database connection failed
        WARNING: Retrying connection
        INFO: Application started successfully
        """
        
        result = scan_logs(test_log)
        if result['issues'] and len(result['issues']) >= 2:  # Should find ERROR and WARNING
            print("✅ log_scan detected errors and warnings correctly")
            return True
        else:
            print("⚠️  log_scan should have detected ERROR and WARNING")
            return False
            
    except Exception as e:
        print(f"❌ log_scan test failed: {e}")
        return False

def test_int_tests():
    """Test int_tests functionality"""
    try:
        from qa_tools.int_tests import run_flow
        
        # Create a simple test flow
        test_flow = {
            "name": "Test Flow",
            "steps": [
                {
                    "name": "Invalid URL Test",
                    "method": "GET",
                    "url": "/nonexistent",
                    "expect": {"status": 404}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(test_flow, f)
            temp_file = f.name
        
        try:
            # This should fail due to invalid URL, which is expected
            result = run_flow(temp_file, "http://httpbin.org")
            print("✅ int_tests executed without crashing")
            return True
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ int_tests test failed: {e}")
        return False

def test_auto_qa():
    """Test auto_qa coordinator"""
    try:
        from qa_tools.auto_qa import get_file_type, get_linter_command
        
        # Test file type detection
        if get_file_type("test.py") == "python":
            print("✅ auto_qa file type detection working")
        else:
            print("⚠️  auto_qa file type detection issue")
            return False
            
        # Test linter command generation
        cmd = get_linter_command("python", "test.py")
        if cmd:
            print("✅ auto_qa linter command generation working")
            return True
        else:
            print("⚠️  auto_qa linter command generation issue")
            return False
            
    except Exception as e:
        print(f"❌ auto_qa test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Auto-QA Installation")
    print("=" * 40)
    
    tests = [
        ("Basic Import", test_basic_import),
        ("Static Check", test_static_check),
        ("Log Scan", test_log_scan),
        ("Integration Tests", test_int_tests),
        ("Auto QA Coordinator", test_auto_qa),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed: {test_name}")
    
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Auto-QA is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())