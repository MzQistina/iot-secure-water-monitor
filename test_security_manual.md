# Manual Security Testing Guide

Quick reference for manual security testing.

**Important Notes:**
- The backticks (`` ` ``) around code examples are markdown formatting - **don't type them**
- Single quotes (`'`) in SQL injection tests **ARE part of the payload** - type them exactly
- Angle brackets (`< >`) in XSS tests **ARE part of the payload** - type them exactly
- Example: For `test@test.com' OR '1'='1`, type: `test@test.com' OR '1'='1` (without the outer backticks)

## Quick Test Checklist

### 1. SQL Injection Tests (5 minutes)

**Login Page:**
1. Go to `/login`
2. Try username: `admin' OR '1'='1`
3. Try username: `admin' UNION SELECT * FROM user_cred--`
4. ✅ Expected: Login fails, no SQL error messages

**Registration Page:**
1. Go to `/register`
2. Try email: `test@test.com' OR '1'='1` (include the single quotes - they're part of the SQL injection attack)
3. Try username: `test'; DROP TABLE user_cred;--` (include the single quotes and semicolon)
4. ✅ Expected: Validation errors, registration fails

### 2. XSS Tests (5 minutes)

**Registration Form:**
1. Go to `/register`
2. Try name: `<script>alert('XSS')</script>`
3. Try email: `<img src=x onerror=alert('XSS')>@test.com`
4. ✅ Expected: Validation fails, no alert popup

**Profile Page (if logged in):**
1. Go to `/profile`
2. Try updating name to: `<script>alert('XSS')</script>`
3. ✅ Expected: Validation fails or text is escaped when displayed

### 3. Security Headers Test (2 minutes)

**Using Browser:**
1. Open DevTools (F12)
2. Go to Network tab
3. Load any page
4. Click on request → Headers tab
5. Check Response Headers for:
   - `X-XSS-Protection`
   - `X-Content-Type-Options`
   - `Content-Security-Policy`
   - `X-Frame-Options`
6. ✅ Expected: All headers present

**Using curl:**
```bash
curl -I http://localhost:5000/login
```
✅ Expected: Security headers in response

### 4. Input Validation Tests (5 minutes)

**Email Validation:**
- ❌ `notanemail` → Should fail
- ❌ `user@` → Should fail
- ✅ `user@example.com` → Should pass

**Username Validation:**
- ❌ `ab` (too short) → Should fail
- ❌ `test user` (spaces) → Should fail
- ✅ `testuser123` → Should pass

**Password Validation:**
- ❌ `short` (too short) → Should fail
- ❌ `nopassword123` (no letters) → Should fail
- ✅ `Test1234` → Should pass

## Browser Console Test

Open browser console (F12 → Console) and try:

```javascript
// Test CSP - should be blocked
var script = document.createElement('script');
script.src = 'https://evil.com/script.js';
document.head.appendChild(script);
// ✅ Expected: CSP violation error in console
```

## Expected Results Summary

| Test Type | Attack | Expected Result |
|-----------|--------|------------------|
| SQL Injection | `' OR '1'='1` | ❌ Blocked/Validation Error |
| SQL Injection | `UNION SELECT` | ❌ Blocked/Validation Error |
| XSS | `<script>alert()</script>` | ❌ Sanitized/Validation Error |
| XSS | `javascript:alert()` | ❌ Blocked/Validation Error |
| XSS | `<img onerror=alert()>` | ❌ Sanitized/Validation Error |
| Invalid Input | Bad email format | ❌ Validation Error |
| Invalid Input | Weak password | ❌ Validation Error |
| Security Headers | Check headers | ✅ All headers present |

## Notes

- All tests should be done in **development/test environment**
- Some tests require the server to be running
- Failed tests don't always mean vulnerability - check error messages
- Security headers can be verified with browser DevTools or `curl -I`

