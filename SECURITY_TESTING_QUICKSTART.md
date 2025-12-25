# Security Testing Quick Start Guide

## Prerequisites

1. **Install Wireshark**
   - Download from: https://www.wireshark.org/
   - Install with Npcap for Windows

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements_security.txt
   ```

## Quick Testing Workflow

### Step 1: Capture Traffic with Wireshark

1. Open Wireshark (as Administrator)
2. Select your network interface (Wi-Fi/Ethernet)
3. Start capture (blue shark fin icon)
4. Apply filter: `tcp.port == 8883 or tcp.port == 1883`
5. Run your MQTT test:
   ```bash
   python test_provision_mqtt.py sal01 update 1
   ```
6. Stop capture and save as `mqtt_capture.pcap`

### Step 2: Analyze Capture File

```bash
python security_test_analyzer.py mqtt_capture.pcap
```

This will:
- Analyze all MQTT traffic
- Check for encryption
- Identify security issues
- Generate a report

### Step 3: Run Attack Simulations

```bash
# Run all tests
python security_test_attacks.py

# Or run individual tests
python security_test_attacks.py tls      # Test TLS requirement
python security_test_attacks.py cert     # Test certificate validation
python security_test_attacks.py auth     # Test authentication
python security_test_attacks.py acl      # Test access control
```

## Common Security Tests

### 1. Check for Unencrypted Traffic

**In Wireshark:**
- Filter: `tcp.port == 1883`
- If you see packets, unencrypted MQTT is enabled (security risk!)

**Expected:** No traffic on port 1883

### 2. Verify TLS Encryption

**In Wireshark:**
- Filter: `tcp.port == 8883`
- Look for TLS handshake packets
- Try to read MQTT payloads - they should be encrypted

**Expected:** All traffic encrypted, payloads not readable

### 3. Test Authentication

**Using attack script:**
```bash
python security_test_attacks.py auth
```

**Expected:** Connection fails without credentials

### 4. Test Access Control

**Using attack script:**
```bash
python security_test_attacks.py acl
```

**Expected:** Unauthorized topics blocked

## Wireshark Display Filters

Save these filters in Wireshark for quick access:

```
# All MQTT traffic
mqtt

# Encrypted MQTT
tcp.port == 8883 and mqtt

# Unencrypted MQTT (should be none!)
tcp.port == 1883 and mqtt

# Provision topics
mqtt.topic contains "provision"

# CONNECT messages (authentication)
mqtt.msgtype == 1

# PUBLISH messages
mqtt.msgtype == 3

# TLS handshake
tls.handshake.type == 1
```

## Interpreting Results

### Security Analyzer Output

- **CRITICAL**: Immediate action required
  - Unencrypted connections
  - Credentials exposed
  
- **HIGH**: Fix soon
  - Weak encryption
  - Authentication bypass
  
- **MEDIUM**: Address when possible
  - Sensitive topic names
  - Weak TLS versions
  
- **INFO**: For awareness
  - High number of topics
  - Multiple clients

### Attack Simulation Results

- **✓ PASS**: Security control working
- **✗ FAIL**: Security control not working (needs fixing)

## Example Testing Session

```bash
# 1. Start Wireshark capture
# (Do this manually in Wireshark GUI)

# 2. Run normal operation
python test_provision_mqtt.py sal01 update 1

# 3. Stop Wireshark, save as capture.pcap

# 4. Analyze
python security_test_analyzer.py capture.pcap

# 5. Run attack simulations
python security_test_attacks.py

# 6. Review reports
# - security_test_results.json
# - capture_security_report.json
```

## Troubleshooting

### "pyshark not found"
```bash
pip install pyshark
```

### "Permission denied" in Wireshark
- Run Wireshark as Administrator
- Or use `tshark` from command line with admin privileges

### "No packets captured"
- Check network interface selection
- Verify MQTT traffic is actually being sent
- Check firewall isn't blocking

### Can't see MQTT protocol
- Go to `Edit` → `Preferences` → `Protocols`
- Enable MQTT protocol
- Restart Wireshark

## Next Steps

1. **For detailed step-by-step instructions**: See `STEP_BY_STEP_TESTING_GUIDE.md`
2. Review all test cases: `SECURITY_TEST_CASES.md`
3. Read full guide: `WIRESHARK_SECURITY_TESTING.md`
4. Document your findings
5. Fix identified vulnerabilities
6. Re-test to verify fixes
7. Create regular testing schedule

## Important Notes

⚠️ **Only test on systems you own or have explicit permission**

⚠️ **Use isolated test environments when possible**

⚠️ **Document all testing activities**

For detailed information, see `WIRESHARK_SECURITY_TESTING.md`
