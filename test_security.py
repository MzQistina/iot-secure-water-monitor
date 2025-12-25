#!/usr/bin/env python3
"""
Security Testing Script for SQL Injection and XSS Protection

This script tests the security protections implemented in the application.
Run this script while the Flask application is running.

Usage:
    python test_security.py
"""

import requests
import json
import sys
from urllib.parse import quote

# Configuration
BASE_URL = "http://localhost:5000"
TEST_EMAIL = "security_test@example.com"
TEST_USERNAME = "security_test_user"
TEST_PASSWORD = "Test1234"
TEST_DEVICE_ID = "security_test_device"

# Test results
passed_tests = 0
failed_tests = 0
test_results = []

def print_test(name, passed, message=""):
    """Print test result."""
    global passed_tests, failed_tests
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")
    if passed:
        passed_tests += 1
    else:
        failed_tests += 1
    test_results.append({"name": name, "passed": passed, "message": message})

def test_sql_injection_login():
    """Test SQL injection protection in login form."""
    print("\n=== Testing SQL Injection Protection (Login) ===")
    
    # Test 1: Basic SQL injection
    test_cases = [
        ("admin' OR '1'='1", "Basic SQL injection"),
        ("admin' UNION SELECT * FROM user_cred--", "UNION SELECT injection"),
        ("admin'--", "Comment-based injection"),
        ("admin'; DROP TABLE user_cred;--", "DROP TABLE injection"),
    ]
    
    for username, test_name in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/login",
                data={
                    "username": username,
                    "password": "anything"
                },
                allow_redirects=False,
                timeout=5
            )
            # Should either fail validation or return error (not 200 OK)
            passed = response.status_code != 200 or "error" in response.text.lower()
            print_test(f"SQL Injection - {test_name}", passed, 
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"SQL Injection - {test_name}", False, f"Error: {str(e)}")

def test_sql_injection_registration():
    """Test SQL injection protection in registration form."""
    print("\n=== Testing SQL Injection Protection (Registration) ===")
    
    test_cases = [
        ("test@test.com' OR '1'='1", "Email SQL injection"),
        ("test'; DROP TABLE user_cred;--", "Username SQL injection"),
    ]
    
    for value, test_name in test_cases:
        try:
            if "'" in value and "@" in value:
                # Email field
                data = {
                    "email": value,
                    "name": "Test User",
                    "username": f"testuser_{hash(value) % 10000}",
                    "password": TEST_PASSWORD,
                    "confirm": TEST_PASSWORD
                }
            else:
                # Username field
                data = {
                    "email": f"test{hash(value) % 10000}@test.com",
                    "name": "Test User",
                    "username": value,
                    "password": TEST_PASSWORD,
                    "confirm": TEST_PASSWORD
                }
            
            response = requests.post(
                f"{BASE_URL}/register",
                data=data,
                allow_redirects=False,
                timeout=5
            )
            # Should fail validation (400) or show error
            passed = response.status_code == 400 or "error" in response.text.lower()
            print_test(f"SQL Injection - {test_name}", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"SQL Injection - {test_name}", False, f"Error: {str(e)}")

def test_xss_protection():
    """Test XSS protection in forms."""
    print("\n=== Testing XSS Protection ===")
    
    xss_payloads = [
        ("<script>alert('XSS')</script>", "Script tag"),
        ("<img src=x onerror=alert('XSS')>", "Image onerror"),
        ("<iframe src='javascript:alert(1)'></iframe>", "Iframe javascript"),
        ("javascript:alert('XSS')", "JavaScript protocol"),
        ("<svg onload=alert('XSS')>", "SVG onload"),
    ]
    
    for payload, test_name in xss_payloads:
        try:
            # Test in registration form (name field)
            data = {
                "email": f"test{hash(payload) % 10000}@test.com",
                "name": payload,
                "username": f"testuser_{hash(payload) % 10000}",
                "password": TEST_PASSWORD,
                "confirm": TEST_PASSWORD
            }
            
            response = requests.post(
                f"{BASE_URL}/register",
                data=data,
                allow_redirects=False,
                timeout=5
            )
            
            # Should fail validation or sanitize payload
            passed = response.status_code == 400 or payload.lower() not in response.text.lower()
            print_test(f"XSS Protection - {test_name}", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"XSS Protection - {test_name}", False, f"Error: {str(e)}")

def test_security_headers():
    """Test security headers are present."""
    print("\n=== Testing Security Headers ===")
    
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=5)
        headers = response.headers
        
        required_headers = {
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": None,  # Just check it exists
            "Referrer-Policy": None,
        }
        
        for header, expected_value in required_headers.items():
            if header in headers:
                if expected_value:
                    passed = headers[header] == expected_value
                else:
                    passed = True  # Just check it exists
                print_test(f"Security Header - {header}", passed,
                          f"Value: {headers.get(header, 'NOT FOUND')}")
            else:
                print_test(f"Security Header - {header}", False, "Header not found")
    except Exception as e:
        print_test("Security Headers", False, f"Error: {str(e)}")

def test_input_validation():
    """Test input validation."""
    print("\n=== Testing Input Validation ===")
    
    # Test invalid email formats
    invalid_emails = [
        "notanemail",
        "user@",
        "@example.com",
        "user@example",
        "user name@example.com",
    ]
    
    for email in invalid_emails:
        try:
            data = {
                "email": email,
                "name": "Test User",
                "username": f"testuser_{hash(email) % 10000}",
                "password": TEST_PASSWORD,
                "confirm": TEST_PASSWORD
            }
            response = requests.post(
                f"{BASE_URL}/register",
                data=data,
                allow_redirects=False,
                timeout=5
            )
            # Should fail validation
            passed = response.status_code == 400 or "error" in response.text.lower()
            print_test(f"Email Validation - {email}", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Email Validation - {email}", False, f"Error: {str(e)}")
    
    # Test invalid usernames
    invalid_usernames = [
        "ab",  # Too short
        "test user",  # Spaces
        "test@user",  # Special chars
    ]
    
    for username in invalid_usernames:
        try:
            data = {
                "email": f"test{hash(username) % 10000}@test.com",
                "name": "Test User",
                "username": username,
                "password": TEST_PASSWORD,
                "confirm": TEST_PASSWORD
            }
            response = requests.post(
                f"{BASE_URL}/register",
                data=data,
                allow_redirects=False,
                timeout=5
            )
            passed = response.status_code == 400 or "error" in response.text.lower()
            print_test(f"Username Validation - {username}", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Username Validation - {username}", False, f"Error: {str(e)}")
    
    # Test weak passwords
    weak_passwords = [
        "short",  # Too short
        "nopassword123",  # No letters
        "NoPassword",  # No numbers
        "password123",  # Too common
    ]
    
    for password in weak_passwords:
        try:
            data = {
                "email": f"test{hash(password) % 10000}@test.com",
                "name": "Test User",
                "username": f"testuser_{hash(password) % 10000}",
                "password": password,
                "confirm": password
            }
            response = requests.post(
                f"{BASE_URL}/register",
                data=data,
                allow_redirects=False,
                timeout=5
            )
            passed = response.status_code == 400 or "error" in response.text.lower()
            print_test(f"Password Validation - {password[:10]}...", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Password Validation - {password[:10]}...", False, f"Error: {str(e)}")

def test_api_endpoints():
    """Test API endpoint security."""
    print("\n=== Testing API Endpoint Security ===")
    
    # Test device_id validation in API
    malicious_device_ids = [
        "sensor1' OR '1'='1",
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
    ]
    
    for device_id in malicious_device_ids:
        try:
            response = requests.get(
                f"{BASE_URL}/api/device/session/request",
                params={"device_id": device_id},
                timeout=5
            )
            # Should return 400 (bad request) for invalid format
            passed = response.status_code == 400
            print_test(f"API Device ID Validation - {device_id[:20]}...", passed,
                      f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"API Device ID Validation - {device_id[:20]}...", False, f"Error: {str(e)}")

def main():
    """Run all security tests."""
    print("=" * 70)
    print("Security Testing Suite")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print("\nNote: Some tests may fail if the server is not running or")
    print("if test data already exists. This is expected behavior.")
    print("=" * 70)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("\n⚠️  Warning: Server may not be running properly")
    except Exception as e:
        print(f"\n❌ Error: Cannot connect to server at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print("\nPlease ensure the Flask application is running before running tests.")
        sys.exit(1)
    
    # Run tests
    test_sql_injection_login()
    test_sql_injection_registration()
    test_xss_protection()
    test_security_headers()
    test_input_validation()
    test_api_endpoints()
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total Tests: {passed_tests + failed_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print("=" * 70)
    
    if failed_tests > 0:
        print("\n⚠️  Some tests failed. Review the results above.")
        print("   Note: Some failures may be expected if:")
        print("   - Test data already exists")
        print("   - Server configuration differs")
        print("   - Additional validation is needed")
    else:
        print("\n✅ All tests passed!")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())







































