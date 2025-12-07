# Provision Agent Automation Guide

**Automate the provision agent to run automatically on Raspbian startup and restart on failure.**

## 🎯 Overview

The provision agent runs on **Raspberry Pi (Raspbian)**, not on Render. This guide shows how to:
- ✅ Auto-start on boot
- ✅ Auto-restart on failure
- ✅ Run as a system service
- ✅ Manage with systemctl commands
- ✅ View logs easily

## 📋 Prerequisites

1. **Provision agent file** on Raspbian: `~/water-monitor/simulators/sensor/provision_agent.py`
2. **Python dependencies** installed: `paho-mqtt pycryptodome`
3. **MQTT broker** accessible from Raspberry Pi

## 🚀 Method 1: Systemd Service (Recommended for Production)

### Step 1: Create Systemd Service File

**On Raspbian, create the service file:**

```bash
sudo nano /etc/systemd/system/provision-agent.service
```

**Paste this configuration:**

```ini
[Unit]
Description=IoT Water Monitor Provision Agent
Documentation=https://github.com/yourusername/iot-secure-water-monitor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/water-monitor

# Environment variables (adjust paths and values as needed)
Environment="MQTT_HOST=your-mqtt-broker-host.com"
Environment="MQTT_PORT=1883"
Environment="MQTT_USER=your_mqtt_username"
Environment="MQTT_PASSWORD=your_mqtt_password"
Environment="MQTT_USE_TLS=false"
Environment="MQTT_PROVISION_TOPIC_BASE=provision"
Environment="MQTT_KEYS_TOPIC_BASE=keys"

# For TLS/SSL (if using secure MQTT)
# Environment="MQTT_USE_TLS=true"
# Environment="MQTT_PORT=8883"
# Environment="MQTT_CA_CERTS=/path/to/ca.crt"
# Environment="MQTT_CERTFILE=/path/to/client.crt"
# Environment="MQTT_KEYFILE=/path/to/client.key"

# Python executable
ExecStart=/usr/bin/python3 /home/pi/water-monitor/simulators/sensor/provision_agent.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=provision-agent

# Security (optional - run as non-root)
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Save and exit:** `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 2: Reload Systemd

```bash
sudo systemctl daemon-reload
```

### Step 3: Enable Auto-Start on Boot

```bash
sudo systemctl enable provision-agent.service
```

### Step 4: Start the Service

```bash
sudo systemctl start provision-agent.service
```

### Step 5: Check Status

```bash
sudo systemctl status provision-agent.service
```

**Expected output:**
```
● provision-agent.service - IoT Water Monitor Provision Agent
   Loaded: loaded (/etc/systemd/system/provision-agent.service; enabled)
   Active: active (running) since ...
```

## 🔧 Method 2: Environment File (Cleaner Configuration)

**Instead of hardcoding environment variables in the service file, use an environment file:**

### Step 1: Create Environment File

```bash
nano /home/pi/water-monitor/.provision-agent.env
```

**Add your configuration:**

```bash
MQTT_HOST=your-mqtt-broker-host.com
MQTT_PORT=1883
MQTT_USER=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
MQTT_USE_TLS=false
MQTT_PROVISION_TOPIC_BASE=provision
MQTT_KEYS_TOPIC_BASE=keys
```

**Save and set permissions:**

```bash
chmod 600 /home/pi/water-monitor/.provision-agent.env
```

### Step 2: Update Service File

**Edit the service file:**

```bash
sudo nano /etc/systemd/system/provision-agent.service
```

**Replace the Environment lines with:**

```ini
# Load environment from file
EnvironmentFile=/home/pi/water-monitor/.provision-agent.env
```

**Full service file with environment file:**

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
EnvironmentFile=/home/pi/water-monitor/.provision-agent.env
ExecStart=/usr/bin/python3 /home/pi/water-monitor/simulators/sensor/provision_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=provision-agent

[Install]
WantedBy=multi-user.target
```

**Reload and restart:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart provision-agent.service
```

## 📊 Management Commands

### Start/Stop/Restart

```bash
# Start service
sudo systemctl start provision-agent.service

# Stop service
sudo systemctl stop provision-agent.service

# Restart service
sudo systemctl restart provision-agent.service

# Reload configuration (if service file changed)
sudo systemctl daemon-reload
sudo systemctl restart provision-agent.service
```

### Check Status

```bash
# Current status
sudo systemctl status provision-agent.service

# Check if running
sudo systemctl is-active provision-agent.service

# Check if enabled (auto-start on boot)
sudo systemctl is-enabled provision-agent.service
```

### View Logs

```bash
# View recent logs
sudo journalctl -u provision-agent.service -n 50

# Follow logs in real-time
sudo journalctl -u provision-agent.service -f

# View logs since boot
sudo journalctl -u provision-agent.service -b

# View logs from today
sudo journalctl -u provision-agent.service --since today

# View logs with timestamps
sudo journalctl -u provision-agent.service --since "1 hour ago"
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable provision-agent.service

# Disable auto-start on boot
sudo systemctl disable provision-agent.service
```

## 🔍 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u provision-agent.service -n 100
```

**Common issues:**

1. **Python path wrong:**
   ```bash
   which python3
   # Update ExecStart in service file with correct path
   ```

2. **File permissions:**
   ```bash
   ls -la /home/pi/water-monitor/simulators/sensor/provision_agent.py
   chmod +x /home/pi/water-monitor/simulators/sensor/provision_agent.py
   ```

3. **Missing dependencies:**
   ```bash
   pip3 install paho-mqtt pycryptodome
   ```

4. **MQTT connection failed:**
   - Check `MQTT_HOST` and `MQTT_PORT` in environment
   - Test MQTT connection manually:
     ```bash
     mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -t "provision/+/request"
     ```

### Service Keeps Restarting

**Check restart count:**
```bash
sudo systemctl status provision-agent.service
```

**View error logs:**
```bash
sudo journalctl -u provision-agent.service -p err
```

**Common causes:**
- MQTT broker unreachable
- Wrong credentials
- Network not ready (add `After=network-online.target`)

### Service Not Auto-Starting on Boot

**Verify it's enabled:**
```bash
sudo systemctl is-enabled provision-agent.service
# Should output: enabled
```

**If not enabled:**
```bash
sudo systemctl enable provision-agent.service
```

## 🔄 Update After Code Changes

**When you update `provision_agent.py` on Raspbian:**

```bash
# 1. Copy updated file to Raspbian
# (from Windows)
scp simulators/sensor/provision_agent.py pi@raspberry-pi-ip:~/water-monitor/simulators/sensor/

# 2. Restart service (on Raspbian)
sudo systemctl restart provision-agent.service

# 3. Verify it's running
sudo systemctl status provision-agent.service
```

## 📝 Configuration for Render Deployment

**Since your server is on Render, update MQTT_HOST:**

**In `/home/pi/water-monitor/.provision-agent.env` or service file:**

```bash
# If MQTT broker is on Render or external
MQTT_HOST=your-mqtt-broker-host.com
MQTT_PORT=1883  # or 8883 for TLS

# If using Render's custom domain
MQTT_HOST=mqtt.your-custom-domain.com
```

**Note:** The provision agent on Raspbian connects to the MQTT broker, which should be accessible from both:
- Render server (publishes provision requests)
- Raspberry Pi (receives requests and publishes keys)

## ✅ Verification Checklist

After setup, verify:

- [ ] Service is running: `sudo systemctl status provision-agent.service`
- [ ] Service is enabled: `sudo systemctl is-enabled provision-agent.service`
- [ ] Logs show connection: `sudo journalctl -u provision-agent.service | grep "connected"`
- [ ] Test provision request from Render server
- [ ] Keys are generated in `sensor_keys/` folder
- [ ] Service auto-starts after reboot: `sudo reboot` (then check status)

## 🎯 Quick Setup Script

**Create a setup script on Raspbian:**

```bash
nano ~/setup-provision-agent.sh
```

**Paste:**

```bash
#!/bin/bash

# Create service file
sudo tee /etc/systemd/system/provision-agent.service > /dev/null <<EOF
[Unit]
Description=IoT Water Monitor Provision Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/water-monitor
EnvironmentFile=/home/pi/water-monitor/.provision-agent.env
ExecStart=/usr/bin/python3 /home/pi/water-monitor/simulators/sensor/provision_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=provision-agent

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable provision-agent.service
sudo systemctl start provision-agent.service

# Show status
sudo systemctl status provision-agent.service
```

**Make executable and run:**

```bash
chmod +x ~/setup-provision-agent.sh
~/setup-provision-agent.sh
```

---

**Your provision agent will now run automatically on boot and restart on failure!** 🚀

