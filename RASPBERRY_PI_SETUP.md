# Raspberry Pi Setup Guide - Complete

Complete guide for setting up Raspberry Pi for the IoT Secure Water Monitor project, including file transfer, MQTT configuration, and troubleshooting.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Files to Copy](#files-to-copy)
3. [Transfer Files (WinSCP/SCP)](#transfer-files)
4. [Install Dependencies](#install-dependencies)
5. [Configure Device](#configure-device)
6. [Test Connection](#test-connection)
7. [Run as Service](#run-as-service)
8. [MQTT Setup (Optional)](#mqtt-setup-optional)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

## Prerequisites

1. **Raspberry Pi** with Python 3 installed
2. **Sensor hardware** connected to Pi
3. **Network connectivity** to Flask server
4. **Sensor keys** generated and public key registered on server

## Files to Copy

### ✅ Essential Files (Required)

1. **`raspberry_pi_client.py`** - Main client script
2. **`encryption_utils.py`** - Encryption utilities
3. **`keys/public.pem`** - Server's public key
4. **`sensor_keys/<device_id>/sensor_private.pem`** - Device's private key
   - Replace `<device_id>` with your device ID (e.g., `pH01`, `tds01`)

### 📋 Optional Files (Recommended)

5. **`requirements_pi.txt`** - Python dependencies list

### 📁 Directory Structure on Raspberry Pi

After copying, your Raspberry Pi should have:

```
~/water-monitor/
├── raspberry_pi_client.py          # Main client script
├── encryption_utils.py              # Encryption utilities
├── requirements_pi.txt              # Python dependencies (optional)
├── keys/
│   └── public.pem                   # Server's public key
└── sensor_keys/
    └── <device_id>/                 # e.g., pH01, tds01
        └── sensor_private.pem       # Device's private key
```

## Transfer Files

### Option 1: Using WinSCP (Windows GUI - Recommended)

**Step 1: Connect to Raspberry Pi**
1. Open WinSCP
2. Click "New Site" or "New Session"
3. Enter connection details:
   - **File protocol**: SFTP
   - **Host name**: `raspberrypi.local` (or your Pi's IP, e.g., `192.168.1.100`)
   - **Port number**: `22`
   - **User name**: `pi`
   - **Password**: Your Raspberry Pi password
4. Click "Login"

**Step 2: Create Directories**
1. Right panel: Navigate to `/home/pi/`
2. Right-click → **New** → **Directory** → Name: `water-monitor`
3. Double-click `water-monitor` to open it
4. Create subdirectories:
   - `keys` (Right-click → New → Directory)
   - `sensor_keys` (Right-click → New → Directory)
5. Open `sensor_keys` and create folder with your device ID (e.g., `pH01`)

**Step 3: Copy Files**
1. **Left panel (Windows)**: Navigate to your `iot-secure-water-monitor` folder
2. **Right panel (Raspberry Pi)**: Navigate to `/home/pi/water-monitor/`

   **Copy these files:**
   - `raspberry_pi_client.py` → `/home/pi/water-monitor/`
   - `encryption_utils.py` → `/home/pi/water-monitor/`
   - `requirements_pi.txt` → `/home/pi/water-monitor/` (optional)
   - `keys/public.pem` → `/home/pi/water-monitor/keys/`
   - `sensor_keys/pH01/sensor_private.pem` → `/home/pi/water-monitor/sensor_keys/pH01/`
     *(Replace `pH01` with your actual device ID)*

   **How to copy:**
   - Select file(s) on left → Drag to right panel
   - OR: Right-click file → **Copy** → Navigate to destination → Right-click → **Paste**

**Step 4: Set File Permissions**
1. Right-click `raspberry_pi_client.py` → **Properties** → Check **Execute** → **OK**
2. Right-click `sensor_keys/pH01/sensor_private.pem` → **Properties** → 
   - Set permissions to `600` (Owner: Read+Write, Others: None)
   - **OK**

### Option 2: Using Command Line (SCP)

```bash
# From your development machine (in project root)
# Create directories on Pi
ssh pi@raspberrypi.local "mkdir -p ~/water-monitor/{keys,sensor_keys}"

# Copy main scripts
scp raspberry_pi_client.py encryption_utils.py pi@raspberrypi.local:~/water-monitor/

# Copy server public key
scp keys/public.pem pi@raspberrypi.local:~/water-monitor/keys/

# Copy device private key (replace pH01 with your device ID)
scp sensor_keys/pH01/sensor_private.pem pi@raspberrypi.local:~/water-monitor/sensor_keys/pH01/

# Copy requirements file
scp requirements_pi.txt pi@raspberrypi.local:~/water-monitor/
```

**Set permissions via SSH:**
```bash
ssh pi@raspberrypi.local
cd ~/water-monitor
chmod +x raspberry_pi_client.py
chmod 600 sensor_keys/pH01/sensor_private.pem
```

## Install Dependencies

SSH into your Raspberry Pi and install required packages:

```bash
ssh pi@raspberrypi.local
cd ~/water-monitor

# Install Python packages
pip3 install requests pycryptodome

# If using MQTT provision agent, also install:
pip3 install paho-mqtt

# Or if using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install requests pycryptodome paho-mqtt
```

**Note**: The `paho-mqtt` package is only needed if you're running the provision agent (`provision_agent.py`) on the Raspberry Pi. The main client (`raspberry_pi_client.py`) only uses HTTP/HTTPS.

## Configure Device

1. **Ensure sensor is registered** on the Flask server:
   - Device ID matches your Pi's device ID
   - Status is `active`
   - Public key is registered

2. **Update the script** to read from your actual sensors:
   - Edit `read_sensor_data()` function in `raspberry_pi_client.py`
   - Replace placeholder code with actual sensor reading code

**Example for reading from I2C sensor:**

```python
def read_sensor_data():
    """Read from actual sensors."""
    import board
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    
    # Initialize ADC
    i2c = board.I2C()
    ads = ADS.ADS1115(i2c)
    channel = AnalogIn(ads, ADS.P0)
    
    # Read and convert to actual values
    ph_value = convert_to_ph(channel.voltage)
    
    return {
        "device_id": device_id,
        "device_type": "ph",
        "ph": ph_value,
        "temperature": read_temperature(),
        # ... other sensor readings
    }
```

## Test Connection

### Test 1: Single Reading

```bash
python3 raspberry_pi_client.py pH01 http://192.168.1.100:5000 --once
```

Expected output:
```
======================================================================
Raspberry Pi Secure Water Monitor Client
======================================================================
Device ID: pH01
Server URL: http://192.168.1.100:5000
Private Key: /home/pi/water-monitor/sensor_keys/pH01/sensor_private.pem
Interval: 60 seconds
======================================================================
[Session] Requesting challenge for device 'pH01'...
[Session] Signing challenge and establishing session...
[Session] ✅ Session established (expires in 900s)
[Submit] ✅ Reading submitted (counter=1)
         Water is safe to drink
```

### Test 2: Continuous Readings

```bash
python3 raspberry_pi_client.py pH01 http://192.168.1.100:5000 --interval 30
```

This will submit readings every 30 seconds. Press Ctrl+C to stop.

## Run as Service

To run the client automatically on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/water-monitor.service
```

Add this content:

```ini
[Unit]
Description=Water Monitor Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/water-monitor
ExecStart=/usr/bin/python3 /home/pi/water-monitor/raspberry_pi_client.py pH01 http://192.168.1.100:5000 --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable water-monitor.service
sudo systemctl start water-monitor.service

# Check status
sudo systemctl status water-monitor.service

# View logs
sudo journalctl -u water-monitor.service -f
```

## MQTT Setup (Optional)

**When do you need MQTT?**
- ✅ Running `provision_agent.py` on Raspberry Pi
- ✅ Using MQTT for key exchange/provisioning

**You DON'T need MQTT if:**
- ❌ Only using `raspberry_pi_client.py` (uses HTTP/HTTPS)
- ❌ Provision agent runs on server/cloud
- ❌ Using HTTP-based key upload only

### Step 1: Install MQTT Client Library

```bash
pip3 install paho-mqtt
```

### Step 2: Configure MQTT Environment Variables

Create configuration script:

```bash
nano ~/water-monitor/mqtt_config.sh
```

Add content:

```bash
#!/bin/bash
# MQTT Configuration for Provision Agent

# Basic MQTT Settings
export MQTT_HOST=your-mqtt-broker.com
export MQTT_PORT=8883  # Use 8883 for TLS, 1883 for plain (not secure)

# TLS Configuration (Required for Production)
export MQTT_USE_TLS=true
export MQTT_CA_CERTS=/home/pi/water-monitor/certs/ca-cert.pem

# Authentication
export MQTT_USER=your_mqtt_username
export MQTT_PASSWORD=your_mqtt_password

# Topic Configuration
export MQTT_PROVISION_TOPIC_BASE=provision
export MQTT_KEYS_TOPIC_BASE=keys
```

Make executable:
```bash
chmod +x ~/water-monitor/mqtt_config.sh
```

### Step 3: Set Up TLS Certificates

```bash
# Create certs directory
mkdir -p ~/water-monitor/certs

# Download CA certificate from your MQTT broker
scp user@mqtt-server:/path/to/ca-cert.pem ~/water-monitor/certs/

# Set permissions
chmod 644 ~/water-monitor/certs/ca-cert.pem
```

### Step 4: Run Provision Agent

```bash
# Source configuration
source ~/water-monitor/mqtt_config.sh

# Run provision agent
cd ~/water-monitor
python3 simulators/sensor/provision_agent.py
```

**See `MQTT_TLS_SETUP.md` for complete TLS configuration details.**

## Troubleshooting

### "device not active or not found"
- Check device is registered: Visit `http://server:5000/sensors` in browser
- Verify device_id matches exactly
- Ensure status is `active`

### "Private key not found"
- Verify path to private key file
- Check file permissions: `chmod 600 sensor_keys/<device_id>/sensor_private.pem`

### "Failed to establish session"
- Check network connectivity: `ping <server_ip>`
- Verify server is running: `curl http://<server_ip>:5000/api/device/session/request?device_id=<device_id>`
- Check server logs for errors

### "Invalid signature"
- Verify you're using the correct private key for the device
- Ensure public key is registered on server
- Check that private/public key pair matches

### "encryption_utils.py not found"
- Ensure `encryption_utils.py` is in the same directory as `raspberry_pi_client.py`
- Check file path: `ls -la ~/water-monitor/encryption_utils.py`

### "Server public key not found"
- Verify `keys/public.pem` exists: `ls -la ~/water-monitor/keys/public.pem`
- Check file was copied correctly

### Session expires frequently
- Default session TTL is 900 seconds (15 minutes)
- Sessions auto-renew on each use
- If readings are less frequent than 15 minutes, increase `DEVICE_SESSION_TTL_SECONDS` on server

### MQTT Connection Issues (If Using Provision Agent)

**Connection Refused:**
- Check `MQTT_HOST` and `MQTT_PORT` are correct
- Verify broker is running and accessible
- Check firewall allows port 8883 (TLS) or 1883 (plain)

**Certificate Verification Failed:**
- Verify `MQTT_CA_CERTS` path is correct
- Ensure CA certificate matches broker's certificate
- For self-signed certificates, set `MQTT_TLS_INSECURE=true` (development only)

## Security Best Practices

1. **Protect Private Keys**
   ```bash
   chmod 600 sensor_keys/*/sensor_private.pem
   ```

2. **Use HTTPS in Production**
   - Set up SSL/TLS certificate on Flask server
   - Update server_url to use `https://` instead of `http://`
   - Example: `https://your-server.com:5000`

3. **Secure MQTT (If Using Provision Agent)**
   - Always use TLS in production (port 8883)
   - Never use plain MQTT (port 1883) for production
   - Use strong passwords for MQTT authentication
   - Protect certificate files: `chmod 644 ~/water-monitor/certs/ca-cert.pem`

4. **Network Security**
   - Use firewall rules to restrict access
   - Consider VPN for remote access

5. **Monitor Sessions**
   - Check database for active sessions:
     ```sql
     SELECT * FROM device_sessions WHERE device_id = 'pH01';
     ```

## Testing Checklist

- [ ] Sensor registered on server with `active` status
- [ ] Public key uploaded to server
- [ ] Private key present on Raspberry Pi
- [ ] Server public key present on Raspberry Pi
- [ ] Network connectivity verified
- [ ] Single reading test successful
- [ ] Continuous readings working
- [ ] Session renewal working (check after 15 minutes)
- [ ] Counter incrementing correctly
- [ ] Service running (if using systemd)
- [ ] MQTT configured (if using provision agent)

## Next Steps

1. Integrate with your actual sensor hardware
2. Add error handling for sensor read failures
3. Implement data buffering for offline scenarios
4. Add logging for debugging
5. Set up monitoring/alerting for failed submissions

## Related Documentation

- **MQTT_TLS_SETUP.md** - Complete MQTT TLS/SSL setup guide
- **RASPBERRY_PI_5_SD_CARD_SETUP.md** - SD card setup for Raspberry Pi 5
- **TROUBLESHOOTING.md** - General troubleshooting guide
