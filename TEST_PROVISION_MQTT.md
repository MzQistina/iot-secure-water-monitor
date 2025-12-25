# Testing MQTT Provision Messages Directly

This guide shows you how to test if MQTT provision messages are being published and received correctly.

## Method 1: Using the Test Script (Recommended)

### Step 1: Test Publishing a Message

```bash
# Test with default values (device: test_device, action: update, user: 1)
python test_provision_mqtt.py

# Test with specific device
python test_provision_mqtt.py sal01

# Test with specific device, action, and user
python test_provision_mqtt.py sal01 update 1

# Test request action
python test_provision_mqtt.py sal01 request 1
```

**Expected output:**
```
================================================================================
MQTT Provision Test
================================================================================
Host: 192.168.43.214:8883
User: water_monitor
TLS: True
Topic: provision/sal01/update
Payload: {"device_id":"sal01","action":"update","user_id":"1"}
================================================================================

📤 Publishing message...
✅ SUCCESS: Message published to provision/sal01/update

💡 Next steps:
   1. Check provision agent console output
   2. Look for: 'Provision agent received message:'
   3. Verify topic matches: provision/+/update
```

### Step 2: Test Subscribing (Listen for Messages)

In a separate terminal, run the subscribe test to see if messages are being published:

```bash
python test_provision_mqtt.py subscribe
```

This will:
- Connect to the MQTT broker
- Subscribe to all provision topics (`provision/+/request`, `provision/+/update`, `provision/+/delete`)
- Display any messages received
- Keep running until you press Ctrl+C

**Expected output:**
```
================================================================================
MQTT Subscribe Test
================================================================================
Subscribing to:
  - provision/+/request
  - provision/+/update
  - provision/+/delete

Waiting for messages (press Ctrl+C to stop)...
================================================================================
✅ Connected to MQTT broker
✅ Subscribed to provision topics

📨 RECEIVED MESSAGE:
   Topic: provision/sal01/update
   Payload: {
     "device_id": "sal01",
     "action": "update",
     "user_id": "1"
   }
```

## Method 2: Using mosquitto_pub (Command Line)

If you have `mosquitto_pub` installed (part of Mosquitto MQTT client tools):

### On Windows (if Mosquitto is installed):
```powershell
# Test publish (plain MQTT, no TLS)
mosquitto_pub -h 192.168.43.214 -p 1883 -u water_monitor -P e2eeWater2025 -t "provision/test123/update" -m '{"device_id":"test123","action":"update","user_id":"1"}'

# Test publish with TLS (if using TLS)
mosquitto_pub -h 192.168.43.214 -p 8883 -u water_monitor -P e2eeWater2025 -t "provision/test123/update" -m '{"device_id":"test123","action":"update","user_id":"1"}' --cafile C:\path\to\ca-cert.pem
```

### On Linux/Raspberry Pi:
```bash
# Test publish (plain MQTT, no TLS)
mosquitto_pub -h 192.168.43.214 -p 1883 -u water_monitor -P e2eeWater2025 -t "provision/test123/update" -m '{"device_id":"test123","action":"update","user_id":"1"}'

# Test publish with TLS (if using TLS)
mosquitto_pub -h 192.168.43.214 -p 8883 -u water_monitor -P e2eeWater2025 -t "provision/test123/update" -m '{"device_id":"test123","action":"update","user_id":"1"}' --cafile /etc/mosquitto/certs/ca-cert.pem
```

## Method 3: Using mosquitto_sub (Listen for Messages)

In a separate terminal, subscribe to see messages:

```bash
# Subscribe to all provision topics
mosquitto_sub -h 192.168.43.214 -p 8883 -u water_monitor -P e2eeWater2025 -t "provision/+/update" -t "provision/+/request" -t "provision/+/delete" -v --cafile /path/to/ca-cert.pem
```

The `-v` flag shows the topic name before each message.

## Method 4: Check Flask App Logs

After making a provision request from the web interface, check the Flask app logs:

**On Windows (Apache error log):**
```powershell
# Check Apache error log
Get-Content C:\path\to\Apache24\logs\error.log -Tail 50

# Or check flask_error.log
Get-Content flask_error.log -Tail 50
```

Look for lines like:
```
[Provision Update] ====== ABOUT TO CALL publish.single() ======
[Provision Update] Publishing to topic: provision/sal01/update
[Provision Update] Payload: {"device_id":"sal01","action":"update","user_id":"1"}
[Provision Update] ✅ Message published to MQTT broker
```

## Method 5: Check Provision Agent Logs

On the Raspberry Pi where provision_agent.py is running, you should see:

```
Provision agent received message:
  Topic: provision/sal01/update
  Payload: {"device_id":"sal01","action":"update","user_id":"1"}
  Device ID: sal01
  User ID: 1
  Action: UPDATE
Updating/regenerating keys for device 'sal01' (user: 1)
✅ Generated keys for device 'sal01' (user: 1) at /path/to/sensor_keys/1/sal01
Provision agent published key: keys/sal01/public (user: 1)
```

## Troubleshooting

### If publish succeeds but provision agent doesn't receive:

1. **Check topic match:**
   - Flask publishes to: `provision/{device_id}/update`
   - Provision agent subscribes to: `provision/+/update` ✅ (should match)

2. **Check MQTT broker ACL:**
   - User must have PUBLISH permission for `provision/+/update`
   - User must have SUBSCRIBE permission for `provision/+/update`

3. **Check provision agent is running:**
   ```bash
   ps aux | grep provision_agent
   ```

4. **Check provision agent connection:**
   - Look for: `Provision agent connected: rc=0`
   - Look for: `Provision agent subscribed to: provision/+/update`

5. **Test network connectivity:**
   ```bash
   # From Windows
   ping 192.168.43.214
   
   # Test MQTT port
   telnet 192.168.43.214 8883
   ```

### If publish fails:

1. **Check MQTT broker is running:**
   ```bash
   # On Raspberry Pi
   sudo systemctl status mosquitto
   ```

2. **Check credentials:**
   - Verify MQTT_USER and MQTT_PASSWORD are correct
   - Check MQTT broker password file

3. **Check TLS certificates:**
   - Verify CA certificate path is correct
   - Check certificate permissions

4. **Check firewall:**
   - Ensure port 8883 (or 1883) is open
   - Check if Windows Firewall is blocking connections

## Quick Test Checklist

- [ ] MQTT broker is running
- [ ] Provision agent is running and connected
- [ ] Test script can publish successfully
- [ ] Test script can subscribe and see messages
- [ ] Provision agent receives test messages
- [ ] Flask app logs show successful publish
- [ ] MQTT ACL allows publish/subscribe







