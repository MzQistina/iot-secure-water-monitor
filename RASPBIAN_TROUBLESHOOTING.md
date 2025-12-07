# Raspbian VirtualBox Troubleshooting Guide

Common issues and solutions when setting up simulation on Raspbian VirtualBox.

---

## 🔒 Issue: Package Manager Lock Error

### Error Message
```
E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 2576 (apt-get)
E: Unable to acquire the dpkg frontend lock
```

### Cause
Another `apt-get` or `dpkg` process is already running (usually an automatic update or previous interrupted installation).

### Solutions

#### Solution 1: Wait for Process to Finish (Recommended)
```bash
# Check if process is still running
ps aux | grep apt-get

# Wait 2-5 minutes, then try again
sudo apt-get update
```

#### Solution 2: Kill the Stuck Process
```bash
# Find the process ID (PID)
ps aux | grep apt-get

# Kill the process (replace 2576 with actual PID)
sudo kill -9 2576

# Wait a few seconds, then remove lock files
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock
sudo rm /var/cache/apt/archives/lock

# Reconfigure dpkg
sudo dpkg --configure -a

# Try again
sudo apt-get update
```

#### Solution 3: Restart System (Last Resort)
```bash
sudo reboot
# Wait for system to restart, then try installation again
```

---

## 📋 Issue: Copy-Paste Errors

### Error Messages
```
bash: $'\E[200~sudo': command not found
bash: ~sudo: command not found
```

### Cause
Copy-pasting from certain terminals or applications adds extra control characters (`^[[200~`, `~`) to commands.

### Solutions

#### Solution 1: Type Commands Manually (Most Reliable)
- Don't copy-paste
- Type each command character by character
- Most reliable method

#### Solution 2: Use Text Editor Script
```bash
# Create a script file
nano install.sh

# Paste commands into nano (Ctrl+Shift+V or right-click)
# Save: Ctrl+O, Enter
# Exit: Ctrl+X

# Run the script
bash install.sh
```

#### Solution 3: Disable Bracketed Paste Mode
```bash
# Disable paste mode
printf '\e[?2004l'

# Now try pasting commands again
```

#### Solution 4: Use SSH with Better Terminal
- Use PuTTY, Windows Terminal, or WSL
- These handle copy-paste better than VirtualBox console

---

## 🌐 Issue: Network Connection Failed

### Error Messages
```
ping: unknown host 10.0.2.2
curl: (7) Failed to connect
```

### Solutions

#### Check VirtualBox Network Settings
1. VirtualBox → Settings → Network
2. Adapter 1 should be:
   - **NAT** (default) → Use `10.0.2.2`
   - **Bridged Adapter** → Use Windows host IP

#### Test Connectivity
```bash
# Test NAT mode
ping -c 3 10.0.2.2

# Test bridged mode (replace with your Windows IP)
ping -c 3 192.168.1.100

# Check network configuration
ip addr show
route -n
```

#### Fix Network Configuration
```bash
# Restart network service
sudo systemctl restart networking

# Or restart network interface
sudo ifdown eth0 && sudo ifup eth0
```

---

## 📦 Issue: Python Package Installation Failed

### Error Messages
```
ERROR: Could not find a version that satisfies the requirement
ERROR: No matching distribution found
```

### Solutions

#### Update pip
```bash
# Upgrade pip first
pip3 install --upgrade pip

# Then install packages
pip3 install requests pycryptodome paho-mqtt
```

#### Use Python 3 Explicitly
```bash
# Make sure you're using Python 3
python3 --version

# Install with python3 -m pip
python3 -m pip install requests pycryptodome paho-mqtt
```

#### Install System Packages First
```bash
# Install build dependencies
sudo apt-get install -y python3-dev build-essential

# Then install Python packages
pip3 install requests pycryptodome paho-mqtt
```

---

## 🔑 Issue: Key Files Not Found

### Error Messages
```
Private key not found: sensor_keys/5/pH01/sensor_private.pem
No active sensors found
```

### Solutions

#### Check Key Structure
```bash
# List all keys
find ~/water-monitor/sensor_keys -name "sensor_private.pem"

# Check specific user's keys
ls -R ~/water-monitor/sensor_keys/5/

# Verify file permissions
ls -la ~/water-monitor/sensor_keys/5/pH01/sensor_private.pem
```

#### Fix Permissions
```bash
# Set correct permissions
chmod 600 ~/water-monitor/sensor_keys/*/*/sensor_private.pem

# Or recursively
find ~/water-monitor/sensor_keys -name "sensor_private.pem" -exec chmod 600 {} \;
```

#### Verify Keys Match Registered Sensors
- Check sensors are registered on server
- Verify `device_id` matches folder name
- Ensure `user_id` matches folder structure

---

## 🚫 Issue: Permission Denied

### Error Messages
```
Permission denied: sensor_keys/5/pH01/sensor_private.pem
bash: multi_sensor_client.py: Permission denied
```

### Solutions

#### Fix File Permissions
```bash
# Make scripts executable
chmod +x ~/water-monitor/multi_sensor_client.py
chmod +x ~/water-monitor/raspberry_pi_client.py

# Fix key permissions
chmod 600 ~/water-monitor/sensor_keys/*/*/sensor_private.pem

# Fix directory permissions
chmod 755 ~/water-monitor/sensor_keys
```

#### Check Ownership
```bash
# Check file owner
ls -la ~/water-monitor/

# Fix ownership if needed (replace 'pi' with your username)
sudo chown -R pi:pi ~/water-monitor/
```

---

## 🔄 Issue: Simulation Not Starting

### Error Messages
```
No active sensors found
Failed to establish session
Connection refused
```

### Solutions

#### Check Server is Running
```bash
# Test server connection
curl http://10.0.2.2/api/public/active_sensors

# Should return JSON with active sensors
```

#### Verify Sensors are Active
- Login to web interface
- Check sensors are registered and status is "active"
- Verify `user_id` matches key folder structure

#### Check Network
```bash
# Test connectivity
ping -c 3 10.0.2.2

# Test HTTP
curl -v http://10.0.2.2/api/public/active_sensors
```

#### Check Logs
```bash
# Run simulation with verbose output
python3 multi_sensor_client.py --all http://10.0.2.2

# Check for error messages in output
```

---

## 💾 Issue: Out of Disk Space

### Error Messages
```
No space left on device
E: Write error - write (28: No space left on device)
```

### Solutions

#### Check Disk Usage
```bash
# Check disk space
df -h

# Check largest files
du -sh ~/* | sort -h | tail -10
```

#### Free Up Space
```bash
# Clean package cache
sudo apt-get clean
sudo apt-get autoremove

# Remove old logs
sudo journalctl --vacuum-time=7d

# Remove temporary files
sudo rm -rf /tmp/*
```

---

## 🔧 Quick Fixes Summary

### Most Common Issues

1. **Package lock**: Wait or kill process, remove locks
2. **Copy-paste errors**: Type commands manually
3. **Network issues**: Check VirtualBox network settings
4. **Permission errors**: Fix file permissions
5. **Missing keys**: Verify key structure matches sensors

### Emergency Reset

If everything fails:
```bash
# Stop all processes
pkill -9 python3
pkill -9 apt-get

# Remove locks
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock

# Restart network
sudo systemctl restart networking

# Try again
sudo apt-get update
```

---

## 📞 Still Having Issues?

1. Check system logs: `journalctl -xe`
2. Check Python version: `python3 --version`
3. Verify file structure: `ls -R ~/water-monitor/`
4. Test network: `ping 10.0.2.2`
5. Check server logs on Windows

---

## 📚 Related Documentation

- **Full Setup Guide**: `RASPBIAN_SIMULATION_GUIDE.md`
- **Commands Reference**: `command.txt`
- **Quick Start**: `RASPBIAN_QUICK_START.md`

