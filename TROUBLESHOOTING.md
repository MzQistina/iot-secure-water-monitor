# Troubleshooting Guide

## Finding Your Server IP Address

### Why `http://192.168.1.100:5000`?

The IP address `192.168.1.100` in examples is **just a placeholder**. Replace it with your **actual server IP address**.

### How to Find Your Server IP Address

**On Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter.

**On Linux/Mac:**
```bash
ifconfig
# Or
ip addr show
```

**On Raspberry Pi:**
```bash
hostname -I
```

**From another device:**
```bash
ping raspberrypi.local
# Or check router admin panel
```

### Understanding the URL

- **`http://`** - Protocol (HTTP)
- **`192.168.1.100`** - Your server's IP address (replace this!)
- **`:5000`** - Port number (Flask's default port)

## What is WSGI and Why Do You Need It?

### Short Answer

**Without WSGI file:**
- ❌ Flask app won't run on production servers
- ❌ You'll see directory listing instead of your app
- ❌ Server doesn't know how to run your Python app
- ❌ Only works locally (using `python app.py`)

### What is WSGI?

**WSGI** (Web Server Gateway Interface) is a **bridge** between:
- Your Flask app (Python code)
- Web server (Apache, LiteSpeed, Nginx, etc.)

**Think of it like this:**
- **Without WSGI:** Server sees files but doesn't know what to do with them
- **With WSGI:** Server knows "run this Python app when someone visits the site"

### Why You Need `app.wsgi`

1. **Tells server where your app is**
2. **Sets up Python environment**
3. **Configures environment variables**
4. **Starts your Flask application**

**Without it:** Server shows directory listing (files/folders)
**With it:** Server runs your Flask app and shows your website

See `APACHE_SETUP.md` or `LITESPEED_DEPLOYMENT_GUIDE.md` for WSGI configuration details.

## Troubleshooting Guide

## "No such file" Errors

### Error: `raspberry_pi_client.py: No such file or directory`

**Problem:** The file doesn't exist in your current directory or hasn't been copied to VirtualBox.

**Solution:**
1. Check if you're in the correct directory:
   ```bash
   pwd
   ls -la
   ```

2. If files are missing, copy them from Windows to VirtualBox:
   - Use shared folder, SCP, or USB
   - See `VIRTUALBOX_SIMULATION_SETUP.md` for transfer methods

3. Navigate to the correct directory:
   ```bash
   cd ~/water-monitor
   python3 raspberry_pi_client.py pH01 http://10.0.2.2:5000 --once
   ```

### Error: `encryption_utils.py: No such file or directory`

**Problem:** `encryption_utils.py` is missing or not in the same directory.

**Solution:**
1. Ensure `encryption_utils.py` is in the same directory as `raspberry_pi_client.py`
2. Check file exists:
   ```bash
   ls -la encryption_utils.py
   ```

### Error: `keys/public.pem: No such file or directory`

**Problem:** Server public key is missing.

**Solution:**
1. Check if keys directory exists:
   ```bash
   ls -la keys/
   ```

2. Copy `keys/public.pem` from Windows to VirtualBox:
   ```bash
   mkdir -p ~/water-monitor/keys
   # Then copy public.pem to ~/water-monitor/keys/
   ```

### Error: `sensor_keys/pH01/sensor_private.pem: No such file or directory`

**Problem:** Device private key is missing.

**Solution:**
1. Check if sensor_keys directory exists:
   ```bash
   ls -la sensor_keys/
   ls -la sensor_keys/pH01/
   ```

2. Copy the entire `sensor_keys` directory from Windows to VirtualBox:
   ```bash
   mkdir -p ~/water-monitor/sensor_keys
   # Then copy sensor_keys/<device_id>/ to ~/water-monitor/sensor_keys/
   ```

## Common File Structure Issues

### Verify All Files Are Present

Run this in VirtualBox to check:
```bash
cd ~/water-monitor
ls -la

# Should show:
# - raspberry_pi_client.py
# - encryption_utils.py
# - requirements_pi.txt (optional)
# - keys/
#   └── public.pem
# - sensor_keys/
#   └── <device_id>/
#       └── sensor_private.pem
```

### Check File Permissions

```bash
# Make script executable
chmod +x raspberry_pi_client.py

# Secure private keys
chmod 600 sensor_keys/*/sensor_private.pem
```

## Python Import Errors

### Error: `ModuleNotFoundError: No module named 'encryption_utils'`

**Solution:**
1. Ensure `encryption_utils.py` is in the same directory
2. Run from the correct directory:
   ```bash
   cd ~/water-monitor
   python3 raspberry_pi_client.py ...
   ```

### Error: `ModuleNotFoundError: No module named 'requests'`

**Solution:** Install dependencies:
```bash
pip3 install requests pycryptodome
# OR
pip3 install -r requirements_pi.txt
```

## Network Connection Errors

### Error: `Connection refused` or `Cannot connect`

**Check:**
1. Server is running on Windows
2. Correct IP address:
   - NAT mode: `10.0.2.2`
   - Bridged: Your Windows IP
3. Port 5000 is correct
4. Firewall allows connection

### Error: `Name or service not known`

**Solution:** Use IP address instead of hostname:
```bash
# Wrong:
python3 raspberry_pi_client.py pH01 http://localhost:5000

# Correct (NAT mode):
python3 raspberry_pi_client.py pH01 http://10.0.2.2:5000
```

## Quick Diagnostic Commands

Run these to diagnose issues:

```bash
# 1. Check current directory
pwd

# 2. List files
ls -la

# 3. Check Python version
python3 --version

# 4. Check if dependencies installed
pip3 list | grep -E "requests|pycryptodome"

# 5. Test network connectivity (NAT mode)
ping 10.0.2.2

# 6. Test HTTP connection
curl http://10.0.2.2:5000

# 7. Check file permissions
ls -la raspberry_pi_client.py encryption_utils.py
ls -la keys/public.pem
ls -la sensor_keys/*/sensor_private.pem
```

## Still Having Issues?

1. **Check the setup guide:** `VIRTUALBOX_SIMULATION_SETUP.md`
2. **Verify file checklist:** `VIRTUALBOX_FILES_CHECKLIST.txt`
3. **Check server IP:** `FINDING_SERVER_IP.md`
4. **Review simulation guide:** `HOW_TO_SIMULATE_READINGS.md`



