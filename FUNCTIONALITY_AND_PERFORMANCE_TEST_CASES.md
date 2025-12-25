# Functionality and Performance Testing Guide

## Overview

This guide provides comprehensive test cases for **functionality** and **performance** testing of the IoT Secure Water Monitor system. These tests are **separate from security testing** and focus on:

- **Functionality Testing**: Verifying that all features work as expected (does it work?)
- **Performance Testing**: Measuring system performance under various conditions (how fast/well does it work?)

## Important: Difference from Security Testing

**This guide is COMPLEMENTARY to security testing, not a replacement.**

### Security Testing (see `STEP_BY_STEP_TESTING_GUIDE.md`) focuses on:
- **Is the system secure?** (TLS enforcement, authentication security, encryption strength)
- **Can attackers break in?** (brute force, MITM, replay attacks)
- **Is data protected?** (encryption verification, tampering detection)
- **Are access controls working?** (ACL, authorization, topic isolation)

### Functionality Testing (this guide) focuses on:
- **Does the system work?** (can users log in, can data be stored, can messages be sent)
- **Do features function correctly?** (registration works, data displays, forms validate)
- **Is the system usable?** (navigation works, UI displays correctly, errors handled)

### Performance Testing (this guide) focuses on:
- **How fast is the system?** (response times, query performance)
- **How much can it handle?** (throughput, concurrent users, message volume)
- **How efficient is it?** (resource usage, scalability)

### Key Differences:

| Aspect | Security Testing | Functionality/Performance Testing |
|--------|-----------------|----------------------------------|
| **Encryption** | Verifies encryption is SECURE (TLS version, certificate validation, E2EE presence) | Verifies encryption WORKS (can encrypt/decrypt, keys load correctly) |
| **Authentication** | Verifies authentication is SECURE (wrong credentials rejected, brute force protection) | Verifies authentication WORKS (can log in with correct credentials, session created) |
| **MQTT** | Verifies MQTT is SECURE (TLS required, ACL enforced, topics isolated) | Verifies MQTT WORKS (can connect, publish, subscribe, reconnect) |
| **Performance** | Tests security resilience (DoS attacks, resource exhaustion under attack) | Tests normal performance (response times, throughput, resource usage) |

**Note**: Some test cases may seem similar but have different objectives:
- **FC-003** (Invalid Login - Functionality): Verifies system rejects invalid login (does it work?)
- **TC-006** (Wrong Credentials - Security): Verifies system securely rejects wrong credentials (is it secure?)

Both are important but test different aspects!

---

## Prerequisites

### Required Tools
- Python 3.8+ installed
- MQTT broker running (Raspberry Pi on port 8883)
- Database (MySQL/PostgreSQL) accessible
- Flask application running
- Network connectivity to Raspberry Pi

### Test Environment Setup
```powershell
# Install test dependencies
pip install -r requirements.txt

# Verify MQTT broker is accessible
python test_provision_mqtt.py sal01 update 1

# Verify database connection
python test_mysql_connection.py
```

---

## Category 1: User Management Functionality

### FC-001: User Authentication and Account Management

**Objective**: Verify user registration, login (valid/invalid), profile updates, and password changes work.

**Test Steps**:
1. **Registration**: Navigate to registration page, fill form with valid data, submit, verify user created and can log in
2. **Valid Login**: Navigate to login page, enter valid credentials, verify session created and redirected to dashboard
3. **Invalid Login**: Enter invalid credentials, verify error displayed and no session created
4. **Profile Update**: Log in, navigate to profile, update fields, verify changes saved and persist
5. **Password Change**: Navigate to password change, enter current and new password, submit, log out, verify new password works

**Expected Result**:
- ✅ User registration and login work
- ✅ Invalid credentials rejected
- ✅ Profile updates saved
- ✅ Password change works

**Pass Criteria**: All user authentication and account management features work correctly

**Note**: For security testing of authentication, see **TC-005, TC-006** in security testing guide.

---

## Category 2: Device/Sensor Management Functionality

### FC-002: Device Management (CRUD and Status)

**Objective**: Verify device registration, listing, updates, deletion, and status monitoring work.

**Test Steps**:
1. **Registration**: Log in, navigate to device registration, fill device info (ID, location, type, public key), submit, verify device created and appears in list
2. **List Display**: Navigate to devices page, verify all devices displayed with correct info (ID, location, status, last update), verify pagination works
3. **Update**: Select device to edit, update location/status, submit, verify changes saved and displayed
4. **Deletion**: Select device to delete, confirm, verify device removed from database and list
5. **Status Monitoring**: Register device, send sensor data, verify status updates to "active", stop sending data, verify status updates to "inactive" (if timeout configured)

**Expected Result**:
- ✅ Device CRUD operations work
- ✅ Device list displays correctly
- ✅ Device status updates correctly
- ✅ All operations persist correctly

**Pass Criteria**: All device management features work correctly

---

## Category 3: Sensor Data Collection and Storage

### FC-011: Sensor Data Reception and Storage

**Objective**: Verify sensor data is received via MQTT and stored in database.

**Test Steps**:
1. Start MQTT listener/subscriber
2. Send sensor data from device simulator:
   ```powershell
   python simulators\sensor\sensor_simulator.py --device-id sal01
   ```
3. Verify data received by MQTT listener
4. Verify data structure is correct
5. Verify data contains required fields
6. Verify data decrypted (if encrypted)
7. Verify data inserted into database
8. Query database to verify data stored correctly
9. Verify timestamp is correct

**Expected Result**:
- ✅ Sensor data received via MQTT
- ✅ Data structure valid
- ✅ Required fields present
- ✅ Data encrypted (E2EE) if applicable
- ✅ Sensor data stored in database
- ✅ All fields stored correctly
- ✅ Timestamp accurate
- ✅ Data integrity maintained

**Pass Criteria**: Sensor data received and stored successfully

---

### FC-003: Sensor Data Display and Historical Viewing

**Objective**: Verify sensor data retrieval, display (dashboard and historical), and multiple sensor type support.

**Test Steps**:
1. **Data Retrieval and Display**: Send multiple sensor readings, wait for storage, log in, navigate to dashboard, verify data displayed correctly, verify data ordered by timestamp, verify visualization works
2. **Historical Viewing**: Navigate to history page, select device and date range, verify historical data displayed and filtered correctly, verify export works (if applicable)
3. **Multiple Sensor Types**: Register devices with different sensor types (pH, temperature, turbidity), send data from each, verify data stored and displayed correctly for each type

**Expected Result**:
- ✅ Sensor data retrieved and displayed correctly
- ✅ Historical data viewing works
- ✅ Multiple sensor types supported
- ✅ Data visualization and filtering work

**Pass Criteria**: Sensor data display and historical viewing work correctly

**Objective**: Verify system handles multiple sensor types.

**Test Steps**:
1. Register devices with different sensor types:
   - pH sensor
   - Temperature sensor
   - Turbidity sensor
   - etc.
2. Send data from each sensor type
3. Verify data stored correctly for each type
4. Verify data displayed correctly for each type
5. Verify type-specific thresholds work (if applicable)

**Expected Result**:
- ✅ Multiple sensor types supported
- ✅ Data stored correctly per type
- ✅ Type-specific handling works
- ✅ Thresholds work per type (if applicable)

**Pass Criteria**: Multiple sensor types work correctly

---

## Category 4: MQTT Communication Functionality

**Note**: Security testing (TC-001, TC-002, TC-005, TC-009, TC-010) verifies MQTT is SECURE. This section verifies MQTT WORKS functionally.

### FC-004: MQTT Communication (Connection, Publishing, Subscription, Reconnection)

**Objective**: Verify MQTT connections, publishing, subscription, reconnection, and topic structure work.

**Test Steps**:
1. **Connection**: Start MQTT client, configure connection (host, port, credentials, TLS), connect, verify connection and TLS handshake successful
2. **Publishing**: Publish message to topic, verify published successfully (return code 0), verify QoS respected
3. **Subscription**: Subscribe to topic with wildcards, publish matching message, verify message received with correct payload and topic
4. **Reconnection**: Disconnect broker, verify disconnection detected, reconnect broker, verify automatic reconnection and messages resume
5. **Topic Structure**: Verify topic naming conventions, verify wildcards work, verify structure is consistent

**Expected Result**:
- ✅ MQTT connection, publishing, and subscription work
- ✅ Reconnection handling works
- ✅ Topic structure correct
- ✅ All MQTT operations functional

**Pass Criteria**: All MQTT communication features work correctly

**Note**: For security testing, see **TC-001, TC-002, TC-005, TC-009, TC-010** in security testing guide.

---

## Category 5: Encryption/Decryption Functionality

**Note**: Security testing (TC-022, TC-023, TC-024, TC-027) verifies encryption is SECURE. This section verifies encryption WORKS functionally.

### FC-005: Encryption, Decryption, and Key Management

**Objective**: Verify data encryption, decryption, key management, and session key rotation work.

**Test Steps**:
1. **Encryption/Decryption**: Prepare test data, encrypt using `encrypt_data()`, verify encrypted payload structure (session_key, ciphertext, nonce, tag), verify data not readable, decrypt using `decrypt_data()`, verify decrypted data matches original, test with invalid data (should fail)
2. **Key Management**: Generate RSA key pair, save public key to user directory, verify key file created, load key from file, verify key is valid and usable for encryption
3. **Session Key Rotation**: Encrypt multiple messages with same public key, extract session_key from each, verify each message has different session_key, verify all messages decryptable with same private key

**Expected Result**:
- ✅ Encryption and decryption work correctly
- ✅ Key management works
- ✅ Session key rotation works
- ✅ All encryption features functional

**Pass Criteria**: All encryption/decryption features work correctly

**Note**: For security testing, see **TC-022, TC-023, TC-024, TC-027** in security testing guide.

---

## Category 6: Provision Agent Functionality

### FC-006: Provision Agent Functionality

**Objective**: Verify provision agent sends messages, distributes keys, and processes messages correctly.

**Test Steps**:
1. **Message Sending**: Log in, navigate to provision page, select device and action, send provision message, verify published to MQTT with correct structure
2. **Key Distribution**: Register new device, send provision request, verify agent receives message, retrieves public key, publishes to device topic, verify device receives key
3. **Message Processing**: Send update and request messages, verify agent processes both, verify invalid messages handled gracefully

**Expected Result**:
- ✅ Provision messages sent and received
- ✅ Key distribution works
- ✅ Message processing works
- ✅ All provision agent features functional

**Pass Criteria**: Provision agent functionality works correctly

**Objective**: Verify provision agent processes messages correctly.

**Test Steps**:
1. Send provision message: `update` action
2. Verify agent processes message
3. Send provision message: `request` action
4. Verify agent processes message
5. Verify agent handles invalid messages gracefully

**Expected Result**:
- ✅ Agent processes update messages
- ✅ Agent processes request messages
- ✅ Invalid messages handled gracefully
- ✅ Errors logged (if applicable)

**Pass Criteria**: Provision agent message processing works

---

## Category 7: Database Functionality

### FC-007: Database Operations (Connection, Schema, Transactions, Performance)

**Objective**: Verify database connections, schema, transactions, and query performance work.

**Test Steps**:
1. **Connection**: Test database connection, verify connection pool works, verify connections acquired/returned/reused correctly
2. **Schema**: Check all required tables exist (users, sensors, sensor_data, sensor_type, device_sessions), verify table structures, foreign keys, and indexes
3. **Transactions**: Start transaction, insert test data, verify isolation (not visible to other connections), commit and verify data visible, test rollback
4. **Query Performance**: Insert large dataset (1000+ records), query recent sensor data, measure execution time, verify completes in reasonable time (< 1 second), verify indexes used

**Expected Result**:
- ✅ Database connection and pool work
- ✅ Schema is correct
- ✅ Transactions work correctly
- ✅ Query performance acceptable

**Pass Criteria**: All database operations work correctly

---

## Category 8: Web Interface Functionality

### FC-008: Web Interface (Dashboard, Navigation, Forms, Responsive Design)

**Objective**: Verify dashboard loading, navigation, form validation, and responsive design work.

**Test Steps**:
1. **Dashboard and Navigation**: Log in, navigate to dashboard, verify loads with all sections and data (< 3 seconds), navigate through all pages (Dashboard, Devices, History, Profile), verify each page loads, verify navigation links and back button work
2. **Form Validation**: Test registration form (empty fields, invalid email, weak password, mismatched passwords - all should fail), test device registration form (empty device ID, invalid format - should fail), verify error messages displayed
3. **Responsive Design**: Open dashboard on desktop, resize to mobile size, verify layout adapts, verify all features accessible, verify no horizontal scrolling

**Expected Result**:
- ✅ Dashboard loads and displays correctly
- ✅ Navigation works
- ✅ Form validation works
- ✅ Responsive design works

**Pass Criteria**: All web interface features work correctly

---

## Category 9: Performance Testing

### PERF-001: Response Times and Query Performance

**Objective**: Measure response times for login, dashboard, and sensor data queries.

**Test Steps**:
1. **Login Response**: Clear cache, time login form submission to dashboard load, repeat 10 times, calculate average
2. **Dashboard Load**: Log in, clear cache, time dashboard navigation to full load, repeat 10 times, calculate average
3. **Query Performance**: Insert 10,000 sensor data records, time query for recent data (last 100 records), repeat 10 times, calculate average

**Expected Result**:
- ✅ Login response time < 2 seconds average
- ✅ Dashboard load time < 3 seconds average
- ✅ Query time < 500ms average
- ✅ All within acceptable limits

**Pass Criteria**: All response times meet targets

---

### PERF-002: Throughput, Concurrency, and High Volume Load

**Objective**: Measure MQTT throughput, sensor data processing, concurrent handling, and high-volume stress testing.

**Test Steps**:
1. **MQTT Throughput**: Establish connection, publish 1000 messages, measure throughput (msg/s), repeat 3 times
2. **Sensor Data Processing**: Start listener, send 1000 sensor messages, measure processing throughput, verify all stored
3. **Concurrency**: Simulate 10 concurrent logins and dashboard access, establish 50 concurrent MQTT connections, publish from all, measure response times and delivery times, monitor resources
4. **High Volume Stress**: Send 10,000 sensor data messages rapidly, monitor system resources, verify all messages processed, verify no data loss, verify system remains stable

**Expected Result**:
- ✅ MQTT publishing > 100 msg/s
- ✅ Sensor processing > 50 msg/s
- ✅ System handles 10 concurrent users
- ✅ System handles 50 concurrent MQTT connections
- ✅ System handles 10,000 messages without issues
- ✅ All operations successful

**Pass Criteria**: Throughput, concurrency, and high-volume load targets met

---

### PERF-003: Database Performance, Resource Usage, and Extended Operation

**Objective**: Measure database performance with large datasets, system resource usage, extended operation stability, and connection pool handling.

**Test Steps**:
1. **Database Load**: Insert 100,000 records, query recent data, query by date range, query by device, measure all query times
2. **Resource Usage**: Monitor baseline memory/CPU, process 1000 then 10,000 sensor messages, monitor usage, check for memory leaks, verify resources return to baseline
3. **Network Bandwidth**: Monitor baseline, send 1000 messages, measure bandwidth used, calculate per message
4. **Encryption Performance**: Prepare 1000 records, time encryption and decryption, calculate per record
5. **Extended Operation**: Run system for 24 hours, send sensor data continuously (1 message per minute), monitor system resources, verify no memory leaks, verify system remains responsive, verify all data stored correctly
6. **Connection Pool Exhaustion**: Configure small connection pool (5 connections), create 10 concurrent database operations, monitor pool usage, verify system handles exhaustion gracefully, verify operations complete when connections available

**Expected Result**:
- ✅ Database queries < 2 seconds with large dataset
- ✅ Memory and CPU usage acceptable, no leaks
- ✅ Network bandwidth measured
- ✅ Encryption/decryption < 50ms per record
- ✅ System stable for 24 hours extended operation
- ✅ Connection pool exhaustion handled gracefully

**Pass Criteria**: Database, resource, and extended operation performance acceptable

---

## Test Execution Checklist

### Pre-Testing
- [ ] Test environment set up
- [ ] Database accessible
- [ ] MQTT broker running
- [ ] Flask application running
- [ ] Test data prepared
- [ ] Test users created

### For Each Test
- [ ] Test prerequisites met
- [ ] Test steps executed
- [ ] Results documented
- [ ] Pass/fail criteria verified
- [ ] Issues logged (if any)

### Post-Testing
- [ ] All test results reviewed
- [ ] Performance metrics documented
- [ ] Issues prioritized
- [ ] Test report generated

---

## Performance Benchmarks

### Target Performance Metrics

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| User Login Response Time | < 1s | < 2s | > 3s |
| Dashboard Load Time | < 2s | < 3s | > 5s |
| Sensor Data Query | < 300ms | < 500ms | > 1s |
| MQTT Message Throughput | > 200 msg/s | > 100 msg/s | < 50 msg/s |
| Sensor Data Processing | > 100 msg/s | > 50 msg/s | < 25 msg/s |
| Concurrent Users | > 50 | > 20 | < 10 |
| Concurrent MQTT Connections | > 100 | > 50 | < 20 |
| Memory Usage | < 500MB | < 1GB | > 2GB |
| CPU Usage (Idle) | < 5% | < 10% | > 20% |
| CPU Usage (Load) | < 50% | < 70% | > 90% |

---

## Test Data Preparation

### Test Users
Create test users with different roles and permissions:
- Admin user
- Regular user
- Test user (for automated tests)

### Test Devices
Create test devices with different configurations:
- pH sensor
- Temperature sensor
- Multiple devices per user
- Devices in different locations

### Test Data
Generate test sensor data:
- Normal readings
- Edge cases (min/max values)
- Invalid data (for negative testing)
- Large volume (for performance testing)

---

## Related Test Documents

### Security Testing
- **`STEP_BY_STEP_TESTING_GUIDE.md`**: Comprehensive security testing guide
  - Encryption & TLS tests (TC-001 to TC-004)
  - Authentication tests (TC-005 to TC-008)
  - Authorization tests (TC-009 to TC-011)
  - Attack simulation tests (TC-012 to TC-021)
  - E2EE tests (TC-022 to TC-027)

### This Document
- **Functionality tests**: Verify features work (FC-001 to FC-008)
- **Performance tests**: Measure system performance including stress testing (PERF-001 to PERF-003)

### When to Use Which Guide

| Test Type | Use This Guide | Focus |
|-----------|---------------|-------|
| Does login work? | Functionality (FC-002) | Feature works |
| Is login secure? | Security (TC-005, TC-006) | Security |
| Can we encrypt data? | Functionality (FC-022) | Feature works |
| Is encryption secure? | Security (TC-022, TC-027) | Security |
| How fast is login? | Performance (PERF-001) | Speed |
| Can system handle high volume? | Performance (PERF-002) | Capacity/Stress |
| Can system run for 24 hours? | Performance (PERF-003) | Stability/Stress |
| Can attackers break in? | Security (TC-012 to TC-021) | Security |

---

## Troubleshooting

### Common Issues

**Issue**: Tests failing due to database connection
- **Solution**: Verify database is running and accessible
- **Solution**: Check connection pool configuration

**Issue**: MQTT connection failures
- **Solution**: Verify MQTT broker is running
- **Solution**: Check network connectivity
- **Solution**: Verify TLS certificates

**Issue**: Performance tests showing slow results
- **Solution**: Check system resources (CPU, memory)
- **Solution**: Verify database indexes exist
- **Solution**: Check network latency

**Issue**: Test data not appearing
- **Solution**: Verify data insertion successful
- **Solution**: Check database queries
- **Solution**: Verify MQTT message delivery

---

## Test Report Template

### Test Execution Summary
- Total Tests: X
- Passed: Y
- Failed: Z
- Skipped: W

### Functionality Tests
- User Management: X/Y passed
- Device Management: X/Y passed
- Sensor Data: X/Y passed
- MQTT Communication: X/Y passed
- Encryption: X/Y passed

### Performance Tests
- Response Times: All within targets
- Throughput and Concurrency: All within targets
- Resource Usage and Extended Operation: All within limits

### Issues Found
1. Issue description
2. Severity
3. Steps to reproduce
4. Recommended fix

---

This guide provides comprehensive test cases for functionality and performance testing. Execute tests systematically and document all results.

