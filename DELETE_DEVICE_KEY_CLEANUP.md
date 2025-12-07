# Deleting Device Keys on Raspbian

When a device is deleted from the server, **you must also delete its keypairs on Raspbian VirtualBox** to maintain security and prevent unauthorized access.

## Why Delete Keys?

- **Security**: Prevents deleted devices from continuing to send data
- **Cleanup**: Removes unused keys from the system
- **Compliance**: Ensures proper key lifecycle management

## When to Delete Keys

Delete keys on Raspbian when:
- ✅ A device is deleted from the server dashboard
- ✅ A device is revoked/deactivated permanently
- ✅ A device is being replaced with a new one

## How to Delete Keys

### Step 1: Identify the Device to Delete

Before deleting on the server, note:
- **Device ID**: e.g., `pH01`, `tds01`
- **User ID**: e.g., `1`, `2` (if using user-specific keys)

### Step 2: Delete Device on Server

1. Log in to the server dashboard
2. Navigate to **Sensors** page
3. Click **Delete** button for the device
4. Confirm deletion

**⚠️ Important**: After deleting on the server, proceed to delete keys on Raspbian.

### Step 3: Delete Keys on Raspbian

**SSH into Raspbian VirtualBox or open terminal:**

```bash
cd ~/water-monitor

# Check if key exists (replace <user_id> and <device_id>)
ls -la sensor_keys/<user_id>/<device_id>/sensor_private.pem

# Delete the device's key directory
rm -rf sensor_keys/<user_id>/<device_id>/

# Verify deletion
ls -la sensor_keys/<user_id>/<device_id>/  # Should show "No such file or directory"
```

**Example:**
```bash
# Delete pH01 for user_id 1
rm -rf sensor_keys/1/pH01/

# Delete tds01 for user_id 2
rm -rf sensor_keys/2/tds01/

# Verify
ls sensor_keys/1/  # pH01 should be gone
ls sensor_keys/2/  # tds01 should be gone
```

### Step 4: Verify Cleanup

```bash
# List all remaining sensor keys
find sensor_keys -name "sensor_private.pem" -type f

# Check specific user's keys
ls -R sensor_keys/<user_id>/

# Should NOT see the deleted device_id
```

## Quick Delete Script

Create a helper script on Raspbian for easier cleanup:

```bash
# Create cleanup script
nano ~/water-monitor/delete_device_keys.sh
```

**Script content:**
```bash
#!/bin/bash
# Usage: ./delete_device_keys.sh <user_id> <device_id>

if [ $# -ne 2 ]; then
    echo "Usage: $0 <user_id> <device_id>"
    echo "Example: $0 1 pH01"
    exit 1
fi

USER_ID=$1
DEVICE_ID=$2
KEY_PATH="sensor_keys/${USER_ID}/${DEVICE_ID}"

if [ ! -d "$KEY_PATH" ]; then
    echo "⚠️  Key directory not found: $KEY_PATH"
    echo "   Checking alternative locations..."
    
    # Check legacy location
    if [ -d "sensor_keys/${DEVICE_ID}" ]; then
        echo "   Found in legacy location: sensor_keys/${DEVICE_ID}"
        read -p "Delete from legacy location? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "sensor_keys/${DEVICE_ID}"
            echo "✅ Deleted: sensor_keys/${DEVICE_ID}"
        fi
    else
        echo "❌ Key directory not found anywhere"
        exit 1
    fi
else
    echo "🗑️  Deleting keys for device: $DEVICE_ID (user: $USER_ID)"
    rm -rf "$KEY_PATH"
    echo "✅ Deleted: $KEY_PATH"
fi

# Verify deletion
if [ ! -d "$KEY_PATH" ] && [ ! -d "sensor_keys/${DEVICE_ID}" ]; then
    echo "✅ Verification: Keys successfully deleted"
else
    echo "⚠️  Warning: Keys may still exist"
fi
```

**Make executable:**
```bash
chmod +x ~/water-monitor/delete_device_keys.sh
```

**Usage:**
```bash
cd ~/water-monitor
./delete_device_keys.sh 1 pH01
```

## Delete Multiple Devices

To delete multiple devices at once:

```bash
cd ~/water-monitor

# Delete multiple devices for same user
rm -rf sensor_keys/1/pH01/
rm -rf sensor_keys/1/tds01/
rm -rf sensor_keys/1/turb01/

# Delete devices for different users
rm -rf sensor_keys/1/pH01/
rm -rf sensor_keys/2/pH01/  # Same device_id, different user

# Verify all deletions
find sensor_keys -name "sensor_private.pem" -type f
```

## Legacy Key Structure

If you're using the legacy key structure (without user_id folders):

```bash
# Delete from legacy location
rm -rf sensor_keys/<device_id>/

# Example
rm -rf sensor_keys/pH01/
```

## Complete Cleanup Checklist

After deleting a device:

- [ ] Device deleted from server dashboard
- [ ] Keys deleted on Raspbian: `sensor_keys/<user_id>/<device_id>/`
- [ ] Verified keys are gone: `ls sensor_keys/<user_id>/`
- [ ] Checked no orphaned keys remain
- [ ] Stopped any running simulations for that device (if any)

## Troubleshooting

### "No such file or directory"

If you see this error, the keys may have already been deleted or are in a different location:

```bash
# Search for the device_id in all locations
find sensor_keys -name "*<device_id>*" -type d

# Check legacy location
ls -la sensor_keys/<device_id>/
```

### "Permission denied"

If you get permission errors:

```bash
# Check permissions
ls -la sensor_keys/<user_id>/<device_id>/

# Fix permissions if needed
chmod -R 755 sensor_keys/<user_id>/<device_id>/

# Then delete
rm -rf sensor_keys/<user_id>/<device_id>/
```

### Device Still Sending Data

If a deleted device is still sending data:

1. **Check if simulation is still running:**
   ```bash
   ps aux | grep multi_sensor_client
   ```

2. **Stop the simulation:**
   ```bash
   pkill -f multi_sensor_client.py
   ```

3. **Verify keys are deleted:**
   ```bash
   ls -la sensor_keys/<user_id>/<device_id>/
   ```

4. **Restart simulation** (it will skip devices without keys)

## Security Best Practices

1. **Delete immediately**: Delete keys as soon as device is removed from server
2. **Verify deletion**: Always verify keys are gone after deletion
3. **Stop simulations**: Stop any running simulations before deleting keys
4. **Document changes**: Keep a log of deleted devices and when keys were removed
5. **Backup before deletion**: If needed, backup keys before deletion (though usually not necessary for deleted devices)

## Automated Cleanup via MQTT

The system now supports **automatic key deletion** when devices are deleted on the server!

### How It Works

1. **Server publishes deletion event** to MQTT topic `devices/delete`
2. **Raspbian cleanup agent** listens for deletion events
3. **Keys are automatically deleted** when event is received

### Setup Instructions

#### Step 1: Configure MQTT on Server (Windows)

Set environment variables or add to your server startup:

```bash
# Windows PowerShell
$env:MQTT_HOST = "192.168.1.100"  # Your MQTT broker IP
$env:MQTT_PORT = "1883"
$env:MQTT_USER = "your_username"  # Optional
$env:MQTT_PASSWORD = "your_password"  # Optional
$env:MQTT_DELETE_TOPIC = "devices/delete"  # Optional, defaults to devices/delete
```

Or add to your Apache/Flask configuration.

#### Step 2: Install Cleanup Agent on Raspbian

**Copy the cleanup agent script:**
```bash
# From Windows PowerShell
scp simulators/sensor/key_cleanup_agent.py pi@<raspbian_ip>:~/water-monitor/
```

**Make executable:**
```bash
# On Raspbian
cd ~/water-monitor
chmod +x key_cleanup_agent.py
```

#### Step 3: Run Cleanup Agent on Raspbian

**Option A: Run in foreground (for testing)**
```bash
cd ~/water-monitor
python3 key_cleanup_agent.py
```

**Option B: Run in background (recommended)**
```bash
cd ~/water-monitor
nohup python3 key_cleanup_agent.py > cleanup_agent.log 2>&1 &
```

**Option C: Run as systemd service (production)**
```bash
# Create service file
sudo nano /etc/systemd/system/key-cleanup-agent.service
```

**Service file content:**
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
Environment="SENSOR_KEYS_DIR=/home/pi/water-monitor/sensor_keys"
ExecStart=/usr/bin/python3 /home/pi/water-monitor/key_cleanup_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl enable key-cleanup-agent.service
sudo systemctl start key-cleanup-agent.service
sudo systemctl status key-cleanup-agent.service
```

#### Step 4: Configure Environment Variables (Optional)

Set on Raspbian if different from defaults:

```bash
export MQTT_HOST="192.168.1.100"
export MQTT_PORT="1883"
export MQTT_USER="your_username"
export MQTT_PASSWORD="your_password"
export MQTT_DELETE_TOPIC="devices/delete"
export SENSOR_KEYS_DIR="/home/pi/water-monitor/sensor_keys"
```

### Testing Automated Cleanup

1. **Start cleanup agent** on Raspbian
2. **Delete a device** from server dashboard
3. **Check agent logs** - should show deletion event received and keys deleted
4. **Verify keys are gone**: `ls sensor_keys/<user_id>/<device_id>/`

### Expected Output

When a device is deleted, you'll see:

**On Server:**
```
Sensor 'pH01' deleted. ✅ Key cleanup notification sent to Raspbian.
```

**On Raspbian (cleanup agent):**
```
🗑️  Received deletion request:
   Device ID: pH01
   User ID: 1
   Topic: devices/delete
✅ Deleted: /home/pi/water-monitor/sensor_keys/1/pH01
✅ Successfully deleted keys for device 'pH01'
```

### Troubleshooting Automated Cleanup

**Agent not receiving messages:**
- Check MQTT broker is running and accessible
- Verify MQTT_HOST and MQTT_PORT are correct
- Check firewall rules allow MQTT traffic
- Verify agent is subscribed to correct topic

**Keys not being deleted:**
- Check agent logs for errors
- Verify SENSOR_KEYS_DIR path is correct
- Check file permissions on sensor_keys directory
- Ensure user_id matches the key structure

**Agent not starting:**
- Check Python dependencies: `pip3 install paho-mqtt`
- Verify script is executable: `chmod +x key_cleanup_agent.py`
- Check Python version: `python3 --version` (requires Python 3.6+)

### Benefits of Automated Cleanup

- ✅ **No manual intervention** - Keys deleted automatically
- ✅ **Immediate cleanup** - No delay between deletion and cleanup
- ✅ **Consistent** - No risk of forgetting to delete keys
- ✅ **Scalable** - Works with multiple Raspbian instances
- ✅ **Auditable** - Logs show when keys were deleted

## Summary

**Quick Command:**
```bash
# On Raspbian, after deleting device on server:
cd ~/water-monitor
rm -rf sensor_keys/<user_id>/<device_id>/
```

**Remember:**
- ✅ Delete keys on Raspbian after deleting device on server
- ✅ Verify deletion with `ls` command
- ✅ Stop any running simulations for deleted devices
- ✅ Keep key structure clean and organized

