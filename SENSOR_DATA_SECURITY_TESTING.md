# Sensor Data Security Testing Guide

## Overview

Sensor data security is **separate** from provision message security. Even if provision messages pass E2EE tests, you still need to verify sensor data is secure.

## Key Differences

| Aspect | Provision Messages | Sensor Data |
|--------|-------------------|-------------|
| **Topic** | `provision/+/+` | `secure/sensor` |
| **E2EE** | ✅ Now implemented | ✅ Already implemented |
| **Hash** | Not typically included | ✅ SHA-256 hash included |
| **Where it runs** | Flask app (Windows) | Sensor simulator (Windows or Raspberry Pi) |

## Can You Assume Sensor Data is Secure from Provision Tests?

**❌ NO** - You cannot assume sensor data is secure just because provision messages pass.

**Why?**
- Different code paths (provision vs sensor data)
- Different topics
- Different encryption keys (device-specific for sensors)
- Different payload structures

**You must test sensor data separately!**

## Where Does Sensor Simulator Run?

The sensor simulator can run from **either location**:

### Option 1: Run from Windows (Easier for Testing)
```powershell
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
python simulators\sensor\sensor_simulator.py --device-id sal01
```

### Option 2: Run from Raspberry Pi
```bash
cd /home/mizan/secure-water-monitor
python3 simulators/sensor/sensor_simulator.py --device-id sal01
```

**For security testing, running from Windows is easier** because:
- You can capture traffic with Wireshark on the same machine
- Easier to analyze and debug
- Same encryption mechanism (E2EE)

## How to Test Sensor Data Security

### Test 1: Verify E2EE on Sensor Data

**Step 1: Subscribe to Sensor Data Topic**

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
        print('[✓] Subscribed to secure/sensor')
        print('[⏳] Waiting for sensor data messages...')
        print('[💡] TIP: In another terminal, run: python simulators\\sensor\\sensor_simulator.py --device-id sal01')
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
        if 'hash' in payload:
            print('  ✓ Has hash (SHA-256 integrity hash)')
        if all(k in payload for k in ['session_key', 'ciphertext', 'nonce', 'tag']):
            print('\n[✅] E2EE is PRESENT - All required fields found!')
        else:
            print('\n[⚠️] E2EE may be MISSING - Some fields not found')
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
    print('[💡] Make sure to run sensor simulator in another terminal:')
    print('     python simulators\\sensor\\sensor_simulator.py --device-id sal01')
else:
    print('\n[✅] Test completed')
"
```

**Step 2: Run Sensor Simulator (in another terminal)**

```powershell
cd C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
python simulators\sensor\sensor_simulator.py --device-id sal01
```

**Expected Result:**
- ✅ Payload contains: `session_key`, `ciphertext`, `nonce`, `tag` (E2EE fields)
- ✅ Payload may contain: `hash` (SHA-256 integrity hash)
- ✅ Data is encrypted and unreadable

### Test 2: Verify Hash Integrity

**Check if hash is present and correct:**

```powershell
python -c "
from encryption_utils import hash_data, decrypt_data
import json

# If you received an encrypted payload, decrypt it first
# Then verify the hash matches the data

# Example: Verify hash computation
test_data = {'device_id': 'sal01', 'ph': 7.2, 'temperature': 25.5}
computed_hash = hash_data(test_data)
print(f'Test data: {test_data}')
print(f'Computed hash: {computed_hash}')
print(f'Hash length: {len(computed_hash)} (should be 64 for SHA-256)')
"
```

### Test 3: Wireshark Capture (Same as Provision)

1. **Start Wireshark** (as admin) on port 8883
2. **Run sensor simulator** to generate traffic
3. **Analyze capture** - should see TLS packets (not MQTT directly)
4. **Verify encryption** - payload should be encrypted

### Test 4: Verify Decryption Works

The Flask app should be able to decrypt sensor data. Check Flask logs when sensor data is received:

```powershell
# Check Flask error log for sensor data decryption
Get-Content flask_error.log -Tail 50 | Select-String -Pattern "sensor|decrypt|secure/sensor"
```

## Security Checklist for Sensor Data

- [ ] **E2EE Present**: Payload contains `session_key`, `ciphertext`, `nonce`, `tag`
- [ ] **Hash Present**: Payload contains `hash` field (SHA-256)
- [ ] **TLS Encryption**: Traffic on port 8883 (encrypted in transit)
- [ ] **Decryption Works**: Flask can decrypt and process sensor data
- [ ] **Integrity Verified**: Hash matches decrypted data
- [ ] **No Plaintext**: Sensor readings not readable in Wireshark

## Common Issues

### Issue 1: "No messages received"
**Solution**: 
- Check sensor simulator is running
- Verify device keys exist: `python check_key_locations.py sal01 1`
- Check MQTT broker is accessible

### Issue 2: "E2EE fields missing"
**Solution**:
- Verify sensor simulator uses `encrypt_data()` function
- Check device public key exists
- Verify encryption_utils.py is imported correctly

### Issue 3: "Hash field missing"
**Solution**:
- Check if sensor simulator includes hash in payload
- Verify `hash_data()` function is called
- Some implementations may not include hash (E2EE tag provides integrity)

## Testing from Raspberry Pi

If you want to test from Raspberry Pi:

1. **SSH to Raspberry Pi**
2. **Run sensor simulator**:
   ```bash
   cd /home/mizan/secure-water-monitor
   python3 simulators/sensor/sensor_simulator.py --device-id sal01
   ```
3. **Capture on Windows** with Wireshark (capture network traffic)
4. **Subscribe on Windows** using the subscriber script above

## Summary

**Key Points:**
1. ✅ Sensor data uses E2EE (same as provision messages)
2. ✅ Sensor data can be tested from Windows (easier)
3. ❌ **Cannot assume** sensor data is secure from provision tests
4. ✅ **Must test separately** using subscriber script
5. ✅ Sensor data typically includes hash for integrity

**Quick Test Command:**
```powershell
# Terminal 1: Subscribe
python -c "...subscriber script for secure/sensor..."

# Terminal 2: Publish
python simulators\sensor\sensor_simulator.py --device-id sal01
```

If you see E2EE fields (`session_key`, `ciphertext`, `nonce`, `tag`) in the payload, sensor data is secure! ✅


