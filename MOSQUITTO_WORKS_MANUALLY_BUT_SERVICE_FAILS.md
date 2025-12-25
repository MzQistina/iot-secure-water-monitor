# Mosquitto Works Manually But Service Fails

If `sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v` runs without errors, but the service fails, there's a difference between manual execution and service execution.

---

## ✅ Verify It's Actually Working

**In another terminal** (while Mosquitto is running in the first terminal):

```bash
# Check if port 8883 is listening
sudo netstat -tlnp | grep 8883

# Should show:
# tcp  0  0  0.0.0.0:8883  0.0.0.0:*  LISTEN  <pid>/mosquitto
```

**If it shows LISTEN, Mosquitto is working!** Press `Ctrl+C` in the first terminal to stop it.

---

## 🔍 Why Service Fails But Manual Works

### Issue 1: Service Using Different Config File

**Check what config the service uses:**
```bash
# Check service file
sudo systemctl cat mosquitto.service

# Look for ExecStart line - see what config it uses
```

**Fix:** Make sure service uses the same config:
```bash
# Check if there's a default config that's different
ls -la /etc/mosquitto/mosquitto.conf*
ls -la /etc/mosquitto/conf.d/

# Service might be loading additional configs from conf.d/
```

### Issue 2: Service Loading Multiple Config Files

Mosquitto might be loading configs from `/etc/mosquitto/conf.d/` that have errors.

**Check:**
```bash
# List all config files
ls -la /etc/mosquitto/
ls -la /etc/mosquitto/conf.d/ 2>/dev/null || echo "No conf.d directory"

# Check if there are other config files
sudo find /etc/mosquitto -name "*.conf"
```

**Fix:** Test with all configs:
```bash
# Mosquitto loads conf.d/*.conf automatically
# Test if any of those have errors
for conf in /etc/mosquitto/conf.d/*.conf; do
    if [ -f "$conf" ]; then
        echo "Testing: $conf"
        sudo -u mosquitto mosquitto -c "$conf" -v 2>&1 | head -5
    fi
done
```

### Issue 3: Environment Variables

Service might need different environment variables.

**Check service environment:**
```bash
# See what environment the service uses
sudo systemctl show mosquitto.service | grep Environment
```

### Issue 4: Working Directory

Service might be running from a different directory.

**Check:**
```bash
# See service working directory
sudo systemctl show mosquitto.service | grep WorkingDirectory
```

---

## 🔧 Fix: Make Service Use Same Config

### Option 1: Ensure Service Uses Your Config

```bash
# Check service file
sudo systemctl cat mosquitto.service

# If ExecStart doesn't specify -c /etc/mosquitto/mosquitto.conf, 
# Mosquitto uses default config search order
```

### Option 2: Test Default Config Behavior

```bash
# Stop service
sudo systemctl stop mosquitto

# Test what config Mosquitto would use by default
sudo -u mosquitto mosquitto -v 2>&1 | head -10

# This shows what config it loads automatically
```

### Option 3: Check for Conflicting Configs

```bash
# Check if there are multiple config files
sudo find /etc/mosquitto -name "*.conf" -type f

# Check if conf.d/ has conflicting configs
ls -la /etc/mosquitto/conf.d/ 2>/dev/null

# Temporarily rename conf.d to test
sudo mv /etc/mosquitto/conf.d /etc/mosquitto/conf.d.backup 2>/dev/null || true
sudo systemctl start mosquitto
sudo systemctl status mosquitto
```

---

## 🎯 Most Likely Fix

Since manual execution works, the service is probably loading a different or additional config file.

**Try this:**

```bash
# 1. Check what configs exist
sudo find /etc/mosquitto -name "*.conf"

# 2. Check if conf.d/ has files
ls -la /etc/mosquitto/conf.d/ 2>/dev/null

# 3. If conf.d/ has files, test them
for file in /etc/mosquitto/conf.d/*.conf; do
    if [ -f "$file" ]; then
        echo "=== Testing: $file ==="
        sudo -u mosquitto mosquitto -c "$file" -v 2>&1 | head -10
        echo ""
    fi
done

# 4. Temporarily disable conf.d/ and test service
sudo mkdir -p /etc/mosquitto/conf.d.backup
sudo mv /etc/mosquitto/conf.d/*.conf /etc/mosquitto/conf.d.backup/ 2>/dev/null || true
sudo systemctl start mosquitto
sudo systemctl status mosquitto
```

---

## ✅ If Manual Works, Start It as Service Properly

If manual execution works, you can:

1. **Verify it's listening:**
   ```bash
   # In another terminal
   sudo netstat -tlnp | grep 8883
   ```

2. **If listening, stop manual and start service:**
   ```bash
   # In first terminal: Ctrl+C to stop
   # Then:
   sudo systemctl start mosquitto
   sudo systemctl status mosquitto
   ```

3. **If service still fails, check for config conflicts:**
   ```bash
   # Check all config files
   sudo find /etc/mosquitto -name "*.conf"
   
   # Check service file
   sudo systemctl cat mosquitto.service
   ```

---

## 📋 Complete Diagnostic

Run this to find the difference:

```bash
echo "=== 1. Manual execution (what works) ==="
sudo systemctl stop mosquitto
timeout 3 sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1 | head -10

echo ""
echo "=== 2. Service config ==="
sudo systemctl cat mosquitto.service | grep -E "(ExecStart|Environment|WorkingDirectory)"

echo ""
echo "=== 3. All config files ==="
sudo find /etc/mosquitto -name "*.conf" -type f

echo ""
echo "=== 4. conf.d directory ==="
ls -la /etc/mosquitto/conf.d/ 2>/dev/null || echo "No conf.d directory"

echo ""
echo "=== 5. Test service with explicit config ==="
# Edit service to use explicit config (if needed)
```

---

## 💡 Quick Test

**Since manual works, try this:**

1. **Verify it's listening manually:**
   ```bash
   # Keep mosquitto running in one terminal
   # In another terminal:
   sudo netstat -tlnp | grep 8883
   ```

2. **If it shows LISTEN, the config is correct!**

3. **The issue is likely:**
   - Service loading additional configs from `conf.d/`
   - Service using a different config file
   - Service environment differences

**Share the output of:**
```bash
sudo find /etc/mosquitto -name "*.conf"
ls -la /etc/mosquitto/conf.d/ 2>/dev/null
sudo systemctl cat mosquitto.service | grep ExecStart
```

This will show us what's different!
