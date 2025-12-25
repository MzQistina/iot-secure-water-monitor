# Get Actual Error for Exit Code 1

Exit code 1 means configuration error. We need to see the actual error message.

---

## 🔍 Get the Actual Error Message

### Method 1: Check Journal Logs for Mosquitto Output

```bash
# Get the actual error from Mosquitto
sudo journalctl -u mosquitto -n 50 --no-pager | grep -i -A 5 "error\|failed\|cannot\|unable"

# Or get all recent logs
sudo journalctl -u mosquitto -n 50 --no-pager
```

### Method 2: Run Mosquitto Directly (Most Reliable)

```bash
# Stop the service
sudo systemctl stop mosquitto

# Run Mosquitto directly to see the error
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1 | head -30

# This will show the exact error message
```

### Method 3: Check Stderr Output

```bash
# Run and capture all output
sudo systemctl stop mosquitto
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1
```

---

## 🎯 Most Important Command

**Run this to see the actual error:**

```bash
sudo systemctl stop mosquitto
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1 | head -30
```

**This will show the exact error message** that's causing exit code 1.

---

## 🐛 Common Exit Code 1 Errors

### Error: "Error loading certificate"
**Fix:** Check certificate file paths and validity

### Error: "Error opening password file"
**Fix:** Check password file path and permissions

### Error: "Error opening log file"
**Fix:** Check log directory permissions

### Error: "Address already in use"
**Fix:** Port 8883 already in use

### Error: "Unknown config variable"
**Fix:** Typo in configuration file

---

## 📋 Complete Diagnostic

Run this complete diagnostic:

```bash
echo "=== 1. Stop service ==="
sudo systemctl stop mosquitto

echo ""
echo "=== 2. Run directly to see error ==="
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1 | head -30

echo ""
echo "=== 3. Check journal logs ==="
sudo journalctl -u mosquitto -n 30 --no-pager | grep -i -A 3 "error\|failed"

echo ""
echo "=== 4. Verify config file paths ==="
sudo grep -E "(cafile|certfile|keyfile|password_file|log_dest)" /etc/mosquitto/mosquitto.conf

echo ""
echo "=== 5. Check if files exist ==="
for path in $(sudo grep -E "(cafile|certfile|keyfile|password_file)" /etc/mosquitto/mosquitto.conf | awk '{print $2}'); do
    if [ -f "$path" ]; then
        echo "✅ $path exists"
    else
        echo "❌ $path MISSING"
    fi
done
```

---

## 💡 Key Point

**Exit code 1 = Configuration error**

**We need the actual error message to fix it!**

Run: `sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v 2>&1`

This will show exactly what's wrong.
