# Fix MQTT "Not authorized" Error

## Problem
Flask is getting "Not authorized" when trying to publish to MQTT topic `provision/+/update`.

## Solution: Configure MQTT ACL (Access Control List)

The MQTT user needs permission to **publish** to the provision topics.

### On Raspberry Pi (where Mosquitto is running):

1. **Check your Mosquitto ACL file** (usually `/etc/mosquitto/acl.conf` or `/etc/mosquitto/conf.d/acl.conf`):

```bash
sudo nano /etc/mosquitto/acl.conf
```

2. **Add publish permissions for the MQTT user**:

```
# Allow user to publish to provision topics
user <YOUR_MQTT_USER>
topic write provision/+/request
topic write provision/+/update
topic write provision/+/delete
topic read keys/+/public
```

Replace `<YOUR_MQTT_USER>` with your actual MQTT username (the value of `MQTT_USER` environment variable).

3. **If using pattern-based ACL**:

```
pattern write provision/%c/request
pattern write provision/%c/update
pattern write provision/%c/delete
pattern read keys/%c/public
```

4. **Restart Mosquitto**:

```bash
sudo systemctl restart mosquitto
```

### Verify MQTT User and Password

On Windows (where Flask runs), check your environment variables:

```powershell
# Check current values
$env:MQTT_USER
$env:MQTT_PASSWORD
$env:MQTT_HOST
$env:MQTT_PORT

# If not set, set them:
$env:MQTT_USER = "your_mqtt_username"
$env:MQTT_PASSWORD = "your_mqtt_password"
$env:MQTT_HOST = "192.168.43.214"  # Your Raspberry Pi IP
$env:MQTT_PORT = "8883"  # or 1883 if not using TLS
```

### Test MQTT Publish Permission

You can test if the user can publish using the test script:

```powershell
.\test_mqtt_publish.ps1
```

Or manually test with Python:

```python
import paho.mqtt.publish as publish
import os

publish.single(
    "provision/test_device/update",
    '{"device_id":"test_device","action":"update"}',
    hostname=os.environ.get('MQTT_HOST'),
    port=int(os.environ.get('MQTT_PORT', '1883')),
    auth={
        'username': os.environ.get('MQTT_USER'),
        'password': os.environ.get('MQTT_PASSWORD')
    }
)
```

If this fails with "Not authorized", the ACL configuration is the issue.

### Common ACL File Locations

- `/etc/mosquitto/acl.conf`
- `/etc/mosquitto/conf.d/acl.conf`
- `/etc/mosquitto/mosquitto.conf` (inline ACL rules)

### Check Mosquitto Logs

On Raspberry Pi:

```bash
sudo tail -f /var/log/mosquitto/mosquitto.log
```

When you try to publish, you should see authorization errors if ACL is blocking.
