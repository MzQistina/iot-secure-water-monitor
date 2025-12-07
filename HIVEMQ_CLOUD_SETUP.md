# HiveMQ Cloud Setup Guide - Complete Walkthrough

**This guide walks you through setting up HiveMQ Cloud for your IoT Water Monitor project.**

## 🎯 Why HiveMQ Cloud?

- ✅ **Serverless option available** - Pay-per-use, auto-scaling
- ✅ **Free tier available** - Great for development and testing
- ✅ **Automatic TLS/SSL** - Secure by default
- ✅ **Easy setup** - No server management needed
- ✅ **Accessible from anywhere** - Works with Render and Raspberry Pi
- ✅ **Web dashboard** - Monitor messages and connections
- ✅ **Reliable** - Managed service, no downtime

## 📋 Step-by-Step Setup

### Step 1: Create HiveMQ Cloud Account

1. **Go to HiveMQ Cloud:**
   - Visit: [https://www.hivemq.com/mqtt-cloud-broker/](https://www.hivemq.com/mqtt-cloud-broker/)
   - Click **"Start Free"** or **"Sign Up"**

2. **Sign Up:**
   - Enter your email address
   - Create a password
   - Accept terms and conditions
   - Click **"Create Account"** or **"Sign Up"**

3. **Verify Email:**
   - Check your email for verification link
   - Click the verification link
   - You'll be redirected to HiveMQ Cloud dashboard

### Step 2: Create a Cluster

**HiveMQ Cloud offers two types of clusters:**

#### Option A: Serverless Cluster (Recommended for Variable Workloads) ⭐

**Serverless clusters are:**
- ✅ **Pay-per-use** - Only pay for what you use
- ✅ **Auto-scaling** - Automatically scales with your workload
- ✅ **No fixed costs** - Great for development and testing
- ✅ **Easy setup** - No infrastructure management

**Steps to create Serverless Cluster:**

1. **Access Dashboard:**
   - After login, you'll see the HiveMQ Cloud dashboard
   - Click **"Create Cluster"** or **"New Cluster"** button

2. **Select Cluster Type:**
   - Choose **"Serverless"** or **"Serverless Cluster"** option
   - You may see options like:
     - **"Serverless"** - Pay-per-use, auto-scaling
     - **"Dedicated"** - Fixed resources (traditional cluster)

3. **Configure Serverless Cluster:**
   - **Cluster Name:** Enter a name (e.g., `iot-water-monitor-serverless`)
   - **Region:** Select closest to you:
     - `eu-central-1` (Europe - Frankfurt)
     - `us-east-1` (US - Virginia)
     - `ap-southeast-1` (Asia - Singapore)
   - **Version:** Use default (latest)

4. **Review Pricing:**
   - Serverless clusters typically charge per:
     - Connection hours
     - Messages sent/received
     - Data transfer
   - Check the pricing information shown

5. **Create Serverless Cluster:**
   - Click **"Create Cluster"** or **"Deploy"**
   - Wait for cluster to be provisioned (usually 1-2 minutes)
   - You'll see a progress indicator
   - Once ready, you'll see the cluster dashboard

#### Option B: Dedicated Cluster (Traditional)

**Dedicated clusters are:**
- Fixed resources (CPU, RAM, connections)
- Predictable pricing
- Better for consistent high workloads

**Steps to create Dedicated Cluster:**

1. **Access Dashboard:**
   - Click **"Create Cluster"** or **"New Cluster"** button

2. **Select Cluster Type:**
   - Choose **"Dedicated"** or **"Fixed"** option

3. **Choose Plan:**
   - Select **"Free Tier"** (if available) or **"Starter"** plan
   - Free tier usually includes:
     - Limited connections (e.g., 10 connections)
     - Limited messages per month
     - Perfect for development/testing

4. **Configure Cluster:**
   - **Cluster Name:** Enter a name (e.g., `iot-water-monitor`)
   - **Region:** Select closest to you
   - **Version:** Use default (latest)

5. **Create Cluster:**
   - Click **"Create Cluster"** or **"Deploy"**
   - Wait for cluster to be provisioned (1-2 minutes)

**Recommendation:** For your IoT Water Monitor project, **Serverless** is recommended because:
- Variable workload (sensors send data periodically)
- Cost-effective for development/testing
- Auto-scales automatically
- No need to manage infrastructure

### Step 3: Get Cluster Connection Details

**📍 Where to Find Your MQTT_HOST Value:**

1. **View Cluster Dashboard:**
   - After cluster is created, you'll see it in your dashboard
   - **Click on your cluster name** (e.g., `iot-water-monitor-serverless`)
   - This opens the cluster details page

2. **Find Connection Information:**
   - Look for one of these sections (varies by HiveMQ Cloud version):
     - **"Connection Details"** tab
     - **"Endpoint"** section
     - **"Broker URL"** or **"Host"** field
     - **"Connection Info"** section
     - **"Overview"** tab (may show connection details)
   
3. **What You're Looking For:**
   - You'll see a URL that looks like:
     ```
     abc123def456.s1.eu.hivemq.cloud
     ```
   - Or it might be displayed as:
     ```
     Host: abc123def456.s1.eu.hivemq.cloud
     Broker URL: abc123def456.s1.eu.hivemq.cloud
     Endpoint: abc123def456.s1.eu.hivemq.cloud
     ```

4. **Copy the Full URL:**
   - Copy the **entire URL** including the domain part
   - Example: `abc123def456.s1.eu.hivemq.cloud`
   - **This is your `MQTT_HOST` value!**

5. **Note the Port:**
   - You'll also see the port number
   - Usually **`8883`** for TLS (secure)
   - Or **`1883`** for non-TLS (not recommended)

**Visual Guide:**
```
HiveMQ Cloud Dashboard
├── Your Clusters
    └── [Click] iot-water-monitor-serverless
        ├── Overview Tab
        ├── Connection Details Tab ← Look here!
        │   ├── Broker URL: abc123def456.s1.eu.hivemq.cloud ← Copy this!
        │   ├── Port: 8883
        │   └── Protocol: MQTT over TLS
        ├── Users Tab
        └── Metrics Tab
```

**Example:**
If you see in the dashboard:
```
Broker URL: abc123def456.s1.eu.hivemq.cloud
Port: 8883
```

Then your `MQTT_HOST` value is: `abc123def456.s1.eu.hivemq.cloud`

### Step 4: Create MQTT User

1. **Access User Management:**
   - In cluster dashboard, go to **"Access Management"** or **"Users"** tab
   - Or look for **"MQTT Users"** section

2. **Create New User:**
   - Click **"Create User"** or **"Add User"** button
   - Enter:
     - **Username:** `water-monitor-user` (or your preferred name)
     - **Password:** Create a strong password (save it securely!)
   - Click **"Create"** or **"Save"**

3. **Set Permissions (if available):**
   - Some plans allow setting topic permissions
   - For your project, you'll need:
     - **Publish** to: `provision/+/request` (server publishes here)
     - **Subscribe** to: `keys/+/public` (provision agent subscribes here)
   - Or use wildcard: `#` (all topics) for simplicity

4. **Save Credentials:**
   - **Username:** `water-monitor-user`
   - **Password:** `your_password_here` (save this!)

### Step 5: Test Connection (Optional)

**Using HiveMQ WebSocket Client:**

1. **Open WebSocket Client:**
   - In cluster dashboard, look for **"WebSocket Client"** or **"Try It"** button
   - Click to open the test client

2. **Connect:**
   - Enter your username and password
   - Click **"Connect"**
   - You should see "Connected" status

3. **Test Publish/Subscribe:**
   - Subscribe to topic: `test/topic`
   - Publish a message to: `test/topic`
   - You should see the message appear

**Using Command Line (mosquitto_pub/sub):**

```bash
# Subscribe (in one terminal)
mosquitto_sub -h your-cluster-id.s1.eu.hivemq.cloud -p 8883 \
  --cafile /path/to/ca.crt \
  -u water-monitor-user -P your_password \
  -t "test/topic"

# Publish (in another terminal)
mosquitto_pub -h your-cluster-id.s1.eu.hivemq.cloud -p 8883 \
  --cafile /path/to/ca.crt \
  -u water-monitor-user -P your_password \
  -t "test/topic" -m "Hello MQTT"
```

## 🔧 Configuration for Your Project

### For Render (Web Server)

**Set these environment variables in Render dashboard:**

```
MQTT_HOST=your-cluster-id.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USER=water-monitor-user
MQTT_PASSWORD=your_password_here
```

**Note:** HiveMQ Cloud uses TLS by default, so:
- Port is `8883` (not `1883`)
- `MQTT_USE_TLS=true` is required
- No need for `MQTT_CA_CERTS` (uses system CA certificates)

### For Raspberry Pi (Provision Agent)

**Set in environment file or systemd service:**

```bash
# In ~/water-monitor/.provision-agent.env
MQTT_HOST=your-cluster-id.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USER=water-monitor-user
MQTT_PASSWORD=your_password_here
```

**Or in systemd service file:**

```ini
Environment="MQTT_HOST=your-cluster-id.s1.eu.hivemq.cloud"
Environment="MQTT_PORT=8883"
Environment="MQTT_USE_TLS=true"
Environment="MQTT_USER=water-monitor-user"
Environment="MQTT_PASSWORD=your_password_here"
```

## 📊 Monitoring and Management

### View Connections

1. **In HiveMQ Cloud Dashboard:**
   - Go to your cluster
   - Click **"Connections"** or **"Clients"** tab
   - You'll see active connections from:
     - Render server (publishing provision requests)
     - Raspberry Pi (provision agent subscribing)

### View Messages

1. **Message Flow:**
   - Go to **"Messages"** or **"Topics"** section
   - You can see:
     - Messages published to `provision/+/request`
     - Messages published to `keys/+/public`

### Monitor Usage

1. **Usage Dashboard:**
   - Check **"Usage"** or **"Metrics"** tab
   - Monitor:
     - Number of connections
     - Messages per day/month
     - Data transfer

## 🔒 Security Notes

1. **TLS/SSL:**
   - HiveMQ Cloud uses TLS by default
   - All connections are encrypted
   - No need for custom certificates

2. **Authentication:**
   - Always use username/password
   - Use strong passwords
   - Don't share credentials publicly

3. **Topic Permissions:**
   - Set specific topic permissions if available
   - Limit access to only needed topics

## ⚠️ Free Tier Limitations

**Check HiveMQ Cloud documentation for current limits:**
- Usually includes:
  - Limited connections (e.g., 10)
  - Limited messages per month
  - Limited data transfer

**If you exceed limits:**
- Upgrade to paid plan
- Or optimize message frequency

## 🐛 Troubleshooting

### Connection Failed

**Check:**
1. Cluster URL is correct
2. Port is `8883` (TLS) not `1883`
3. Username and password are correct
4. `MQTT_USE_TLS=true` is set
5. Firewall allows outbound connections on port 8883

### Authentication Failed

**Check:**
1. Username is correct (case-sensitive)
2. Password is correct (no extra spaces)
3. User exists in HiveMQ Cloud dashboard

### Messages Not Received

**Check:**
1. Topics match exactly (case-sensitive)
2. Client is subscribed to correct topic
3. Client is connected (check connections tab)
4. Permissions allow subscribe/publish

## 📝 Quick Reference

**Your HiveMQ Cloud Configuration:**

```
MQTT_HOST=your-cluster-id.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USER=water-monitor-user
MQTT_PASSWORD=your_password_here
```

**Topics Used:**
- `provision/<device_id>/request` - Server publishes provision requests
- `keys/<device_id>/public` - Provision agent publishes public keys

## 🔗 Next Steps

1. ✅ Set up HiveMQ Cloud cluster
2. ✅ Create MQTT user
3. ✅ Configure Render environment variables
4. ✅ Configure Raspberry Pi provision agent
5. ✅ Test connection
6. ✅ Deploy and monitor

---

**Your MQTT broker is now ready!** 🚀

For Render deployment, see: [RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)
For Provision Agent setup, see: [PROVISION_AGENT_AUTOMATION.md](PROVISION_AGENT_AUTOMATION.md)

