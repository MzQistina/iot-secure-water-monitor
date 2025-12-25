# Physical Raspberry Pi - Complete Setup Guide

Complete guide for setting up secure MQTT and provision agent on a **physical Raspberry Pi**.

---

## 🎯 What You'll Set Up

1. **Find your Pi's IP address** and connection details
2. **Set up virtual environment** (fixes pip install errors)
3. **Set up MQTT broker** with TLS/SSL encryption
4. **Configure provision agent** for automatic key generation
5. **Connect Flask server** to your Pi's MQTT broker

---

## 📋 Step 1: Find Your Raspberry Pi's IP Address

### On Raspberry Pi:

```bash
# Find IP address
hostname -I

# Example output: 192.168.1.100 192.168.56.102
# Use the first one (usually your main network IP)
```

### On Windows (PowerShell):

```powershell
# Scan network for Raspberry Pi (if on same network)
arp -a | Select-String "b8-27-eb"  # Raspberry Pi MAC prefix

# Or ping the hostname
ping raspberrypi.local
```

**Note:** Write down your Pi's IP address - you'll need it for all connections!

---

## 🚀 Step 2: Set Up Virtual Environment

**On Raspberry Pi:**

```bash
cd ~/secure-water-monitor  # or your project directory

# Install python3-venv if needed
sudo apt-get update
sudo apt-get install -y python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt now
```

**Install dependencies:**
```bash
# Install packages (this will work now!)
pip install --upgrade pip
pip install -r requirements_pi.txt

# Or install core packages manually:
pip install requests pycryptodome paho-mqtt
```

**Verify:**
```bash
pip list
# Should show: requests, pycryptodome, paho-mqtt
```

---

## 🔐 Step 3: Set Up MQTT Broker on Physical Pi

### Step 3.1: Install Mosquitto

**Note:** This installs system packages (not Python packages), so you don't need the virtual environment activated.

```bash
# On Raspberry Pi (venv activation not needed for apt-get)
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients

# Verify installation
mosquitto -v

# Verify mosquitto_passwd is available
which mosquitto_passwd
# Should show: /usr/bin/mosquitto_passwd

# Verify /etc/mosquitto/ directory exists
ls -la /etc/mosquitto/
# Should show the directory and default config files
```

**Why no venv?** `apt-get` installs system-level packages. Virtual environments are only for Python packages installed via `pip`.

**Troubleshooting:** If `/etc/mosquitto/` doesn't exist after installation, create it:
```bash
sudo mkdir -p /etc/mosquitto
sudo chown mosquitto:mosquitto /etc/mosquitto
```

### Step 3.2: Generate TLS Certificates

**Note:** Certificate generation uses system tools (OpenSSL), so venv activation is not needed.

```bash
# Create certificates directory
sudo mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs

# Generate CA
sudo openssl genrsa -out ca-key.pem 2048
sudo openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem
# Enter details when prompted (Common Name: "MQTT CA")

# Generate server certificate
sudo openssl genrsa -out server-key.pem 2048
sudo openssl req -new -key server-key.pem -out server.csr
```

**⚠️ IMPORTANT:** When prompted for **Common Name (CN)**, enter your Pi's IP address:
- Example: `192.168.1.100` (use the IP from Step 1)

```bash
# Sign server certificate
# Note: The backslash (\) continues the command on the next line
# You can type this as one line or keep it split across two lines
# You can also rename server-cert.pem to any name you want (e.g., mqtt-cert.pem)
sudo openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365

# Alternative: You can also type it as one line (without the backslash):
# sudo openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -days 365

# Optional: Rename the certificate file (if you want a different name)
# sudo mv server-cert.pem mqtt-cert.pem  # Example: rename to mqtt-cert.pem
# If you rename it, remember to update the certfile path in mosquitto.conf!

# Set permissions
sudo chmod 600 ca-key.pem server-key.pem
sudo chmod 644 ca-cert.pem server-cert.pem
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/*
sudo rm server.csr
```

### Step 3.3: Configure Mosquitto

**Note:** This edits system configuration files, so venv activation is not needed.

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

**Add this configuration:**
```conf
# TLS/SSL MQTT (port 8883)
listener 8883
protocol mqtt

# TLS Configuration
cafile /etc/mosquitto/certs/ca-cert.pem
certfile /etc/mosquitto/certs/server-cert.pem
keyfile /etc/mosquitto/certs/server-key.pem
tls_version tlsv1.2

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
```

**⚠️ Important:** Make sure you type `allow_anonymous` (with underscore), NOT `allow anonymous` (with space) or just `allow`. Common typos:
- ❌ `allow anonymous false` (space instead of underscore)
- ❌ `allow false` (missing "anonymous")
- ✅ `allow_anonymous false` (correct)

**Save:** `Ctrl+X`, then `Y`, then `Enter`

### Step 3.4: Create MQTT User

**Note:** System commands, venv activation not needed.

**Troubleshooting:** If you get "no such file or directory", ensure Mosquitto is installed and the directory exists:

```bash
# First, verify Mosquitto is installed
which mosquitto_passwd
# Should show: /usr/bin/mosquitto_passwd

# If not found, install Mosquitto:
sudo apt-get install -y mosquitto mosquitto-clients

# Ensure the directory exists (it should be created during installation)
ls -la /etc/mosquitto/
# Should show the directory exists

# Create password for MQTT user
# The -c flag creates the file if it doesn't exist
sudo mosquitto_passwd -c /etc/mosquitto/passwd water_monitor
# Enter password when prompted (remember this!)

# Set permissions
sudo chmod 600 /etc/mosquitto/passwd
```

**Note:** If the file already exists and you want to add another user (or change password), omit the `-c` flag:
```bash
# Add another user (file already exists)
sudo mosquitto_passwd /etc/mosquitto/passwd another_user

# Change password for existing user
sudo mosquitto_passwd /etc/mosquitto/passwd water_monitor
```

### Step 3.5: Start Mosquitto

**Note:** System service commands, venv activation not needed. These commands work from **any directory** - they don't depend on your current location.

**Troubleshooting:** If commands fail, check the following:

```bash
# Step 1: Verify Mosquitto is installed
dpkg -l | grep mosquitto
# Should show: mosquitto and mosquitto-clients

# If not installed:
sudo apt-get install -y mosquitto mosquitto-clients

# Step 2: Check if service exists
systemctl list-unit-files | grep mosquitto
# Should show: mosquitto.service

# Step 3: Check for configuration errors
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v
# This will show any configuration errors

# Step 4: Try starting the service
sudo systemctl start mosquitto

# Step 5: If it fails, check the EXACT error message
sudo systemctl status mosquitto
# Look for the error message - it will tell you what's wrong

# Step 6: Get detailed error logs
sudo journalctl -u mosquitto -n 50 --no-pager
# This shows the last 50 log entries with full error details

# Step 7: Common issues to check:

# A. Missing certificate files
ls -la /etc/mosquitto/certs/
# Should show: ca-cert.pem, server-cert.pem, server-key.pem

# B. Wrong file paths in config
sudo grep -E "(cafile|certfile|keyfile)" /etc/mosquitto/mosquitto.conf
# Verify paths match actual file locations

# C. Permission issues
sudo ls -la /etc/mosquitto/certs/
# Files should be owned by mosquitto:mosquitto

# D. Missing password file
ls -la /etc/mosquitto/passwd
# If missing, create it: sudo mosquitto_passwd -c /etc/mosquitto/passwd water_monitor

# E. Test configuration manually
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v
# This will show the exact error

# F. Exit code 13 = Permission denied - Fix file permissions:
sudo chmod 644 /etc/mosquitto/certs/ca-cert.pem
sudo chmod 644 /etc/mosquitto/certs/server-cert.pem
sudo chmod 600 /etc/mosquitto/certs/server-key.pem
sudo chmod 600 /etc/mosquitto/certs/ca-key.pem
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/*
sudo chmod 600 /etc/mosquitto/passwd
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd

# Step 7: If service starts successfully, enable it
sudo systemctl enable mosquitto

# Step 8: Verify it's listening on port 8883
sudo netstat -tlnp | grep 8883
# Should show: tcp  0  0  0.0.0.0:8883  0.0.0.0:*  LISTEN  <pid>/mosquitto

# Alternative: Use ss command if netstat not available
sudo ss -tlnp | grep 8883
```

**Common Errors and Solutions:**

1. **"Unit mosquitto.service not found"**
   ```bash
   # Mosquitto not installed - install it:
   sudo apt-get install -y mosquitto mosquitto-clients
   ```

2. **"Failed to start mosquitto.service"**
   ```bash
   # Check configuration file for errors:
   sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v
   
   # Common issues:
   # - Certificate file paths incorrect
   # - Certificate files don't exist
   # - Permission issues on certificate files
   # - Syntax errors in mosquitto.conf
   ```

3. **"Address already in use"**
   ```bash
   # Port 8883 already in use - check what's using it:
   sudo lsof -i :8883
   # Or
   sudo ss -tlnp | grep 8883
   ```

4. **"Permission denied" on certificate files**
   ```bash
   # Fix permissions:
   sudo chmod 644 /etc/mosquitto/certs/*.pem
   sudo chmod 600 /etc/mosquitto/certs/*-key.pem
   sudo chown mosquitto:mosquitto /etc/mosquitto/certs/*
   ```

**Directory doesn't matter:** `systemctl` and `netstat` are system commands that work from anywhere. You can run them from:
- Your home directory: `~`
- Project directory: `~/secure-water-monitor`
- Any other directory

---

## 📁 Step 4: Copy Files to Raspberry Pi

### From Windows PowerShell:

```powershell
# Replace with your Pi's IP address
$PI_IP = "192.168.1.100"  # Use the IP from Step 1
$PI_USER = "mizan"  # Your Pi username (or "pi" if default)

# Create directory structure on Pi
ssh ${PI_USER}@${PI_IP} "mkdir -p ~/secure-water-monitor/{simulators/sensor,keys,sensor_keys}"

# Copy essential files
scp raspberry_pi_client.py ${PI_USER}@${PI_IP}:~/secure-water-monitor/
scp encryption_utils.py ${PI_USER}@${PI_IP}:~/secure-water-monitor/
scp requirements_pi.txt ${PI_USER}@${PI_IP}:~/secure-water-monitor/
scp simulators\sensor\provision_agent.py ${PI_USER}@${PI_IP}:~/secure-water-monitor/simulators/sensor/

# Copy server public key (if you have it)
scp keys\public.pem ${PI_USER}@${PI_IP}:~/secure-water-monitor/keys/
```

### Or using WinSCP:

1. Connect to your Pi:
   - Host: `192.168.1.100` (your Pi's IP)
   - Username: `mizan` (or `pi`)
   - Password: Your Pi password

2. Navigate to `/home/mizan/secure-water-monitor/` (or `/home/pi/secure-water-monitor/`)

3. Copy files:
   - `raspberry_pi_client.py`
   - `encryption_utils.py`
   - `requirements_pi.txt`
   - `simulators/sensor/provision_agent.py`
   - `keys/public.pem` (if available)

---

## 🤖 Step 5: Set Up Provision Agent

### Step 5.1: Create Configuration

**On Raspberry Pi:**

```bash
cd ~/secure-water-monitor

# Activate virtual environment
source venv/bin/activate

# Create MQTT config
nano mqtt_config.sh
```

**Add content:**
```bash
#!/bin/bash
# MQTT Configuration for Provision Agent

export MQTT_USE_TLS=true
export MQTT_HOST=localhost  # Broker is on same Pi
export MQTT_PORT=8883
export MQTT_USER=water_monitor
export MQTT_PASSWORD=your_password  # Password from Step 3.4
export MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem
export MQTT_PROVISION_TOPIC_BASE=provision
export MQTT_KEYS_TOPIC_BASE=keys
```

**Make executable:**
```bash
chmod +x mqtt_config.sh
```

### Step 5.2: Test Provision Agent

```bash
# Activate venv
source venv/bin/activate

# Source config
source mqtt_config.sh

# Test run
python simulators/sensor/provision_agent.py
```

**Expected output:**
```
Provision agent connected: rc=0
Provision agent subscribed to: provision/+/request
Waiting for provision requests...
```

Press `Ctrl+C` to stop.

### Step 5.3: Create Systemd Service

```bash
sudo nano /etc/systemd/system/provision-agent.service
```

**Add content (replace `mizan` with your username and update password):**
```ini
[Unit]
Description=IoT Water Monitor Provision Agent
After=network.target mosquitto.service
Wants=network-online.target

[Service]
Type=simple
User=mizan
Group=mizan
WorkingDirectory=/home/mizan/secure-water-monitor

Environment="MQTT_USE_TLS=true"
Environment="MQTT_HOST=localhost"
Environment="MQTT_PORT=8883"
Environment="MQTT_USER=water_monitor"
Environment="MQTT_PASSWORD=your_password"
Environment="MQTT_CA_CERTS=/etc/mosquitto/certs/ca-cert.pem"
Environment="MQTT_PROVISION_TOPIC_BASE=provision"
Environment="MQTT_KEYS_TOPIC_BASE=keys"

# Use virtual environment Python
ExecStart=/home/mizan/secure-water-monitor/venv/bin/python3 /home/mizan/secure-water-monitor/simulators/sensor/provision_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=provision-agent

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable provision-agent.service
sudo systemctl start provision-agent.service

# Check status
sudo systemctl status provision-agent.service

# View logs
sudo journalctl -u provision-agent.service -f
```

---

## 💻 Step 6: Configure Flask Server (Windows)

### Step 6.1: Copy CA Certificate to Windows

**From Windows PowerShell:**

```powershell
# Create certs directory
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
mkdir -Force certs

# Copy CA certificate from Pi (replace with your Pi's IP and username)
$PI_IP = "192.168.1.100"
$PI_USER = "mizan"
scp ${PI_USER}@${PI_IP}:/etc/mosquitto/certs/ca-cert.pem certs\ca-cert.pem
```

### Step 6.2: Update MQTT Environment Variables

**Edit `setup-mqtt-env.ps1`:**

```powershell
# Update these values:
$env:MQTT_HOST = "192.168.1.100"  # Your Pi's IP from Step 1
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_USER = "water_monitor"
$env:MQTT_PASSWORD = "your_password"  # Password from Step 3.4
$env:MQTT_TLS_INSECURE = "false"
```

**Run before starting Flask:**
```powershell
.\setup-mqtt-env.ps1
python app.py
```

---

## 🧪 Step 7: Test Complete Flow

### Test 1: MQTT Connection

**On Raspberry Pi:**
```bash
# Subscribe to test topic
mosquitto_sub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic

# In another terminal, publish
mosquitto_pub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic -m "Hello!"
```

### Test 2: Provision Flow

1. **Start Flask app** on Windows (with MQTT env vars set)
2. **Check provision agent** is running:
   ```bash
   sudo systemctl status provision-agent.service
   ```
3. **Open web interface** → Register sensor → Click "Provision"
4. **Check provision agent logs:**
   ```bash
   sudo journalctl -u provision-agent.service -f
   ```
5. **Verify keys created:**
   ```bash
   ls -la ~/secure-water-monitor/sensor_keys/
   ```

---

## 📋 Quick Reference

### Your Pi's Details

| Item | Value |
|------|-------|
| **IP Address** | `192.168.1.100` (update with yours) |
| **Username** | `mizan` (or `pi`) |
| **MQTT Port** | `8883` |
| **MQTT User** | `water_monitor` |
| **Project Path** | `~/secure-water-monitor` |

### Important Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Check provision agent
sudo systemctl status provision-agent.service

# View logs
sudo journalctl -u provision-agent.service -f

# Check MQTT broker
sudo systemctl status mosquitto
```

---

## 🐛 Troubleshooting

### "Connection refused" when connecting from Windows

**Check:**
1. Pi and Windows are on same network
2. Firewall allows port 8883: `sudo ufw allow 8883/tcp`
3. Mosquitto is running: `sudo systemctl status mosquitto`

### "Certificate verification failed"

**Solution:**
```bash
# Check certificate CN matches Pi's IP
sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject

# If CN doesn't match, regenerate certificate with correct IP
```

### Provision agent not receiving messages

**Check:**
1. Service is running: `sudo systemctl status provision-agent.service`
2. MQTT broker is accessible
3. Flask server MQTT connection (check Flask logs)

---

## ✅ Checklist

- [ ] Found Pi's IP address
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] MQTT broker installed and configured
- [ ] TLS certificates generated
- [ ] MQTT user created
- [ ] Files copied to Pi
- [ ] Provision agent configured
- [ ] Systemd service created and running
- [ ] CA certificate copied to Windows
- [ ] Flask server MQTT environment variables set
- [ ] Test provision flow successful

---

## 🎉 Summary

You now have:
- ✅ Secure MQTT broker (TLS/SSL) on physical Raspberry Pi
- ✅ Provision agent automatically generating keys
- ✅ Flask server connected to secure MQTT
- ✅ Complete secure key provisioning workflow

**Next:** Use the provision agent to generate keys for all your sensors!

