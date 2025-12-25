# Physical Raspberry Pi - MQTT Setup Guide

Complete guide for setting up secure MQTT on a physical Raspberry Pi for the IoT Water Monitor project.

---

## 🤔 Do You Need MQTT?

### ✅ **You NEED MQTT if:**
- Running `provision_agent.py` on the physical Pi (automatic key generation)
- Using MQTT for sensor data transmission (instead of HTTP)
- Want centralized key provisioning via MQTT

### ❌ **You DON'T need MQTT if:**
- Only using `raspberry_pi_client.py` (uses HTTP/HTTPS for data)
- Manually uploading keys via HTTP (`--upload-key` flag)
- Provision agent runs on server/cloud instead of Pi

**Most users can skip MQTT** - the HTTP-based client works perfectly fine!

---

## 📊 Architecture Options

### Option 1: No MQTT (Simplest) ✅ Recommended for Most Users

```
Physical Raspberry Pi
├── raspberry_pi_client.py (HTTP/HTTPS)
└── Manual key upload via HTTP

Flask Server (Windows/Cloud)
└── Receives data via HTTP/HTTPS
```

**Setup:** Just follow `RASPBERRY_PI_SETUP.md` - no MQTT needed!

---

### Option 2: MQTT Broker on Physical Pi

```
Physical Raspberry Pi
├── Mosquitto MQTT Broker (port 8883 TLS)
├── raspberry_pi_client.py (HTTP/HTTPS)
└── provision_agent.py (MQTT client)

Flask Server (Windows/Cloud)
└── MQTT subscriber (connects to Pi's broker)
```

**Use case:** When you want the Pi to handle key provisioning locally.

---

### Option 3: MQTT Broker on Server/Cloud

```
Physical Raspberry Pi
├── raspberry_pi_client.py (HTTP/HTTPS)
└── provision_agent.py (MQTT client → connects to server)

Flask Server (Windows/Cloud)
├── Mosquitto MQTT Broker (port 8883 TLS)
└── MQTT subscriber
```

**Use case:** Centralized MQTT broker for multiple Pis.

---

## 🚀 Setting Up MQTT Broker on Physical Pi

If you chose **Option 2** (MQTT broker on physical Pi), follow these steps:

### Step 1: Install Mosquitto

```bash
# SSH into your physical Raspberry Pi
ssh pi@raspberrypi.local

# Update package list
sudo apt-get update

# Install Mosquitto broker and clients
sudo apt-get install -y mosquitto mosquitto-clients

# Verify installation
mosquitto -v
```

### Step 2: Generate TLS Certificates

```bash
# Create certificates directory
sudo mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs

# Generate CA private key
sudo openssl genrsa -out ca-key.pem 2048

# Generate CA certificate (valid for 10 years)
sudo openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem
# Enter details when prompted (Common Name: "MQTT CA")

# Generate server private key
sudo openssl genrsa -out server-key.pem 2048

# Generate server certificate signing request
sudo openssl req -new -key server-key.pem -out server.csr
# ⚠️ IMPORTANT: When prompted for Common Name (CN), enter your Pi's IP or hostname
# Examples:
#   - If Flask connects via IP: Use Pi's IP (e.g., "192.168.1.100")
#   - If Flask connects via hostname: Use hostname (e.g., "raspberrypi.local")
#   - For local testing: Use "localhost"

# Sign server certificate with CA
sudo openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365

# Set permissions
sudo chmod 600 ca-key.pem server-key.pem
sudo chmod 644 ca-cert.pem server-cert.pem
sudo rm server.csr  # Clean up

# Set ownership
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/*
```

### Step 3: Configure Mosquitto

```bash
# Edit Mosquitto configuration
sudo nano /etc/mosquitto/mosquitto.conf
```

**Add/update configuration:**

```conf
# ============================================
# Basic Settings
# ============================================

# Plain MQTT (port 1883) - Optional, can disable for security
listener 1883
allow_anonymous false

# TLS/SSL MQTT (port 8883) - Required for secure connections
listener 8883
protocol mqtt

# ============================================
# TLS/SSL Configuration
# ============================================

# CA certificate (for client certificate validation)
cafile /etc/mosquitto/certs/ca-cert.pem

# Server certificate
certfile /etc/mosquitto/certs/server-cert.pem

# Server private key
keyfile /etc/mosquitto/certs/server-key.pem

# TLS version (recommended: tlsv1.2 or higher)
tls_version tlsv1.2

# ============================================
# Authentication
# ============================================

# Disable anonymous access
allow_anonymous false

# Password file for username/password authentication
password_file /etc/mosquitto/passwd

# ============================================
# Logging
# ============================================

# Log to file
log_dest file /var/log/mosquitto/mosquitto.log

# Log types
log_type error
log_type warning
log_type notice
log_type information
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Create User Accounts

```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd water_monitor
# Enter password when prompted (twice)

# Set permissions
sudo chmod 600 /etc/mosquitto/passwd
```

### Step 5: Restart Mosquitto

```bash
# Restart service
sudo systemctl restart mosquitto

# Enable on boot
sudo systemctl enable mosquitto

# Check status
sudo systemctl status mosquitto

# Verify it's listening on port 8883
sudo netstat -tlnp | grep 8883
# Should show: tcp  0  0  0.0.0.0:8883  0.0.0.0:*  LISTEN  <pid>/mosquitto
```

### Step 6: Copy CA Certificate to Flask Server

**From your Windows machine (PowerShell):**

```powershell
# Create certs directory in project
mkdir -Force certs

# Copy CA certificate from Pi
scp pi@raspberrypi.local:/etc/mosquitto/certs/ca-cert.pem certs\ca-cert.pem
```

**Or manually:**
1. Use WinSCP/SFTP to download `/etc/mosquitto/certs/ca-cert.pem` from Pi
2. Save to `C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem`

### Step 7: Configure Flask Server (Windows)

**Set environment variables (PowerShell):**

```powershell
# MQTT broker is now on physical Pi
$env:MQTT_HOST = "192.168.1.100"  # Replace with your Pi's IP
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_USER = "water_monitor"
$env:MQTT_PASSWORD = "your_password"  # Password you set in Step 4
$env:MQTT_TLS_INSECURE = "false"  # Use "true" only for testing
```

**Or set in Apache/mod_wsgi configuration** (see `APACHE_SETUP.md`)

### Step 8: Configure Provision Agent (if using)

**On Physical Pi, create configuration:**

```bash
nano ~/water-monitor/mqtt_config.sh
```

**Add content:**

```bash
#!/bin/bash
# MQTT Configuration for Provision Agent

# MQTT broker is on same machine (localhost)
export MQTT_USE_TLS=true
export MQTT_HOST=localhost
export MQTT_PORT=8883
export MQTT_USER=water_monitor
export MQTT_PASSWORD=your_password

# CA certificate path
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem

# Topic configuration
export MQTT_PROVISION_TOPIC_BASE=provision
export MQTT_KEYS_TOPIC_BASE=keys
```

**Make executable:**

```bash
chmod +x ~/water-monitor/mqtt_config.sh
```

**Run provision agent:**

```bash
cd ~/water-monitor
source mqtt_config.sh
python3 simulators/sensor/provision_agent.py
```

---

## 🧪 Testing MQTT Connection

### Test 1: From Physical Pi (Local)

```bash
# Subscribe to test topic
mosquitto_sub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic

# In another terminal, publish a message
mosquitto_pub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic -m "Hello from Pi!"
```

### Test 2: From Flask Server (Windows)

**PowerShell:**

```powershell
# Test connection
Test-NetConnection -ComputerName 192.168.1.100 -Port 8883

# If mosquitto tools installed on Windows:
mosquitto_sub -h 192.168.1.100 -p 8883 `
  --cafile "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem" `
  -u water_monitor -P your_password `
  -t test/topic
```

### Test 3: Flask MQTT Listener

**On Windows:**

```powershell
# Set environment variables (if not already set)
$env:MQTT_HOST = "192.168.1.100"
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_USER = "water_monitor"
$env:MQTT_PASSWORD = "your_password"

# Run MQTT listener
python mqtt_listener.py
```

**You should see:**
```
Connecting to MQTT broker: 192.168.1.100:8883 (TLS)
TLS enabled with CA cert: C:\Users\...\certs\ca-cert.pem
Connected with result code 0
Subscribed to topics: water/data, secure/sensor
```

---

## 🔒 Security Best Practices

1. **Always use TLS** - Never use plain MQTT (port 1883) in production
2. **Strong passwords** - Use complex passwords for MQTT authentication
3. **Certificate CN matching** - Ensure server certificate CN matches IP/hostname
4. **Firewall rules** - Restrict access to port 8883 if possible
5. **Regular updates** - Keep Mosquitto and certificates updated

---

## 🐛 Troubleshooting

### Problem: "Certificate Verification Failed"

**Solution:**
- Check certificate CN matches Pi's IP/hostname:
  ```bash
  sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject
  ```
- Regenerate certificate with correct CN if needed
- For testing only: Set `MQTT_TLS_INSECURE=true` (NOT for production)

### Problem: "Connection Refused"

**Solutions:**
```bash
# Check Mosquitto is running
sudo systemctl status mosquitto

# Check port is listening
sudo netstat -tlnp | grep 8883

# Check firewall
sudo ufw status
```

### Problem: "Bad User Name or Password"

**Solutions:**
```bash
# Verify user exists
sudo cat /etc/mosquitto/passwd

# Reset password
sudo mosquitto_passwd /etc/mosquitto/passwd water_monitor
```

---

## 📋 Quick Reference

### Certificate Locations

**On Physical Pi:**
- CA Certificate: `/etc/mosquitto/certs/ca-cert.pem`
- Server Certificate: `/etc/mosquitto/certs/server-cert.pem`
- Server Key: `/etc/mosquitto/certs/server-key.pem`

**On Flask Server (Windows):**
- CA Certificate: `C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem`

### Ports

- **8883** - MQTT over TLS (secure) ✅ Use this
- **1883** - Plain MQTT (insecure) ❌ Disable in production

### Configuration Files

- **Mosquitto Config:** `/etc/mosquitto/mosquitto.conf`
- **Password File:** `/etc/mosquitto/passwd`
- **Log File:** `/var/log/mosquitto/mosquitto.log`

---

## ✅ Summary

**For most users:** You don't need MQTT! Just use `raspberry_pi_client.py` with HTTP/HTTPS.

**If you need MQTT:**
1. Install Mosquitto on physical Pi
2. Generate TLS certificates
3. Configure Mosquitto
4. Copy CA certificate to Flask server
5. Update environment variables
6. Test connection

**Related Guides:**
- `RASPBERRY_PI_SETUP.md` - Basic Pi setup (no MQTT)
- `SELF_HOSTED_MQTT_TLS_SETUP.md` - Detailed MQTT setup
- `MQTT_TLS_SETUP.md` - General MQTT TLS guide
- `PROVISION_AGENT_GUIDE.md` - Provision agent setup


















