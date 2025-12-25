# Security Testing Test Cases

## Overview

This document lists all security test cases for the IoT MQTT Water Monitoring System. Each test case includes objectives, procedures, expected results, and execution methods.

---

## Test Case Categories

1. [Encryption & TLS Tests](#1-encryption--tls-tests)
2. [End-to-End Encryption (E2EE) Tests](#2-end-to-end-encryption-e2ee-tests)
3. [Message Integrity Tests](#3-message-integrity-tests)
4. [Authentication Tests](#4-authentication-tests)
5. [Authorization Tests](#5-authorization-tests)
6. [Attack Simulation Tests](#6-attack-simulation-tests)
7. [Traffic Analysis Tests](#7-traffic-analysis-tests)
8. [System Resilience Tests](#8-system-resilience-tests)

---

## 1. Encryption & TLS Tests

### TC-001: TLS Requirement Enforcement

**Objective**: Verify that unencrypted MQTT connections are blocked or disabled.

**Priority**: CRITICAL

**Test Procedure**:
1. Start Wireshark capture on port 1883 (unencrypted)
2. Attempt to connect to MQTT broker on port 1883 without TLS
3. Analyze captured traffic

**Expected Result**: 
- Connection should fail or be rejected
- No unencrypted MQTT traffic should be allowed
- Broker should only accept connections on port 8883 (TLS)

**How to Run**:
```bash
# Automated test
python security_test_attacks.py tls

# Manual test with Wireshark
# Filter: tcp.port == 1883
# Try: python test_provision_mqtt.py (with TLS disabled)
```

**Pass Criteria**: Connection fails, no unencrypted traffic observed

---

### TC-002: TLS Configuration and Validation

**Objective**: Verify that TLS is properly configured with certificate validation and secure versions.

**Priority**: HIGH

**Test Procedure**:

**Part A: Certificate Validation**
1. Attempt connection with invalid/self-signed certificate
2. Attempt connection with wrong hostname certificate
3. Attempt connection with expired certificate
4. Monitor certificate validation behavior

**Part B: TLS Version Check**
1. Capture TLS handshake packets in Wireshark
2. Analyze TLS version in Client Hello and Server Hello
3. Check for weak TLS versions (1.0, 1.1)
4. Verify strong cipher suites are negotiated

**Expected Result**:
- Invalid certificates should be rejected
- Certificate hostname validation should work
- Expired certificates should be rejected
- Only valid certificates should be accepted
- TLS 1.2 or 1.3 should be used
- TLS 1.0 and 1.1 should be rejected
- Strong cipher suites should be negotiated

**How to Run**:
```bash
# Automated test
python security_test_attacks.py cert

# Wireshark analysis for TLS version
# Filter: tls.handshake.type == 1 (Client Hello)
# Filter: tls.handshake.type == 2 (Server Hello)
# Check: tls.handshake.version field
```

**Pass Criteria**: All invalid certificate attempts fail, valid certificate succeeds, TLS 1.2 or higher used, weak versions rejected

---

### TC-004: Encrypted Payload Verification

**Objective**: Verify that MQTT message payloads are encrypted and not readable.

**Priority**: CRITICAL

**Test Procedure**:
1. Capture MQTT traffic on port 8883
2. Attempt to read message payloads in Wireshark
3. Verify payloads appear as encrypted data

**Expected Result**:
- Payloads should be encrypted (not readable)
- Only encrypted binary data visible
- No plaintext device IDs, sensor data, or credentials visible

**How to Run**:
```bash
# Wireshark capture
# 1. Start capture on port 8883
# 2. Run: python test_provision_mqtt.py sal01 update 1
# 3. Filter: mqtt.msgtype == 3 (PUBLISH)
# 4. Check payload - should be encrypted
```

**Pass Criteria**: All payloads encrypted, no plaintext data visible

---

## 2. End-to-End Encryption (E2EE) Tests

### TC-022: Application-Layer Encryption Verification

**Objective**: Verify that application-layer encryption (E2EE) is implemented beyond TLS transport encryption.

**Priority**: CRITICAL

**Test Procedure**:
1. Capture MQTT traffic with TLS decryption (if possible)
2. Analyze decrypted payload structure
3. Verify payload contains encrypted data fields (ciphertext, session_key, nonce, tag)
4. Confirm payload is not readable even if TLS is bypassed

**Expected Result**:
- Payload should contain encrypted fields (ciphertext, session_key, nonce, tag)
- Even with TLS decrypted, application data should remain encrypted
- Only intended recipient with private key can decrypt

**How to Run**:
```bash
# Wireshark analysis
# 1. Capture MQTT traffic
# 2. If TLS keys available, decrypt TLS layer
# 3. Analyze MQTT payload structure
# 4. Verify payload contains encrypted fields
# Check for: session_key, nonce, ciphertext, tag fields
```

**Pass Criteria**: Application-layer encryption present, payload unreadable even after TLS decryption

---

### TC-023: E2EE Implementation Verification

**Objective**: Verify that E2EE implementation uses strong RSA key exchange and AES encryption.

**Priority**: HIGH

**Test Procedure**:

**Part A: RSA Key Exchange Verification**
1. Analyze encrypted payload structure
2. Verify session_key is encrypted with RSA
3. Check that different messages use different session keys
4. Verify key exchange mechanism

**Part B: AES Encryption Strength**
1. Analyze encryption implementation in code
2. Verify AES mode (should be EAX or CBC with proper IV)
3. Check key size (should be 128-bit or higher)
4. Verify nonce/IV usage and uniqueness

**Expected Result**:
- Session keys should be RSA-encrypted
- Each message should use unique session key
- Key exchange should be secure
- AES-128 or higher should be used
- Proper encryption mode (EAX, CBC with IV)
- Nonce/IV should be unique per message
- No weak encryption algorithms

**How to Run**:
```bash
# Analyze captured messages
# Check payload structure for encrypted session_key
# Verify session keys are different for each message

# Code review of encryption_utils.py
# Verify AES.new() parameters
# Check key size and mode
```

**Pass Criteria**: RSA encryption used for key exchange, unique session keys per message, strong AES encryption with proper mode and key size

---

### TC-027: Sensor Data E2EE Verification

**Objective**: Verify that sensor data messages use E2EE encryption.

**Priority**: CRITICAL

**Test Procedure**:
1. Subscribe to sensor data topic (`secure/sensor`)
2. Run sensor simulator to publish sensor data
3. Analyze received payload structure
4. Verify payload contains E2EE fields (session_key, ciphertext, nonce, tag)
5. Confirm sensor readings are encrypted and unreadable

**Expected Result**:
- Payload should contain encrypted fields (session_key, ciphertext, nonce, tag)
- Sensor readings (pH, temperature, etc.) should be encrypted
- Data should be unreadable even if TLS is decrypted
- Hash field may be present for integrity (SHA-256)

**How to Run**:
```bash
# Use subscriber script to receive sensor data
# Run sensor simulator: python simulators/sensor/sensor_simulator.py --device-id sal01
# Verify E2EE fields are present in payload
```

**Pass Criteria**: 
- E2EE present for sensor data messages
- All required encryption fields found
- Sensor readings unreadable
- Hash present and correct (if implemented)

**Important Notes**:
- ⚠️ **Cannot assume** sensor data is secure from provision message tests
- ✅ **Must test separately** - sensor data uses different code path
- ✅ Sensor data typically includes hash for integrity (in addition to E2EE)
- ✅ Same E2EE mechanism as provision messages, but different implementation

---

## 3. Message Integrity Tests

### TC-025: SHA-256 Hash Verification

**Objective**: Verify that SHA-256 hashes are used for message integrity checking.

**Priority**: CRITICAL

**Test Procedure**:
1. Capture MQTT message with hash
2. Extract hash from payload
3. Compute SHA-256 hash of decrypted data
4. Compare computed hash with received hash
5. Test with modified message (hash should fail)

**Expected Result**:
- Messages should include SHA-256 hash
- Hash verification should detect tampering
- Modified messages should be rejected
- Hash mismatch should trigger error

**How to Run**:
```bash
# Manual test
# 1. Capture message with hash
# 2. Modify message payload
# 3. Verify hash mismatch is detected
# 4. Check server logs for hash verification errors
```

**Pass Criteria**: SHA-256 hash present, tampering detected, modified messages rejected

---

### TC-026: Message Tampering Detection

**Objective**: Verify that message tampering is detected and rejected.

**Priority**: CRITICAL

**Test Procedure**:
1. Capture a valid MQTT message
2. Modify the encrypted payload
3. Modify the hash value
4. Replay modified message
5. Verify system rejects tampered message

**Expected Result**:
- Tampered messages should be rejected
- Hash verification should fail
- System should log tampering attempts
- No processing of tampered data

**How to Run**:
```bash
# Manual test
# 1. Capture valid message
# 2. Modify ciphertext or hash
# 3. Replay message
# 4. Verify rejection
```

**Pass Criteria**: Tampered messages rejected, hash verification works

---

## 4. Authentication Tests

### TC-005: Authentication Requirement

**Objective**: Verify that authentication is required for MQTT connections.

**Priority**: CRITICAL

**Test Procedure**:
1. Attempt to connect without username/password
2. Monitor connection attempt
3. Check broker logs for authentication failures

**Expected Result**:
- Connection should fail without credentials
- Broker should reject unauthenticated connections
- Error message should indicate authentication required

**How to Run**:
```bash
# Automated test
python security_test_attacks.py auth

# Manual test - modify client to not send credentials
```

**Pass Criteria**: Connection fails without credentials

---

### TC-006: Wrong Credentials Rejection

**Objective**: Verify that incorrect credentials are properly rejected.

**Priority**: HIGH

**Test Procedure**:
1. Attempt connection with wrong username
2. Attempt connection with wrong password
3. Attempt connection with both wrong
4. Monitor failed authentication attempts

**Expected Result**:
- All wrong credential attempts should fail
- Broker should reject invalid credentials
- Failed attempts should be logged
- Rate limiting may be applied after multiple failures

**How to Run**:
```bash
# Automated test
python security_test_attacks.py credentials

# Manual test
# Try: python test_provision_mqtt.py (with wrong credentials)
```

**Pass Criteria**: Wrong credentials rejected, correct credentials accepted

---

### TC-007: Credential Sniffing Protection

**Objective**: Verify that credentials are not visible in network traffic.

**Priority**: CRITICAL

**Test Procedure**:
1. Capture MQTT CONNECT packets in Wireshark
2. Analyze CONNECT packet structure
3. Check if username/password are visible
4. Verify credentials are protected by TLS

**Expected Result**:
- Username may be visible (acceptable if TLS protects it)
- Password should not be visible in plaintext
- All credential data should be encrypted by TLS

**How to Run**:
```bash
# Wireshark analysis
# Filter: mqtt.msgtype == 1 (CONNECT)
# Check: mqtt.username and mqtt.password fields
# Should be encrypted if TLS is working
```

**Pass Criteria**: Credentials encrypted, not readable in plaintext

---

### TC-008: Brute Force Protection

**Objective**: Verify protection against brute force authentication attacks.

**Priority**: MEDIUM

**Test Procedure**:
1. Attempt multiple failed logins rapidly
2. Monitor broker response
3. Check for rate limiting or account lockout
4. Verify legitimate access still works after failures

**Expected Result**:
- Rate limiting should activate after multiple failures
- Account may be temporarily locked
- Legitimate access should still work after cooldown
- Failed attempts should be logged

**How to Run**:
```bash
# Manual test - rapid failed login attempts
# Monitor: sudo journalctl -u mosquitto -f
# Check for rate limiting messages
```

**Pass Criteria**: Rate limiting or protection mechanism activates

---

## 5. Authorization Tests

### TC-009: ACL and Authorization Tests

**Objective**: Verify that Access Control Lists (ACL) properly restrict topic access, including device isolation and provision topic protection.

**Priority**: HIGH

**Test Procedure**:

**Part A: General ACL Verification**
1. Connect with valid credentials
2. Attempt to publish to unauthorized topic
3. Attempt to subscribe to unauthorized topic
4. Verify authorized topics still work

**Part B: Device-Specific Topic Isolation**
1. Connect as device A
2. Attempt to publish to device B's topic
3. Attempt to subscribe to device B's topic
4. Verify device A can only access its own topics

**Part C: Provision Topic Protection**
1. Attempt to publish to provision topics without authorization
2. Attempt to subscribe to provision topics
3. Verify only authorized users can access provision topics

**Expected Result**:
- Unauthorized publish attempts should be blocked
- Unauthorized subscribe attempts should be blocked
- Authorized topics should work normally
- ACL violations should be logged
- Devices should only access their assigned topics
- Cross-device topic access should be blocked
- Topic patterns like `sensor/{device_id}/+` should be enforced
- Unauthorized provision topic access should be blocked
- Only authorized users (e.g., web application) should access provision topics
- Provision commands should be logged

**How to Run**:
```bash
# Automated test
python security_test_attacks.py acl

# Manual test - try accessing topics not in ACL
# Connect as device "sal01", try to access "sal02" topics
python test_provision_mqtt.py sal01 update 1
# Then try to publish to provision/sal02/update
# Try publishing to provision topics with different user credentials
# Check ACL configuration
```

**Pass Criteria**: Unauthorized access blocked, authorized access works, device isolation enforced, cross-device access blocked, provision topics protected

---

## 6. Attack Simulation Tests

### TC-012: Eavesdropping Attack (Passive)

**Objective**: Test if unencrypted traffic can be intercepted and read.

**Priority**: CRITICAL

**Test Procedure**:
1. Start Wireshark capture
2. Run normal MQTT operations
3. Analyze captured packets
4. Attempt to read message contents

**Expected Result**:
- With TLS: All data encrypted, not readable
- Without TLS: Data visible (security vulnerability)
- Credentials and sensor data should be protected

**How to Run**:
```bash
# Wireshark capture
# 1. Start capture
# 2. Run: python test_provision_mqtt.py sal01 update 1
# 3. Analyze packets
# 4. Check if payloads are readable
```

**Pass Criteria**: All traffic encrypted, no readable data

---

### TC-013: Man-in-the-Middle (MITM) Attack

**Objective**: Test TLS protection against MITM attacks.

**Priority**: HIGH

**Test Procedure**:
1. Set up MITM tool (Bettercap/Ettercap)
2. Install fake CA certificate
3. Attempt to intercept and decrypt traffic
4. Verify certificate validation prevents MITM

**Expected Result**:
- Client should reject invalid certificates
- MITM should fail due to certificate validation
- TLS should prevent traffic interception

**How to Run**:
```bash
# Requires MITM tools setup
# Test certificate validation
python security_test_attacks.py cert
```

**Pass Criteria**: MITM prevented by certificate validation

---

### TC-014: Replay Attack with Timestamp/Nonce Validation

**Objective**: Test if old messages can be replayed successfully, verifying timestamp/nonce protection.

**Priority**: HIGH

**Test Procedure**:
1. Capture a valid MQTT message
2. Extract the message payload (note timestamp/nonce)
3. Replay the same message immediately
4. Replay the same message after delay
5. Replay message with modified timestamp
6. Check if system accepts replayed messages

**Expected Result**:
- System should detect or reject replayed messages
- Timestamp checks should prevent old message replay
- Nonce checks should prevent duplicate message processing
- Old provision commands should not be accepted
- Timestamp validation should work correctly

**How to Run**:
```bash
# Automated test
python security_test_attacks.py replay

# Manual test - capture and replay message
# Check for timestamp/nonce in payload
# Verify timestamp validation logic
```

**Pass Criteria**: Replay attacks detected/prevented, timestamp/nonce validation works

---

### TC-015: Topic Enumeration Attack

**Objective**: Test if MQTT topics can be discovered through traffic analysis.

**Priority**: MEDIUM

**Test Procedure**:
1. Capture MQTT traffic for extended period
2. Extract all PUBLISH and SUBSCRIBE messages
3. List all discovered topics
4. Analyze topic patterns

**Expected Result**:
- Topics may be discoverable through traffic analysis
- Sensitive topic names should be avoided
- Topic structure should not reveal sensitive information

**How to Run**:
```bash
# Wireshark analysis
# Filter: mqtt.msgtype == 3 or mqtt.msgtype == 8
# Export: Statistics → Protocol Hierarchy → MQTT
# Or use: python security_test_analyzer.py capture.pcap
```

**Pass Criteria**: Sensitive topics not exposed, topic naming secure

---

### TC-016: Unauthorized Access Attempt

**Objective**: Test authentication and authorization mechanisms.

**Priority**: HIGH

**Test Procedure**:
1. Attempt connection with invalid credentials
2. Attempt to access unauthorized topics
3. Monitor failed access attempts
4. Check logging and alerting

**Expected Result**:
- Failed attempts should be logged
- Unauthorized access should be blocked
- Rate limiting should activate
- Alerts should be generated

**How to Run**:
```bash
# Wireshark filter
# Filter: mqtt.msgtype == 1 and mqtt.conack.flags == 5
# Check broker logs: sudo journalctl -u mosquitto
```

**Pass Criteria**: Failed attempts logged, unauthorized access blocked

---

## 7. Traffic Analysis Tests

### TC-017: Traffic Analysis and Metadata Tests

**Objective**: Analyze traffic patterns and verify that metadata doesn't leak sensitive information.

**Priority**: MEDIUM

**Test Procedure**:

**Part A: Traffic Pattern Analysis**
1. Capture normal traffic baseline
2. Analyze connection patterns
3. Identify unusual traffic patterns
4. Check for anomalies

**Part B: Metadata Leakage Verification**
1. Analyze packet headers and metadata
2. Check for device identifiers in headers
3. Verify client IDs don't reveal sensitive info
4. Check topic names for information leakage

**Expected Result**:
- Normal traffic patterns established
- Anomalies can be detected
- Baseline for monitoring established
- No sensitive information in metadata
- Client IDs should be generic or encrypted
- Topic names should not reveal sensitive data

**How to Run**:
```bash
# Wireshark statistics
# Statistics → IO Graph
# Statistics → Conversations
# Statistics → Endpoints

# Wireshark analysis for metadata
# Check: mqtt.clientid, mqtt.topic fields
# Use: python security_test_analyzer.py capture.pcap
```

**Pass Criteria**: Baseline established, anomalies detectable, no sensitive metadata leakage

---

## 8. System Resilience Tests

### TC-019: DoS and System Resilience Tests

**Objective**: Test broker resilience against various denial-of-service attacks and resource exhaustion.

**Priority**: MEDIUM

**Test Procedure**:

**Part A: Connection Flood Attack**
1. Start resource monitoring on broker
2. Create multiple simultaneous connections
3. Monitor broker performance
4. Check for connection limits and rate limiting

**Part B: Message Flood Attack**
1. Connect with valid credentials
2. Send high volume of messages rapidly
3. Monitor broker performance
4. Check for message rate limiting

**Part C: Resource Exhaustion**
1. Monitor CPU, memory, disk usage
2. Generate high load (combinations of connections and messages)
3. Check system stability
4. Verify graceful degradation

**Expected Result**:
- Broker should handle connections gracefully
- Connection limits should be enforced
- Rate limiting should prevent overload
- Broker should not crash
- Broker should handle message flood
- Rate limiting should activate
- Broker should not crash or become unresponsive
- Legitimate messages should still be processed
- System should handle high load
- Resource limits should be enforced
- System should not crash
- Graceful degradation acceptable

**How to Run**:
```bash
# Automated test
python security_test_attacks.py dos

# Monitor on Pi: ./monitor_resources.sh
# Manual test - rapid message publishing
# Monitor: sudo journalctl -u mosquitto -f
# Monitor resources: htop, iotop
```

**Pass Criteria**: Broker remains stable, limits enforced, rate limiting works, system stable under load

---

## Test Execution Summary

### Quick Test Execution

```bash
# Run all automated tests
python security_test_attacks.py

# Run specific test category
python security_test_attacks.py tls      # Encryption tests
python security_test_attacks.py auth    # Authentication tests
python security_test_attacks.py acl     # Authorization tests
python security_test_attacks.py replay  # Replay attack
python security_test_attacks.py dos    # DoS tests

# Analyze capture file
python security_test_analyzer.py capture.pcap
```

### Test Coverage Matrix

| Test Case | Automated | Manual | Wireshark | Priority |
|-----------|-----------|--------|-----------|----------|
| TC-001 | ✓ | ✓ | ✓ | CRITICAL |
| TC-002 | ✓ | ✓ | ✓ | HIGH |
| TC-004 | - | ✓ | ✓ | CRITICAL |
| TC-005 | ✓ | ✓ | ✓ | CRITICAL |
| TC-006 | ✓ | ✓ | ✓ | HIGH |
| TC-007 | - | ✓ | ✓ | CRITICAL |
| TC-008 | - | ✓ | ✓ | MEDIUM |
| TC-009 | ✓ | ✓ | ✓ | HIGH |
| TC-012 | - | ✓ | ✓ | CRITICAL |
| TC-013 | ✓ | ✓ | - | HIGH |
| TC-014 | ✓ | ✓ | ✓ | MEDIUM |
| TC-015 | - | ✓ | ✓ | MEDIUM |
| TC-016 | - | ✓ | ✓ | HIGH |
| TC-017 | ✓ | ✓ | ✓ | MEDIUM |
| TC-019 | ✓ | ✓ | ✓ | MEDIUM |
| TC-022 | - | ✓ | ✓ | CRITICAL |
| TC-023 | - | ✓ | ✓ | HIGH |
| TC-025 | - | ✓ | ✓ | CRITICAL |
| TC-026 | - | ✓ | ✓ | CRITICAL |
| TC-027 | - | ✓ | ✓ | CRITICAL |

### Test Results Documentation

After running tests, document:
1. Test case ID and name
2. Test date and time
3. Test result (PASS/FAIL)
4. Evidence (screenshots, logs, capture files)
5. Issues found
6. Recommendations

### Test Schedule

**Recommended Testing Frequency**:
- **Critical Tests (TC-001, TC-004, TC-005, TC-007, TC-012, TC-022, TC-025, TC-026, TC-027)**: Before each deployment
- **High Priority Tests (TC-002, TC-006, TC-009, TC-013, TC-016, TC-023)**: Weekly
- **Medium Priority Tests (TC-008, TC-014, TC-015, TC-017, TC-019)**: Monthly
- **High Priority Tests**: Weekly
- **Medium Priority Tests**: Monthly
- **Low Priority Tests**: Quarterly

---

## Test Environment Requirements

1. **Isolated Test Network**: Use separate network for testing
2. **Test Broker**: Dedicated test MQTT broker (not production)
3. **Monitoring Tools**: Wireshark, resource monitoring on broker
4. **Documentation**: Test results, evidence, logs

---

## Important Notes

⚠️ **Only test on systems you own or have explicit permission**

⚠️ **Use isolated test environments**

⚠️ **Document all test activities**

⚠️ **Do not test on production systems without authorization**

---

For detailed procedures, see:
- `WIRESHARK_SECURITY_TESTING.md` - Detailed testing procedures
- `RASPBERRY_PI_CAPTURE_GUIDE.md` - Broker-side capture guide
- `SECURITY_TESTING_QUICKSTART.md` - Quick start guide
