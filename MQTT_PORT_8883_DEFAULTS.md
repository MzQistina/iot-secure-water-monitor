# MQTT Port 8883 Defaults - Updated

The provision agent and sensor simulator now default to using port **8883** (TLS) instead of port 1883 (plain MQTT) for secure communication.

---

## ✅ Changes Made

### 1. `provision_agent.py`
- **Default port:** Changed from `1883` → `8883`
- **Default TLS:** Changed from `false` → `true`
- **Default CA cert:** Set to `/etc/mosquitto/certs/ca-cert.pem`

### 2. `sensor_simulator.py`
- **Default port:** Changed from `1883` → `8883` (in `publish_mqtt_payload()`)
- **Default TLS:** Changed from `false` → `true`
- **Default CA cert:** Set to `/etc/mosquitto/certs/ca-cert.pem`

---

## 🚀 Usage

### Running Provision Agent (No environment variables needed)

**On Raspbian:**
```bash
cd ~/Desktop/fyp/iot-secure-water-monitor
python simulators/sensor/provision_agent.py
```

**It will automatically:**
- Connect to `localhost:8883` (TLS)
- Use CA cert at `/etc/mosquitto/certs/ca-cert.pem`
- Use TLS encryption

### Running Sensor Simulator (No environment variables needed)

**On Raspbian:**
```bash
cd ~/Desktop/fyp/iot-secure-water-monitor
python simulators/sensor/sensor_simulator.py --all
```

**It will automatically:**
- Connect to `localhost:8883` (TLS)
- Use CA cert at `/etc/mosquitto/certs/ca-cert.pem`
- Use TLS encryption

---

## 🔧 Overriding Defaults (Optional)

You can still override these defaults by setting environment variables:

```bash
# Use different port
export MQTT_PORT=1883

# Disable TLS (not recommended)
export MQTT_USE_TLS=false

# Use different CA cert path
export MQTT_CA_CERTS=/path/to/ca-cert.pem

# Set MQTT host (if broker is not on localhost)
export MQTT_HOST=192.168.56.102
```

---

## 📝 What This Means

- **Before:** You had to manually set `MQTT_PORT=8883` and `MQTT_USE_TLS=true` every time
- **After:** Scripts default to secure MQTT (port 8883 with TLS) automatically
- **Benefit:** More secure by default, easier to use on Raspbian

---

## ⚠️ Important Notes

1. **TLS Certificate:** The default CA cert path (`/etc/mosquitto/certs/ca-cert.pem`) must exist on Raspbian. This is where Mosquitto stores certificates.

2. **Localhost vs IP:** 
   - On **Raspbian**: Use `MQTT_HOST=localhost` (broker is on same machine)
   - On **Windows**: Use `MQTT_HOST=192.168.56.102` (connecting to remote broker)

3. **Environment Variables Still Work:** You can override any default by setting environment variables before running the scripts.

---

## 🔍 Verification

After running provision agent, you should see:
```
Provision agent: Connecting to localhost:8883 (TLS)
Provision agent: TLS enabled with CA cert: /etc/mosquitto/certs/ca-cert.pem
Provision agent connected: rc=0
```

After running sensor simulator, you should see:
```
Published encrypted data to MQTT (localhost:8883 with TLS).
```

---

## 🎉 Summary

- ✅ **Provision agent** now defaults to port 8883 (TLS)
- ✅ **Sensor simulator** now defaults to port 8883 (TLS)
- ✅ **No need to set environment variables** for basic usage on Raspbian
- ✅ **Secure by default** - uses TLS encryption automatically





















