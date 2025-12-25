# Wireshark Security Testing Guide for IoT MQTT System

## Table of Contents
1. [Setup and Configuration](#setup-and-configuration)
2. [Capturing MQTT Traffic](#capturing-mqtt-traffic)
3. [Attack Simulation Scenarios](#attack-simulation-scenarios)
4. [Traffic Analysis](#traffic-analysis)
5. [Security Testing Checklist](#security-testing-checklist)

---

## Setup and Configuration

### 1. Install Wireshark
- Download from: https://www.wireshark.org/
- Install with Npcap (for Windows packet capture)
- Ensure you have administrator privileges

### 2. Configure Wireshark for MQTT Analysis

#### Enable MQTT Protocol Support
1. Open Wireshark
2. Go to `Edit` → `Preferences` → `Protocols`
3. Search for "MQTT" and ensure it's enabled
4. Search for "TLS" and ensure it's enabled for encrypted traffic analysis

#### Set Up Display Filters
Create custom display filters for quick analysis:
- `mqtt` - All MQTT traffic
- `mqtt.msgtype == 3` - PUBLISH messages
- `mqtt.msgtype == 8` - SUBSCRIBE messages
- `tcp.port == 8883` - MQTT over TLS port
- `tcp.port == 1883` - MQTT unencrypted port
- `mqtt.topic contains "provision"` - Provision-related topics

---

## Capturing MQTT Traffic

### Method 1: Capture on Local Machine (Testing Client)

1. **Start Capture**
   - Open Wireshark
   - Select your network interface (Wi-Fi or Ethernet)
   - Click the blue shark fin icon to start capture

2. **Run Your Test Script**
   ```bash
   python test_provision_mqtt.py sal01 update 1
   ```

3. **Stop Capture**
   - Click the red square to stop
   - Save the capture file (`.pcap` format)

### Method 2: Capture on Network (Requires Network Access)

**Option A: Port Mirroring (Switch Configuration)**
- Configure switch to mirror traffic to your capture machine
- Requires managed switch with port mirroring capability

**Option B: ARP Spoofing/MITM (For Testing Only)**
- Use tools like Ettercap or Bettercap
- **WARNING**: Only use on networks you own or have explicit permission
- Intercept traffic between MQTT broker and clients

### Method 3: Capture on Broker Machine

If you have access to the MQTT broker (Raspberry Pi):
```bash
# SSH into Raspberry Pi
sudo tcpdump -i any -w mqtt_capture.pcap port 8883 or port 1883
```

Then transfer the `.pcap` file to your Windows machine for analysis.

**📋 For comprehensive broker-side captures, see: `RASPBERRY_PI_CAPTURE_GUIDE.md`**

This guide covers:
- Network packet capture
- Mosquitto broker logs
- System logs and resource monitoring
- Authentication and connection monitoring
- Complete capture scripts for automated testing

---

## Attack Simulation Scenarios

### Scenario 1: Eavesdropping Attack (Passive)

**Objective**: Verify if unencrypted traffic can be intercepted

**Steps**:
1. Temporarily disable TLS in your MQTT config
2. Start Wireshark capture
3. Run your test script
4. Analyze captured packets

**What to Look For**:
- Can you see MQTT message contents?
- Are credentials visible in plaintext?
- Are device IDs and sensor data readable?

**Expected Result**: With TLS enabled, you should only see encrypted data. Without TLS, all data should be visible.

### Scenario 2: Man-in-the-Middle (MITM) Attack

**Objective**: Test TLS certificate validation

**Tools Needed**:
- Bettercap or Ettercap
- Custom CA certificate

**Steps**:
1. Set up MITM tool to intercept traffic
2. Install a fake CA certificate
3. Capture traffic between client and broker
4. Analyze if TLS prevents interception

**What to Look For**:
- Does the client reject invalid certificates?
- Can you decrypt TLS traffic with a fake certificate?
- Are certificate validation checks working?

**Test Script** (Create `test_mitm_detection.py`):
```python
import ssl
import socket
from paho.mqtt import client as mqtt

# Test with invalid certificate
def test_certificate_validation():
    client = mqtt.Client()
    client.tls_set(ca_certs="fake_ca.pem", cert_reqs=ssl.CERT_REQUIRED)
    # Should fail if certificate validation is working
    client.connect("192.168.43.214", 8883)
```

### Scenario 3: Credential Sniffing

**Objective**: Verify if credentials are protected

**Steps**:
1. Capture MQTT CONNECT packets
2. Look for username/password fields
3. Check if they're encrypted

**Wireshark Filter**: `mqtt.msgtype == 1` (CONNECT messages)

**What to Look For**:
- Usernames in plaintext (acceptable if TLS is used)
- Passwords should be hashed or encrypted
- Check MQTT CONNECT packet structure

### Scenario 4: Topic Enumeration Attack

**Objective**: Discover MQTT topics through traffic analysis

**Steps**:
1. Capture all MQTT traffic for extended period
2. Filter for PUBLISH and SUBSCRIBE messages
3. Extract all unique topics

**Wireshark Filter**: 
```
mqtt.msgtype == 3 or mqtt.msgtype == 8
```

**Analysis**:
- Export topic list: `Statistics` → `Protocol Hierarchy` → `MQTT`
- Look for patterns: `provision/+/update`, `sensor/+/data`
- Identify sensitive topics

### Scenario 5: Replay Attack

**Objective**: Test if old messages can be replayed

**Steps**:
1. Capture a valid MQTT message
2. Extract the packet
3. Replay it using a tool like `tcpreplay` or custom script

**Wireshark Export**:
1. Right-click on MQTT packet → `Export Packet Bytes`
2. Save as raw data
3. Use Python script to replay

**Test Script** (Create `test_replay_attack.py`):
```python
import paho.mqtt.client as mqtt
import json

# Replay captured message
def replay_message():
    client = mqtt.Client()
    client.username_pw_set("water_monitor", "e2eeWater2025")
    client.connect("192.168.43.214", 8883)
    
    # Replay captured payload
    topic = "provision/test_device/update"
    payload = json.dumps({
        "device_id": "test_device",
        "action": "update",
        "user_id": "1"
    })
    client.publish(topic, payload, qos=1)
```

**What to Look For**:
- Does the system accept replayed messages?
- Are there timestamp/nonce checks?
- Can you replay old provision commands?

### Scenario 6: Denial of Service (DoS) Attack

**Objective**: Test broker resilience

**Steps**:
1. Capture normal traffic patterns
2. Generate high-volume traffic
3. Monitor broker response

**Wireshark Statistics**:
- `Statistics` → `IO Graph` - View traffic volume
- `Statistics` → `Conversations` - Identify high-traffic sources

**What to Look For**:
- Broker crash or slowdown
- Connection limits
- Rate limiting behavior

### Scenario 7: Unauthorized Access Attempt

**Objective**: Test authentication mechanisms

**Steps**:
1. Capture failed authentication attempts
2. Try connecting with wrong credentials
3. Analyze error responses

**Wireshark Filter**: `mqtt.msgtype == 1 and mqtt.conack.flags == 5`

**What to Look For**:
- Are failed attempts logged?
- Error messages reveal information?
- Rate limiting on failed attempts?

---

## Traffic Analysis

### Analyzing Encrypted Traffic (TLS)

Even with TLS, you can analyze:
1. **Connection Patterns**
   - When connections are established
   - Connection duration
   - Frequency of reconnections

2. **Traffic Volume**
   - Size of encrypted packets
   - Frequency of messages
   - Identify patterns (e.g., sensor sends data every 5 seconds)

3. **TLS Handshake Analysis**
   - Filter: `tls.handshake.type == 1` (Client Hello)
   - Check TLS version (should be 1.2 or 1.3)
   - Verify cipher suites
   - Check certificate information

**Wireshark Filter for TLS**:
```
tls.record.content_type == 22  # Handshake
tls.handshake.type == 1        # Client Hello
tls.handshake.type == 2        # Server Hello
```

### Extracting Metadata

1. **Export Statistics**
   - `Statistics` → `Protocol Hierarchy`
   - `Statistics` → `Conversations`
   - `Statistics` → `Endpoints`

2. **Follow TCP Stream**
   - Right-click packet → `Follow` → `TCP Stream`
   - See complete conversation
   - Export for further analysis

3. **Export Objects**
   - `File` → `Export Objects` → `HTTP` (if applicable)
   - Extract files transferred

### Creating Custom Columns

Add useful columns in Wireshark:
1. `Edit` → `Preferences` → `Columns`
2. Add columns:
   - MQTT Topic: `mqtt.topic`
   - MQTT Message Type: `mqtt.msgtype`
   - Packet Length: `frame.len`

---

## Security Testing Checklist

### Pre-Testing Setup
- [ ] Wireshark installed with administrator privileges
- [ ] Network interface selected for capture
- [ ] MQTT protocol enabled in Wireshark
- [ ] Display filters configured
- [ ] Test environment isolated (not production)

### Encryption Testing
- [ ] Verify TLS is enabled (port 8883)
- [ ] Confirm traffic is encrypted (cannot read payloads)
- [ ] Test certificate validation (reject invalid certs)
- [ ] Verify TLS version (1.2 or higher)
- [ ] Check cipher suite strength

### Authentication Testing
- [ ] Credentials not visible in plaintext
- [ ] Failed authentication attempts logged
- [ ] Rate limiting on failed attempts
- [ ] Strong password requirements enforced

### Authorization Testing
- [ ] Topic access control (ACL) working
- [ ] Devices can only access their topics
- [ ] Provision topics protected
- [ ] Unauthorized publish attempts blocked

### Message Integrity
- [ ] Messages cannot be modified in transit
- [ ] Replay attacks detected/prevented
- [ ] Message ordering maintained
- [ ] QoS levels working correctly

### Network Security
- [ ] Port 1883 (unencrypted) disabled or restricted
- [ ] Firewall rules configured
- [ ] Network segmentation in place
- [ ] VPN required for remote access

### Monitoring and Detection
- [ ] Unusual traffic patterns detectable
- [ ] Failed connection attempts logged
- [ ] High-volume traffic alerts
- [ ] Anomaly detection in place

---

## Advanced Analysis Techniques

### 1. Statistical Analysis

**Traffic Patterns**:
```
Statistics → IO Graph
- X-axis: Time
- Y-axis: Packets or Bytes
- Filter: mqtt
```

**Identify Anomalies**:
- Sudden spikes in traffic
- Unusual connection times
- Abnormal message sizes

### 2. Exporting Data for Further Analysis

**Export to CSV**:
1. `File` → `Export Packet Dissections` → `As CSV`
2. Analyze in Excel/Python

**Export Specific Fields**:
1. `File` → `Export Packet Dissections` → `As JSON`
2. Parse with Python script

### 3. Creating Custom Dissectors

For proprietary protocols or custom MQTT extensions:
- Lua scripting in Wireshark
- Create custom protocol dissector
- Document in your project

### 4. Automated Analysis Scripts

Create Python scripts to:
- Parse `.pcap` files using `scapy` or `pyshark`
- Automate security checks
- Generate reports

Example:
```python
import pyshark

def analyze_mqtt_security(pcap_file):
    cap = pyshark.FileCapture(pcap_file, display_filter='mqtt')
    
    unencrypted = 0
    encrypted = 0
    
    for packet in cap:
        if hasattr(packet, 'mqtt'):
            if packet.transport_layer == 'TCP' and packet.tcp.dstport == '1883':
                unencrypted += 1
            elif packet.transport_layer == 'TCP' and packet.tcp.dstport == '8883':
                encrypted += 1
    
    print(f"Encrypted connections: {encrypted}")
    print(f"Unencrypted connections: {unencrypted}")
```

---

## Reporting Security Findings

### Document Your Findings

1. **Capture Evidence**
   - Screenshots of Wireshark captures
   - Export relevant packets
   - Save filter expressions used

2. **Create Report**
   - Vulnerability description
   - Risk level (Critical/High/Medium/Low)
   - Steps to reproduce
   - Impact assessment
   - Recommended fixes

3. **Test Fixes**
   - Re-run tests after fixes
   - Verify vulnerabilities are resolved
   - Update documentation

---

## Legal and Ethical Considerations

⚠️ **IMPORTANT**: 
- Only test on systems you own or have explicit written permission
- Do not test on production systems without authorization
- Follow responsible disclosure practices
- Document all testing activities
- Use isolated test environments when possible

---

## Tools and Resources

### Additional Tools
- **tcpdump**: Command-line packet capture
- **tshark**: Command-line version of Wireshark
- **scapy**: Python packet manipulation
- **Bettercap**: MITM framework
- **mosquitto_pub/sub**: MQTT testing tools

### Learning Resources
- Wireshark User's Guide: https://www.wireshark.org/docs/
- MQTT Protocol Specification: https://mqtt.org/mqtt-specification/
- OWASP IoT Security: https://owasp.org/www-project-internet-of-things/

---

## Quick Reference: Wireshark Filters

```
# MQTT Filters
mqtt                                    # All MQTT traffic
mqtt.msgtype == 1                       # CONNECT
mqtt.msgtype == 3                       # PUBLISH
mqtt.msgtype == 8                       # SUBSCRIBE
mqtt.topic contains "provision"         # Provision topics
mqtt.topic contains "sensor"            # Sensor topics

# Port Filters
tcp.port == 8883                        # MQTT over TLS
tcp.port == 1883                        # MQTT unencrypted

# TLS Filters
tls.handshake.type == 1                 # Client Hello
tls.handshake.type == 2                 # Server Hello
tls.record.content_type == 22           # Handshake messages

# Combined Filters
mqtt and tcp.port == 8883               # Encrypted MQTT
mqtt.msgtype == 3 and mqtt.topic contains "provision"  # Provision publishes
```

---

## Next Steps

1. Set up Wireshark capture environment
2. Run baseline capture of normal operations
3. Execute attack scenarios one by one
4. Document findings
5. Implement fixes
6. Re-test to verify fixes

For questions or issues, refer to your project documentation or MQTT broker logs.
