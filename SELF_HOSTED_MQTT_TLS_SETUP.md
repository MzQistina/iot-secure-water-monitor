# Self-Hosted MQTT Broker with TLS/SSL - Complete Setup Guide

Complete guide for setting up a self-hosted MQTT broker (Mosquitto) with TLS/SSL encryption for your IoT Water Monitor project.

---

## 📋 Prerequisites

- ✅ Linux server (Ubuntu/Debian recommended)
- ✅ Root/sudo access
- ✅ OpenSSL installed
- ✅ Port 8883 open in firewall (for TLS)

---

## 🚀 Step-by-Step Setup

### Step 1: Install Mosquitto MQTT Broker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients
```

**Verify installation:**
```bash
mosquitto -v
# Should show version information
```

**Check service status:**
```bash
sudo systemctl status mosquitto
```

**⚠️ Important:** If you see "Address already in use" when running `mosquitto -v`, it means Mosquitto is already running as a service. This is normal! Use `systemctl` commands to manage it instead of running mosquitto directly.

---

### Step 2: Generate TLS Certificates

**Create certificates directory:**

**Use system directory (standard location):**
```bash
sudo mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs
```

**Why system directory?**
- ✅ Mosquitto is installed in `/etc/mosquitto/` - certificates belong here
- ✅ Standard Linux location for Mosquitto certificates
- ✅ Follows Linux conventions
- ✅ Persistent across system updates
- ✅ Mosquitto config expects certificates here by default

#### 2.1: Generate CA (Certificate Authority)

**Generate CA private key:**
```bash
sudo openssl genrsa -out ca-key.pem 2048
```

**Generate CA certificate (valid for 10 years):**
```bash
sudo openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem
```

**You'll be prompted for:**
- Country Name: `MY` (or your country code)
- State/Province: `Your State`
- City: `Your City`
- Organization: `Your Organization`
- Organizational Unit: `IT Department`
- Common Name: `MQTT CA` (or any name)
- Email: `your@email.com`

**Set permissions:**
```bash
sudo chmod 600 ca-key.pem
sudo chmod 644 ca-cert.pem
```

#### 2.2: Generate Server Certificate

**Generate server private key:**
```bash
sudo openssl genrsa -out server-key.pem 2048
```

**Generate server certificate signing request (CSR):**
```bash
sudo openssl req -new -key server-key.pem -out server.csr
```

**Important:** When prompted for **Common Name (CN)**, enter what clients will use to connect to the MQTT broker:

**For your setup (Flask on Windows, MQTT broker on Raspbian):**
- **If Flask connects via IP:** Use Raspbian's IP address (e.g., `10.0.2.2` for VirtualBox NAT, or `192.168.1.100` for bridged mode)
- **If Flask connects via hostname:** Use the hostname (e.g., `raspberrypi.local`)
- **For local testing only:** Use `localhost` (only works if Flask is also on Raspbian)

**Recommended for VirtualBox:**
- Use `localhost` if you're only testing on Raspbian (provision agent)
- Use Raspbian's IP address if Flask on Windows needs to connect
- **Best practice:** Use the actual IP or hostname that clients will use

**Example:**
- Flask on Windows connects to `10.0.2.2` → Use CN: `10.0.2.2`
- Flask on Windows connects to `192.168.1.100` → Use CN: `192.168.1.100`
- Only testing on Raspbian → Use CN: `localhost`

**Sign server certificate with CA:**
```bash
sudo openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365
```

**Set permissions:**
```bash
sudo chmod 600 server-key.pem
sudo chmod 644 server-cert.pem
sudo rm server.csr  # Clean up CSR file
```

#### 2.3: Verify Certificates

**Check certificate details:**
```bash
# Check CA certificate
sudo openssl x509 -in ca-cert.pem -text -noout

# Check server certificate
sudo openssl x509 -in server-cert.pem -text -noout
```

---

### Step 3: Configure Mosquitto for TLS

**Edit Mosquitto configuration:**
```bash
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

# Require client certificates (optional - for maximum security)
# Uncomment to require client certificates:
# require_certificate true

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

# ============================================
# Connection Settings
# ============================================

# Maximum number of connections
max_connections -1  # Unlimited

# Keep alive interval (seconds)
keepalive_interval 60

# Maximum message size (bytes)
message_size_limit 0  # Unlimited
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

---

### Step 4: Create User Accounts

**Create password file:**
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd water_monitor
```

**You'll be prompted to enter a password twice.**

**Add more users (optional):**
```bash
sudo mosquitto_passwd /etc/mosquitto/passwd another_user
```

**Set permissions:**
```bash
sudo chmod 600 /etc/mosquitto/passwd
```

---

### Step 5: Restart Mosquitto

**⚠️ If Mosquitto is already running (you see "Address already in use"):**

**Stop the service first:**
```bash
sudo systemctl stop mosquitto
```

**Test configuration (optional - to verify config is valid):**
```bash
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v
```

**If no errors, press `Ctrl+C` and start the service:**
```bash
sudo systemctl start mosquitto
sudo systemctl enable mosquitto  # Enable on boot
```

**Or restart directly:**
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto  # Enable on boot
```

**Check status:**
```bash
sudo systemctl status mosquitto
```

**Check if it's listening on port 8883 (TLS):**
```bash
sudo netstat -tlnp | grep 8883
# Should show: tcp  0  0  0.0.0.0:8883  0.0.0.0:*  LISTEN  <pid>/mosquitto
```

**⚠️ If no output:** Mosquitto is not configured for TLS yet. You need to:
1. Generate TLS certificates (Step 2)
2. Configure Mosquitto for TLS (Step 3)
3. Restart Mosquitto (Step 5)

**Check what ports Mosquitto is currently listening on:**
```bash
sudo netstat -tlnp | grep mosquitto
# Or
sudo ss -tlnp | grep mosquitto
```

**If you only see port 1883, TLS is not configured yet.**

**Check logs:**
```bash
sudo tail -f /var/log/mosquitto/mosquitto.log
```

---

### Step 6: Configure Firewall

**Check if firewall is installed:**
```bash
# Check for UFW
which ufw

# Check for iptables
which iptables

# Check for firewalld (some systems)
which firewall-cmd
```

**Allow MQTT TLS port (8883):**

**Option 1: UFW (Ubuntu/Debian)**
```bash
sudo ufw allow 8883/tcp
sudo ufw status
```

**Option 2: iptables**
```bash
sudo iptables -A INPUT -p tcp --dport 8883 -j ACCEPT
# Save rules (depends on your system)
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

**Option 3: firewalld (RHEL/CentOS/Fedora)**
```bash
sudo firewall-cmd --permanent --add-port=8883/tcp
sudo firewall-cmd --reload
```

**Option 4: No Firewall (Common on Raspberry Pi)**
If neither `ufw` nor `iptables` are installed, you might not have a firewall configured. This is common on:
- Fresh Raspberry Pi OS installations
- Local network setups
- Development environments

**⚠️ Important:** 
- If you're on a **local network** (home/office), no firewall configuration may be needed
- If you're on a **public network** or **exposed to internet**, consider installing and configuring a firewall
- For **development/testing**, you can skip this step

**Optional: Block plain MQTT (port 1883) for security:**
```bash
# Only if firewall is installed
sudo ufw deny 1883/tcp
# Or
sudo iptables -A INPUT -p tcp --dport 1883 -j DROP
```

---

### Step 7: Copy CA Certificate to Client Machines

**Copy CA certificate to your development machine:**
```bash
# From server
scp /etc/mosquitto/certs/ca-cert.pem user@your-machine:/path/to/certs/

# Or download via web browser/SFTP
```

**Copy to Raspberry Pi:**
```bash
# From server
scp /etc/mosquitto/certs/ca-cert.pem pi@raspberrypi:~/water-monitor/certs/

# Or from your development machine
scp ca-cert.pem pi@raspberrypi:~/water-monitor/certs/
```

**Set permissions on client:**
```bash
# On Raspberry Pi
chmod 644 ~/water-monitor/certs/ca-cert.pem
```

---

### Step 8: Configure Your Application

#### 8.1: Server Configuration (Flask app)

**Set environment variables:**

**For Apache/WSGI:**
```python
# Edit app.wsgi or set in Apache config
import os
os.environ['MQTT_USE_TLS'] = 'true'
os.environ['MQTT_HOST'] = '10.0.2.2'  # VirtualBox NAT gateway (or Raspbian IP)
os.environ['MQTT_PORT'] = '8883'
os.environ['MQTT_USER'] = 'water_monitor'
os.environ['MQTT_PASSWORD'] = 'your_password'

# CA certificate in project directory (same level as app.py)
project_root = os.path.dirname(__file__)
os.environ['MQTT_CA_CERTS'] = os.path.join(project_root, 'certs', 'ca-cert.pem')
```

**For systemd service:**
```ini
[Service]
Environment="MQTT_USE_TLS=true"
Environment="MQTT_HOST=192.168.1.100"
Environment="MQTT_PORT=8883"
Environment="MQTT_USER=water_monitor"
Environment="MQTT_PASSWORD=your_password"
Environment="MQTT_CA_CERTS=/etc/ssl/certs/mqtt-ca.pem"
```

#### 8.2: Raspberry Pi Configuration

**Create configuration file:**
```bash
nano ~/water-monitor/mqtt_config.sh
```

**Add content:**
```bash
#!/bin/bash
# Self-Hosted MQTT Configuration

export MQTT_USE_TLS=true
export MQTT_HOST=localhost  # Broker is on same machine (Raspbian)
export MQTT_PORT=8883
export MQTT_USER=water_monitor
export MQTT_PASSWORD=your_password

# CA certificate path (in project directory, same as keys/ and sensor_keys/)
export MQTT_CA_CERTS=/home/pi/water-monitor/certs/ca-cert.pem

# Topic configuration
export MQTT_PROVISION_TOPIC_BASE=provision
export MQTT_KEYS_TOPIC_BASE=keys
```

**Make executable:**
```bash
chmod +x ~/water-monitor/mqtt_config.sh
```

---

### Step 9: Test TLS Connection

#### 9.1: Test from Server

**Subscribe to test topic:**
```bash
mosquitto_sub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic
```

**In another terminal, publish a message:**
```bash
mosquitto_pub -h localhost -p 8883 \
  --cafile /etc/mosquitto/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic -m "Hello TLS!"
```

**You should see "Hello TLS!" in the subscriber terminal.**

#### 9.2: Test from Remote Machine

**From your development machine:**
```bash
mosquitto_sub -h your-server-ip -p 8883 \
  --cafile /path/to/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic
```

**From Raspberry Pi:**
```bash
mosquitto_sub -h 192.168.1.100 -p 8883 \
  --cafile ~/water-monitor/certs/ca-cert.pem \
  -u water_monitor -P your_password \
  -t test/topic
```

---

### Step 10: Start Provision Agent

**On Raspberry Pi:**
```bash
cd ~/water-monitor
source mqtt_config.sh
python3 simulators/sensor/provision_agent.py
```

**You should see:**
```
Provision agent: Connecting to 192.168.1.100:8883 (TLS)
Provision agent: TLS enabled with CA cert: /home/pi/water-monitor/certs/ca-cert.pem
Provision agent connected: 0
```

---

## 🔒 Security Best Practices

### 1. Disable Plain MQTT (Port 1883)

**Edit `/etc/mosquitto/mosquitto.conf`:**
```conf
# Comment out or remove plain MQTT listener
# listener 1883
```

**Restart Mosquitto:**
```bash
sudo systemctl restart mosquitto
```

### 2. Use Strong Passwords

```bash
# Generate strong password
openssl rand -base64 32

# Update password
sudo mosquitto_passwd /etc/mosquitto/passwd water_monitor
```

### 3. Restrict File Permissions

```bash
# Certificates
sudo chmod 600 /etc/mosquitto/certs/*.pem
sudo chmod 644 /etc/mosquitto/certs/ca-cert.pem

# Password file
sudo chmod 600 /etc/mosquitto/passwd

# Config file
sudo chmod 644 /etc/mosquitto/mosquitto.conf
```

### 4. Enable Client Certificate Authentication (Optional - Maximum Security)

**Edit `/etc/mosquitto/mosquitto.conf`:**
```conf
require_certificate true
```

**Generate client certificates:**
```bash
# Generate client key
openssl genrsa -out client-key.pem 2048

# Generate client CSR
openssl req -new -key client-key.pem -out client.csr

# Sign with CA
openssl x509 -req -in client.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out client-cert.pem -days 365
```

**Configure application with client certificates:**
```bash
export MQTT_CERTFILE=/path/to/client-cert.pem
export MQTT_KEYFILE=/path/to/client-key.pem
```

### 5. Use Firewall Rules

```bash
# Only allow specific IPs (if possible)
sudo ufw allow from 192.168.1.0/24 to any port 8883

# Or restrict to specific IPs
sudo ufw allow from 192.168.1.100 to any port 8883
```

### 6. Regular Certificate Rotation

**Certificates expire after 1 year (as configured). Plan to:**
- Generate new certificates before expiration
- Update all clients with new CA certificate
- Restart services

---

## 🐛 Troubleshooting

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

### Problem: "Certificate Verification Failed"

**Solutions:**
- ✅ Verify CA certificate path is correct
- ✅ Ensure server certificate CN matches hostname/IP
- ✅ Check certificate hasn't expired: `openssl x509 -in server-cert.pem -noout -dates`
- ✅ Regenerate certificates if needed

### Problem: "Bad User Name or Password"

**Solutions:**
```bash
# Verify user exists
sudo cat /etc/mosquitto/passwd

# Reset password
sudo mosquitto_passwd /etc/mosquitto/passwd water_monitor
```

### Problem: "Address Already in Use"

**Solutions:**
```bash
# Check if another instance is running
sudo ps aux | grep mosquitto

# Kill old process
sudo pkill mosquitto

# Restart service
sudo systemctl restart mosquitto
```

### Problem: "Permission Denied" on Certificates

**Solutions:**
```bash
# Fix permissions
sudo chmod 600 /etc/mosquitto/certs/*-key.pem
sudo chmod 644 /etc/mosquitto/certs/*-cert.pem
sudo chown mosquitto:mosquitto /etc/mosquitto/certs/*
```

---

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Recent errors
sudo grep -i error /var/log/mosquitto/mosquitto.log

# Connection attempts
sudo grep -i connect /var/log/mosquitto/mosquitto.log
```

### Check Active Connections

```bash
# List connections
sudo netstat -an | grep 8883

# Count connections
sudo netstat -an | grep 8883 | wc -l
```

---

## 📋 Complete Configuration Checklist

- [ ] Mosquitto installed
- [ ] CA certificate generated
- [ ] Server certificate generated
- [ ] Certificates have correct permissions
- [ ] Mosquitto configured for TLS (port 8883)
- [ ] User accounts created
- [ ] Firewall allows port 8883
- [ ] CA certificate copied to clients
- [ ] Application configured with TLS settings
- [ ] Test connection successful
- [ ] Provision agent connects successfully
- [ ] Logs show TLS connections

---

## 🎯 Quick Reference

### Certificate Locations

**Server:**
- CA Certificate: `/etc/mosquitto/certs/ca-cert.pem`
- Server Certificate: `/etc/mosquitto/certs/server-cert.pem`
- Server Key: `/etc/mosquitto/certs/server-key.pem`

**On Raspbian (Provision Agent):**
- CA Certificate: `/etc/mosquitto/certs/ca-cert.pem` (same as broker)

**On Windows (Flask App):**
- CA Certificate: Copy to your project `certs/` directory
  - `C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem`

### Ports

- **8883** - MQTT over TLS (secure)
- **1883** - Plain MQTT (insecure, can disable)

### Configuration Files

- **Mosquitto Config:** `/etc/mosquitto/mosquitto.conf`
- **Password File:** `/etc/mosquitto/passwd`
- **Log File:** `/var/log/mosquitto/mosquitto.log`

---

## 🔗 Next Steps

1. ✅ **Test connection** - Verify TLS works
2. ✅ **Configure application** - Set environment variables
3. ✅ **Deploy to production** - Start using secure MQTT
4. ✅ **Monitor logs** - Watch for connection issues
5. ✅ **Set up backups** - Backup certificates and config

---

**🎉 Your self-hosted MQTT broker with TLS/SSL is now ready!**

For application configuration, see:
- **[ENABLE_SECURE_MQTT_QUICK_START.md](ENABLE_SECURE_MQTT_QUICK_START.md)**
- **[MQTT_TLS_SETUP.md](MQTT_TLS_SETUP.md)**

