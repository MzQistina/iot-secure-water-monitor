# Fix: Keys Not Deleted on Raspbian (MQTT Notification Sent)

Since you see "✅ Key cleanup notification sent", the server is working correctly. The issue is on Raspbian. Follow these steps:

## Step 1: Check if Cleanup Agent is Running

**On Raspbian:**
```bash
ps aux | grep key_cleanup_agent
```

**Expected output:**
```
pi 1234 0.1 2.3 ... python3 key_cleanup_agent.py
```

**If NOT running:**
```bash
cd ~/water-monitor

# Check if file exists
ls -la key_cleanup_agent.py

# If file doesn't exist, copy it from Windows:
# (From Windows PowerShell)
# scp simulators/sensor/key_cleanup_agent.py pi@<raspbian_ip>:~/water-monitor/

# Start agent
python3 key_cleanup_agent.py
```

---

## Step 2: Check Agent Logs

**If running in background:**
```bash
tail -f ~/water-monitor/cleanup_agent.log
```

**If running in foreground**, you should see:
```
✅ Connected to MQTT broker: <broker_ip>:1883
📡 Subscribed to topic: devices/delete
👂 Listening for device deletion events...
```

**When you delete a device, you should see:**
```
🗑️  Received deletion request:
   Device ID: pH01
   User ID: 1
   Topic: devices/delete
✅ Deleted: /home/pi/water-monitor/sensor_keys/1/pH01
✅ Successfully deleted keys for device 'pH01'
```

---

## Step 3: Verify MQTT Configuration

**Check agent's MQTT settings:**
```bash
cd ~/water-monitor
python3 -c "
import os
print('MQTT_HOST:', os.environ.get('MQTT_HOST', 'localhost (default)'))
print('MQTT_PORT:', os.environ.get('MQTT_PORT', '1883 (default)'))
print('MQTT_DELETE_TOPIC:', os.environ.get('MQTT_DELETE_TOPIC', 'devices/delete (default)'))
"
```

**Set if needed:**
```bash
export MQTT_HOST="192.168.1.100"  # Your MQTT broker IP
export MQTT_PORT="1883"
export MQTT_DELETE_TOPIC="devices/delete"

# Then start agent
python3 key_cleanup_agent.py
```

**Important:** The `MQTT_HOST` on Raspbian must match the broker IP that the server is using.

---

## Step 4: Test MQTT Connection Manually

**On Raspbian, test if you can receive messages:**
```bash
# Install mosquitto clients if needed
sudo apt-get install mosquitto-clients

# Subscribe to deletion topic
mosquitto_sub -h <broker_ip> -t devices/delete -v
```

**In another terminal (or from Windows), send test message:**
```bash
mosquitto_pub -h <broker_ip> -t devices/delete -m '{"action":"delete","device_id":"test01","user_id":"1"}'
```

**Expected:** You should see the message in the first terminal.

**If you DON'T see the message:**
- MQTT broker is not accessible from Raspbian
- Check firewall: `sudo ufw allow 1883/tcp`
- Check broker IP is correct
- Check network connectivity: `ping <broker_ip>`

---

## Step 5: Check Key Locations

**Verify keys exist:**
```bash
cd ~/water-monitor

# List all keys
find sensor_keys -name "sensor_private.pem" -type f

# Check specific device (replace with your device_id and user_id)
ls -la sensor_keys/1/pH01/
```

**Check agent's expected path:**
```bash
python3 -c "
import os
SENSOR_KEYS_DIR = os.path.abspath('sensor_keys')
print(f'Agent expects keys in: {SENSOR_KEYS_DIR}')
print(f'Directory exists: {os.path.exists(SENSOR_KEYS_DIR)}')

# Check specific device
user_id = '1'
device_id = 'pH01'  # Replace with your device
key_path = os.path.join(SENSOR_KEYS_DIR, user_id, device_id)
print(f'Key path: {key_path}')
print(f'Exists: {os.path.exists(key_path)}')
"
```

**If keys are in different location:**
```bash
# Set explicit path
export SENSOR_KEYS_DIR="/home/pi/water-monitor/sensor_keys"
python3 key_cleanup_agent.py
```

---

## Step 6: Test Deletion Function Directly

**Test if deletion function works:**
```bash
cd ~/water-monitor
python3 -c "
import sys
import os
sys.path.insert(0, '.')
from simulators.sensor.key_cleanup_agent import delete_device_keys

# Test with your actual device_id and user_id
user_id = '1'
device_id = 'pH01'  # Replace with device you want to test

print(f'Testing deletion of {device_id} for user {user_id}...')
result = delete_device_keys(user_id, device_id)
print(f'Result: {result}')
"
```

**If this works but agent doesn't:** The issue is with MQTT message reception.

---

## Step 7: Run Agent in Foreground with Debug

**Stop any running agent:**
```bash
pkill -f key_cleanup_agent.py
```

**Run in foreground to see all output:**
```bash
cd ~/water-monitor
python3 key_cleanup_agent.py
```

**Now delete a device from server and watch the output.**

**Expected output when deletion happens:**
```
🗑️  Received deletion request:
   Device ID: pH01
   User ID: 1
   Topic: devices/delete
✅ Deleted: /home/pi/water-monitor/sensor_keys/1/pH01
✅ Successfully deleted keys for device 'pH01'
```

**If you see errors:**
- Note the exact error message
- Check file permissions
- Check key path

---

## Step 8: Check Permissions

**Verify agent can delete keys:**
```bash
cd ~/water-monitor

# Check permissions
ls -la sensor_keys/1/pH01/

# Test deletion manually
rm -rf sensor_keys/1/pH01/test 2>&1
mkdir sensor_keys/1/pH01/test
rm -rf sensor_keys/1/pH01/test

# If successful, permissions are OK
```

**Fix permissions if needed:**
```bash
chmod -R 755 sensor_keys/
chmod 600 sensor_keys/*/*/sensor_private.pem
```

---

## Step 9: Verify Topic Name Matches

**Check server topic:**
- Server uses: `devices/delete` (default)
- Check server logs or code: `MQTT_DELETE_TOPIC`

**Check agent topic:**
```bash
cd ~/water-monitor
grep "MQTT_DELETE_TOPIC" key_cleanup_agent.py
```

**Must match!** If different, set environment variable:
```bash
export MQTT_DELETE_TOPIC="devices/delete"
python3 key_cleanup_agent.py
```

---

## Step 10: Run Agent as Background Service

**Create systemd service for reliable operation:**
```bash
sudo nano /etc/systemd/system/key-cleanup-agent.service
```

**Service file:**
```ini
[Unit]
Description=Key Cleanup Agent for Water Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/water-monitor
Environment="MQTT_HOST=192.168.1.100"
Environment="MQTT_PORT=1883"
Environment="MQTT_DELETE_TOPIC=devices/delete"
Environment="SENSOR_KEYS_DIR=/home/pi/water-monitor/sensor_keys"
ExecStart=/usr/bin/python3 /home/pi/water-monitor/key_cleanup_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable key-cleanup-agent.service
sudo systemctl start key-cleanup-agent.service
sudo systemctl status key-cleanup-agent.service
```

**View logs:**
```bash
sudo journalctl -u key-cleanup-agent.service -f
```

---

## Quick Test Script

**Create test script on Raspbian:**
```bash
cat > ~/water-monitor/test_deletion.sh << 'EOF'
#!/bin/bash
echo "=== Testing Key Deletion ==="

echo "1. Checking agent process..."
if pgrep -f key_cleanup_agent.py > /dev/null; then
    echo "   ✅ Agent is running"
    ps aux | grep key_cleanup_agent | grep -v grep
else
    echo "   ❌ Agent is NOT running"
fi

echo ""
echo "2. Checking MQTT connectivity..."
MQTT_HOST=${MQTT_HOST:-localhost}
if ping -c 1 $MQTT_HOST > /dev/null 2>&1; then
    echo "   ✅ Can ping MQTT broker: $MQTT_HOST"
else
    echo "   ❌ Cannot ping MQTT broker: $MQTT_HOST"
fi

echo ""
echo "3. Checking sensor keys..."
if [ -d "sensor_keys" ]; then
    echo "   ✅ sensor_keys directory exists"
    echo "   Found devices:"
    find sensor_keys -name "sensor_private.pem" -type f | head -5
else
    echo "   ❌ sensor_keys directory not found"
fi

echo ""
echo "4. Testing MQTT subscription (5 second timeout)..."
timeout 5 mosquitto_sub -h ${MQTT_HOST:-localhost} -t devices/delete -C 1 > /dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "   ✅ Can subscribe to devices/delete topic"
else
    echo "   ❌ Cannot subscribe to topic (check MQTT_HOST)"
fi

echo ""
echo "=== Test Complete ==="
EOF

chmod +x ~/water-monitor/test_deletion.sh
~/water-monitor/test_deletion.sh
```

---

## Most Common Issues

### Issue 1: Agent Not Running
**Fix:** Start agent: `python3 key_cleanup_agent.py`

### Issue 2: Wrong MQTT Broker IP
**Fix:** Set `export MQTT_HOST="<correct_ip>"`

### Issue 3: Keys in Wrong Location
**Fix:** Set `export SENSOR_KEYS_DIR="/home/pi/water-monitor/sensor_keys"`

### Issue 4: Topic Mismatch
**Fix:** Ensure both server and agent use `devices/delete`

### Issue 5: Permission Denied
**Fix:** `chmod -R 755 sensor_keys/`

---

## Manual Deletion (Temporary Workaround)

If automated deletion still doesn't work, delete manually:

```bash
cd ~/water-monitor

# Delete keys for specific device
rm -rf sensor_keys/<user_id>/<device_id>/

# Example:
rm -rf sensor_keys/1/pH01/

# Verify
ls sensor_keys/1/pH01/  # Should show "No such file"
```

---

## Next Steps

1. **Run the test script** above
2. **Check agent logs** when deleting a device
3. **Verify MQTT connection** manually
4. **Report findings** - which step fails?

The most likely issue is that the cleanup agent is not running or not receiving MQTT messages.









