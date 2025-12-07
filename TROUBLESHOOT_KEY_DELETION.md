# Troubleshooting: Keys Not Deleted on Raspbian

If keys are not being automatically deleted on Raspbian, follow these troubleshooting steps.

## Quick Diagnosis

### Step 1: Check if MQTT Notification Was Sent

**On Windows Server:**
- Check server logs when deleting a device
- Look for: `"MQTT: Sent key cleanup notification"` or `"MQTT: Error sending cleanup notification"`

**Expected messages:**
```
✅ If MQTT configured: "MQTT: Sent key cleanup notification for device 'pH01' (user: 1)"
❌ If MQTT not configured: No MQTT message (silent failure)
```

### Step 2: Check if Cleanup Agent is Running

**On Raspbian:**
```bash
# Check if agent process is running
ps aux | grep key_cleanup_agent

# Should show something like:
# pi 1234 0.1 2.3 ... python3 key_cleanup_agent.py
```

**If not running:**
```bash
cd ~/water-monitor
python3 key_cleanup_agent.py
```

### Step 3: Check Agent Logs

**On Raspbian:**
```bash
# If running in background
tail -f cleanup_agent.log

# Or check systemd logs
sudo journalctl -u key-cleanup-agent.service -f
```

**Look for:**
- Connection messages
- Received deletion messages
- Deletion success/failure

---

## Common Issues and Fixes

### Issue 1: MQTT Not Configured on Server

**Symptoms:**
- Server shows: "⚠️ Remember to delete keys on Raspbian"
- No MQTT messages in server logs

**Fix:**
```powershell
# On Windows (PowerShell)
$env:MQTT_HOST = "192.168.1.100"  # Your MQTT broker IP
$env:MQTT_PORT = "1883"
$env:MQTT_USER = "your_username"  # Optional
$env:MQTT_PASSWORD = "your_password"  # Optional

# Restart Flask server/Apache
```

**Or add to Apache config:**
```apache
SetEnv MQTT_HOST "192.168.1.100"
SetEnv MQTT_PORT "1883"
```

**Verify:**
```python
# Test in Python
import os
print(os.environ.get('MQTT_HOST'))  # Should show broker IP
```

---

### Issue 2: Cleanup Agent Not Running

**Symptoms:**
- MQTT messages sent but keys not deleted
- No agent process running

**Fix:**
```bash
# On Raspbian - Start agent
cd ~/water-monitor
python3 key_cleanup_agent.py

# Or run in background
nohup python3 key_cleanup_agent.py > cleanup_agent.log 2>&1 &

# Or install as systemd service (see DELETE_DEVICE_KEY_CLEANUP.md)
```

**Verify:**
```bash
ps aux | grep key_cleanup_agent
```

---

### Issue 3: MQTT Broker Not Accessible

**Symptoms:**
- Agent shows: "Failed to connect to MQTT broker"
- Connection errors in logs

**Fix:**

**Test connectivity:**
```bash
# On Raspbian
ping <mqtt_broker_ip>

# Test MQTT connection
mosquitto_sub -h <broker_ip> -t devices/delete -v
```

**Check firewall:**
```bash
# Allow MQTT port (1883)
sudo ufw allow 1883/tcp
```

**Verify broker is running:**
```bash
# On broker machine
sudo systemctl status mosquitto
```

---

### Issue 4: Wrong MQTT Topic

**Symptoms:**
- Agent connected but not receiving messages
- Messages published but not received

**Fix:**

**Check topic configuration:**

**On Server (app.py):**
```python
delete_topic = os.environ.get('MQTT_DELETE_TOPIC', 'devices/delete')
```

**On Raspbian (key_cleanup_agent.py):**
```python
MQTT_DELETE_TOPIC = os.environ.get('MQTT_DELETE_TOPIC', 'devices/delete')
```

**Must match!** Set both:
```bash
# On Windows
$env:MQTT_DELETE_TOPIC = "devices/delete"

# On Raspbian
export MQTT_DELETE_TOPIC="devices/delete"
```

**Test topic:**
```bash
# On Raspbian - listen to topic
mosquitto_sub -h <broker_ip> -t devices/delete -v

# On Windows - publish test message
mosquitto_pub -h <broker_ip> -t devices/delete -m '{"action":"delete","device_id":"test","user_id":"1"}'
```

---

### Issue 5: Keys in Wrong Location

**Symptoms:**
- Agent receives message but shows "Keys not found"
- Deletion fails silently

**Fix:**

**Check key location:**
```bash
# On Raspbian
ls -R ~/water-monitor/sensor_keys/

# Should see:
# sensor_keys/1/pH01/sensor_private.pem
```

**Verify SENSOR_KEYS_DIR:**
```bash
# Check agent's key directory
cd ~/water-monitor
python3 -c "
import os
SENSOR_KEYS_DIR = os.path.abspath('sensor_keys')
print(f'Agent will look in: {SENSOR_KEYS_DIR}')
print(f'Directory exists: {os.path.exists(SENSOR_KEYS_DIR)}')
"
```

**Set explicit path:**
```bash
export SENSOR_KEYS_DIR="/home/pi/water-monitor/sensor_keys"
python3 key_cleanup_agent.py
```

---

### Issue 6: Permission Issues

**Symptoms:**
- Agent receives message but can't delete keys
- Permission denied errors

**Fix:**
```bash
# Check permissions
ls -la ~/water-monitor/sensor_keys/1/pH01/

# Fix permissions
chmod -R 755 ~/water-monitor/sensor_keys/
chmod 600 ~/water-monitor/sensor_keys/*/*/sensor_private.pem

# Ensure agent can write
touch ~/water-monitor/sensor_keys/test.txt
rm ~/water-monitor/sensor_keys/test.txt
```

---

### Issue 7: JSON Parsing Errors

**Symptoms:**
- Agent receives message but shows "Invalid JSON"
- Malformed message errors

**Fix:**

**Check message format:**
```bash
# Test message format
python3 -c "
import json
msg = '{\"action\":\"delete\",\"device_id\":\"pH01\",\"user_id\":\"1\"}'
data = json.loads(msg)
print('Valid JSON:', data)
"
```

**Verify server sends correct format:**
- Check `app.py` `notify_raspbian_key_cleanup()` function
- Message should be valid JSON with `device_id` and `user_id`

---

## Step-by-Step Debugging

### 1. Test MQTT Connection

**On Raspbian:**
```bash
# Install mosquitto clients if needed
sudo apt-get install mosquitto-clients

# Subscribe to deletion topic
mosquitto_sub -h <broker_ip> -t devices/delete -v
```

**On Windows (separate terminal):**
```bash
# Publish test message
mosquitto_pub -h <broker_ip> -t devices/delete -m '{"action":"delete","device_id":"test01","user_id":"1"}'
```

**Expected:** Should see message in Raspbian terminal

---

### 2. Test Agent Manually

**On Raspbian:**
```bash
cd ~/water-monitor

# Run agent in foreground to see output
python3 key_cleanup_agent.py
```

**In another terminal, publish test:**
```bash
mosquitto_pub -h <broker_ip> -t devices/delete -m '{"action":"delete","device_id":"pH01","user_id":"1"}'
```

**Expected:** Agent should show deletion message and delete keys

---

### 3. Check Key Locations

**On Raspbian:**
```bash
# List all keys
find ~/water-monitor/sensor_keys -name "sensor_private.pem" -type f

# Check specific device
ls -la ~/water-monitor/sensor_keys/1/pH01/
```

**Verify agent can access:**
```bash
python3 -c "
import os
path = '/home/pi/water-monitor/sensor_keys/1/pH01'
print(f'Exists: {os.path.exists(path)}')
print(f'Is dir: {os.path.isdir(path)}')
print(f'Readable: {os.access(path, os.R_OK)}')
print(f'Writable: {os.access(path, os.W_OK)}')
"
```

---

### 4. Test Deletion Function Directly

**On Raspbian:**
```bash
cd ~/water-monitor
python3 -c "
import sys
sys.path.insert(0, 'simulators/sensor')
from key_cleanup_agent import delete_device_keys

# Test deletion
result = delete_device_keys('1', 'pH01')
print(f'Deletion result: {result}')
"
```

---

## Manual Deletion (Temporary Fix)

If automated deletion isn't working, delete keys manually:

```bash
# On Raspbian
cd ~/water-monitor

# Delete specific device keys
rm -rf sensor_keys/1/pH01/

# Or use helper script
./delete_device_keys.sh 1 pH01

# Verify deletion
ls sensor_keys/1/pH01/  # Should show "No such file"
```

---

## Complete Setup Verification

Run this checklist:

- [ ] **Server MQTT configured:** `echo $env:MQTT_HOST` shows broker IP
- [ ] **MQTT broker running:** `systemctl status mosquitto` shows active
- [ ] **Agent running:** `ps aux | grep key_cleanup_agent` shows process
- [ ] **Agent connected:** Logs show "Connected to MQTT broker"
- [ ] **Agent subscribed:** Logs show "Subscribed to topic: devices/delete"
- [ ] **Keys exist:** `ls sensor_keys/1/pH01/sensor_private.pem` shows file
- [ ] **Permissions OK:** Agent can read/write sensor_keys directory
- [ ] **Topic matches:** Server and agent use same topic name

---

## Quick Fix Script

Create a test script to verify everything:

**On Raspbian - `test_deletion.sh`:**
```bash
#!/bin/bash
echo "=== Testing Key Deletion Setup ==="

echo "1. Checking MQTT broker connectivity..."
ping -c 1 ${MQTT_HOST:-localhost} > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ MQTT broker reachable"
else
    echo "   ❌ MQTT broker not reachable"
fi

echo "2. Checking cleanup agent..."
if pgrep -f key_cleanup_agent.py > /dev/null; then
    echo "   ✅ Agent is running"
else
    echo "   ❌ Agent is NOT running"
fi

echo "3. Checking sensor keys directory..."
if [ -d "sensor_keys" ]; then
    echo "   ✅ sensor_keys directory exists"
    echo "   Found devices:"
    find sensor_keys -name "sensor_private.pem" -type f | head -5
else
    echo "   ❌ sensor_keys directory not found"
fi

echo "4. Testing MQTT subscription..."
timeout 2 mosquitto_sub -h ${MQTT_HOST:-localhost} -t devices/delete -C 1 > /dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "   ✅ Can subscribe to devices/delete topic"
else
    echo "   ❌ Cannot subscribe to topic"
fi

echo "=== Test Complete ==="
```

**Run:**
```bash
chmod +x test_deletion.sh
./test_deletion.sh
```

---

## Still Not Working?

If keys still aren't being deleted:

1. **Check all logs:**
   - Server logs (Apache/Flask)
   - Agent logs (`cleanup_agent.log`)
   - MQTT broker logs

2. **Test each component separately:**
   - MQTT publish/subscribe
   - Agent key deletion function
   - File permissions

3. **Use manual deletion** as temporary workaround:
   ```bash
   rm -rf sensor_keys/<user_id>/<device_id>/
   ```

4. **Report issue** with:
   - Server logs
   - Agent logs
   - MQTT broker status
   - Key directory structure











