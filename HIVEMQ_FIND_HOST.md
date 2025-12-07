# How to Find Your HiveMQ Cloud MQTT_HOST Value

## 🎯 Quick Answer

**Your `MQTT_HOST` is the Broker URL shown in your HiveMQ Cloud cluster dashboard.**

## 📍 Step-by-Step: Where to Find It

### Step 1: Log into HiveMQ Cloud
1. Go to [HiveMQ Cloud Console](https://console.hivemq.cloud/)
2. Log in with your account

### Step 2: Open Your Cluster
1. You'll see a list of your clusters
2. **Click on your cluster name** (e.g., `iot-water-monitor-serverless`)

### Step 3: Find Connection Details
Once you're in the cluster dashboard, look for:

**Option A: Connection Details Tab**
- Click on **"Connection Details"** tab (usually in the top menu)
- You'll see:
  ```
  Broker URL: abc123def456.s1.eu.hivemq.cloud
  Port: 8883
  ```

**Option B: Overview Tab**
- The **"Overview"** tab may show connection information
- Look for **"Endpoint"** or **"Broker URL"**

**Option C: Settings/Configuration**
- Some versions show it under **"Settings"** or **"Configuration"**
- Look for **"Host"** or **"Endpoint"**

### Step 4: Copy the Broker URL
- You'll see a URL like: `abc123def456.s1.eu.hivemq.cloud`
- **Copy this entire URL** - this is your `MQTT_HOST` value!

## 📋 What It Looks Like

**In HiveMQ Cloud Dashboard, you'll see something like:**

```
┌─────────────────────────────────────────┐
│ Connection Details                      │
├─────────────────────────────────────────┤
│ Broker URL:                             │
│ abc123def456.s1.eu.hivemq.cloud  ← Copy this! │
│                                         │
│ Port: 8883                              │
│ Protocol: MQTT over TLS                 │
└─────────────────────────────────────────┘
```

## ✅ Example

**If you see:**
```
Broker URL: abc123def456.s1.eu.hivemq.cloud
Port: 8883
```

**Then use:**
```
MQTT_HOST=abc123def456.s1.eu.hivemq.cloud
MQTT_PORT=8883
```

## 🔍 Common URL Formats

Your cluster URL will be in one of these formats:
- `{cluster-id}.s1.{region}.hivemq.cloud`
- `{cluster-id}.{region}.hivemq.cloud`
- `{cluster-id}.hivemq.cloud`

**Examples:**
- `abc123def456.s1.eu.hivemq.cloud` (Europe)
- `xyz789ghi012.s1.us.hivemq.cloud` (US)
- `mno345pqr678.s1.ap.hivemq.cloud` (Asia Pacific)

## ⚠️ Important Notes

1. **Copy the entire URL** - Don't miss any part
2. **Include the domain** - Must include `.hivemq.cloud` part
3. **No protocol prefix** - Don't add `mqtt://` or `https://`
4. **Case sensitive** - Copy exactly as shown

## 🐛 Can't Find It?

**If you can't find the Broker URL:**

1. **Check different tabs:**
   - Overview
   - Connection Details
   - Settings
   - Configuration

2. **Look for these labels:**
   - "Broker URL"
   - "Endpoint"
   - "Host"
   - "Connection String"
   - "MQTT Endpoint"

3. **Check cluster status:**
   - Make sure cluster is fully created and running
   - Status should be "Running" or "Active"

4. **Try the API/CLI:**
   - HiveMQ Cloud may provide API access
   - Check documentation for CLI commands

## 📝 Quick Checklist

- [ ] Logged into HiveMQ Cloud
- [ ] Clicked on cluster name
- [ ] Found "Connection Details" or "Endpoint" section
- [ ] Copied the Broker URL (e.g., `abc123def456.s1.eu.hivemq.cloud`)
- [ ] Noted the port (usually `8883`)

## 🔗 Next Steps

Once you have your `MQTT_HOST`:
1. Use it in Render environment variables
2. Use it in Raspberry Pi provision agent configuration
3. Test the connection

---

**Still can't find it?** Take a screenshot of your cluster dashboard and check the tabs - the Broker URL should be visible somewhere in the cluster details!

