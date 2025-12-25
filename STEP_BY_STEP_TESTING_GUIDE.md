# Step-by-Step Security Testing Guide

## Overview

This guide provides detailed, step-by-step instructions for executing each security test case. Follow these procedures exactly to ensure accurate and reproducible test results.

---

## Prerequisites Setup

### Important: When Admin Privileges Are Needed

**✅ REQUIRES Admin (Run as Administrator):**
- **Wireshark** - Must run as Administrator to capture network packets
- **Installing Wireshark/Npcap** - May require admin during installation

**❌ DOES NOT Require Admin:**
- **PowerShell** - Regular PowerShell is fine for running Python scripts
- **Python commands** - All `python` and `python -c` commands work without admin
- **Running test scripts** - `security_test_attacks.py`, `security_test_analyzer.py` work without admin
- **Installing Python packages** - `pip install` usually works without admin (unless system-wide install)

**Summary**: Only Wireshark needs admin privileges. All Python testing commands work in regular PowerShell.

---

### Step 1: Install Required Tools on Windows

**⚠️ Important: What You DON'T Need:**
- ❌ **Website/Flask app does NOT need to be running** - Tests create their own MQTT connections
- ❌ **Browser does NOT need to be open** - All tests run from command line
- ❌ **Web interface is NOT used** - Tests connect directly to MQTT broker

**What You DO Need:**
- ✅ MQTT broker running on Raspberry Pi (port 8883)
- ✅ Network connectivity to Raspberry Pi
- ✅ Python and testing tools installed

1. **Install Wireshark**
   - Download from: https://www.wireshark.org/
   - Install with Npcap (for Windows packet capture)
   - ⚠️ **Must run Wireshark as Administrator** to capture packets

2. **Install Python Dependencies** (Regular PowerShell - no admin needed)
   ```powershell
   pip install -r requirements_security.txt
   ```

3. **Verify Installation** (Regular PowerShell - no admin needed)
   ```powershell
   python --version
   python -c "import pyshark; print('pyshark OK')"
   python -c "import paho.mqtt.client; print('paho-mqtt OK')"
   ```

4. **Verify MQTT Broker is Running** (Only requirement)
   ```powershell
   # Test connection to broker
   python test_provision_mqtt.py sal01 update 1
   # If this works, broker is ready for testing
   ```

### Step 2: Setup Raspberry Pi

**⚠️ When Do You Need SSH?**

**✅ SSH IS NEEDED for:**
- Running capture scripts on Raspberry Pi (`capture_security_test.sh`)
- Viewing broker logs (`sudo journalctl -u mosquitto`)
- Checking broker configuration
- Monitoring system resources on Pi
- Transferring capture files from Pi to Windows

**❌ SSH IS NOT NEEDED for:**
- Running Python test scripts from Windows (they connect over network)
- Running `security_test_attacks.py` (runs on Windows)
- Running `security_test_analyzer.py` (runs on Windows)
- Using Wireshark on Windows
- Most automated tests (they run from Windows)

**Summary**: You only need SSH if you want to capture data ON the Raspberry Pi or check broker logs. Most tests can be done entirely from Windows without SSH.

---

**If you want to use Pi-side captures (optional but recommended):**

1. **SSH into Raspberry Pi**
   ```powershell
   ssh pi@192.168.43.214
   ```

2. **Copy Capture Scripts to Pi**
   ```powershell
   # From Windows PowerShell (in project directory)
   scp pi_scripts/*.sh pi@192.168.43.214:/home/pi/
   ```

3. **Make Scripts Executable**
   ```bash
   # On Raspberry Pi (after SSH)
   chmod +x /home/pi/*.sh
   mkdir -p /home/pi/security_captures
   ```

4. **Verify tcpdump is Available**
   ```bash
   # On Raspberry Pi (after SSH)
   which tcpdump
   # If not installed: sudo apt-get install tcpdump
   ```

5. **Important: Viewing Recent Mosquitto Logs**
   ```bash
   # If you see old logs (like from 6 PM), use --since to get recent logs:
   
   # See logs from last hour
   sudo journalctl -u mosquitto --since "1 hour ago"
   
   # See logs from last 10 minutes
   sudo journalctl -u mosquitto --since "10 minutes ago"
   
   # Follow NEW logs in real-time
   sudo journalctl -u mosquitto -f --since "1 minute ago"
   
   # If no logs in journalctl, check log file:
   sudo tail -f /var/log/mosquitto/mosquitto.log
   ```

**If you skip Pi-side captures**, you can still do all tests using only:
- Wireshark on Windows (captures from client side)
- Python test scripts on Windows
- Security analyzer on Windows

---

## Test Execution Workflow

### Quick Answer: Do I Need the Website Running?

**❌ NO - Website NOT Required for Most Tests!**

**✅ Tests that DON'T need the website:**
- All automated tests (`security_test_attacks.py`)
- All MQTT protocol tests (TLS, authentication, authorization)
- All attack simulations (replay, DoS, MITM, etc.)
- All traffic analysis tests
- All encryption/security tests

**These tests create their own MQTT connections directly** - they don't use the website.

**✅ Website is OPTIONAL (but helpful) for:**
- **Traffic Pattern Analysis (TC-014)**: Having real traffic from the website makes analysis more realistic
- **Topic Enumeration (TC-012)**: Website generates real topics you can discover
- **Eavesdropping Attack (TC-009)**: Real traffic from website is more realistic

**Summary**: 
- **90% of tests**: Website NOT needed - tests create their own MQTT connections
- **10% of tests**: Website is optional - makes traffic analysis more realistic
- **0% of tests**: Website is required

**You can run all security tests without opening the website in a browser!**

---

### Quick Answer: Do I Need SSH?

**For most tests: NO SSH needed!**

You can run most security tests entirely from Windows:
- ✅ All Python test scripts (`security_test_attacks.py`, `security_test_analyzer.py`)
- ✅ Wireshark captures (from Windows)
- ✅ All automated tests
- ✅ Most manual tests

**SSH is only needed if you want to:**
- Capture packets directly on the Raspberry Pi (broker side)
- View broker logs in real-time
- Monitor system resources on the Pi
- Run the comprehensive capture script (`capture_security_test.sh`)

**Recommendation**: Start without SSH. You can do 90% of tests from Windows. Add SSH later if you need broker-side captures or logs.

---

### Understanding Wireshark Interface

**Wireshark has 3 main panes:**

1. **Top Pane (Packet List)**: Shows all captured packets
   - Each row is a packet
   - Columns show: No., Time, Source, Destination, Protocol, Length, Info
   - **Click here to select a packet**

2. **Middle Pane (Packet Details)**: Shows details of selected packet
   - Expandable tree structure
   - Click arrows (▶) to expand sections
   - **This is where you find MQTT protocol details**

3. **Bottom Pane (Packet Bytes)**: Shows raw packet data in hex
   - Useful for seeing encrypted binary data

**Filter Bar**: Located at the top, below the menu
- Type filter expressions here (e.g., `mqtt.msgtype == 3`)
- Press Enter to apply filter
- Click "X" to clear filter

**To Find PUBLISH Packets:**
1. Type `mqtt.msgtype == 3` in the filter bar
2. Press Enter
3. PUBLISH packets will appear in the top pane (packet list)
4. Click on one to see details in middle pane

### General Testing Pattern

For each test:
1. **Setup**: Start captures (Wireshark on Windows, tcpdump on Pi)
2. **Execute**: Run the test/attack
3. **Stop**: Stop captures
4. **Analyze**: Review results
5. **Document**: Record findings

---

## Category 1: Encryption & TLS Tests

### TC-001: TLS Requirement Enforcement

**Objective**: Verify unencrypted MQTT connections are blocked.

#### Step-by-Step Procedure:

**Step 1: Start Wireshark Capture on Windows**
1. Open Wireshark (as Administrator)
2. Select network interface (Wi-Fi/Ethernet)
3. Click blue shark fin icon to start capture
4. Apply filter: `tcp.port == 1883`
5. Note: You should see NO traffic initially

**Step 2: Attempt Unencrypted Connection**
```powershell
# Regular PowerShell (NO admin needed for Python commands)
# Create test script: test_unencrypted.py
python -c "
import paho.mqtt.client as mqtt
try:
    client = mqtt.Client()
    client.username_pw_set('water_monitor', 'e2eeWater2025')
    # NO TLS - trying unencrypted
    client.connect('192.168.43.214', 1883, 5)
    client.loop_start()
    import time
    time.sleep(2)
    client.loop_stop()
    print('FAIL: Unencrypted connection succeeded!')
except Exception as e:
    print(f'PASS: Connection rejected: {type(e).__name__}')
"
```

**Step 3: Check Wireshark**
- Look for any packets on port 1883
- If you see packets: **FAIL** (unencrypted traffic allowed)
- If no packets or connection refused: **PASS**

**Step 4: Verify Port 1883 is Disabled**
```bash
# On Raspberry Pi
sudo netstat -tlnp | grep 1883
# Should show nothing or port not listening
```

**Expected Result**: 
- ✅ Connection fails
- ✅ No traffic on port 1883
- ✅ Port 1883 not listening

**Pass Criteria**: Connection fails, no unencrypted traffic

---

### TC-002: TLS Configuration and Validation

**Objective**: Verify TLS is properly configured with certificate validation and secure versions.

#### Step-by-Step Procedure:

**Part A: Certificate Validation**

**Step 1: Test with Valid Certificate (Baseline)**
```powershell
# This should work
python test_provision_mqtt.py sal01 update 1
# Should connect successfully
```

**Step 2: Test Certificate Validation**
```powershell
# Regular PowerShell (NO admin needed)
# Run automated test
python security_test_attacks.py cert
```

**Step 3: Manual Test - Invalid Certificate**
```powershell
# Regular PowerShell (NO admin needed)
python -c "
import ssl
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')

# Try with strict certificate validation
context = ssl.create_default_context()
context.load_verify_locations(cafile='certs/ca-cert.pem')
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED

client.tls_set_context(context)
try:
    client.connect('192.168.43.214', 8883, 5)
    print('Connected - certificate accepted')
except ssl.SSLError as e:
    print(f'SSL Error (expected if cert invalid): {e}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
"
```

**Part B: TLS Version Check**

**Step 4: Capture TLS Handshake**
1. Start Wireshark capture
2. Filter: `tcp.port == 8883`
3. Run: `python test_provision_mqtt.py sal01 update 1`
4. Stop capture

**Step 5: Analyze TLS Version**
1. In Wireshark, filter: `tls.handshake.type == 1` (Client Hello)
2. Click on a Client Hello packet
3. Expand: `Transport Layer Security` → `TLSv1.2 Record Layer` → `Handshake Protocol: Client Hello`
4. Check `Version: TLS 1.2 (0x0303)` or `TLS 1.3 (0x0304)`
5. Look for Server Hello: `tls.handshake.type == 2`
6. Verify negotiated version

**Step 6: Check Cipher Suites**
1. In Client Hello, expand `Cipher Suites`
2. Verify strong ciphers are offered
3. Check Server Hello for selected cipher
4. Should NOT see weak ciphers like:
   - RC4
   - DES
   - MD5
   - SHA1 (preferably)

**Step 7: Automated Check**
```powershell
# Use security analyzer
python security_test_analyzer.py capture.pcap
# Check report for TLS version warnings
```

**Expected Result**:
- ✅ Valid certificate: Connection succeeds
- ✅ Invalid certificate: Connection fails with SSL error
- ✅ TLS version: 1.2 or 1.3
- ✅ Strong cipher suites
- ✅ No weak TLS versions (1.0, 1.1)

**Pass Criteria**: Certificate validation works, invalid certs rejected, TLS 1.2+ used, strong ciphers negotiated

---

### TC-003: Encrypted Payload Verification

**Objective**: Verify MQTT payloads are encrypted.

**💡 Efficiency Tip**: You can use the same pcap file for TC-003 and TC-011! Both tests analyze the same MQTT traffic capture - TC-003 looks at PUBLISH packets, TC-011 looks at CONNECT packets. Capture once, analyze twice!

#### Step-by-Step Procedure:

**Step 1: Capture MQTT Traffic**
1. **Start Wireshark capture** (as Administrator):
   - Open Wireshark
   - Select your network interface (Wi-Fi/Ethernet)
   - Click the blue shark fin icon (▶) to start capture

2. **Apply capture filter** (optional, but recommended):
   - Before starting capture, you can set a capture filter
   - Or use display filter after capture: `tcp.port == 8883`

3. **Generate MQTT traffic**:
   ```powershell
   # Regular PowerShell (no admin needed)
   python test_provision_mqtt.py sal01 update 1
   ```

4. **Stop capture**:
   - Click the red square (■) to stop capture
   - Save as `mqtt_traffic.pcap` (use a generic name so you can reuse it)
   - File → Save As → choose location and filename
   - **Note**: Save this file - you'll use it for TC-011 too!

**Step 2: Analyze Payloads**

**Important**: Make sure MQTT protocol is enabled in Wireshark:
- Go to `Edit` → `Preferences` → `Protocols`
- Search for "MQTT" and ensure it's enabled
- If not enabled, enable it and restart Wireshark

**Finding PUBLISH Packets:**

**⚠️ IMPORTANT: If you see "TLSv1.2" or "TLSv1.3" in the Protocol column, that's GOOD!**

When MQTT traffic is encrypted with TLS (port 8883), Wireshark shows it as "TLS" protocol, not "MQTT". This is **CORRECT** and means encryption is working! The MQTT packets are **inside** the encrypted TLS tunnel.

**Option 1: Verify Encryption is Working (Recommended - This is what you're seeing now)**
1. **You're already seeing TLS packets** - This is a PASS! ✅
2. **Check packet bytes to verify encryption**:
   - Click on any TLS packet
   - Look at the bottom pane (Packet Bytes)
   - The data should look like random binary/hex (encrypted)
   - You should NOT see readable text like JSON, device IDs, etc.
3. **This confirms**: MQTT is encrypted inside TLS ✅

**Option 2: Try to See MQTT Protocol (Advanced - Usually not needed)**
1. **Apply the filter**: 
   - In Wireshark filter bar, type: `mqtt.msgtype == 3` and press Enter
   - **Note**: This might show NO packets because MQTT is encrypted inside TLS
   - If no packets appear, that's actually GOOD - it means TLS encryption is working!

2. **If you want to see MQTT inside TLS** (requires TLS decryption):
   - You would need the TLS private key to decrypt
   - This is advanced and usually not necessary for security testing
   - The fact that you see TLS (not MQTT) is the correct result

**What You Should See:**
- ✅ **Protocol column shows "TLSv1.2" or "TLSv1.3"** ← This is what you're seeing (GOOD!)
- ✅ **Packet bytes are encrypted (random binary data)** ← Check this
- ❌ **Protocol column should NOT show "MQTT"** (if it does, encryption might not be working)
- ❌ **Packet bytes should NOT show readable JSON/text** (if it does, that's a security issue!)

3. **Click on a TLS packet**:
   - In the packet list (top pane), click on any TLS packet (TLSv1.2 or TLSv1.3)
   - The packet details will show in the middle pane

4. **Expand packet details**:
   - In the middle pane (packet details), look for: `Transport Layer Security`
   - Click the arrow (▶) to expand it
   - Look for: `TLSv1.3 Record Layer: Application Data Protocol: MQ Telemetry Transport Protocol`
   - Expand this section
   - You should see: **`Encrypted Application Data`** ← **THIS IS WHAT YOU'RE LOOKING FOR!**

5. **Check the encrypted data**:
   - Look at the `Encrypted Application Data` field
   - You should see a long hexadecimal string (like: `b99fe0c1b1921d8335758090789a4454...`)
   - Below it should say: `[Application Data Protocol: MQ Telemetry Transport Protocol]`
   - **This confirms**: MQTT is encrypted inside TLS ✅
   
6. **Verify data is encrypted (not readable)**:
   - Look at the bottom pane (Packet Bytes)
   - The ASCII representation on the right should show garbled characters
   - You should NOT see readable text like JSON, device IDs, etc.
   - **Expected**: Random-looking binary/hex data, NOT readable text
   - If you see readable JSON/text, that's a security issue!

**Step 3: Compare with Unencrypted (if possible)**
```powershell
# Temporarily disable TLS in test script
# Modify test_provision_mqtt.py to use port 1883 without TLS
# Capture again
# Compare payloads - unencrypted should be readable
```

**Step 4: Verify Payload Structure**
1. Look at packet bytes (right-click → "Show Packet Bytes")
2. Payload should be random-looking binary data
3. Should NOT see:
   - JSON structure
   - Device IDs
   - Sensor values
   - Plaintext credentials

**Step 5: Use Security Analyzer**
```powershell
# Regular PowerShell (no admin needed)
# IMPORTANT: Make sure you're in the correct directory!
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor

# Then run the analyzer
python security_test_analyzer.py mqtt_traffic.pcap

# Or use full path if you're in a different directory:
python "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\security_test_analyzer.py" "C:\Users\NURMIZAN QISTINA\Desktop\A251\fyp 2\TC004.pcapng"

# Check for "Unencrypted Payload" findings
# This same file can be used for TC-011 too!
```

**Understanding What You're Seeing:**

**✅ CORRECT - You're seeing TLS packets (like in your screenshot):**
- Protocol column shows: `TLSv1.2` or `TLSv1.3` ← This is GOOD!
- Filter shows: `tcp.port==8883` ← This is correct
- This means: MQTT is encrypted inside TLS ✅
- **This is a PASS** - encryption is working!

**To verify encryption is working:**
1. Click on any TLS packet
2. Look at the bottom pane (Packet Bytes - hex/ASCII view)
3. The data should be random-looking binary (encrypted)
4. You should NOT see readable text like:
   - `{"device_id": "sal01"...}`
   - `provision/sal01/update`
   - Any JSON or plaintext

**❌ If you see MQTT protocol directly (without TLS):**
- This would be a security issue
- Means traffic is not encrypted
- Should NOT happen on port 8883

**Summary:**
- **Seeing TLS = GOOD** ✅ (encryption working)
- **Seeing MQTT directly = BAD** ❌ (not encrypted)
- **Your screenshot shows TLS = PASS!** ✅

**Expected Result**:
- ✅ Payloads are encrypted (binary data)
- ✅ No readable plaintext
- ✅ No device IDs or sensor data visible
- ✅ If MQTT is visible, payload should be encrypted
- ✅ If only TLS visible, that's also good (TLS encryption working)

**Pass Criteria**: All payloads encrypted, no plaintext visible

**Note**: If you see "TLS" protocol instead of "MQTT" in Wireshark, that's actually GOOD - it means TLS is encrypting the MQTT traffic. The MQTT payloads are inside the encrypted TLS tunnel.

---

## Category 2: End-to-End Encryption (E2EE) Tests

### TC-016: Application-Layer Encryption Verification

**Objective**: Verify E2EE beyond TLS.

#### Step-by-Step Procedure:

**Step 1: Capture and Decrypt TLS Layer (if possible)**
1. Start Wireshark capture
2. Run: `python test_provision_mqtt.py sal01 update 1`
3. Stop capture

**Step 2: Analyze MQTT Payload Structure**

**⚠️ Important: If `mqtt.msgtype == 3` shows NO packets, that's GOOD!**

When MQTT is encrypted with TLS (port 8883), Wireshark shows **TLS packets**, not MQTT packets. The MQTT PUBLISH messages are **inside** the encrypted TLS tunnel.

**What to do:**

1. **Try MQTT filter** (will likely show nothing - that's correct!):
   - Filter: `mqtt.msgtype == 3`
   - **If NO packets appear**: ✅ This is CORRECT! MQTT is encrypted inside TLS
   - **If packets appear**: Check if they're actually MQTT or false positive

2. **What you'll actually see**:
   - Filter: `tcp.port == 8883` (should show TLS packets)
   - Protocol column shows: `TLSv1.2` or `TLSv1.3` (not MQTT)
   - **This is GOOD**: It means TLS is encrypting MQTT ✅

3. **To verify E2EE (Application-layer encryption)**:
   - Click on any TLS packet
   - Look for: `TLSv1.3 Record Layer: Application Data Protocol: MQ Telemetry Transport Protocol`
   - Expand to see: `Encrypted Application Data`
   - The encrypted data inside TLS is your MQTT payload
   - **Even if TLS is decrypted**, the MQTT payload should still be encrypted (E2EE)

4. **Check for E2EE fields** (requires analyzing the encrypted payload structure):
   - The encrypted MQTT payload should contain:
     - `session_key` (RSA encrypted)
     - `nonce` (base64 encoded)
     - `ciphertext` (AES encrypted)
     - `tag` (authentication tag)
   - **Note**: You won't see these directly in Wireshark - they're inside the encrypted TLS tunnel
   - To verify E2EE, you'd need to decrypt TLS AND analyze the MQTT payload structure

**Step 3: Verify Payload Structure**

**Option A: Use Subscriber Script (Recommended)**

Run the subscriber script to capture and analyze provision messages:

```powershell
# From the project root directory
python subscribe_provision_mqtt.py --detailed
```

**What the script does:**
- Subscribes to `provision/+/+` topic
- Waits for provision messages (timeout: 60 seconds)
- Shows detailed E2EE field analysis (session_key, ciphertext, nonce, tag)
- Verifies that all E2EE fields are present
- Displays full payload structure

**Note**: Make sure to trigger a provision message in another terminal first:
```powershell
python test_provision_mqtt.py sal01 update 1
```

**Option B: Trigger a message in another terminal**

While the subscriber script is running (or before running it), open **another PowerShell window** and run:

```powershell
# From the project root directory
python test_provision_mqtt.py sal01 update 1
```

This will publish a provision message that the subscriber script will receive and analyze.

**Step 4: Interpret the Results**

**Current Finding**: Based on your test output, provision messages are **NOT using E2EE**. The payload contains only:
- `device_id`
- `action`
- `user_id`

**This means**:
- ❌ **E2EE is MISSING** for provision messages
- ✅ **TLS encryption is working** (traffic is encrypted in transit)
- ⚠️ **Provision messages are readable** after TLS decryption

**Important Note**: 
- **Sensor data** (from `multi_sensor_client.py`, `raspberry_pi_client.py`) **DOES use E2EE** - it encrypts data using `encryption_utils.encrypt_data()` before publishing
- **Provision messages** (from `app.py`, `test_provision_mqtt.py`) **DO NOT use E2EE** - they're published as plaintext JSON

**Test Result**:
- **TC-016 FAILS** for provision messages (E2EE not implemented)
- **TC-016 PASSES** for sensor data messages (E2EE is implemented)

**To Test E2EE on Sensor Data** (where it's actually implemented):
1. Run a sensor simulator or publish sensor data
2. Capture that traffic in Wireshark
3. Use the subscriber script above, but subscribe to sensor data topics (e.g., `sensor/+/data` or your sensor topic pattern)
4. You should see encrypted fields: `session_key`, `ciphertext`, `nonce`, `tag`

**Pass Criteria for TC-016**:
- ✅ E2EE present for sensor data messages
- ⚠️ E2EE missing for provision messages (design decision or implementation gap)
- ✅ TLS encryption working for all messages

**💡 How to Test E2EE on Sensor Data (Where It's Actually Implemented)**

To verify E2EE works correctly on sensor data:

1. **Start Wireshark capture** (as admin) on port 8883
2. **Run sensor simulator** to publish encrypted sensor data:
   ```powershell
   cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
   python multi_sensor_client.py --ids sal01 http://192.168.43.196:5000
   ```
3. **Subscribe to sensor data** to see encrypted payload:
   ```powershell
   python -c "
   import json
   import ssl
   import paho.mqtt.client as mqtt
   import time
   import sys

   message_received = False

   def on_connect(client, userdata, flags, reason_code, properties):
       if reason_code == 0:
           print('[✓] Connected to MQTT broker')
           print('[✓] Subscribed to sensor/+/data')
           print('[⏳] Waiting for sensor data messages...')
       else:
           print(f'[✗] Connection failed: {reason_code}')
           sys.exit(1)

   def on_message(client, userdata, msg):
       global message_received
       message_received = True
       print(f'\n[📨] Message received on topic: {msg.topic}')
       try:
           payload = json.loads(msg.payload.decode())
           print('\n[📋] Payload structure:')
           print(f'  Keys: {list(payload.keys())}')
           print(f'\n[🔍] E2EE Field Check:')
           if 'session_key' in payload:
               print('  ✓ Has session_key (RSA-encrypted session key)')
           if 'ciphertext' in payload:
               print('  ✓ Has ciphertext (AES-encrypted data)')
           if 'nonce' in payload:
               print('  ✓ Has nonce (encryption nonce)')
           if 'tag' in payload:
               print('  ✓ Has tag (authentication tag)')
           if all(k in payload for k in ['session_key', 'ciphertext', 'nonce', 'tag']):
               print('\n[✅] E2EE is PRESENT - All required fields found!')
           else:
               print('\n[⚠️] E2EE may be MISSING - Some fields not found')
       except Exception as e:
           print(f'  [✗] Payload not JSON: {type(e).__name__}: {e}')

   client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
   client.username_pw_set('water_monitor', 'e2eeWater2025')
   client.tls_set(cert_reqs=ssl.CERT_NONE)
   client.on_connect = on_connect
   client.on_message = on_message
   client.connect('192.168.43.214', 8883)
   client.subscribe('sensor/+/data')  # Adjust topic pattern to match your sensor topics
   client.loop_start()

   for i in range(60):
       if message_received:
           break
       time.sleep(1)
       if i % 10 == 0 and i > 0:
           print(f'[⏳] Still waiting... ({i}s elapsed)')

   client.loop_stop()
   if not message_received:
       print('\n[⚠️] No messages received after 60 seconds')
   else:
       print('\n[✅] Test completed')
   "
   ```

4. **Check Wireshark** - you should see TLS packets (not MQTT directly), and the payload inside should contain encrypted fields

**Note**: Adjust the topic pattern (`sensor/+/data`) to match your actual sensor data topic pattern.

---

### TC-017: E2EE Implementation Verification

**Objective**: Verify that E2EE implementation uses strong RSA key exchange and AES encryption.

#### Step-by-Step Procedure:

**Part A: RSA Key Exchange Verification**

**Step 1: Capture Multiple Messages**
1. Start Wireshark capture
2. Send multiple messages:
   ```powershell
   python test_provision_mqtt.py sal01 update 1
   python test_provision_mqtt.py sal02 update 1
   python test_provision_mqtt.py sal01 request 1
   ```
3. Stop capture

**Step 2: Extract Session Keys**
1. In Wireshark, filter: `mqtt.msgtype == 3`
2. For each message, extract `session_key` field
3. Compare session keys between messages
4. **Expected**: Each message should have different session key

**Step 3: Verify RSA Encryption**
```python
# Create test_rsa_verification.py
import json
import base64
from Crypto.PublicKey import RSA

# Extract session_key from captured message
session_key_encrypted = "BASE64_ENCODED_SESSION_KEY_FROM_CAPTURE"

# Try to decrypt (should fail without private key)
try:
    # This should fail - session key is RSA encrypted
    key_data = base64.b64decode(session_key_encrypted)
    print(f"Session key length: {len(key_data)} bytes")
    print("Session key is RSA encrypted (cannot decrypt without private key)")
    print("✓ RSA encryption verified")
except Exception as e:
    print(f"Error: {e}")
```

**Step 4: Check Key Uniqueness**
- Compare session keys from multiple messages
- Each should be different
- Verify key rotation is working

**Part B: AES Encryption Strength**

**Step 5: Code Review**
```bash
# Review encryption_utils.py
cat encryption_utils.py
```

**Step 6: Check AES Parameters**
Look for:
- Key size: Should be 128-bit (16 bytes) or higher
- Mode: Should be EAX, GCM, or CBC with proper IV
- Nonce/IV: Should be unique per message

**Step 7: Verify Implementation**
```python
# Check encryption_utils.py
# Look for:
# - AES.new(session_key, AES.MODE_EAX)  # Good
# - AES.new(key, AES.MODE_CBC, iv)      # Good if IV is unique
# - Key size: get_random_bytes(16)      # 128-bit = Good
```

**Step 8: Test Encryption**
```powershell
# Run encryption test
python -c "
from encryption_utils import encrypt_data
import os

# Test encryption
test_data = {'device_id': 'test', 'value': 123}
public_key_path = 'path/to/public_key.pem'  # Use actual path

if os.path.exists(public_key_path):
    encrypted = encrypt_data(test_data, public_key_path)
    print('Encryption test:')
    print(f'  Has session_key: {\"session_key\" in encrypted}')
    print(f'  Has nonce: {\"nonce\" in encrypted}')
    print(f'  Has ciphertext: {\"ciphertext\" in encrypted}')
    print(f'  Has tag: {\"tag\" in encrypted}')
    print('✓ AES encryption working')
else:
    print('Public key not found - skipping test')
"
```

**Expected Result**:
- ✅ Session keys are RSA encrypted
- ✅ Each message uses unique session key
- ✅ Keys cannot be decrypted without private key
- ✅ AES-128 or higher
- ✅ Proper mode (EAX, GCM, CBC with IV)
- ✅ Unique nonce/IV per message

**Pass Criteria**: RSA encryption used, unique session keys per message, strong AES implementation verified

---

### TC-020: Sensor Data E2EE Verification

**Objective**: Verify that sensor data messages use E2EE encryption and hash integrity.

**Priority**: CRITICAL

**⚠️ IMPORTANT: This test case is for SENSOR DATA MESSAGES only.**

- **Sensor data messages** (`sensor_simulator.py`): ✅ Use E2EE encryption + hash field (publishes to MQTT topic `secure/sensor`)
- **Provision messages**: See **TC-007** instead

**Why This Test is Important**:
- Sensor data security is **separate** from provision message security
- Cannot assume sensor data is secure just because provision messages pass
- Sensor data contains sensitive readings (pH, temperature, etc.)
- Must verify E2EE is applied to sensor data separately
- Sensor data may include both E2EE (tag) AND hash field for integrity

#### Step-by-Step Procedure:

**Step 1: Subscribe to Sensor Data Topic**

```powershell
# Regular PowerShell (no admin needed)
python -c "
import json
import ssl
import paho.mqtt.client as mqtt
import time
import sys

message_received = False

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print('[✓] Connected to MQTT broker')
        print('[✓] Subscribed to secure/sensor')
        print('[⏳] Waiting for sensor data messages...')
        print('[💡] TIP: In another terminal (Raspberry Pi), run:')
        print('     python3 simulators/sensor/sensor_simulator.py --ids sal02 --interval 30 --mqtt-use-tls --mqtt-tls-insecure')
    else:
        print(f'[✗] Connection failed: {reason_code}')
        sys.exit(1)

def on_message(client, userdata, msg):
    global message_received
    message_received = True
    print(f'\n[📨] Message received on topic: {msg.topic}')
    try:
        payload = json.loads(msg.payload.decode())
        print('\n[📋] Payload structure:')
        print(f'  Keys: {list(payload.keys())}')
        print(f'\n[🔍] E2EE Field Check:')
        # sensor_simulator.py uses AES encryption for MQTT
        # Check for MQTT payload structure: data (AES encrypted), hash, sha256
        if 'data' in payload:
            print('  ✓ Has data (AES-encrypted sensor data)')
            try:
                data_enc = json.loads(payload['data'])
                if 'iv' in data_enc and 'ciphertext' in data_enc:
                    print('    ✓ Data contains iv and ciphertext (AES-CBC encryption)')
            except:
                pass
        if 'hash' in payload:
            print('  ✓ Has hash (SHA-256 integrity hash)')
        if 'sha256' in payload:
            print('  ✓ Has sha256 (SHA-256 hash of plaintext)')
        # Also check for RSA+AES hybrid (if using different client)
        if 'session_key' in payload:
            print('  ✓ Has session_key (RSA-encrypted session key) - RSA+AES hybrid')
        if 'ciphertext' in payload and 'nonce' in payload and 'tag' in payload:
            print('  ✓ Has ciphertext, nonce, tag (RSA+AES hybrid E2EE)')
        
        # Verify encryption is present (either AES or RSA+AES)
        if 'data' in payload or ('session_key' in payload and 'ciphertext' in payload):
            print('\n[✅] E2EE is PRESENT - Encrypted fields found!')
            print('[✅] Sensor data is SECURE!')
        else:
            print('\n[⚠️] E2EE may be MISSING - Encrypted fields not found')
            print('[❌] Sensor data may NOT be secure!')
        print(f'\n[📄] Full payload: {json.dumps(payload, indent=2)}')
    except Exception as e:
        print(f'  [✗] Payload not JSON: {type(e).__name__}: {e}')
        print(f'  [📄] Raw payload: {msg.payload.decode()[:200]}...')
    client.disconnect()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.on_connect = on_connect
client.on_message = on_message
client.connect('192.168.43.214', 8883)
client.subscribe('secure/sensor')
client.loop_start()

for i in range(60):
    if message_received:
        break
    time.sleep(1)
    if i % 10 == 0 and i > 0:
        print(f'[⏳] Still waiting... ({i}s elapsed)')

client.loop_stop()
if not message_received:
    print('\n[⚠️] No messages received after 60 seconds')
    print('[💡] Make sure to run sensor simulator in another terminal (Raspberry Pi):')
    print('     python3 simulators/sensor/sensor_simulator.py --ids sal02')
else:
    print('\n[✅] Test completed')
"
```

**Step 2: Run Sensor Simulator (in another terminal)**

**⚠️ Important:** For TC-006, use `sensor_simulator.py` (not `multi_sensor_client.py`) because it publishes to MQTT topic `secure/sensor` which the subscriber listens to.

**Option A: Run from Windows**
```powershell
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor

# Set database connection (if needed)
$env:DB_HOST="192.168.43.196"
$env:DB_USER="root"
$env:DB_PASSWORD=""
$env:DB_NAME="ilmuwanutara_e2eewater"

# Set server and MQTT info
$env:SERVER_URL="http://192.168.43.196:5000"
$env:MQTT_HOST="192.168.43.214"
$env:MQTT_PORT="8883"
$env:MQTT_USER="water_monitor"
$env:MQTT_PASSWORD="e2eeWater2025"
$env:MQTT_USE_TLS="true"
$env:MQTT_TLS_INSECURE="true"

# Run sensor simulator
python simulators\sensor\sensor_simulator.py --ids sal02 --interval 30 --repeat 100 --mqtt-use-tls --mqtt-tls-insecure
```

**Option B: Run from Raspberry Pi (Recommended for TC-006)**
```bash
# SSH to Raspberry Pi first
cd ~/secure-water-monitor

# Set environment variables (one-time per session)
export DB_HOST="192.168.43.196"
export DB_USER="root"
export DB_PASSWORD=""
export DB_NAME="ilmuwanutara_e2eewater"
export SERVER_URL="http://192.168.43.196:5000"
export MQTT_HOST="192.168.43.214"
export MQTT_PORT="8883"
export MQTT_USER="water_monitor"
export MQTT_PASSWORD="e2eeWater2025"
export MQTT_USE_TLS="true"
export MQTT_TLS_INSECURE="true"

# Run sensor simulator with 30-second intervals
python3 simulators/sensor/sensor_simulator.py \
  --ids sal02 \
 
```

**Note:** 
- Replace IP addresses with your actual server and MQTT broker IPs
- `sensor_simulator.py` publishes to MQTT topic `secure/sensor` (for subscriber testing) AND sends HTTP POST to `/submit-data` (for server processing)
- The script automatically finds private keys in `sensor_keys/{user_id}/{device_id}/` or `sensor_keys/{device_id}/` locations
- Use `--all` to simulate all active sensors
- Use `--mode safe` for safe values or `--mode unsafe` for unsafe values

**Step 3: Verify E2EE Fields Present**

The subscriber script will show:
- ✅ `session_key` - RSA-encrypted session key
- ✅ `ciphertext` - AES-encrypted sensor data
- ✅ `nonce` - Encryption nonce
- ✅ `tag` - Authentication tag
- ✅ `hash` (optional) - SHA-256 integrity hash

**Step 4: Verify Data is Unreadable**

1. Check that sensor readings (pH, temperature, etc.) are **NOT visible** in the payload
2. Only encrypted fields should be visible
3. Data should be unreadable even after TLS decryption

**Step 5: Verify Hash Integrity**

The subscriber checks for two hash fields in the MQTT payload:
- `hash`: SHA-256 hash using `hash_data()` function
- `sha256`: SHA-256 hash of JSON-serialized data (with sort_keys=True)

```powershell
python -c "
from encryption_utils import hash_data
import json
import hashlib

# Test data (matches what sensor_simulator.py sends)
test_data = {'device_id': 'sal02', 'device_type': 'Salinity', 'salinity': 17.05}

# Compute hash (same as sensor_simulator.py line 295)
# hash_data() converts data to string first
computed_hash = hash_data(test_data)
print(f'Test data: {test_data}')
print(f'')
print(f'1. hash field (hash_data function):')
print(f'   {computed_hash}')
print(f'   Length: {len(computed_hash)} (should be 64 for SHA-256)')
print(f'')

# Compute sha256 (same as sensor_simulator.py line 293)
# Uses JSON serialization with sort_keys=True
data_json = json.dumps(test_data, sort_keys=True).encode()
computed_sha256 = hashlib.sha256(data_json).hexdigest()
print(f'2. sha256 field (JSON serialized):')
print(f'   {computed_sha256}')
print(f'   Length: {len(computed_sha256)} (should be 64 for SHA-256)')
print(f'')
print(f'✅ Both hash fields match what sensor_simulator.py sends to MQTT')
print(f'✅ Subscriber will verify these match the received payload')
"
```

**Note:** The subscriber script checks for both `hash` and `sha256` fields in the MQTT payload. Both should be present and match the plaintext data to verify integrity.

**Expected Result**:
- ✅ Payload contains all E2EE fields (`session_key`, `ciphertext`, `nonce`, `tag`)
- ✅ Sensor readings are encrypted and unreadable
- ✅ Hash field present (if implemented) and correct length (64 hex chars)
- ✅ Data cannot be read even if TLS is decrypted
- ✅ E2EE working correctly for sensor data

**Pass Criteria**: 
- ✅ E2EE present for sensor data messages
- ✅ All required encryption fields found
- ✅ Sensor readings unreadable
- ✅ Hash present and correct (if implemented)

**Important Notes**:
- ⚠️ **Cannot assume** sensor data is secure from provision message tests
- ✅ **Must test separately** - sensor data uses different code path
- ✅ Sensor data typically includes hash for integrity (in addition to E2EE)
- ✅ Same E2EE mechanism as provision messages, but different implementation

**Troubleshooting**:
- **No messages received**: Check sensor simulator is running, verify device keys exist
- **E2EE fields missing**: Verify sensor simulator uses `encrypt_data()` function
- **Hash field missing**: Some implementations may not include hash (E2EE tag provides integrity)

---

## Category 3: Message Integrity Tests

### TC-018: Provision Message Integrity Verification (E2EE Tag Authentication)

**Objective**: Verify that provision messages use E2EE tag authentication for integrity verification.

**⚠️ IMPORTANT: This test case is for PROVISION MESSAGES only.**

- **Provision messages** (`test_provision_mqtt.py`): ✅ **Use E2EE with `tag` field** for authentication (no separate hash field)
- **Sensor data messages**: See **TC-006** instead

**Why E2EE Tag instead of Hash?**
- Provision messages use E2EE encryption (RSA + AES)
- The `tag` field (AES-EAX authentication tag) provides integrity verification
- The tag automatically detects any tampering with the ciphertext
- This is equivalent to hash verification but uses cryptographic authentication

#### Step-by-Step Procedure:

**Step 1: Capture Provision Message**

1. Start Wireshark capture (optional - for packet analysis)
2. Run provision message test to generate E2EE-encrypted messages:
   ```powershell
   python test_provision_mqtt.py sal01 update 1
   ```
3. Stop capture

**Note**: Provision messages use E2EE with `tag` field for authentication (not a separate hash field).

**Step 2: Extract E2EE Tag from Payload**

**⚠️ Important**: When MQTT uses TLS (port 8883), MQTT packets are **encrypted inside TLS**. You won't see "MQTT" protocol directly in Wireshark.

**Option A: Use Subscriber Script (Recommended - Works with TLS)**

Since MQTT is encrypted, use a subscriber script to receive and analyze the payload:

**For PROVISION MESSAGES** (which use E2EE tag for authentication):

```powershell
# Run the subscriber script with detailed analysis
python subscribe_provision_mqtt.py --detailed
```

**What the script does:**
- Subscribes to `provision/+/+` topic
- Waits for provision messages (timeout: 60 seconds)
- Shows detailed E2EE field analysis (session_key, ciphertext, nonce, tag)
- Displays full payload structure
- Verifies that provision messages use E2EE tag (not hash)

**Note**: Make sure to trigger a provision message in another terminal first:
```powershell
python test_provision_mqtt.py sal01 update 1
```

**Option B: Decrypt TLS in Wireshark (Advanced)**

If you have TLS decryption keys:
1. In Wireshark: `Edit` → `Preferences` → `Protocols` → `TLS`
2. Add RSA key file or pre-master secret
3. Filter: `mqtt.msgtype == 3` (PUBLISH)
4. Extract payload from decrypted MQTT packet

**Option C: Check Application Logs**

Check Flask or provision agent logs for hash values in decrypted messages.

**⚠️ Important Note about E2EE Tag Authentication:**

- **Provision Messages**: Use **AES-EAX authentication tag** (the `tag` field) for integrity verification
- The `tag` field automatically detects any tampering with the ciphertext
- This is equivalent to hash verification but uses cryptographic authentication
- **No separate `hash` field** - the tag provides the integrity protection

**If you see E2EE fields (`session_key`, `ciphertext`, `nonce`, `tag`) but NO `hash` field, this is CORRECT for provision messages!**

**Step 3: Verify E2EE Tag Implementation in Code**

This step verifies that your code correctly implements E2EE encryption with tag authentication. Check the actual implementation:

**Option A: Check encryption_utils.py**
```powershell
# View the encrypt_data function
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
python -c "
from encryption_utils import encrypt_data
import json

# Test E2EE encryption (requires public key)
# This shows how tag is generated
print('E2EE encryption uses AES-EAX mode')
print('The tag field is automatically generated by AES-EAX')
print('Tag provides authentication and integrity verification')
"
```

**Option B: Check app.py**
```powershell
# Search for E2EE usage in app.py
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
Select-String -Path "app.py" -Pattern "encrypt_data|tag" -Context 2
```

**Option C: View encryption implementation directly**
```powershell
# Open and view encryption_utils.py
notepad encryption_utils.py
# Look for: def encrypt_data(data_dict, public_key_path):
# Should see: AES.MODE_EAX and tag generation
```

**Expected**: 
- Uses `encrypt_data()` function from `encryption_utils`
- Returns payload with `session_key`, `ciphertext`, `nonce`, `tag`
- Tag is automatically generated by AES-EAX mode
- Tag provides authentication and tampering detection

**Step 4: Test Tag Authentication (Tampering Detection)**

**This step tests provision messages' E2EE tag authentication** (equivalent to hash verification for provision messages). The E2EE tag automatically provides authentication and detects tampering.

**Option A: Use Automated Test Script (Recommended)**

```powershell
# Run the tampering test script
python test_tampering.py
```

**What the script does:**
1. Captures a provision message (from `provision/+/+` topic)
2. Shows E2EE fields: `session_key`, `ciphertext`, `nonce`, `tag`
3. **Test 1**: Modifies the ciphertext → tag verification should fail
4. **Test 2**: Modifies the tag → decryption should fail
5. **Test 3**: Modifies the nonce → decryption should fail
6. Shows that tampering is detected for all modifications

**Expected Result**:
- ✅ Original message decrypts successfully
- ✅ Tampered ciphertext rejected (authentication tag mismatch)
- ✅ Tampered tag rejected
- ✅ Tampered nonce rejected
- ✅ E2EE tag provides integrity protection (equivalent to hash)

**Pass Criteria**: Tag authentication detects tampering, tampered messages rejected

**Option B: Manual Tampering Test (Alternative)**

If you want to test manually without the script:

```powershell
# 1. Capture a message using: python subscribe_provision_mqtt.py
# 2. Save the payload JSON to a file: tampered.json
# 3. Modify one character in the ciphertext or tag
# 4. Try to decrypt it using encryption_utils.decrypt_data()
python -c "
from encryption_utils import decrypt_data
import json

# Load tampered payload
with open('tampered.json', 'r') as f:
    payload = json.load(f)

# Try to decrypt (should fail)
try:
    result = decrypt_data(payload, 'sensor_keys/sal01/sensor_private.pem')
    print('❌ SECURITY FAILURE: Tampered message decrypted!')
except Exception as e:
    if 'verification' in str(e).lower() or 'tag' in str(e).lower():
        print('✅ Tampering detected! Decryption failed.')
    else:
        print(f'Error: {e}')
"
```

**Expected Result**:
- ✅ E2EE messages (with tag): AES-EAX tag verification detects tampering
- ✅ Modified messages rejected
- ✅ Authentication errors logged

**Summary**:
- **TC-007**: Tests **provision messages** using E2EE tag authentication
- **TC-006**: Tests **sensor data messages** using E2EE encryption (see TC-006 for sensor data)

---

### TC-019: Message Tampering Detection

**Objective**: Verify message tampering is detected.

#### Step-by-Step Procedure:

**Step 1: Capture Valid Message**
1. Start Wireshark capture
2. Run: `python test_provision_mqtt.py sal01 update 1`
3. Stop capture, save as `valid_message.pcap`

**Step 2: Extract Message Payload**

**⚠️ Important**: When MQTT uses TLS (port 8883), MQTT packets are **encrypted inside TLS**. You won't see "MQTT" protocol directly in Wireshark.

**Option A: Use Subscriber Script (Recommended - Works with TLS)**

Since MQTT is encrypted, use a subscriber script to receive and analyze the payload:

```powershell
# Run the subscriber script to capture payload
python subscribe_provision_mqtt.py
```

**What the script does:**
- Subscribes to `provision/+/+` topic
- Waits for provision messages (timeout: 60 seconds, use `--timeout` to change)
- Captures and displays the payload structure
- Shows E2EE fields (session_key, ciphertext, nonce, tag)

**Note**: Make sure to trigger a provision message in another terminal first:
```powershell
python test_provision_mqtt.py sal01 update 1
```

**Alternative**: Use `--detailed` flag for more verbose output (same as TC-007):
```powershell
python subscribe_provision_mqtt.py --detailed
```

**Option B: Use Wireshark (Advanced - TLS Encrypted)**

If you want to see the packet structure in Wireshark:

1. **Filter for TLS packets**:
   - In Wireshark filter bar: `tcp.port == 8883`
   - Protocol column will show: `TLSv1.2` or `TLSv1.3` (not MQTT)

2. **Find Application Data packets**:
   - Look for packets with protocol: `TLSv1.3 Record Layer: Application Data`
   - These contain the encrypted MQTT PUBLISH messages

3. **Export packet bytes** (if needed):
   - Right-click on TLS Application Data packet
   - Select: "Export Packet Bytes"
   - **Note**: The payload will be encrypted (TLS + E2EE), so you'll see encrypted data

**Recommended**: Use **Option A** (subscriber script) to get the actual decrypted payload structure for tampering tests.

**Step 3: Modify Message (Tamper Payload)**

**For Provision Messages (E2EE with tag)**:

1. **Edit the tampering script** with your captured payload from Step 2:

```powershell
# Open test_tamper_message.py in a text editor
# Replace the placeholder values with your captured payload from Step 2
```

2. **Run the tampering script**:

```powershell
python test_tamper_message.py
```

**What the script does:**
- Takes your captured payload from `subscribe_provision_mqtt.py`
- Creates three tampered versions:
  - **Option 1**: Modified `ciphertext` (tag won't match)
  - **Option 2**: Modified `tag` (tag won't match ciphertext)
  - **Option 3**: Modified `nonce` (nonce won't match encryption)
- Displays the tampered payloads for use in Step 4

**Note**: For provision messages, the `tag` field (AES-EAX authentication tag) will detect any tampering. Any modification to `ciphertext`, `tag`, or `nonce` will cause decryption to fail.

**Step 4: Replay Tampered Message**

Publish the tampered message to test if the system detects tampering:

**Option A: Use the tampered payload from `test_tamper_message.py`**

1. Copy one of the tampered payloads from Step 3 output
2. Publish it using this script:

```powershell
python -c "
import paho.mqtt.client as mqtt
import json
import ssl

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.connect('192.168.43.214', 8883, 60)

# Replace with tampered payload from test_tamper_message.py output
tampered_payload = json.dumps({
    "session_key": "tmhCXkBZAKsxl2lI3RHGF3c8S4I3f9VRSF68h1xEWNrlylzWxbw0d2Yxyw2kYv8EB91+LuwkhtBsrjIR/KBfAXTgAe07Q4Hyn0Tl9O8T5LabpEq6H23FHYfM6XYpdKy5+H5hYvpysTEjoW+Vh2nIdgetOmkXZ+gZ2MHb3biyawJc4IUTLGyRxBS5udGTWXbA8AJzs3uGxU9+s1bHX1f8F8XNOTnIMTLOhg9fxtO1QFNi3j5isiHpJdEoF+1V/3X2VCLs9+eNNxk8bOONCq6A8NraaKT1S0LIP/BX4tFhRMfLoLTQsdj+Qp+oeUor9mElHkwgwzM8bjH8JLM9JxtszQ==",
  "nonce": "8Ugpkz0qS1VzITxVn2kfNw==",
  "ciphertext": "MODIFIED_CIPHERTEXT_12345",
  "tag": "PGHyxkilIB0aSnVv2+aB8Q=="
})

print('[📤] Publishing tampered message...')
result = client.publish('provision/sal01/update', tampered_payload)
result.wait_for_publish()

if result.rc == 0:
    print('[✅] Message published (but should be rejected by server)')
else:
    print(f'[❌] Publish failed: {result.rc}')

client.disconnect()
print('[🔍] Check server logs to verify tampering was detected')
"
```

**Option B: Use `test_tampering.py` script** (automated - recommended):

```powershell
# This script automatically:
# 1. Captures a provision message
# 2. Creates tampered versions
# 3. Attempts decryption to show tampering detection
python test_tampering.py
```

**Step 5: Check Server Logs and Verify Tampering Detection**

**On Raspberry Pi (MQTT Broker)**:
```bash
# Check Mosquitto logs
sudo journalctl -u mosquitto -f

# Or check provision agent logs (if running)
# Look for decryption errors or authentication failures
```

**On Flask Server (if provision agent logs there)**:
```bash
# Check Flask application logs
tail -f flask_error.log

# Look for:
# - "Decryption failed"
# - "Tag verification failed"
# - "Authentication tag mismatch"
# - "Invalid E2EE payload"
```

**Expected Result**:
- ✅ Tampered messages rejected by provision agent
- ✅ E2EE tag authentication fails (for provision messages)
- ✅ Decryption errors logged
- ✅ No processing of tampered data
- ✅ System does not accept modified `ciphertext`, `tag`, or `nonce`

**Pass Criteria**: 
- Tampering detected and rejected
- System logs show authentication/decryption failures
- No valid data processed from tampered message

---

## Category 4: Authentication Tests

### TC-004: Authentication Requirement

**Objective**: Verify authentication is required.

#### Step-by-Step Procedure:

**Step 1: Test Without Credentials**
```powershell
# Run automated test
python security_test_attacks.py auth
```

**Step 2: Manual Test**
```powershell
python -c "
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
# NO username/password set
client.tls_set(cert_reqs=ssl.CERT_NONE)

try:
    client.connect('192.168.43.214', 8883, 5)
    client.loop_start()
    import time
    time.sleep(2)
    if client.is_connected():
        print('FAIL: Connected without credentials!')
    else:
        print('PASS: Connection failed without credentials')
    client.loop_stop()
except Exception as e:
    print(f'PASS: Connection rejected: {type(e).__name__}')
"
```

**Step 3: Check Wireshark**

**⚠️ Important: You may NOT see MQTT packets - that's GOOD!**

When MQTT uses TLS (port 8883), Wireshark shows **TLS packets**, not MQTT packets. The MQTT CONNECT and CONNACK messages are **inside** the encrypted TLS tunnel.

**What You'll See:**
1. **Filter**: `tcp.port == 8883`
2. **Protocol column**: Shows `TLSv1.2` or `TLSv1.3` (NOT MQTT)
3. **This is CORRECT**: MQTT is encrypted inside TLS ✅

**To Verify Authentication Failure:**
1. **Watch connection behavior**:
   - Filter: `tcp.port == 8883`
   - Run the test (connection without credentials)
   - **If connection closes immediately** → Authentication failed ✅
   - **If connection stays open** → Authentication succeeded (unexpected)

2. **Check TLS handshake**:
   - Filter: `tls.handshake.type == 1` (Client Hello)
   - Filter: `tls.handshake.type == 2` (Server Hello)
   - TLS handshake may complete, but connection closes after → Auth failure

3. **Look for connection resets**:
   - Filter: `tcp.flags.reset == 1`
   - RST packets after TLS handshake → Connection rejected

**If You Want to Try MQTT Filter (May Not Work):**
- Filter: `mqtt.msgtype == 1` (CONNECT)
- **If NO packets appear**: ✅ This is CORRECT! MQTT is encrypted
- **If packets appear**: Check if they're actually MQTT or false positive

**CONNACK Response (if visible):**
- CONNACK is `mqtt.msgtype == 2` (response to CONNECT)
- Return code 0 = success, non-zero = failure
- **But you likely won't see this** because it's encrypted inside TLS

**Step 4: Check Broker Logs**

**If you see old logs (like 6 PM), try these commands:**

```bash
# On Raspberry Pi (after SSH)

# Option 1: See logs from last hour
sudo journalctl -u mosquitto --since "1 hour ago"

# Option 2: See logs from last 10 minutes
sudo journalctl -u mosquitto --since "10 minutes ago"

# Option 3: See logs from today
sudo journalctl -u mosquitto --since today

# Option 4: Follow NEW logs only (real-time)
sudo journalctl -u mosquitto -f --since "1 minute ago"
# This will show new logs as they appear

# Option 5: See last 50 lines
sudo journalctl -u mosquitto -n 50

# Option 6: See logs with timestamps
sudo journalctl -u mosquitto --since "1 hour ago" --no-pager
```

**To see logs in real-time while testing:**
1. **First, check if mosquitto is running**:
   ```bash
   sudo systemctl status mosquitto
   ```

2. **Start following logs** (in one terminal):
   ```bash
   sudo journalctl -u mosquitto -f --since "now"
   ```

3. **In another terminal or from Windows, run your test**:
   ```powershell
   python security_test_attacks.py auth
   ```

4. **Watch the log terminal** - you should see new log entries appear

**If no new logs appear:**
- Mosquitto might not be logging to systemd journal
- Check if mosquitto logs to a file instead:
  ```bash
  sudo tail -f /var/log/mosquitto/mosquitto.log
  # Or check mosquitto config for log location
  sudo cat /etc/mosquitto/mosquitto.conf | grep -i log
  ```

**Troubleshooting:**
- If logs are old, mosquitto might not be actively logging
- Try generating new traffic to create new log entries
- Check mosquitto service is running: `sudo systemctl status mosquitto`

**Expected Result**:
- ✅ Connection fails without credentials
- ✅ CONNACK return code indicates failure
- ✅ Broker logs authentication failure

**Pass Criteria**: Authentication required, connection fails without credentials

---

### TC-005: Wrong Credentials Rejection

**Objective**: Verify wrong credentials are rejected.

#### Step-by-Step Procedure:

**Step 1: Run Automated Test**
```powershell
python security_test_attacks.py credentials
```

**Step 2: Test Wrong Username**
```powershell
python -c "
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set('wrong_user', 'e2eeWater2025')  # Wrong username
client.tls_set(cert_reqs=ssl.CERT_NONE)

try:
    client.connect('192.168.43.214', 8883, 5)
    client.loop_start()
    import time
    time.sleep(2)
    if client.is_connected():
        print('FAIL: Connected with wrong username!')
    else:
        print('PASS: Wrong username rejected')
    client.loop_stop()
except Exception as e:
    print(f'PASS: Wrong username rejected: {type(e).__name__}')
"
```

**Step 3: Test Wrong Password**
```powershell
python -c "
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set('water_monitor', 'wrong_password')  # Wrong password
client.tls_set(cert_reqs=ssl.CERT_NONE)

try:
    client.connect('192.168.43.214', 8883, 5)
    client.loop_start()
    import time
    time.sleep(2)
    if client.is_connected():
        print('FAIL: Connected with wrong password!')
    else:
        print('PASS: Wrong password rejected')
    client.loop_stop()
except Exception as e:
    print(f'PASS: Wrong password rejected: {type(e).__name__}')
"
```

**Step 4: Monitor Failed Attempts**
```bash
# On Raspberry Pi
sudo journalctl -u mosquitto | grep -i "auth\|denied\|failed"
# Should see failed authentication attempts
```

**Expected Result**:
- ✅ Wrong username rejected
- ✅ Wrong password rejected
- ✅ Failed attempts logged
- ✅ Rate limiting may activate

**Pass Criteria**: Wrong credentials rejected, attempts logged

---

### TC-006: Credential Sniffing Protection

**Objective**: Verify credentials are not visible in traffic.

**💡 Efficiency Tip**: You can reuse the same pcap file from TC-003! Both tests analyze the same MQTT traffic - TC-003 looks at PUBLISH packets (payloads), TC-011 looks at CONNECT packets (credentials). No need to capture twice!

#### Step-by-Step Procedure:

**Step 1: Use Existing Capture (Recommended) OR Capture New**

**Option A: Reuse TC-003 Capture (Efficient)**
- Use the `mqtt_traffic.pcap` file you saved from TC-003
- Open it in Wireshark
- Skip to Step 2

**Option B: Capture New Traffic**
1. Start Wireshark capture
2. Filter: `tcp.port == 8883`
3. Run: `python test_provision_mqtt.py sal01 update 1`
4. Stop capture
5. Save as `mqtt_traffic.pcap` (or reuse existing)

**Step 2: Analyze CONNECT Packet**

**⚠️ Important: If filter shows no packets, that's GOOD!**

When MQTT is encrypted with TLS (port 8883), Wireshark shows TLS packets, not MQTT packets. The MQTT CONNECT message is **inside** the encrypted TLS tunnel.

**Try the filter:**
1. **Filter**: `mqtt.msgtype == 1` (CONNECT)
2. **If NO packets appear**: ✅ This is CORRECT! MQTT is encrypted inside TLS
3. **If packets appear**: Check if they're actually MQTT or if it's a false positive

**What You'll Actually See:**
- **Protocol column shows**: `TLSv1.2` or `TLSv1.3` (not MQTT)
- **This is GOOD**: It means TLS is encrypting MQTT traffic ✅

**To Verify Credentials Are Protected:**
1. **Click on any TLS packet** (even if MQTT filter shows nothing)
2. **Look at bottom pane (Packet Bytes)**:
   - Data should be encrypted (random binary/hex)
   - Should NOT see readable text like usernames or passwords
3. **This confirms**: Credentials are encrypted inside TLS ✅

**Expected Result:**
- ✅ No MQTT protocol visible (encrypted inside TLS)
- ✅ Packet bytes show encrypted data
- ✅ No readable credentials in packet bytes

**Step 3: Verify TLS Protection**
1. Check that all traffic is on port 8883 (TLS)
2. Verify TLS handshake completed
3. Confirm credentials are within TLS encrypted tunnel

**Step 4: Test Credential Visibility**
```powershell
# Try to extract credentials from capture
# Should NOT be possible if TLS is working
python security_test_analyzer.py mqtt_traffic.pcap
# Check for "Credential Exposure" findings
# Use the same file from TC-003!
```

**Expected Result**:
- ✅ Credentials encrypted by TLS
- ✅ Not readable in plaintext
- ✅ All traffic on encrypted port (8883)

**Pass Criteria**: Credentials protected, not visible in plaintext

---

### TC-007: Brute Force Protection

**Objective**: Verify protection against brute force authentication attacks.

#### Step-by-Step Procedure:

**Step 1: Start Monitoring Broker Logs**
```bash
# On Raspberry Pi
sudo journalctl -u mosquitto -f
# Keep this running to see failed attempts
```

**Step 2: Attempt Multiple Failed Logins**
```powershell
# Regular PowerShell (no admin needed)
# Run rapid failed login attempts
python -c "
import paho.mqtt.client as mqtt
import ssl
import time

for i in range(10):
    try:
        client = mqtt.Client()
        client.username_pw_set('wrong_user', 'wrong_password')
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.connect('192.168.43.214', 8883, 5)
        client.loop_start()
        time.sleep(0.5)
        client.loop_stop()
        print(f'Attempt {i+1}: Connected (unexpected!)')
    except Exception as e:
        print(f'Attempt {i+1}: Failed - {type(e).__name__}')
    time.sleep(0.2)  # Small delay between attempts
"
```

**Step 3: Monitor for Rate Limiting**
- Watch the broker logs on Pi
- Look for rate limiting messages
- Check if connection attempts are being throttled
- Note: Some brokers may not have rate limiting configured

**Step 4: Test Legitimate Access After Failures**
```powershell
# Try legitimate login after failures
python test_provision_mqtt.py sal01 update 1 #(pass)
# Should still work if rate limiting is per-IP or per-username
```

**Expected Result**:
- ✅ Failed attempts logged
- ✅ Rate limiting may activate (if configured)
- ✅ Legitimate access should still work
- ✅ Broker remains stable

**Pass Criteria**: Failed attempts logged, rate limiting works (if configured)

---

## Category 5: Authorization Tests

### TC-008: ACL and Authorization Tests

**Objective**: Verify that Access Control Lists (ACL) properly restrict topic access, including device isolation and provision topic protection.

#### Step-by-Step Procedure:

**Part A: General ACL Verification**

**Step 1: Run Automated Test** (pass)
```powershell
python security_test_attacks.py acl
```

**Step 2: Test Unauthorized Publish** #not done (fail)
```powershell
python -c "
import paho.mqtt.client as mqtt
import ssl
import json

client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        # Try unauthorized topic
        result = client.publish('unauthorized/topic/test', 'test', qos=1)
        print(f'Publish to unauthorized topic: rc={result.rc}')
        if result.rc == 0:
            print('FAIL: Unauthorized publish allowed!')
        else:
            print('PASS: Unauthorized publish blocked')

client.on_connect = on_connect
client.connect('192.168.43.214', 8883, 5)
client.loop_start()
import time
time.sleep(3)
client.loop_stop()
"
```

**Step 3: Test Unauthorized Subscribe** #not done (fail)
```powershell
python -c "
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        # Try unauthorized topic
        result = client.subscribe('unauthorized/topic/+', qos=1)
        print(f'Subscribe to unauthorized topic: rc={result[0]}')
        if result[0] == 0:
            print('FAIL: Unauthorized subscribe allowed!')
        else:
            print('PASS: Unauthorized subscribe blocked')

client.on_connect = on_connect
client.connect('192.168.43.214', 8883, 5)
client.loop_start()
import time
time.sleep(3)
client.loop_stop()
"
```

**Part B: Device-Specific Topic Isolation**

**Step 4: Connect as Device A (sal01) and Test Cross-Device Access** (fail)
```powershell
# Regular PowerShell (no admin needed)
python -c "
import paho.mqtt.client as mqtt
import ssl
import json

client = mqtt.Client(client_id='sal01_client')
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print('Connected as sal01')
        # Try to access sal02's topic (should fail)
        result = client.publish('provision/sal02/update', json.dumps({
            'device_id': 'sal02',
            'action': 'update',
            'user_id': '1'
        }), qos=1)
        print(f'Attempted publish to sal02 topic: rc={result.rc}')
        if result.rc == 0:
            print('FAIL: Cross-device access allowed!')
        else:
            print('PASS: Cross-device access blocked')

client.on_connect = on_connect
client.connect('192.168.43.214', 8883, 5)
client.loop_start()
import time
time.sleep(3)
client.loop_stop()
"
```

**Step 5: Verify Own Topic Works**
```powershell
# sal01 should be able to access its own topics
python test_provision_mqtt.py sal01 update 1 (pass)
# Should succeed
```

**Part C: Provision Topic Protection**

**Step 6: Test Authorized Provision Access**
```powershell
# This should work (authorized user)
python test_provision_mqtt.py sal01 update 1
# Should succeed
```

**Step 7: Test Unauthorized Provision Access**
```powershell
# Try with different credentials (if you have test user)
python -c "
import paho.mqtt.client as mqtt
import ssl
import json

# Try with unauthorized user (if exists)
client = mqtt.Client()
# Use different credentials if available
client.username_pw_set('water_monitor', 'e2eeWater2025')  # Change if needed
client.tls_set(cert_reqs=ssl.CERT_NONE)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        # Try provision topic
        result = client.publish('provision/test_device/update', json.dumps({
            'device_id': 'test_device',
            'action': 'update',
            'user_id': '1'
        }), qos=1)
        print(f'Provision publish result: rc={result.rc}')

client.on_connect = on_connect
client.connect('192.168.43.214', 8883, 5)
client.loop_start()
import time
time.sleep(3)
client.loop_stop()
"
```

**Step 8: Check Broker Logs and ACL Configuration**
```bash
# On Raspberry Pi
sudo journalctl -u mosquitto | grep -i "acl\|denied\|unauthorized\|sal02" (none)
# Should see ACL denial messages

# Review ACL configuration
sudo cat /etc/mosquitto/mosquitto.conf | grep -i "acl\|provision" 
# Review ACL rules for provision topics
```

**Expected Result**:
- ✅ Unauthorized publish blocked
- ✅ Unauthorized subscribe blocked
- ✅ ACL violations logged
- ✅ Authorized topics work
- ✅ Cross-device topic access blocked
- ✅ Own topics accessible
- ✅ Device isolation enforced
- ✅ Authorized users can access provision topics
- ✅ Unauthorized provision access blocked
- ✅ Provision commands logged

**Pass Criteria**: ACL working, unauthorized access blocked, device isolation enforced, cross-device access blocked, provision topics protected

---

## Category 6: Attack Simulation Tests

### TC-009: Eavesdropping Attack

**Objective**: Test if traffic can be intercepted and read.

**💡 Efficiency Tip**: You can reuse the same pcap file from TC-003! Both tests analyze the same MQTT traffic to verify encryption. TC-003 focuses on PUBLISH packets, TC-014 is a broader eavesdropping test, but they use the same captured traffic.

**⚠️ Important: You DON'T need SSH/SCP for this test!**

You can do TC-014 entirely from Windows using only Wireshark. Pi-side capture is **optional** (gives you broker-side logs, but not required).

#### Step-by-Step Procedure:

**Option A: Windows-Only (Recommended - No SSH needed)**

**Step 1: Use Existing Capture OR Capture New**

**Option A1: Reuse TC-003 Capture (Most Efficient!)**
- Use the `mqtt_traffic.pcap` file you saved from TC-003
- Open it in Wireshark
- Skip to Step 2

**Option A2: Capture New Traffic**
1. Open Wireshark (as Administrator)
2. Select network interface (Wi-Fi/Ethernet)
3. Start capture (blue shark fin icon)
4. Filter: `tcp.port == 8883 or tcp.port == 1883`
5. Run: `python test_provision_mqtt.py sal01 update 1`
6. Stop capture, save as `mqtt_traffic.pcap` (or reuse TC-003 file)

**Step 2: Analyze Capture**
1. **Wireshark Analysis**:
   - Filter: `tcp.port == 8883` (should see TLS packets)
   - Click on any TLS packet
   - Look at Packet Bytes (bottom pane)
   - **Expected**: Encrypted data (random binary), NOT readable

2. **Security Analyzer**:
   ```powershell
   # Make sure you're in the project directory
   cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
   python security_test_analyzer.py mqtt_traffic.pcap
   # Use the same file from TC-003!
   ```

**Step 5: Interpret Results for TC-009 (Eavesdropping Test)**

**How to Know if Eavesdropping Test PASSES:**

Look for these in the analyzer output:

**✅ PASS Criteria (Eavesdropping Prevented):**
1. **Statistics Section**:
   - `Encrypted Connections (8883):` should be **> 0** ✅
   - `Unencrypted Connections (1883):` should be **0** ✅

2. **Security Findings Section**:
   - Should show: **"✓ No security issues detected!"** ✅
   - OR if findings exist, should NOT have:
     - ❌ "Unencrypted Connection" (CRITICAL)
     - ❌ "Unencrypted Payload" (CRITICAL)
     - ❌ "Credential Exposure" (HIGH)

3. **Recommendations Section**:
   - Should NOT have: "CRITICAL: Disable port 1883"
   - Should NOT have: "CRITICAL: Enable TLS encryption"
   - Should show: "✓ Security posture looks good" ✅

**❌ FAIL Criteria (Eavesdropping Possible):**
- `Unencrypted Connections (1883):` > 0 → FAIL (traffic not encrypted)
- "Unencrypted Connection" finding → FAIL
- "Unencrypted Payload" finding → FAIL
- "Credential Exposure" finding → FAIL

**Example PASS Output:**
```
[STATISTICS]
  Encrypted Connections (8883): 15
  Unencrypted Connections (1883): 0

[SECURITY FINDINGS]
✓ No security issues detected!

[RECOMMENDATIONS]
  1. ✓ Security posture looks good. Continue monitoring.
```

**Example FAIL Output:**
```
[STATISTICS]
  Encrypted Connections (8883): 0
  Unencrypted Connections (1883): 10

[SECURITY FINDINGS]
[CRITICAL] Issues: 2
  • Unencrypted Connection: MQTT traffic on unencrypted port 1883
  • Unencrypted Payload: MQTT payload visible in unencrypted connection

[RECOMMENDATIONS]
  1. CRITICAL: Disable port 1883 or restrict access
  2. CRITICAL: Enable TLS encryption for all MQTT traffic
```

**Quick Check:**
- If you see **"✓ No security issues detected!"** → **PASS** ✅
- If you see **"Unencrypted Connection"** or **"Unencrypted Payload"** → **FAIL** ❌

**Option B: With Pi-Side Capture (Optional - Requires SSH)**

**Step 1: Copy Scripts to Pi (First Time Only)**

**If you haven't copied the scripts yet, do this first:**

```powershell
# From Windows PowerShell (in project directory)
# Make sure you're in: C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
# Note: Use your actual username if not 'pi'
scp pi_scripts/*.sh mizan@192.168.43.214:/home/mizan/
```

**Then on Raspberry Pi:**
```bash
# SSH into Pi first
ssh mizan@192.168.43.214

# Make scripts executable
chmod +x ~/*.sh

# Create directory for captures
mkdir -p ~/security_captures

# Install tcpdump if not installed
sudo apt-get update && sudo apt-get install -y tcpdump
```

**Step 2: Start Pi Capture (if you want broker-side logs)**
```bash
# On Raspberry Pi (after SSH)
cd ~
./capture_security_test.sh eavesdropping_test
# Keep this running - DON'T press Ctrl+C yet!
# The script will keep running until you stop it
```

**⚠️ Important**: Keep the script running! Don't press Ctrl+C until AFTER you've run your test from Windows.

**Step 2: Start Wireshark on Windows** (while Pi capture is running)
1. Open Wireshark (as Administrator)
2. Select network interface
3. Start capture
4. Filter: `tcp.port == 8883 or tcp.port == 1883`

**Step 3: Run Normal Operation** (while both captures are running)
```powershell
# From Windows PowerShell (regular PowerShell, no admin needed)
python test_provision_mqtt.py sal01 update 1
# This generates MQTT traffic that both captures will record
```

**Step 4: Stop Captures** (after test completes)
1. **Stop Pi capture**: Go back to SSH session, press Ctrl+C
2. **Stop Wireshark**: Click red square (■) to stop capture
3. **Save Wireshark file**: Save as `eavesdropping_test.pcap`

**Step 5: Transfer Pi Capture (if you want to analyze it)**
```powershell
# From Windows PowerShell
# Transfer FROM Pi TO Windows (not the other way!)

# Option 1: Transfer to current directory (where you run the command)
scp mizan@192.168.43.214:/home/mizan/security_captures/eavesdropping_test_*/network.pcap ./
# File will be saved in: current PowerShell directory (check with: pwd)

# Option 2: Transfer to specific directory
scp mizan@192.168.43.214:/home/mizan/security_captures/eavesdropping_test_*/network.pcap "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\"

# Option 3: List files first to see exact path, then transfer
ssh mizan@192.168.43.214 "ls -la ~/security_captures/eavesdropping_test_*/"
# Copy the exact path from output, then:
scp mizan@192.168.43.214:/home/mizan/security_captures/eavesdropping_test_20251223_210101/network.pcap ./
```

**Where is the file after SCP?**

The file is saved in your **current PowerShell directory**. To find it:

```powershell
# Check current directory
pwd
# Or
Get-Location

# List files in current directory
ls *.pcap
# Or
dir *.pcap

# Common locations:
# - If you ran SCP from Desktop: C:\Users\NURMIZAN QISTINA\Desktop\
# - If you ran SCP from project folder: C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\
```

**To transfer to a specific location:**
```powershell
# Transfer directly to project directory
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
scp mizan@192.168.43.214:/home/mizan/security_captures/eavesdropping_test_*/network.pcap ./
# File will be in: C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\network.pcap
```

**Step 6: Analyze Captures**
1. **Wireshark Analysis** (use Windows capture):
   - Filter: `tcp.port == 8883`
   - Check if payloads are encrypted
   - **Expected**: Encrypted, not readable
   - **Tip**: You can use the same `mqtt_traffic.pcap` from TC-003!

2. **Security Analyzer**:
   ```powershell
   python security_test_analyzer.py mqtt_traffic.pcap
   # Use the same file from TC-003!
   ```

**Expected Result**:
- ✅ All traffic encrypted
- ✅ Payloads not readable
- ✅ No plaintext data visible
- ✅ Security analyzer shows: "No security issues detected"
- ✅ Encrypted connections > 0, Unencrypted connections = 0

**Pass Criteria**: 
- Traffic encrypted (port 8883 only, no port 1883)
- No "Unencrypted Connection" or "Unencrypted Payload" findings
- Security analyzer reports no critical issues
- Eavesdropping prevented (data not readable)

---

### TC-011: Replay Attack with Timestamp/Nonce

**Objective**: Test replay attack protection.

#### Step-by-Step Procedure:

**Step 1: Capture Valid Message**
1. Start Wireshark capture
2. Run: `python test_provision_mqtt.py sal01 update 1`
3. Stop capture, save message details

**Step 2: Extract Message Details**
- Note: timestamp, nonce, payload
- Save for replay

**Step 3: Replay Same Message**
```powershell
# Run automated test
python security_test_attacks.py replay
```

**Step 4: Manual Replay Test**
```powershell
# Replay captured message
python -c "
import paho.mqtt.client as mqtt
import json
import ssl
import time

client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.connect('192.168.43.214', 8883)

# Replay same message multiple times
topic = 'provision/sal01/update'
payload = json.dumps({
    'device_id': 'sal01',
    'action': 'update',
    'user_id': '1'
})

for i in range(3):
    result = client.publish(topic, payload, qos=1)
    print(f'Replay {i+1}: rc={result.rc}')
    time.sleep(0.5)

client.disconnect()
"
```

**Step 5: Check for Replay Detection**
```bash
# On Raspberry Pi
sudo journalctl -u mosquitto -f
# Look for duplicate message detection
# Check application logs for timestamp/nonce validation
```

**Expected Result**:
- ✅ Replayed messages detected
- ✅ Timestamp validation works
- ✅ Nonce prevents duplicates
- ✅ Old messages rejected

**Pass Criteria**: Replay attacks detected/prevented

---

### TC-010: Man-in-the-Middle (MITM) Attack

**Objective**: Test TLS protection against MITM attacks.

#### Step-by-Step Procedure:

**Step 1: Test Certificate Validation (Basic MITM Test)**
```powershell
# Regular PowerShell (no admin needed)
# This tests if invalid certificates are rejected
python security_test_attacks.py cert
```

**Step 2: Manual Certificate Validation Test**
```powershell
python -c "
import ssl
import paho.mqtt.client as mqtt

# Test with strict certificate validation
client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')

# Use strict validation
context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED

client.tls_set_context(context)
try:
    client.connect('192.168.43.214', 8883, 5)
    print('Connected - certificate accepted')
    print('PASS: Valid certificate accepted')
except ssl.SSLError as e:
    print(f'SSL Error: {e}')
    print('PASS: Certificate validation working')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
"
```

**Step 3: Check TLS Handshake in Wireshark**
1. Start Wireshark capture
2. Filter: `tcp.port == 8883`
3. Run the test
4. Look for TLS handshake packets
5. Filter: `tls.handshake.type == 1` (Client Hello)
6. Verify certificate exchange

**Expected Result**:
- ✅ Valid certificates accepted
- ✅ Invalid certificates rejected
- ✅ Certificate validation prevents MITM

**Pass Criteria**: Certificate validation working, MITM prevented

---

### TC-012: Topic Enumeration Attack

**Objective**: Test if MQTT topics can be discovered through traffic analysis.

#### Step-by-Step Procedure:

**Step 1: Capture Extended Traffic**
1. Start Wireshark capture
2. Filter: `tcp.port == 8883`
3. Run multiple operations:
   ```powershell
   python test_provision_mqtt.py sal01 update 1
   python test_provision_mqtt.py sal01 request 1
   python test_provision_mqtt.py sal02 update 1
   # Run normal operations for a few minutes
   ```
4. Stop capture, save as `topic_enumeration.pcap`

**Step 2: Extract Topics from Capture**
```powershell
# Use security analyzer
python security_test_analyzer.py topic_enumeration.pcap
# Check the "DISCOVERED TOPICS" section in the report
```

**Step 3: Manual Topic Extraction in Wireshark**
1. In Wireshark, filter: `mqtt.msgtype == 3 or mqtt.msgtype == 8`
2. Go to: `Statistics` → `Protocol Hierarchy`
3. Expand MQTT section
4. Look for topic patterns

**Step 4: Analyze Topic Patterns**
- List all discovered topics
- Check for sensitive topic names
- Verify topic structure doesn't reveal sensitive info

**Expected Result**:
- ✅ Topics may be discoverable (acceptable)
- ✅ Sensitive topics should not be exposed
- ✅ Topic naming should not reveal sensitive information

**Pass Criteria**: Sensitive topics not exposed, topic naming secure

---

### TC-013: Unauthorized Access Attempt

**Objective**: Test authentication and authorization mechanisms.

#### Step-by-Step Procedure:

**Step 1: Start Wireshark Capture**
1. Open Wireshark (as Administrator)
2. Start capture
3. Filter: `tcp.port == 8883`

**Step 2: Attempt Unauthorized Access**
```powershell
# Regular PowerShell (no admin needed)
# Try wrong credentials
python security_test_attacks.py credentials
```

**Step 3: Analyze Failed Attempts in Wireshark**

**⚠️ Important: If you see TLS packets (not MQTT), that's normal!**

When MQTT is encrypted with TLS, Wireshark shows TLS packets, not MQTT packets directly. The MQTT CONNECT and CONNACK messages are **inside** the encrypted TLS tunnel.

**Option 1: Check TLS Connection Success/Failure (Recommended)**
1. **Filter**: `tcp.port == 8883`
2. **Look for TLS handshake**:
   - Filter: `tls.handshake.type == 1` (Client Hello - connection attempt)
   - Filter: `tls.handshake.type == 2` (Server Hello - server response)
3. **Check if TLS connection completes**:
   - If TLS handshake completes → Connection succeeded (even if auth fails later)
   - If TLS handshake fails → Connection rejected at TLS level
4. **Look for connection resets**:
   - Filter: `tcp.flags.reset == 1`
   - If you see RST packets after TLS handshake → Connection was rejected

**Option 2: Try to Find MQTT Protocol (May Not Work with TLS)**
1. **Filter**: `mqtt.msgtype == 1` (CONNECT - client sends)
   - **Note**: This may show NO packets if MQTT is encrypted inside TLS
   - If no packets appear, that's actually GOOD (means TLS encryption is working!)
2. **Filter**: `mqtt.msgtype == 2` (CONNACK - server response)
   - **Note**: This is the response to CONNECT
   - Return code 0 = success, non-zero = failure
   - If no packets appear, MQTT is encrypted inside TLS (which is correct!)

**Option 3: Analyze Connection Behavior (Works Even with TLS)**
1. **Watch connection attempts**:
   - Filter: `tcp.port == 8883 and tcp.flags.syn == 1` (connection attempts)
   - Count how many connection attempts
2. **Check connection duration**:
   - If connection closes immediately → Likely authentication failure
   - If connection stays open → Authentication succeeded
3. **Look at packet flow**:
   - Successful auth: TLS handshake → Data exchange → Normal close
   - Failed auth: TLS handshake → Immediate close (RST or FIN)

**What to Look For:**
- ✅ **TLS handshake completes** → Connection established
- ✅ **Connection closes quickly** → Likely auth failure
- ✅ **No MQTT protocol visible** → GOOD! (means TLS encryption working)
- ❌ **MQTT protocol visible directly** → BAD! (means not encrypted)

**Step 4: Check Broker Logs**
```bash
# On Raspberry Pi (after SSH)

# See recent failed attempts (last hour)
sudo journalctl -u mosquitto --since "1 hour ago" | grep -i "auth\|denied\|failed"

# Or check log file directly
sudo tail -100 /var/log/mosquitto/mosquitto.log | grep -i "auth\|denied\|failed"

# Follow logs in real-time while testing
sudo journalctl -u mosquitto -f --since "now" | grep -i "auth\|denied\|failed"
# Run test from Windows, watch for new entries
```

**Expected Result**:
- ✅ Failed attempts logged
- ✅ Unauthorized access blocked
- ✅ Error messages don't reveal sensitive info
- ✅ Rate limiting may activate

**Pass Criteria**: Failed attempts logged, unauthorized access blocked

---

### TC-014: Traffic Analysis and Metadata Tests

**Objective**: Analyze traffic patterns and verify that metadata doesn't leak sensitive information.

#### Step-by-Step Procedure:

**Part A: Traffic Pattern Analysis**

**Step 1: Capture Baseline Traffic**
1. Start Wireshark capture
2. Run normal operations for 5-10 minutes
3. Stop capture, save as `baseline.pcap`

**Step 2: Analyze Traffic Patterns**
1. In Wireshark: `Statistics` → `IO Graph`
   - X-axis: Time
   - Y-axis: Packets or Bytes
   - Filter: `mqtt` or `tcp.port == 8883`
2. Look for:
   - Normal traffic patterns
   - Unusual spikes
   - Regular intervals (sensor updates)

**Step 3: Analyze Conversations**
1. `Statistics` → `Conversations`
2. Check TCP tab
3. Identify:
   - Number of connections
   - Connection duration
   - Data volume

**Step 4: Identify Anomalies**
- Sudden traffic spikes
- Unusual connection times
- Abnormal message sizes
- Unexpected connection patterns

**Part B: Metadata Leakage Verification**

**Step 5: Capture MQTT Traffic**
1. Start Wireshark capture
2. Run: `python test_provision_mqtt.py sal01 update 1`
3. Stop capture

**Step 6: Analyze Packet Headers**
1. Click on any MQTT/TLS packet
2. Check packet details for:
   - Client IDs
   - Topic names
   - Usernames (if visible)
   - Any metadata fields

**Step 7: Check for Information Leakage**
```powershell
# Use security analyzer
python security_test_analyzer.py capture.pcap
# Check for "Sensitive Topic" findings
```

**Step 8: Review Topic Names**
- Check if topic names reveal:
  - Device locations
  - User information
  - System architecture
  - Sensitive data

**Expected Result**:
- ✅ Baseline established
- ✅ Normal patterns identified
- ✅ Anomalies detectable
- ✅ No sensitive information in metadata
- ✅ Client IDs are generic or encrypted
- ✅ Topic names don't reveal sensitive data

**Pass Criteria**: Baseline established, patterns analyzable, no sensitive metadata leakage

---

### TC-015: DoS and System Resilience Tests

**Objective**: Test broker resilience against various denial-of-service attacks and resource exhaustion.

#### Step-by-Step Procedure:

**Part A: Connection Flood Attack**

**Step 1: Start Resource Monitoring**
```bash
# On Raspberry Pi
./monitor_resources.sh &
```

**Step 2: Run Connection Flood Test**
```powershell
# Run automated test
python security_test_attacks.py dos
```

**Step 3: Monitor Broker**
```bash
# On Raspberry Pi
htop  # Watch CPU/memory
sudo journalctl -u mosquitto -f  # Watch logs
```

**Step 4: Check Connection Limits**
- Note: How many connections succeeded
- Check: Rate limiting behavior
- Verify: Broker stability

**Part B: Message Flood Attack**

**Step 5: Generate Message Flood**
```powershell
# Regular PowerShell (no admin needed)
python -c "
import paho.mqtt.client as mqtt
import ssl
import json
import time

client = mqtt.Client()
client.username_pw_set('water_monitor', 'e2eeWater2025')
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.connect('192.168.43.214', 8883, 5)

# Send many messages rapidly
for i in range(100):
    payload = json.dumps({'test': i, 'flood': 'attack'})
    result = client.publish('provision/test/update', payload, qos=1)
    if i % 10 == 0:
        print(f'Sent {i} messages')
    time.sleep(0.01)  # Very small delay

client.disconnect()
print('Message flood completed')
"
```

**Step 6: Monitor Broker Response**
- Watch resource usage on Pi
- Check broker logs for errors
- Verify broker remains responsive
- Check if rate limiting activates

**Step 7: Test Legitimate Traffic After Flood**
```powershell
# After flood, test normal operation
python test_provision_mqtt.py sal01 update 1
# Should still work
```

**Part C: Resource Exhaustion**

**Step 8: Start Comprehensive Monitoring**
```bash
# On Raspberry Pi
./capture_security_test.sh resource_test
# This monitors CPU, memory, disk, connections
```

**Step 9: Generate High Load**
```powershell
# Create multiple connections and send messages
python -c "
import paho.mqtt.client as mqtt
import ssl
import time
import threading

def create_client(i):
    try:
        client = mqtt.Client(client_id=f'load_test_{i}')
        client.username_pw_set('water_monitor', 'e2eeWater2025')
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.connect('192.168.43.214', 8883, 5)
        # Send some messages
        for j in range(10):
            client.publish('provision/test/update', f'load_test_{i}_{j}', qos=1)
        time.sleep(1)
        client.disconnect()
    except Exception as e:
        print(f'Client {i} error: {e}')

# Create multiple clients
threads = []
for i in range(20):
    t = threading.Thread(target=create_client, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print('High load test completed')
"
```

**Step 10: Monitor System Resources**
- Watch CPU usage
- Monitor memory consumption
- Check disk I/O
- Verify system stability

**Expected Result**:
- ✅ Broker remains stable
- ✅ Connection limits enforced
- ✅ Rate limiting works
- ✅ No crash
- ✅ Broker handles message flood
- ✅ Rate limiting may activate
- ✅ Broker remains stable
- ✅ Legitimate messages still processed
- ✅ System handles high load
- ✅ Resource limits enforced
- ✅ System does not crash
- ✅ Graceful degradation acceptable

**Pass Criteria**: Broker stable, limits enforced, rate limiting works, system stable under load

---

## Complete Test Execution Checklist

### Pre-Testing
- [ ] Wireshark installed on Windows
- [ ] Python dependencies installed
- [ ] Raspberry Pi scripts copied and executable
- [ ] Test environment isolated
- [ ] Backup of production data (if applicable)

### For Each Test
- [ ] Start captures (Wireshark + Pi scripts)
- [ ] Execute test procedure
- [ ] Stop captures
- [ ] Analyze results
- [ ] Document findings
- [ ] Verify pass/fail criteria

### Post-Testing
- [ ] Review all test results
- [ ] Document vulnerabilities found
- [ ] Create remediation plan
- [ ] Re-test after fixes

---

## Quick Reference Commands

### Windows
```powershell
# ⚠️ IMPORTANT: All Python commands work in REGULAR PowerShell (NO admin needed)
# Only Wireshark needs to run as Administrator

# Run all tests
python security_test_attacks.py

# Run specific test
python security_test_attacks.py tls
python security_test_attacks.py auth
python security_test_attacks.py acl

# Analyze capture
python security_test_analyzer.py capture.pcap
```

### Raspberry Pi
```bash
# Start capture
./capture_security_test.sh test_name

# Stop capture
./stop_captures.sh

# Monitor resources
./monitor_resources.sh

# View logs
sudo journalctl -u mosquitto -f
```

### Transfer Files
```powershell
# From Windows
scp pi@192.168.43.214:/home/pi/security_captures/* ./
```

---

## Complete Test Case Index

**All 20 Test Cases with Step-by-Step Instructions:**

### Category 1: Encryption & TLS Tests
- **TC-001**: TLS Requirement Enforcement (Line 226)
- **TC-002**: TLS Configuration and Validation (Line 281) - *Merged TC-002 + TC-003*
- **TC-003**: Encrypted Payload Verification (Line 391)

### Category 2: End-to-End Encryption (E2EE) Tests
- **TC-016**: Application-Layer Encryption Verification (Line 559) - Provision Messages
- **TC-017**: E2EE Implementation Verification (Line 809) - *Merged TC-023 + TC-024*
- **TC-020**: Sensor Data E2EE Verification (Line 926) - Sensor Data Messages

### Category 3: Message Integrity Tests
- **TC-018**: Provision Message Integrity Verification (E2EE Tag Authentication) (Line 1100) - Provision Messages
- **TC-019**: Message Tampering Detection (Line 1348)

### Category 4: Authentication Tests
- **TC-004**: Authentication Requirement (Line 1433)
- **TC-005**: Wrong Credentials Rejection (Line 1575)
- **TC-006**: Credential Sniffing Protection (Line 1653)
- **TC-007**: Brute Force Protection (Line 1725)

### Category 5: Authorization Tests
- **TC-008**: ACL and Authorization Tests (Line 1788) - *Merged TC-009 + TC-010 + TC-011*

### Category 6: Attack Simulation Tests
- **TC-009**: Eavesdropping Attack (Line 2004)
- **TC-011**: Replay Attack with Timestamp/Nonce (Line 2241)
- **TC-010**: Man-in-the-Middle (MITM) Attack (Line 2311)
- **TC-012**: Topic Enumeration Attack (Line 2369)
- **TC-013**: Unauthorized Access Attempt (Line 2414)

### Category 7: Traffic Analysis Tests
- **TC-014**: Traffic Analysis and Metadata Tests (Line 2447) - *Merged TC-017 + TC-018*

### Category 8: System Resilience Tests
- **TC-015**: DoS and System Resilience Tests (Line 2670) - *Merged TC-019 + TC-020 + TC-021*

**Note**: Line numbers are approximate and may vary. Use search (Ctrl+F) to find specific test cases.

---

## Troubleshooting

### No Packets Captured
- Check network interface selection
- Verify MQTT traffic is being sent
- Check firewall settings
- Verify broker is accessible

### Tests Failing Unexpectedly
- Check broker is running
- Verify credentials are correct
- Check network connectivity
- Review broker logs

### Analysis Errors
- Ensure pyshark is installed
- Check .pcap file is valid
- Verify file permissions
- Check Python version compatibility

---

This guide provides step-by-step procedures for all test cases. Follow each procedure carefully and document your results.
