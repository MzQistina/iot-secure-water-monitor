# How to Run Provision Agent

The provision agent runs on **Raspbian** and listens for key provisioning requests from the Flask app.

## Quick Start

### Step 1: On Raspbian - Set Environment Variables

```bash
cd ~/water-monitor  # or your project directory

# Set MQTT environment variables
export MQTT_HOST=localhost  # Use localhost (broker is on same machine)
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
```

### Step 2: Run Provision Agent

```bash
python simulators/sensor/provision_agent.py
```

**Expected output:**
```
Provision agent: Connecting to localhost:8883 (TLS)
Provision agent: TLS enabled with CA cert: /etc/mosquitto/certs/ca-cert.pem
Provision agent: TLS insecure mode enabled
Provision agent connected: 0
```

The agent is now listening for provision requests on topic: `provision/+/request`

## How It Works

1. **Flask app (Windows)** sends a provision request to MQTT topic: `provision/{device_id}/request`
2. **Provision agent (Raspbian)** receives the request
3. **Provision agent** generates RSA key pair for the device
4. **Provision agent** publishes public key to MQTT topic: `keys/{device_id}/public`
5. **Flask app (Windows)** receives and stores the public key

## Testing

### Test 1: Check Provision Agent is Running

**On Raspbian, you should see:**
```
Provision agent connected: 0
```

### Test 2: Trigger Provision Request from Flask App

**On Windows Flask app:**
1. Open browser: `http://127.0.0.1:5000`
2. Log in
3. Go to "Add Sensor" or "Register Device"
4. Enter device ID (e.g., `sensor001`)
5. Click "Provision" or "Request Key"

**On Raspbian (provision agent terminal), you should see:**
```
Provision agent received message:
  Topic: provision/sensor001/request
  Payload: {"device_id": "sensor001", "user_id": 1}
  Device ID: sensor001
  User ID: 1
Generating keys for device 'sensor001' (user: 1)
✅ Generated keys for device 'sensor001' (user: 1) at /path/to/sensor_keys/1/sensor001
Provision agent published key: keys/sensor001/public (user: 1)
```

**On Windows (Flask app terminal), you should see:**
```
MQTT: received key for unregistered device 'sensor001' (stored pending)
```

Or if device is already registered:
```
MQTT: updated public key in DB for sensor 'sensor001'
```

## Troubleshooting

### Provision agent can't connect to MQTT

**Check:**
1. Mosquitto is running:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Environment variables are set:
   ```bash
   echo $MQTT_HOST
   echo $MQTT_PORT
   echo $MQTT_USE_TLS
   ```

3. Test MQTT connection manually:
   ```bash
   mosquitto_sub -h localhost -p 8883 -t test --cafile /etc/mosquitto/certs/ca-cert.pem
   ```

### No provision requests received

**Check:**
1. Flask app is connected to MQTT:
   - Look for: `MQTT: connected rc=0; subscribed to 'keys/+/public'`

2. Flask app can publish to MQTT:
   - Check Flask logs for MQTT publish errors

3. Topics match:
   - Flask publishes to: `provision/{device_id}/request`
   - Provision agent subscribes to: `provision/+/request`

### Keys generated but not received by Flask

**Check:**
1. Flask app is subscribed to: `keys/+/public`
2. Network connectivity between Windows and Raspbian
3. MQTT broker is accessible from Windows

## Environment Variables Summary

| Variable | Value (Raspbian) | Description |
|----------|------------------|-------------|
| `MQTT_HOST` | `localhost` | MQTT broker host (use localhost on Raspbian) |
| `MQTT_PORT` | `8883` | MQTT broker port (TLS) |
| `MQTT_USE_TLS` | `true` | Enable TLS/SSL |
| `MQTT_CA_CERTS` | `/etc/mosquitto/certs/ca-cert.pem` | CA certificate path |
| `MQTT_TLS_INSECURE` | `true` | Skip certificate validation (for testing) |
| `MQTT_PROVISION_TOPIC_BASE` | `provision` (default) | Base topic for provision requests |
| `MQTT_KEYS_TOPIC_BASE` | `keys` (default) | Base topic for publishing keys |

## Key Storage

Keys are stored in:
```
~/water-monitor/sensor_keys/{user_id}/{device_id}/
  ├── sensor_private.pem  (600 permissions)
  └── sensor_public.pem   (644 permissions)
```

Or if no user_id:
```
~/water-monitor/sensor_keys/{device_id}/
  ├── sensor_private.pem
  └── sensor_public.pem
```

