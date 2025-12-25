# Test Key Provisioning

Your Flask app is now connected to MQTT! Let's test key provisioning.

## Current Status ✅

- Flask app running on `http://127.0.0.1:5000`
- MQTT connected to `192.168.56.102:8883` (TLS)
- Subscribed to `keys/+/public` topic
- Ready to receive device keys!

## Test Key Provisioning

### Step 1: On Raspbian - Set Environment Variables

**SSH into your Raspbian VM or open terminal:**

```bash
cd ~/water-monitor  # or your project directory

# Set MQTT environment variables
export MQTT_HOST=localhost
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
```

### Step 2: On Raspbian - Run Provision Agent

**Run the provision agent:**

```bash
python simulators/sensor/provision_agent.py
```

**What this does:**
- Generates RSA key pairs for devices
- Publishes public keys to MQTT topic `keys/{device_id}/public`
- Flask app receives and stores the keys

**Expected output on Raspbian:**
```
Provision agent started...
Listening for provision requests on topic: provision/+
```

### Step 3: On Windows - Trigger Provision Request

**Option A: Via Web Interface**
1. Open browser: `http://127.0.0.1:5000`
2. Log in to your account
3. Go to "Add Sensor" or "Register Device"
4. Enter a device ID (e.g., `sensor001`)
5. Click "Provision" or "Request Key"

**Option B: Via API (using curl or PowerShell)**

```powershell
# Get your session cookie first by logging in via browser
# Then use the session cookie:

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/provision" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"device_id": "sensor001"}' `
  -SessionVariable session

# Or using curl (if installed):
# curl -X POST http://127.0.0.1:5000/api/provision -H "Content-Type: application/json" -d "{\"device_id\": \"sensor001\"}"
```

### Step 4: Watch the Logs

**On Windows (Flask app terminal), you should see:**
```
MQTT: received key for unregistered device 'sensor001' (stored pending)
```

**Or if the device is already registered:**
```
MQTT: updated public key in DB for sensor 'sensor001'
```

**On Raspbian (provision agent terminal), you should see:**
```
Provision agent published key: keys/sensor001/public (user: 1)
```

## Verify Keys Were Received

### Check Flask App Logs

Look for messages like:
- `MQTT: received key for unregistered device 'sensor001' (stored pending)`
- `MQTT: updated public key in DB for sensor 'sensor001'`

### Check Database

**In your Flask app, you can check:**
1. Go to the web interface
2. Navigate to "Sensors" or "Devices"
3. Check if the device has a public key stored

### Check Key Files

**Keys are stored in:**
```
C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\user_keys\{user_id}\{device_id}_public.pem
```

## Troubleshooting

### No keys received?

1. **Check MQTT connection:**
   - Flask app should show: `MQTT: connected rc=0; subscribed to 'keys/+/public'`
   - If not, check environment variables

2. **Check provision agent is running:**
   - Should show: `Listening for provision requests on topic: provision/+`

3. **Check MQTT broker:**
   ```bash
   # On Raspbian
   sudo systemctl status mosquitto
   ```

4. **Test MQTT manually:**
   ```bash
   # On Raspbian - publish a test key
   mosquitto_pub -h localhost -p 8883 -t keys/test001/public -m "test-key" --cafile /etc/mosquitto/certs/ca-cert.pem
   ```
   
   **On Windows Flask app, you should see:**
   ```
   MQTT: received key for unregistered device 'test001' (stored pending)
   ```

### Provision agent not responding?

1. **Check environment variables on Raspbian:**
   ```bash
   echo $MQTT_HOST
   echo $MQTT_PORT
   echo $MQTT_USE_TLS
   ```

2. **Check provision agent can connect:**
   - Look for connection errors in provision agent output
   - Verify MQTT broker is accessible: `mosquitto_sub -h localhost -p 8883 -t test --cafile /etc/mosquitto/certs/ca-cert.pem`

### Keys received but not stored?

1. **Check database connection:**
   - Flask app should show database connection messages
   - Verify database credentials in environment variables

2. **Check device registration:**
   - Device must be registered in the database first
   - Or keys will be stored as "pending" until device is registered

## Next Steps

After key provisioning works:
1. ✅ Test sensor data transmission
2. ✅ Verify data is encrypted and decrypted correctly
3. ✅ Check web interface displays sensor data

See `NEXT_STEPS_AFTER_MQTT_SETUP.md` for complete testing guide.























