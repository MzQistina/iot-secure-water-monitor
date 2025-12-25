# Get Full Mosquitto Error Messages

When `systemctl status` output is truncated, use these commands to see the full error.

---

## 🔍 Commands to Get Full Error

### Method 1: Full Status Output (No Pager)

```bash
# Show full status without pager (shows all lines)
sudo systemctl status mosquitto.service --no-pager -l

# Or with more lines
sudo systemctl status mosquitto.service --no-pager -l | tail -50
```

### Method 2: Journal Logs (Most Detailed)

```bash
# Show last 50 log entries
sudo journalctl -u mosquitto.service -n 50 --no-pager

# Show last 100 entries
sudo journalctl -u mosquitto.service -n 100 --no-pager

# Show only errors
sudo journalctl -u mosquitto.service --no-pager | grep -i error

# Show everything since last boot
sudo journalctl -u mosquitto.service --no-pager -b
```

### Method 3: Test Configuration Directly

```bash
# Run Mosquitto manually to see exact error
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v

# This will show the exact error message
```

### Method 4: Check Recent Logs

```bash
# Check system logs
sudo journalctl -u mosquitto.service --since "10 minutes ago" --no-pager

# Check for specific errors
sudo journalctl -u mosquitto.service --no-pager | tail -30
```

---

## 📋 What to Look For

After running the commands above, look for:

1. **Permission errors:**
   - "Permission denied"
   - "Cannot open file"
   - "Access denied"

2. **File not found:**
   - "No such file or directory"
   - "Cannot find file"

3. **Configuration errors:**
   - "Error loading config"
   - "Unknown config variable"
   - "Syntax error"

4. **Certificate errors:**
   - "Error loading certificate"
   - "Cannot load key file"
   - "Certificate verification failed"

---

## 🎯 Quick Diagnostic Commands

Run these in order:

```bash
# 1. Full status
sudo systemctl status mosquitto.service --no-pager -l

# 2. Recent logs
sudo journalctl -u mosquitto.service -n 30 --no-pager

# 3. Test config manually
sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v

# 4. Check file permissions
ls -la /etc/mosquitto/certs/
ls -la /etc/mosquitto/passwd

# 5. Check if files exist
sudo test -f /etc/mosquitto/certs/ca-cert.pem && echo "CA cert exists" || echo "CA cert missing"
sudo test -f /etc/mosquitto/certs/server-cert.pem && echo "Server cert exists" || echo "Server cert missing"
sudo test -f /etc/mosquitto/certs/server-key.pem && echo "Server key exists" || echo "Server key missing"
sudo test -f /etc/mosquitto/passwd && echo "Password file exists" || echo "Password file missing"
```

---

## 💡 Pro Tip

If output is still truncated in terminal, save to file:

```bash
# Save full output to file
sudo systemctl status mosquitto.service --no-pager -l > mosquitto-status.txt
sudo journalctl -u mosquitto.service -n 50 --no-pager > mosquitto-logs.txt

# Then view the files
cat mosquitto-status.txt
cat mosquitto-logs.txt
```

---

## 📝 Share the Error

After running the diagnostic commands, share:
1. The output of `sudo journalctl -u mosquitto.service -n 30 --no-pager`
2. The output of `sudo -u mosquitto mosquitto -c /etc/mosquitto/mosquitto.conf -v`

This will show the exact error we need to fix!
