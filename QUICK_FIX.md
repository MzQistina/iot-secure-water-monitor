# Quick Fix for MQTT "Not authorized" Error

## Option 1: Run the Fix Script on Raspberry Pi (RECOMMENDED)

1. **Copy the fix script to your Raspberry Pi:**
   ```bash
   # On Windows, use SCP or copy the file manually
   # File: fix_mqtt_acl.sh
   ```

2. **On Raspberry Pi, run:**
   ```bash
   chmod +x fix_mqtt_acl.sh
   sudo MQTT_USER=your_username ./fix_mqtt_acl.sh
   ```
   
   Or let it prompt you:
   ```bash
   sudo ./fix_mqtt_acl.sh
   ```

## Option 2: Manual Fix (if script doesn't work)

### Step 1: Find your MQTT username
On Windows (PowerShell):
```powershell
$env:MQTT_USER
```

### Step 2: On Raspberry Pi, edit ACL file:
```bash
sudo nano /etc/mosquitto/acl.conf
```

### Step 3: Add these lines (replace `your_username` with actual username):
```
user your_username
topic write provision/+/request
topic write provision/+/update
topic write provision/+/delete
topic read keys/+/public
```

### Step 4: Make sure Mosquitto uses the ACL file:
```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add or verify this line exists:
```
acl_file /etc/mosquitto/acl.conf
```

### Step 5: Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

### Step 6: Verify it's running:
```bash
sudo systemctl status mosquitto
```

## Option 3: Temporary Workaround (NOT RECOMMENDED - Security Risk)

If you need a quick test and your broker is on a private network, you can temporarily disable ACL:

**On Raspberry Pi:**
```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Comment out or remove the `acl_file` line:
```
# acl_file /etc/mosquitto/acl.conf
```

Then restart:
```bash
sudo systemctl restart mosquitto
```

**⚠️ WARNING:** This disables access control. Only use for testing on a secure private network!

## Verify the Fix

After applying the fix, test from Windows:
```powershell
# Set environment variables first
$env:MQTT_HOST = "192.168.43.214"
$env:MQTT_USER = "your_username"
$env:MQTT_PASSWORD = "your_password"
$env:MQTT_PORT = "8883"

# Run test
.\test_mqtt_publish.ps1
```

If the test passes, try the provision request from the web interface again.
