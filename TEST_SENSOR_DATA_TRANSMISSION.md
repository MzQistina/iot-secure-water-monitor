# Test Sensor Data Transmission - Next Steps

Since the provision agent is working, let's test the complete end-to-end flow by sending sensor data.

---

## ✅ What's Already Working

- ✅ MQTT broker running on Raspbian (192.168.56.102:8883 with TLS)
- ✅ Provision agent working and publishing keys
- ✅ Flask app receiving keys (if running)

---

## 🎯 Next Steps

### Step 1: Ensure Flask App is Running on Windows

**Option A: Run Flask directly (for testing)**
```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"

# Set environment variables
$env:MQTT_HOST = "192.168.56.102"
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_TLS_INSECURE = "true"
$env:MQTT_KEYS_TOPIC = "keys/+/public"

# Run Flask
python app.py
```

**Option B: Use Apache/mod_wsgi (production)**

Make sure Apache is configured correctly (see `UPDATE_APACHE_MQTT_ENV.md`) and restart Apache:
```powershell
net stop Apache2.4
net start Apache2.4
```

Check Apache logs:
```powershell
Get-Content C:\Apache24\logs\error.log -Tail 30
```

Look for:
```
MQTT: Connecting to 192.168.56.102:8883 (TLS)
MQTT: connected rc=0; subscribed to 'keys/+/public'
```

---

### Step 2: Run Sensor Simulator on Raspbian

**Important:** Use `localhost` (not `192.168.56.102`) because the broker is on the same machine.

**Set environment variables on Raspbian:**
```bash
cd ~/Desktop/fyp/iot-secure-water-monitor  # or your project directory
export MQTT_HOST=localhost  # Use localhost on Raspbian (broker is on same machine)
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
```

**Run sensor simulator:**

```bash
# Simulate all active sensors (recommended)
python simulators/sensor/sensor_simulator.py --all

# Or simulate specific sensors
python simulators/sensor/sensor_simulator.py --ids sensor1,sensor2

# With options (send 5 readings, 2 seconds apart, safe mode)
python simulators/sensor/sensor_simulator.py --all --repeat 5 --interval 2.0 --mode safe
```

**What happens:**
- Sensor simulator reads active sensors from database
- Generates simulated sensor readings
- Encrypts data with AES
- Publishes to MQTT topic: `secure/sensor`
- Flask app receives, decrypts, and stores data

---

### Step 3: Verify Data Reception

**Check Flask logs (if running directly):**
Look for:
```
MQTT: Message received on topic: secure/sensor
Decrypted data: {...}
```

**Check Apache logs (if using Apache):**
```powershell
Get-Content C:\Apache24\logs\error.log -Tail 50 | Select-String "MQTT|sensor|secure"
```

**Check database:**
- Open web interface: `http://localhost`
- Navigate to sensor data/logs
- Verify new readings appear

---

## 📋 Complete End-to-End Test Flow

### Test Sequence:

1. **Start Flask app** (Windows)
   ```powershell
   # Set env vars and run
   python app.py
   ```
   
2. **Run provision agent** (Raspbian) - ✅ Already working
   ```bash
   export MQTT_HOST=localhost
   export MQTT_PORT=8883
   export MQTT_USE_TLS=true
   export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
   python simulators/sensor/provision_agent.py
   ```
   
3. **Verify keys received** (Windows)
   - Check Flask logs for key reception
   - Keys should be stored in database
   
4. **Run sensor simulator** (Raspbian)
   ```bash
   export MQTT_HOST=localhost
   export MQTT_PORT=8883
   export MQTT_USE_TLS=true
   export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
   python simulators/sensor/sensor_simulator.py --all --repeat 5
   ```
   
5. **Verify data received** (Windows)
   - Check Flask logs
   - Check web interface
   - Verify data in database

---

## 🔧 Troubleshooting

### Sensor simulator can't connect to MQTT

**Error:** `Connection refused` or `TLS error`

**Fix:**
- Verify `MQTT_HOST=localhost` (not `192.168.56.102`)
- Check Mosquitto is running: `sudo systemctl status mosquitto`
- Verify TLS config: `sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v`

### Flask app not receiving sensor data

**Check:**
1. Flask app is subscribed to `secure/sensor` topic
2. MQTT connection is active: Look for "MQTT: connected" in logs
3. Network connectivity: `Test-NetConnection -ComputerName 192.168.56.102 -Port 8883`
4. Sensor simulator is publishing: Check simulator output for "Published message"

### Data not decrypting

**Error:** `Failed to decrypt data` or `Invalid hash`

**Fix:**
- Verify keys are provisioned (run provision agent first)
- Check sensor has valid encryption key in database
- Verify AES key matches (should be `my16bytepassword` for testing)

### No sensors found

**Error:** `No active sensors found`

**Fix:**
- Ensure sensors exist in database
- Check sensors are marked as active/online
- Verify sensor IDs match between database and simulator

---

## 📡 MQTT Topics Used

| Purpose | Topic | Publisher | Subscriber |
|---------|-------|-----------|------------|
| **Key Provisioning** | `keys/{device_id}/public` | Provision Agent (Raspbian) | Flask App (Windows) |
| **Sensor Data** | `secure/sensor` | Sensor Simulator (Raspbian) | Flask App (Windows) |

---

## 🎉 Success Indicators

✅ **Provision agent working:**
- Keys published successfully
- No connection errors

✅ **Sensor simulator working:**
- Messages published successfully
- No encryption errors

✅ **Flask app working:**
- Receives keys from provision agent
- Receives sensor data from simulator
- Data decrypted successfully
- Data stored in database
- Data visible in web interface

---

## 📚 Next Steps After Testing

1. ✅ Test end-to-end flow (you are here)
2. Fix certificate CN for production (remove insecure mode)
3. Set up MQTT authentication (username/password)
4. Connect real sensors (if applicable)
5. Configure production settings

---

## 🔍 Quick Verification Commands

**On Raspbian:**
```bash
# Test MQTT subscription (should see messages)
mosquitto_sub -h localhost -p 8883 -t secure/sensor --cafile /etc/mosquitto/certs/ca-cert.pem -v

# Check Mosquitto is listening
sudo netstat -tlnp | grep mosquitto
```

**On Windows:**
```powershell
# Test network connectivity
Test-NetConnection -ComputerName 192.168.56.102 -Port 8883

# Check Flask app logs (if running directly)
# Look for MQTT connection and message reception

# Check Apache logs (if using Apache)
Get-Content C:\Apache24\logs\error.log -Tail 50 | Select-String "MQTT"
```





















