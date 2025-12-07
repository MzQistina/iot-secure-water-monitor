# Security Testing Guide

This guide explains how to test the SQL injection and XSS protections implemented in the application.

## Prerequisites

1. The Flask application should be running
2. A test user account should be created
3. Browser developer tools should be available (F12)

## 1. SQL Injection Testing

### Test 1: Login Form SQL Injection Attempts

**Test Case 1.1: Basic SQL Injection in Username**
```
Username: admin' OR '1'='1
Password: anything
```
**Expected Result:** Login should fail with "Invalid credentials" - the SQL injection pattern should be blocked.

**Test Case 1.2: UNION SELECT Attack**
```
Username: admin' UNION SELECT * FROM user_cred--
Password: anything
```
**Expected Result:** Login should fail - the UNION SELECT pattern should be sanitized.

**Test Case 1.3: Comment-based Injection**
```
Username: admin'--
Password: anything
```
**Expected Result:** Login should fail - SQL comments should be removed.

### Test 2: Registration Form SQL Injection

**Test Case 2.1: Email Field**
```
Email: test@test.com' OR '1'='1
Name: Test User
Username: testuser
Password: Test1234
```
**Expected Result:** Registration should fail with validation error - SQL patterns should be sanitized.

**Test Case 2.2: Username Field**
```
Email: test@test.com
Name: Test User
Username: test'; DROP TABLE user_cred;--
Password: Test1234
```
**Expected Result:** Registration should fail - DROP command should be sanitized.

### Test 3: Device ID SQL Injection

**Test Case 3.1: Sensor Registration**
```
Device ID: sensor1' OR '1'='1
Device Type: ph
Location: Test Location
```
**Expected Result:** Registration should fail - SQL injection pattern should be blocked.

**Test Case 3.2: API Endpoint**
```bash
curl -X GET "http://localhost:5000/api/device/session/request?device_id=sensor1' OR '1'='1"
```
**Expected Result:** Should return 400 error - invalid device_id format.

## 2. XSS (Cross-Site Scripting) Testing

### Test 1: Reflected XSS in Forms

**Test Case 1.1: Registration Form - Name Field**
```
Name: <script>alert('XSS')</script>
Email: test@test.com
Username: testuser
Password: Test1234
```
**Expected Result:** 
- Form submission should fail validation
- If error message is displayed, it should show escaped HTML (not execute script)
- Check browser console - no alert should appear

**Test Case 1.2: Registration Form - Email Field**
```
Email: <img src=x onerror=alert('XSS')>@test.com
Name: Test User
Username: testuser
Password: Test1234
```
**Expected Result:** Email validation should fail - XSS patterns should be sanitized.

**Test Case 1.3: Username Field**
```
Username: <iframe src="javascript:alert('XSS')"></iframe>
Email: test@test.com
Name: Test User
Password: Test1234
```
**Expected Result:** Username validation should fail - iframe tags should be removed.

### Test 2: Stored XSS (if data is displayed)

**Test Case 2.1: Profile Update**
1. Login with valid credentials
2. Go to Profile page
3. Try to update name with: `<script>alert('XSS')</script>`
4. Submit form

**Expected Result:** 
- Validation should fail
- If somehow stored, when displayed it should be escaped (show as text, not execute)

**Test Case 2.2: Sensor Location**
1. Register a sensor with location: `Test<script>alert('XSS')</script>`
2. View sensor list

**Expected Result:** Location should be sanitized or validation should fail.

### Test 3: JavaScript Protocol XSS

**Test Case 3.1: Device ID**
```
Device ID: javascript:alert('XSS')
```
**Expected Result:** Validation should fail - javascript: protocol should be blocked.

**Test Case 3.2: Location Field**
```
Location: javascript:alert('XSS')
```
**Expected Result:** Validation should fail or be sanitized.

## 3. Input Validation Testing

### Test 1: Email Validation

**Test Cases:**
```
Valid: user@example.com
Invalid: notanemail
Invalid: user@
Invalid: @example.com
Invalid: user@example
Invalid: user name@example.com (with spaces)
```
**Expected Result:** Only valid email should pass validation.

### Test 2: Username Validation

**Test Cases:**
```
Valid: testuser123
Valid: test_user
Valid: test-user
Invalid: test user (spaces)
Invalid: test@user (special chars)
Invalid: ab (too short)
Invalid: <script> (XSS attempt)
```
**Expected Result:** Only valid usernames should pass.

### Test 3: Password Strength

**Test Cases:**
```
Invalid: short (too short)
Invalid: nopassword123 (no letters)
Invalid: NoPassword (no numbers)
Invalid: password123 (too common)
Valid: Test1234 (meets requirements)
```
**Expected Result:** Only strong passwords should pass.

### Test 4: Device ID Validation

**Test Cases:**
```
Valid: sensor01
Valid: sensor_01
Valid: sensor-01
Valid: sensor.01
Invalid: sensor 01 (spaces)
Invalid: sensor@01 (special chars)
Invalid: ab (too short)
Invalid: <script>sensor01</script> (XSS)
```
**Expected Result:** Only valid device IDs should pass.

## 4. Security Headers Testing

### Test 1: Check Security Headers

**Using Browser Developer Tools:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Load any page (e.g., login page)
4. Click on the request
5. Check Response Headers

**Expected Headers:**
```
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), ...
```

### Test 2: CSP Violation Testing

**Using Browser Console:**
1. Open browser DevTools Console
2. Try to inject external script:
```javascript
var script = document.createElement('script');
script.src = 'https://evil.com/script.js';
document.head.appendChild(script);
```
**Expected Result:** CSP should block the external script - check console for violation message.

## 5. Automated Testing Script

Run the automated test script:
```bash
python test_security.py
```

## 6. Manual Testing Checklist

- [ ] SQL injection attempts in login form fail
- [ ] SQL injection attempts in registration form fail
- [ ] SQL injection attempts in API endpoints fail
- [ ] XSS attempts in text fields are sanitized
- [ ] XSS attempts in error messages are escaped
- [ ] Security headers are present in all responses
- [ ] CSP blocks external scripts
- [ ] Input validation rejects invalid formats
- [ ] Password strength requirements are enforced
- [ ] Email format validation works correctly

## 7. Testing Tools

### Browser Extensions:
- **XSS Hunter** - For XSS testing
- **SQLMap** - For SQL injection testing (use carefully on test environment only)

### Online Tools:
- **OWASP ZAP** - Security testing tool
- **Burp Suite** - Web security testing (Community Edition available)

## 8. Expected Behavior Summary

✅ **Should Block:**
- SQL injection patterns (`' OR '1'='1`, `UNION SELECT`, `DROP TABLE`, etc.)
- XSS patterns (`<script>`, `javascript:`, `onerror=`, etc.)
- Invalid input formats (invalid email, weak passwords, etc.)
- External resource loading (via CSP)

✅ **Should Allow:**
- Valid user inputs
- Legitimate database queries (via parameterized queries)
- Same-origin scripts and styles
- Properly formatted data

## 9. Reporting Issues

If you find a security vulnerability:
1. **DO NOT** exploit it in production
2. Document the issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots/logs
3. Report to the development team immediately

## Notes

- All tests should be performed in a **test/development environment only**
- Never test security vulnerabilities on production systems
- Some tests may require valid authentication - use test accounts
- Security headers can be verified using browser DevTools or tools like `curl`











