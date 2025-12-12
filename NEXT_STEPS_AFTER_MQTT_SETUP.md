# Next Steps After MQTT TLS Setup

You've successfully set up secure MQTT communication! Here's what's done and what's next.

---

## ✅ What's Completed

1. **MQTT Broker (Raspbian)**
   - ✅ Mosquitto installed and running
   - ✅ TLS/SSL configured (port 8883)
   - ✅ Certificates generated
   - ✅ Listening on 192.168.56.102:8883

2. **Windows Client**
   - ✅ CA certificate copied to Windows
   - ✅ Environment variables configured
   - ✅ `mqtt_listener.py` working and receiving messages
   - ✅ Test messages successfully decrypted and verified

3. **Network**
   - ✅ Host-only adapter configured
   - ✅ Static IP (192.168.56.102) on Raspbian
   - ✅ Network connectivity verified

---

## 🎯 Next Steps

### 1. Integrate Flask App with MQTT

**Your Flask app (`app.py`) already has MQTT support built in!**

**On Windows, set environment variables using one of these methods:**

**Option A: Use the setup script (Recommended)**
```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
.\setup-mqtt-env.ps1
python app.py
```

**Option B: Set manually in PowerShell**
```powershell
$env:MQTT_HOST = "192.168.56.102"
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_TLS_INSECURE = "true"  # For testing (remove for production)
$env:MQTT_KEYS_TOPIC = "keys/+/public"  # Topic for key provisioning
python app.py
```

**Note:** The Flask app subscribes to these MQTT topics:
- `keys/+/public` - For receiving device public keys (provisioning)
- `water/data` - For sensor data (optional, used by some clients)
- `secure/sensor` - For sensor data (used by sensor simulator)

**Option C: Use .env file (requires python-dotenv)**
1. Copy `.env.example` to `.env`
2. Update values in `.env`
3. Install python-dotenv: `pip install python-dotenv`
4. Update `app.py` to load `.env` (add `from dotenv import load_dotenv; load_dotenv()` at the top)

**Check logs for:**
```
MQTT: Connecting to 192.168.56.102:8883 (TLS)
MQTT: connected rc=0; subscribed to 'keys/+/public'
```

---

### 2. Test Key Provisioning

**On Raspbian, run the provision agent:**

**Important:** Use `localhost` (not `192.168.56.102`) because the broker is on the same machine.

```bash
cd ~/water-monitor  # or wherever your project is
export MQTT_HOST=localhost  # Use localhost on Raspbian (broker is on same machine)
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
python simulators/sensor/provision_agent.py
```

**Note:** 
- On **Raspbian**: Use `MQTT_HOST=localhost` (broker is local)
- On **Windows**: Use `MQTT_HOST=192.168.56.102` (connecting to remote broker)

**This will:**
- Generate device keys
- Publish public keys to `keys/{device_id}/public` topic
- Flask app will receive and store the keys

---

### 3. Test Sensor Data Transmission

**Option A: Use Sensor Simulator (Raspbian)**

**Set environment variables on Raspbian:**

**Important:** Use `localhost` (not `192.168.56.102`) because the broker is on the same machine.

```bash
cd ~/water-monitor  # or your project directory
export MQTT_HOST=localhost  # Use localhost on Raspbian (broker is on same machine)
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
# Optional: MQTT authentication
# export MQTT_USER=your_username
# export MQTT_PASSWORD=your_password
```

**Note:** 
- On **Raspbian**: Use `MQTT_HOST=localhost` (broker is local)
- On **Windows**: Use `MQTT_HOST=192.168.56.102` (connecting to remote broker)

**Run sensor simulator:**
```bash
# Simulate all active sensors
python simulators/sensor/sensor_simulator.py --all

# Or simulate specific sensors
python simulators/sensor/sensor_simulator.py --ids sensor1,sensor2

# With options
python simulators/sensor/sensor_simulator.py --all --repeat 5 --interval 2.0 --mode safe
```

**Note:** The sensor simulator publishes to topic `secure/sensor` (hardcoded). The Flask app's MQTT listener subscribes to both `secure/sensor` and `water/data` topics.

**Option B: Use Real Sensors**
- Connect physical sensors to Raspbian
- Update `read_sensor_data()` function in your client code
- Send encrypted sensor data via MQTT

---

### 4. Fix Certificate CN for Production

**Currently using `MQTT_TLS_INSECURE=true` for testing.**

**For production, fix the certificate CN:**

**On Raspbian:**
```bash
# Check current CN
sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject

# If CN is not 192.168.56.102, regenerate:
cd /etc/mosquitto/certs
sudo openssl req -new -x509 -days 365 -key server-key.pem -out server-cert.pem -subj "/CN=192.168.56.102"
sudo chown mosquitto:mosquitto server-cert.pem
sudo chmod 644 server-cert.pem
sudo systemctl restart mosquitto

# Copy new CA cert to Windows
# Then remove MQTT_TLS_INSECURE=true
```

---

### 5. Set Up Authentication (Optional but Recommended)

**Currently using anonymous access (`allow_anonymous true`).**

**For production, set up username/password:**

**On Raspbian:**
```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user
# Enter password when prompted

# Update Mosquitto config
sudo nano /etc/mosquitto/conf.d/local.conf
```

**Add:**
```
allow_anonymous false
password_file /etc/mosquitto/passwd
```

**On Windows, set:**
```powershell
$env:MQTT_USER = "mqtt_user"
$env:MQTT_PASSWORD = "your_password"
```

---

### 6. Test End-to-End Flow

**Complete test:**

1. **Raspbian:** Run provision agent → Publishes keys
2. **Windows:** Flask app receives keys → Stores them
3. **Raspbian:** Run sensor simulator → Publishes encrypted data
4. **Windows:** Flask app receives data → Decrypts and displays
5. **Windows:** Open browser → View sensor data in web interface

---

## 📋 Checklist

- [ ] Flask app connected to MQTT broker
- [ ] Key provisioning tested (provision agent → Flask)
- [ ] Sensor data transmission tested (sensor simulator → Flask)
- [ ] Web interface displays sensor data
- [ ] Certificate CN fixed (remove insecure mode)
- [ ] Authentication configured (optional)
- [ ] Real sensors connected (if applicable)

---

## 🔧 Troubleshooting

### Flask app can't connect to MQTT
- Check environment variables: `echo $env:MQTT_HOST`
- Test network: `Test-NetConnection -ComputerName 192.168.56.102 -Port 8883`
- Check Flask logs for MQTT connection errors

### Keys not being received
- Verify provision agent is running on Raspbian
- Check MQTT topic: `keys/+/public`
- Check Flask logs for MQTT messages

### Sensor data not appearing
- Verify sensor simulator is running on Raspbian
- Check MQTT topics: 
  - Sensor simulator publishes to: `secure/sensor`
  - Flask app subscribes to: `secure/sensor` and `water/data`
- Verify environment variables are set on Raspbian (MQTT_HOST, MQTT_PORT, MQTT_USE_TLS, MQTT_CA_CERTS)
- Check Flask logs for decryption errors
- Test MQTT connection from Raspbian: `mosquitto_sub -h localhost -p 8883 -t secure/sensor --cafile /etc/mosquitto/certs/ca-cert.pem`

---

## 📡 MQTT Topics Reference

| Purpose | Topic | Publisher | Subscriber |
|---------|-------|-----------|------------|
| **Key Provisioning** | `keys/{device_id}/public` | Provision Agent (Raspbian) | Flask App (Windows) |
| **Provision Request** | `provision/{device_id}` | Flask App (Windows) | Provision Agent (Raspbian) |
| **Sensor Data** | `secure/sensor` | Sensor Simulator (Raspbian) | Flask App, mqtt_listener.py (Windows) |
| **Sensor Data (Alt)** | `water/data` | Manual/Other clients | Flask App, mqtt_listener.py (Windows) |
| **Device Deletion** | `devices/delete` | Flask App (Windows) | Key Cleanup Agent (Raspbian) |

**Environment Variables for Data Simulation (Raspbian):**

**Important:** Use `localhost` (not `192.168.56.102`) because the broker is on the same machine.

```bash
export MQTT_HOST=localhost  # Use localhost on Raspbian (broker is on same machine)
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
# Optional authentication:
# export MQTT_USER=your_username
# export MQTT_PASSWORD=your_password
```

**Note:** 
- On **Raspbian**: Use `MQTT_HOST=localhost` (broker is local)
- On **Windows**: Use `MQTT_HOST=192.168.56.102` (connecting to remote broker)
- The sensor simulator hardcodes the topic as `secure/sensor`. The Flask app's MQTT listener subscribes to both `secure/sensor` and `water/data` to support different clients.

---

## 📚 Related Documentation

- **[AFTER_TLS_MQTT_WORKING.md](AFTER_TLS_MQTT_WORKING.md)** - Windows setup guide
- **[SELF_HOSTED_MQTT_TLS_SETUP.md](SELF_HOSTED_MQTT_TLS_SETUP.md)** - Complete TLS setup
- **[RASPBERRY_VS_WINDOWS_SETUP.md](RASPBERRY_VS_WINDOWS_SETUP.md)** - What runs where

---

## 🎉 Summary

**You're ready to:**
1. ✅ Start Flask app with MQTT support
2. ✅ Test key provisioning
3. ✅ Test sensor data transmission
4. ✅ View data in web interface

**Next:** Start Flask app and test the complete flow!


