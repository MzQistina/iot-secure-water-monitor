# MQTT Broker Host Configuration Guide

## 🤔 What is Your MQTT Broker Host?

Your MQTT broker host depends on where your MQTT broker is running. Here are the common options:

## 📍 Option 1: Local MQTT Broker (Development/Testing)

**If you're running MQTT broker on your local machine or same network:**

### On Windows (Local Development):
```
MQTT_HOST=localhost
MQTT_PORT=1883
```

### On Same Network (e.g., Raspberry Pi on same WiFi):
```
MQTT_HOST=192.168.1.100  # IP address of machine running MQTT broker
MQTT_PORT=1883
```

**To find the IP address:**
- **Windows:** Open Command Prompt → `ipconfig` → Look for "IPv4 Address"
- **Raspberry Pi:** Run `hostname -I` or `ip addr show`

## 📍 Option 2: Cloud MQTT Broker (Recommended for Production)

### Option 2A: HiveMQ Cloud (Free Tier Available) ⭐ Recommended

**Step-by-Step Setup:**

1. **Sign up for HiveMQ Cloud:**
   - Go to [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)
   - Click "Start Free" or "Sign Up"
   - Create an account (free tier available)

2. **Create a Cluster:**
   - After signing in, click **"Create Cluster"** or **"New Cluster"**
   - Choose **"Free Tier"** (if available) or select a plan
   - Select a **region** closest to you (e.g., `eu-central-1` for Europe, `us-east-1` for US)
   - Give your cluster a name (e.g., `iot-water-monitor`)
   - Click **"Create Cluster"**
   - Wait for cluster to be created (usually 1-2 minutes)

3. **Get Your Cluster Details:**
   - Once created, you'll see your cluster dashboard
   - Note down:
     - **Cluster URL** (e.g., `abc123def456.s1.eu.hivemq.cloud`)
     - **Port** (usually `8883` for TLS)
     - **Username** (usually provided or you create one)
     - **Password** (you'll set this)

4. **Create MQTT User (if needed):**
   - Go to **"Access Management"** or **"Users"** section
   - Click **"Create User"** or **"Add User"**
   - Enter username (e.g., `water-monitor-user`)
   - Enter password (save this securely!)
   - Set permissions (usually "Publish/Subscribe" for all topics)
   - Click **"Save"** or **"Create"**

5. **Get Your Connection Details:**
   ```
   MQTT_HOST=your-cluster-id.s1.eu.hivemq.cloud  # From cluster dashboard
   MQTT_PORT=8883  # TLS port (standard for HiveMQ Cloud)
   MQTT_USE_TLS=true
   MQTT_USER=your_username  # The username you created
   MQTT_PASSWORD=your_password  # The password you set
   ```

6. **Test Connection (Optional):**
   - HiveMQ Cloud provides a **WebSocket Client** in the dashboard
   - You can test publishing/subscribing to topics
   - Or use MQTT client tools like MQTT.fx or mosquitto_pub/sub

**Example Configuration:**
```
MQTT_HOST=abc123def456.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USER=water-monitor-user
MQTT_PASSWORD=your_secure_password_here
```

**Note:** 
- HiveMQ Cloud uses TLS by default (port 8883)
- Free tier usually has message limits (check HiveMQ Cloud documentation)
- Cluster URL format: `{cluster-id}.s1.{region}.hivemq.cloud`

### Option 2B: Mosquitto Cloud (Eclipse Mosquitto)

1. **Sign up:** Go to [Mosquitto Cloud](https://mosquitto.org/cloud/)
2. **Get your broker URL:**
   ```
   MQTT_HOST=broker.hivemq.com  # Public test broker (no auth)
   MQTT_PORT=1883
   ```
   **Note:** Public broker is for testing only. For production, use a private broker.

### Option 2C: AWS IoT Core

1. **Set up AWS IoT Core**
2. **Get your endpoint:**
   ```
   MQTT_HOST=your-endpoint.iot.region.amazonaws.com
   MQTT_PORT=8883
   MQTT_USE_TLS=true
   ```

### Option 2D: Google Cloud IoT Core

1. **Set up Google Cloud IoT Core**
2. **Get your broker URL:**
   ```
   MQTT_HOST=mqtt.googleapis.com
   MQTT_PORT=8883
   MQTT_USE_TLS=true
   ```

## 📍 Option 3: Supervisor's MQTT Broker

**If your supervisor provides an MQTT broker:**

Ask your supervisor for:
- MQTT broker hostname/IP
- MQTT port (usually 1883 or 8883)
- Username and password (if required)
- TLS/SSL configuration (if using secure connection)

**Example:**
```
MQTT_HOST=mqtt.supervisor-university.edu.my
MQTT_PORT=1883  # or 8883 for TLS
MQTT_USER=your_username
MQTT_PASSWORD=your_password
```

## 📍 Option 4: Self-Hosted MQTT Broker

**If you're running your own MQTT broker (e.g., Mosquitto):**

### On Render (Same as your Flask app):
- You'll need to deploy a separate MQTT broker service
- Use the service's internal URL or public URL

### On Separate Server:
```
MQTT_HOST=your-mqtt-server.com
MQTT_PORT=1883  # or 8883 for TLS
```

## 🔍 How to Find Your Current MQTT Broker

### Check Your Current Configuration:

**On Windows (if running locally):**
```powershell
# Check if Mosquitto is running
Get-Service | Where-Object {$_.Name -like "*mosquitto*"}

# Check environment variables
$env:MQTT_HOST
```

**On Raspberry Pi:**
```bash
# Check if Mosquitto is installed
which mosquitto

# Check if Mosquitto is running
sudo systemctl status mosquitto

# Check environment variables
echo $MQTT_HOST
```

### Check Your Code:

Look for MQTT configuration in:
- Environment variables (`.env` file)
- `app.py` (default values)
- Render dashboard (Environment tab)

## 🚀 Quick Setup Options

### For Development/Testing (Quick Start):

**Option A: Use Public Test Broker (No Setup Required)**
```
MQTT_HOST=broker.hivemq.com
MQTT_PORT=1883
MQTT_USER=  # Leave empty (no auth)
MQTT_PASSWORD=  # Leave empty (no auth)
```
⚠️ **Warning:** Public broker is for testing only, not production!

**Option B: Install Local Mosquitto (Windows)**
1. Download: [Mosquitto for Windows](https://mosquitto.org/download/)
2. Install and start service
3. Use:
   ```
   MQTT_HOST=localhost
   MQTT_PORT=1883
   ```

**Option C: Install Local Mosquitto (Raspberry Pi)**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```
Then use:
```
MQTT_HOST=localhost  # On Raspberry Pi
# Or use Raspberry Pi's IP if connecting from other devices
MQTT_HOST=192.168.1.XXX  # Raspberry Pi's IP
MQTT_PORT=1883
```

## 📋 For Your Render Deployment

**Since your server is on Render, you need an MQTT broker that's accessible from:**
1. **Render server** (to publish provision requests)
2. **Raspberry Pi** (to receive requests and publish keys)

### Recommended Setup:

**Option 1: Cloud MQTT Broker (Easiest)**
- Use HiveMQ Cloud (free tier)
- Accessible from both Render and Raspberry Pi
- Automatic TLS/SSL

**Option 2: Supervisor's MQTT Broker**
- If supervisor provides one
- Ask for connection details

**Option 3: Self-Hosted on Separate Server**
- Deploy Mosquitto on a VPS
- Configure firewall to allow connections
- Set up TLS/SSL certificates

## ✅ Next Steps

1. **Determine which option you're using:**
   - [ ] Local development (localhost)
   - [ ] Cloud broker (HiveMQ, etc.)
   - [ ] Supervisor's broker
   - [ ] Self-hosted

2. **Get the connection details:**
   - Hostname/IP address
   - Port (1883 for plain, 8883 for TLS)
   - Username/password (if required)
   - TLS configuration (if using secure connection)

3. **Set in Render environment variables:**
   - `MQTT_HOST=your-broker-host.com`
   - `MQTT_PORT=1883` (or 8883)
   - `MQTT_USER=your_username` (if required)
   - `MQTT_PASSWORD=your_password` (if required)
   - `MQTT_USE_TLS=true` (if using TLS)

4. **Set on Raspberry Pi (for provision agent):**
   - Same values as Render
   - See `PROVISION_AGENT_AUTOMATION.md` for setup

## 🔗 Related Documentation

- **[MQTT_TLS_SETUP.md](MQTT_TLS_SETUP.md)** - Secure MQTT with TLS/SSL
- **[PROVISION_AGENT_GUIDE.md](PROVISION_AGENT_GUIDE.md)** - Provision agent setup
- **[RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)** - Render deployment

---

**Still not sure?** Check with your supervisor or use a cloud MQTT broker for easiest setup! 🚀

