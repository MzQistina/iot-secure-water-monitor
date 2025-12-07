# Provision Agent Guide

Guide for running `provision_agent.py` to automatically generate sensor keys via MQTT.

## ✅ Good News: No Changes Needed!

The `provision_agent.py` **already supports user-specific key storage**. It automatically:
- ✅ Extracts `user_id` from MQTT message payload
- ✅ Creates keys in `sensor_keys/<user_id>/<device_id>/` structure
- ✅ Falls back to legacy structure if `user_id` is not provided

---

## 📋 How It Works

### 1. Server Sends Provision Request

When a user clicks "Provision" button on the web interface, the server sends an MQTT message:

**Topic:** `provision/<device_id>/request`

**Payload:**
```json
{
  "device_id": "pH01",
  "action": "generate_and_publish_key",
  "user_id": "5"
}
```

### 2. Provision Agent Receives Request

The `provision_agent.py` running on Raspberry Pi:
1. Subscribes to `provision/+/request` topic
2. Receives the message with `device_id` and `user_id`
3. Generates RSA key pair in `sensor_keys/<user_id>/<device_id>/`
4. Publishes public key to `keys/<device_id>/public` topic

### 3. Server Receives Public Key

The server's MQTT subscriber receives the public key and stores it in the database.

---

## 🚀 Running Provision Agent

### Prerequisites

1. **MQTT Broker** must be running and accessible
2. **Python dependencies** installed:
   ```bash
   pip3 install paho-mqtt pycryptodome
   ```

### Step 1: Set Environment Variables

**On Raspberry Pi (where provision agent runs):**

```bash
# Required: MQTT broker connection
export MQTT_HOST="192.168.1.100"        # MQTT broker IP
export MQTT_PORT="1883"                  # MQTT port

# Optional: MQTT authentication
export MQTT_USER="your_mqtt_username"
export MQTT_PASSWORD="your_mqtt_password"

# Optional: Topic configuration
export MQTT_PROVISION_TOPIC_BASE="provision"  # Default: "provision"
export MQTT_KEYS_TOPIC_BASE="keys"            # Default: "keys"

# Optional: TLS/SSL configuration
export MQTT_USE_TLS="false"                    # Enable TLS: "true"
export MQTT_CA_CERTS="/path/to/ca.crt"         # CA certificate
export MQTT_CERTFILE="/path/to/client.crt"    # Client certificate
export MQTT_KEYFILE="/path/to/client.key"      # Client private key
export MQTT_TLS_INSECURE="false"               # Skip cert validation: "true"
```

### Step 2: Run Provision Agent

**From project root directory:**

```bash
cd ~/water-monitor  # Or your project directory
python3 simulators/sensor/provision_agent.py
```

**Or run in background:**

```bash
nohup python3 simulators/sensor/provision_agent.py > provision_agent.log 2>&1 &
```

**Or run as systemd service** (recommended for production - auto-starts on boot):

See **[PROVISION_AGENT_AUTOMATION.md](PROVISION_AGENT_AUTOMATION.md)** for complete automation setup with:
- ✅ Auto-start on boot
- ✅ Auto-restart on failure
- ✅ Environment file configuration
- ✅ Log management
- ✅ Troubleshooting guide

**Quick setup:**

Create `/etc/systemd/system/provision-agent.service`:
```ini
[Unit]
Description=IoT Water Monitor Provision Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/water-monitor
Environment="MQTT_HOST=your-mqtt-broker-host.com"
Environment="MQTT_PORT=1883"
Environment="MQTT_USER=your_mqtt_username"
Environment="MQTT_PASSWORD=your_mqtt_password"
ExecStart=/usr/bin/python3 /home/pi/water-monitor/simulators/sensor/provision_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=provision-agent

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable provision-agent.service
sudo systemctl start provision-agent.service
sudo systemctl status provision-agent.service
```

**For detailed automation guide, see:** `PROVISION_AGENT_AUTOMATION.md`

---

## 📁 Key Storage Structure

### With `user_id` (New Structure)

When `user_id` is provided in MQTT payload:
```
sensor_keys/
└── 5/                    # User ID folder
    └── pH01/             # Device ID folder
        ├── sensor_private.pem
        └── sensor_public.pem
```

### Without `user_id` (Legacy Structure)

When `user_id` is NOT provided:
```
sensor_keys/
└── pH01/                 # Device ID folder (legacy)
    ├── sensor_private.pem
    └── sensor_public.pem
```

**Note:** The provision agent automatically detects `user_id` from the MQTT message and uses the appropriate structure.

---

## 🔍 Verification

### Check Provision Agent is Running

```bash
# Check if process is running
ps aux | grep provision_agent

# Check logs (if running in background)
tail -f provision_agent.log
```

### Test Provision Request

**From server (Windows), trigger provision:**

```powershell
# Via web interface: Click "Provision" button for a sensor
# OR via API:
curl -X POST http://localhost/api/provision/request \
  -H "Content-Type: application/json" \
  -d '{"device_id": "pH01"}'
```

**Expected output on provision agent:**
```
Provision agent connected: 0
Provision agent received message:
  Topic: provision/pH01/request
  Payload: {"device_id": "pH01", "action": "generate_and_publish_key", "user_id": "5"}
  Device ID: pH01
  User ID: 5
Generating keys for device 'pH01' (user: 5)
✅ Generated keys for device 'pH01' (user: 5) at /path/to/sensor_keys/5/pH01
Provision agent published key: keys/pH01/public (user: 5)
```

### Verify Keys Generated

```bash
# Check keys exist
ls -la ~/water-monitor/sensor_keys/5/pH01/

# Should show:
# sensor_private.pem
# sensor_public.pem
```

---

## 🐛 Troubleshooting

### Problem: "Provision agent not receiving messages"

**Solutions:**
1. Check MQTT broker is running and accessible
2. Verify `MQTT_HOST` and `MQTT_PORT` are correct
3. Test MQTT connection:
   ```bash
   mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -t "provision/+/request"
   ```
4. Check firewall allows MQTT port (usually 1883)

### Problem: "Keys generated in wrong location"

**Check:**
1. Verify `user_id` is included in MQTT payload (check server logs)
2. Check provision agent logs for `user_id` extraction
3. Verify `PROJECT_ROOT` is correct (should be project root directory)

### Problem: "Permission denied" when creating keys

**Solution:**
```bash
# Ensure directory is writable
chmod 755 ~/water-monitor/sensor_keys
chmod 755 ~/water-monitor/sensor_keys/* 2>/dev/null
```

### Problem: "TLS connection failed"

**Solutions:**
1. Verify certificate paths are correct
2. Check certificate permissions:
   ```bash
   chmod 644 $MQTT_CA_CERTS
   chmod 644 $MQTT_CERTFILE
   chmod 600 $MQTT_KEYFILE
   ```
3. For self-signed certs, set `MQTT_TLS_INSECURE="true"`

---

## 📊 Expected Behavior

### When `user_id` is Provided

1. ✅ Keys generated in `sensor_keys/<user_id>/<device_id>/`
2. ✅ Public key published to MQTT
3. ✅ Server receives and stores public key
4. ✅ Sensor can use private key for authentication

### When `user_id` is NOT Provided

1. ✅ Keys generated in `sensor_keys/<device_id>/` (legacy)
2. ✅ Public key published to MQTT
3. ✅ Server receives and stores public key
4. ✅ Sensor can use private key for authentication

**Both structures work!** The provision agent automatically handles both cases.

---

## 🔐 Security Notes

1. **Private keys** are stored with restricted permissions (`600`)
2. **Public keys** are published via MQTT (this is safe - they're public)
3. **TLS/SSL** should be enabled for production MQTT connections
4. **Authentication** should be configured (`MQTT_USER`/`MQTT_PASSWORD`)

---

## 📝 Summary

**No changes needed to run `provision_agent.py`!**

The code already:
- ✅ Supports user-specific key storage
- ✅ Extracts `user_id` from MQTT messages
- ✅ Creates keys in correct folder structure
- ✅ Falls back to legacy structure if needed

**Just run it:**
```bash
python3 simulators/sensor/provision_agent.py
```

The server automatically includes `user_id` when sending provision requests, so keys will be generated in the correct location automatically!

