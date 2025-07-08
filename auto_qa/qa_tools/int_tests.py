"""Integration Flow Testing Tool

Executes multi-step API sequences defined in YAML/JSON collections.
Records per-step status and surfaces the first failing step.
"""

import json
import yaml
import requests
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


def _log_result(result: Dict[str, Any]) -> None:
    """Log result to qa_results.ndjson"""
    log_path = Path("logs/qa_results.ndjson")
    log_path.parent.mkdir(exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": "int_tests",
        **result
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def _load_collection(collection_path: str) -> Dict[str, Any]:
    """Load test collection from YAML or JSON file"""
    path = Path(collection_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Collection file not found: {collection_path}")
    
    with open(path, 'r') as f:
        if path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)


def _substitute_variables(text: str, variables: Dict[str, Any]) -> str:
    """Substitute variables in text using {{variable}} syntax"""
    if not isinstance(text, str):
        return text
    
    result = text
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    
    return result


def _extract_response_data(response: requests.Response, extract_config: Dict[str, str]) -> Dict[str, Any]:
    """Extract data from response for use in subsequent steps"""
    extracted = {}
    
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        response_data = {"text": response.text}
    
    for var_name, json_path in extract_config.items():
        try:
            # Simple JSON path extraction (supports dot notation)
            value = response_data
            for key in json_path.split('.'):
                if key.isdigit():
                    value = value[int(key)]
                else:
                    value = value[key]
            extracted[var_name] = value
        except (KeyError, IndexError, TypeError):
            extracted[var_name] = None
    
    return extracted


def _validate_response(response: requests.Response, expectations: Dict[str, Any]) -> List[str]:
    """Validate response against expectations"""
    errors = []
    
    # Check status code
    expected_status = expectations.get("status", 200)
    if response.status_code != expected_status:
        errors.append(f"Expected status {expected_status}, got {response.status_code}")
    
    # Check response body
    if "body" in expectations:
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        expected_body = expectations["body"]
        if isinstance(expected_body, dict) and isinstance(response_data, dict):
            # Check if all expected keys/values are present
            for key, expected_value in expected_body.items():
                if key not in response_data:
                    errors.append(f"Missing expected key '{key}' in response")
                elif response_data[key] != expected_value:
                    errors.append(f"Expected {key}='{expected_value}', got '{response_data[key]}'")
        elif str(expected_body) not in str(response_data):
            errors.append(f"Expected body content '{expected_body}' not found in response")
    
    # Check headers
    if "headers" in expectations:
        for header, expected_value in expectations["headers"].items():
            if header not in response.headers:
                errors.append(f"Missing expected header '{header}'")
            elif response.headers[header] != expected_value:
                errors.append(f"Expected header {header}='{expected_value}', got '{response.headers[header]}'")
    
    # Check response time
    if "max_response_time" in expectations:
        max_time = expectations["max_response_time"]
        if response.elapsed.total_seconds() > max_time:
            errors.append(f"Response time {response.elapsed.total_seconds():.2f}s exceeds limit {max_time}s")
    
    return errors


def run_single_test(method: str, url: str, base_url: str, 
                   expected_status: int = 200, body: Optional[str] = None,
                   headers: Optional[str] = None, extract: Optional[str] = None,
                   timeout: int = 30) -> Dict[str, Any]:
    """Execute a single HTTP request test
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL path (will be joined with base_url)
        base_url: Base URL for the request
        expected_status: Expected HTTP status code
        body: Request body (JSON string)
        headers: Request headers (JSON string)
        extract: Variables to extract from response (JSON string)
        timeout: Request timeout in seconds
        
    Returns:
        Dict with 'success' bool, 'issues' list, and optionally 'extracted' dict
    """
    result = {
        "success": True,
        "issues": [],
        "response": None
    }
    
    try:
        # Parse headers if provided
        request_headers = {}
        if headers:
            try:
                request_headers = json.loads(headers)
            except json.JSONDecodeError as e:
                result["issues"].append({
                    "type": "flow",
                    "location": "cli",
                    "message": f"Invalid headers JSON: {str(e)}",
                    "step": "setup"
                })
                result["success"] = False
                _log_result(result)
                return result
        
        # Parse body if provided
        request_data = None
        request_json = None
        if body:
            try:
                request_json = json.loads(body)
            except json.JSONDecodeError:
                request_data = body
        
        # Build full URL
        full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}" if not url.startswith("http") else url
        
        # Make the request
        response = requests.request(
            method=method,
            url=full_url,
            headers=request_headers,
            json=request_json,
            data=request_data if request_data else None,
            timeout=timeout
        )
        
        # Store response for potential extraction
        result["response"] = response
        
        # Validate status code
        if response.status_code != expected_status:
            result["issues"].append({
                "type": "flow",
                "location": "cli",
                "message": f"Expected status {expected_status}, got {response.status_code}",
                "step": f"{method} {url}",
                "response_status": response.status_code,
                "response_body": response.text[:500] + "..." if len(response.text) > 500 else response.text
            })
            result["success"] = False
        
        # Extract variables if requested
        if extract and result["success"]:
            try:
                extract_config = json.loads(extract)
                result["extracted"] = _extract_response_data(response, extract_config)
            except json.JSONDecodeError as e:
                result["issues"].append({
                    "type": "flow",
                    "location": "cli",
                    "message": f"Invalid extract JSON: {str(e)}",
                    "step": f"{method} {url}"
                })
                result["success"] = False
        
    except requests.exceptions.RequestException as e:
        result["issues"].append({
            "type": "flow",
            "location": "cli",
            "message": f"Request failed: {str(e)}",
            "step": f"{method} {url}"
        })
        result["success"] = False
    
    except Exception as e:
        result["issues"].append({
            "type": "flow",
            "location": "cli",
            "message": f"Unexpected error: {str(e)}",
            "step": f"{method} {url}"
        })
        result["success"] = False
    
    # Log the result (remove response object for serialization)
    log_result = {k: v for k, v in result.items() if k != 'response'}
    _log_result(log_result)
    
    return result


def run_flow(collection: str, base_url: str) -> Dict[str, Any]:
    """Execute integration flow test collection
    
    Args:
        collection: Path to YAML/JSON collection file
        base_url: Base URL for API requests
        
    Returns:
        Dict with 'success' bool and 'issues' list
    """
    result = {
        "success": True,
        "issues": []
    }
    
    try:
        # Load the test collection
        collection_data = _load_collection(collection)
        
        # Extract test configuration
        name = collection_data.get("name", "Unnamed Flow")
        description = collection_data.get("description", "")
        steps = collection_data.get("steps", [])
        
        if not steps:
            result["issues"].append({
                "type": "flow",
                "location": collection,
                "message": "No test steps found in collection",
                "step": "setup"
            })
            result["success"] = False
            _log_result(result)
            return result
        
        # Initialize variables for substitution
        variables = collection_data.get("variables", {})
        variables["base_url"] = base_url
        
        # Execute each step
        session = requests.Session()
        
        for step_idx, step in enumerate(steps):
            step_name = step.get("name", f"Step {step_idx + 1}")
            
            try:
                # Substitute variables in step configuration
                method = _substitute_variables(step.get("method", "GET"), variables)
                url = _substitute_variables(step.get("url", ""), variables)
                headers = step.get("headers", {})
                body = step.get("body")
                
                # Make the request
                full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}" if not url.startswith("http") else url
                
                request_kwargs = {
                    "method": method,
                    "url": full_url,
                    "headers": headers,
                    "timeout": step.get("timeout", 30)
                }
                
                if body:
                    if isinstance(body, (dict, list)):
                        request_kwargs["json"] = body
                    else:
                        request_kwargs["data"] = _substitute_variables(str(body), variables)
                
                response = session.request(**request_kwargs)
                
                # Validate response
                expectations = step.get("expect", {})
                validation_errors = _validate_response(response, expectations)
                
                if validation_errors:
                    # Record validation failures
                    for error in validation_errors:
                        result["issues"].append({
                            "type": "flow",
                            "location": f"{collection}:{step_idx + 1}",
                            "message": error,
                            "step": step_name,
                            "response_status": response.status_code,
                            "response_body": response.text[:500] + "..." if len(response.text) > 500 else response.text
                        })
                    
                    result["success"] = False
                    # Stop on first failure
                    break
                
                # Extract variables from response for next steps
                if "extract" in step:
                    extracted_vars = _extract_response_data(response, step["extract"])
                    variables.update(extracted_vars)
                
            except requests.exceptions.RequestException as e:
                result["issues"].append({
                    "type": "flow",
                    "location": f"{collection}:{step_idx + 1}",
                    "message": f"Request failed: {str(e)}",
                    "step": step_name
                })
                result["success"] = False
                break
            
            except Exception as e:
                result["issues"].append({
                    "type": "flow",
                    "location": f"{collection}:{step_idx + 1}",
                    "message": f"Step execution failed: {str(e)}",
                    "step": step_name
                })
                result["success"] = False
                break
        
        # Add summary if successful
        if result["success"]:
            result["summary"] = f"Successfully executed {len(steps)} steps in flow '{name}'"
        
    except FileNotFoundError as e:
        result["issues"].append({
            "type": "flow",
            "location": collection,
            "message": f"Collection file not found: {str(e)}",
            "step": "setup"
        })
        result["success"] = False
    
    except yaml.YAMLError as e:
        result["issues"].append({
            "type": "flow", 
            "location": collection,
            "message": f"YAML parsing error: {str(e)}",
            "step": "setup"
        })
        result["success"] = False
    
    except json.JSONDecodeError as e:
        result["issues"].append({
            "type": "flow",
            "location": collection,
            "message": f"JSON parsing error: {str(e)}",
            "step": "setup"
        })
        result["success"] = False
    
    except Exception as e:
        result["issues"].append({
            "type": "flow",
            "location": collection,
            "message": f"Unexpected error: {str(e)}",
            "step": "setup"
        })
        result["success"] = False
    
    # Log the result
    _log_result(result)
    
    return result


def main():
    """CLI interface for integration testing"""
    parser = argparse.ArgumentParser(
        description="Integration Testing Tool - Execute API tests via YAML/JSON files or direct CLI arguments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # File-based testing (traditional mode)
  python -m qa_tools.int_tests flow.yaml http://localhost:8000
  python -m qa_tools.int_tests --file flow.yaml --base-url http://localhost:8000
  
  # Direct testing (new mode)
  python -m qa_tools.int_tests --method GET --url /api/health --status 200 --base-url http://localhost:8000
  python -m qa_tools.int_tests --method POST --url /api/users --body '{"name":"test"}' --status 201 --base-url http://localhost:8000
  
  # With headers and extraction
  python -m qa_tools.int_tests --method GET --url /api/user/123 --headers '{"Authorization":"Bearer token"}' --extract '{"user_id":"id"}' --base-url http://localhost:8000
        """
    )
    
    # Support both positional arguments (legacy) and named arguments
    parser.add_argument('collection', nargs='?', help='Path to YAML/JSON collection file (legacy mode)')
    parser.add_argument('base_url_pos', nargs='?', help='Base URL for API requests (legacy mode)')
    
    # Named arguments for both modes
    parser.add_argument('--file', '-f', help='Path to YAML/JSON collection file')
    parser.add_argument('--base-url', '-b', help='Base URL for API requests')
    
    # Direct mode arguments
    parser.add_argument('--method', '-m', help='HTTP method (GET, POST, PUT, DELETE, etc.)')
    parser.add_argument('--url', '-u', help='URL path or full URL')
    parser.add_argument('--status', '-s', type=int, default=200, help='Expected HTTP status code (default: 200)')
    parser.add_argument('--body', help='Request body (JSON string or plain text)')
    parser.add_argument('--headers', help='Request headers as JSON string')
    parser.add_argument('--extract', help='Variables to extract from response as JSON string')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    
    # Output options
    parser.add_argument('--json-output', action='store_true', help='Output results as JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Determine base URL
    base_url = args.base_url or args.base_url_pos
    if not base_url:
        parser.error("Base URL is required. Use --base-url or provide it as second positional argument")
    
    # Determine mode: file-based or direct
    collection_file = args.file or args.collection
    
    if collection_file:
        # File-based mode
        result = run_flow(collection_file, base_url)
    elif args.method and args.url:
        # Direct mode
        result = run_single_test(
            method=args.method,
            url=args.url,
            base_url=base_url,
            expected_status=args.status,
            body=args.body,
            headers=args.headers,
            extract=args.extract,
            timeout=args.timeout
        )
    else:
        parser.error("Either provide a collection file or use --method and --url for direct testing")
    
    # Output results
    if args.json_output:
        # Remove response object for JSON serialization
        if 'response' in result:
            del result['response']
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result['success']:
            print("✅ Integration test passed!")
            if 'summary' in result:
                print(f"   {result['summary']}")
            if 'extracted' in result and args.verbose:
                print("\n📤 Extracted variables:")
                for key, value in result['extracted'].items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Integration test failed!")
            print(f"\n🔍 Found {len(result['issues'])} issue(s):")
            for issue in result['issues']:
                print(f"\n   📍 Location: {issue['location']}")
                print(f"   📝 Step: {issue['step']}")
                print(f"   ⚠️  Message: {issue['message']}")
                if 'response_status' in issue:
                    print(f"   🔢 Response status: {issue['response_status']}")
                if 'response_body' in issue and args.verbose:
                    print(f"   📄 Response body: {issue['response_body']}")
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()