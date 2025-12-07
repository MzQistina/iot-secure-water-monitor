# Raspbian VirtualBox Sensor Simulation Guide

Complete step-by-step instructions for simulating sensor data in Raspbian VirtualBox.

## 📋 Prerequisites

- ✅ Raspbian VirtualBox installed and running
- ✅ Windows host running Flask server (Apache on port 80)
- ✅ Sensors registered on the server
- ✅ Sensor keys generated (`sensor_keys/<user_id>/<device_id>/sensor_private.pem`)

---

## 🚀 Quick Start

### Step 1: Find Your Server IP Address

**On Windows (Host):**
```powershell
# Find your Windows IP address
ipconfig | findstr IPv4
```

**Common IPs:**
- **NAT Mode**: Use `10.0.2.2` (VirtualBox NAT default gateway)
- **Bridged Mode**: Use your Windows IP (e.g., `192.168.1.100`)

---

### Step 2: Transfer Files to Raspbian

**Project Location on Windows:**
```
C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor
```

**Files to Transfer:**
- `multi_sensor_client.py`
- `encryption_utils.py`
- `requirements_pi.txt`
- `keys/` directory
- `sensor_keys/` directory

#### Method 1: Using SCP (Recommended)

**From Windows PowerShell (in project directory):**

```powershell
# Navigate to project directory
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"

# Set variables
$RASPBIAN_IP = "10.0.2.15"  # Change to your Raspbian IP
$RASPBIAN_USER = "pi"        # Change if different

# Create directory on Raspbian
ssh $RASPBIAN_USER@$RASPBIAN_IP "mkdir -p ~/water-monitor"

# Transfer Python files
scp multi_sensor_client.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp encryption_utils.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp requirements_pi.txt $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Transfer keys directories
scp -r keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp -r sensor_keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
```

**OR transfer everything at once:**
```powershell
scp -r multi_sensor_client.py encryption_utils.py requirements_pi.txt keys/ sensor_keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
```

**Troubleshooting SCP:**
- If connection refused, enable SSH on Raspbian: `sudo systemctl enable ssh && sudo systemctl start ssh`
- If permission denied, check username or set up SSH keys

#### Method 2: Using VirtualBox Shared Folder

1. **Configure Shared Folder in VirtualBox:**
   - Select your Raspbian VM → Settings → Shared Folders
   - Add new shared folder:
     - **Folder Path**: `C:\Users\NURMIZAN QISTINA\Desktop\fyp`
     - **Folder Name**: `fyp`
     - **Auto-mount**: ✓
     - **Mount Point**: `/media/sf_fyp`

2. **Mount Shared Folder (on Raspbian - one-time setup):**
   ```bash
   # Add user to vboxsf group
   sudo usermod -aG vboxsf $USER
   # Logout and login again
   ```

3. **Copy Files (on Raspbian):**
   ```bash
   mkdir -p ~/water-monitor
   cp /media/sf_fyp/iot-secure-water-monitor/multi_sensor_client.py ~/water-monitor/
   cp /media/sf_fyp/iot-secure-water-monitor/encryption_utils.py ~/water-monitor/
   cp /media/sf_fyp/iot-secure-water-monitor/requirements_pi.txt ~/water-monitor/
   cp -r /media/sf_fyp/iot-secure-water-monitor/keys ~/water-monitor/
   cp -r /media/sf_fyp/iot-secure-water-monitor/sensor_keys ~/water-monitor/
   ```

**If shared folder not visible:**
```bash
# Check if mounted
ls /media/sf_*

# Manually mount if needed
sudo mount -t vboxsf fyp /media/sf_fyp
```

#### Method 3: Using USB Drive

1. Copy files to USB drive on Windows
2. Insert USB into VirtualBox (Devices → USB → Select USB device)
3. Mount USB on Raspbian
4. Copy files from USB to `~/water-monitor/`

#### Verify Files Transferred

**On Raspbian:**
```bash
cd ~/water-monitor
ls -la
# Should show: multi_sensor_client.py, encryption_utils.py, requirements_pi.txt, keys/, sensor_keys/

# Verify keys structure
ls -R sensor_keys/
```

---

### Step 3: Install Dependencies on Raspbian

**SSH into Raspbian or open terminal:**

```bash
# Navigate to project directory
cd ~/water-monitor

# Update package list
sudo apt-get update

# Install Python 3 and pip (if not installed)
sudo apt-get install -y python3 python3-pip

# Install required Python packages
pip3 install requests pycryptodome

# OR use requirements file
pip3 install -r requirements_pi.txt
```

**Verify installation:**
```bash
python3 -c "import requests; import Crypto; print('✅ Dependencies installed')"
```

---

### Step 4: Verify File Structure

**On Raspbian, check your directory structure:**

```bash
cd ~/water-monitor
tree -L 3
```

**Expected structure:**
```
water-monitor/
├── multi_sensor_client.py
├── encryption_utils.py
├── requirements_pi.txt
├── keys/
│   └── public.pem
└── sensor_keys/
    ├── 5/                    # User ID folder
    │   ├── pH01/
    │   │   └── sensor_private.pem
    │   └── tds01/
    │       └── sensor_private.pem
    └── 6/                    # Another user
        └── turb01/
            └── sensor_private.pem
```

---

### Step 5: Test Network Connectivity

**On Raspbian, test connection to server:**

```bash
# Test NAT mode (default VirtualBox networking)
ping -c 3 10.0.2.2

# OR test bridged mode (if configured)
ping -c 3 192.168.1.100  # Replace with your Windows IP

# Test HTTP connection
curl http://10.0.2.2/api/public/active_sensors
# OR
curl http://192.168.1.100/api/public/active_sensors
```

**If connection fails:**
- Check VirtualBox network settings (NAT vs Bridged)
- Check Windows firewall (allow port 80)
- Verify Flask server is running on Windows

---

### Step 6: Run Simulation

**Option A: Simulate ALL Active Sensors (Recommended)**

```bash
cd ~/water-monitor

# Using NAT mode (default VirtualBox)
python3 multi_sensor_client.py --all http://10.0.2.2

# OR using Bridged mode (if configured)
python3 multi_sensor_client.py --all http://192.168.1.100
```

**Option B: Simulate Specific Sensors**

```bash
# Simulate specific sensors by device_id
python3 multi_sensor_client.py --ids pH01,tds01,turb01 http://10.0.2.2

# With custom interval (default is 60 seconds)
python3 multi_sensor_client.py --ids pH01,tds01 --interval 30 http://10.0.2.2
```

**Option C: Simulate Sensors from One Location**

```bash
# Filter by location
python3 multi_sensor_client.py --all --location "Tank A" http://10.0.2.2
```

---

## 📝 Command Reference

### Basic Usage

```bash
python3 multi_sensor_client.py [OPTIONS] <SERVER_URL>
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--all` | Simulate all active sensors from server | `--all` |
| `--ids` | Simulate specific sensors (comma-separated) | `--ids pH01,tds01` |
| `--interval` | Seconds between readings (default: 60) | `--interval 30` |
| `--location` | Filter sensors by location | `--location "Tank A"` |

### Examples

```bash
# Simulate all sensors, 30-second interval
python3 multi_sensor_client.py --all --interval 30 http://10.0.2.2

# Simulate specific sensors
python3 multi_sensor_client.py --ids pH01,tds01 http://10.0.2.2

# Simulate sensors from specific location
python3 multi_sensor_client.py --all --location "Tank A" http://10.0.2.2

# Simulate with custom server port
python3 multi_sensor_client.py --all http://10.0.2.2:8080
```

---

## 🔍 Troubleshooting

### Problem: "No active sensors found"

**Solution:**
1. Check sensors are registered and active on server
2. Verify sensor keys exist: `ls -R ~/water-monitor/sensor_keys/`
3. Check server URL is correct: `curl http://10.0.2.2/api/public/active_sensors`

### Problem: "Connection refused" or "Cannot connect"

**Solution:**
1. **Check VirtualBox network mode:**
   - NAT mode: Use `10.0.2.2`
   - Bridged mode: Use Windows host IP

2. **Test connectivity:**
   ```bash
   ping 10.0.2.2
   curl http://10.0.2.2/api/public/active_sensors
   ```

3. **Check Windows firewall:**
   - Allow port 80 in Windows Firewall
   - Verify Apache/Flask is running

4. **Check server is running:**
   ```powershell
   # On Windows
   netstat -ano | findstr :80
   ```

### Problem: "Private key not found"

**Solution:**
1. Verify key structure:
   ```bash
   ls ~/water-monitor/sensor_keys/<user_id>/<device_id>/sensor_private.pem
   ```

2. Check file permissions:
   ```bash
   chmod 600 ~/water-monitor/sensor_keys/*/*/sensor_private.pem
   ```

3. Ensure keys match registered sensors on server

### Problem: "Failed to establish session"

**Solution:**
1. Check server error logs: `C:\Apache24\logs\error.log`
2. Verify sensor is active on server
3. Check server URL includes correct port (80 or 8080)

### Problem: "Module not found" errors

**Solution:**
```bash
# Install missing packages
pip3 install requests pycryptodome

# Verify installation
python3 -c "import requests; import Crypto; print('OK')"
```

---

## 📊 Expected Output

**Successful simulation:**

```
======================================================================
Multi-Sensor Secure Water Monitor Client
======================================================================
Server URL: http://10.0.2.2
Sensors: pH01, tds01, turb01
Interval: 60 seconds
Total sensors: 3
======================================================================

Starting simulation (Press Ctrl+C to stop)...

[pH01] Starting simulation (type: ph, interval: 60s)
[tds01] Starting simulation (type: tds, interval: 60s)
[turb01] Starting simulation (type: turbidity, interval: 60s)
[pH01] ✅ Session established
[tds01] ✅ Session established
[turb01] ✅ Session established
[pH01] ✅ Reading submitted: ph=7.23
[tds01] ✅ Reading submitted: tds=245
[turb01] ✅ Reading submitted: turbidity=2.15
...
```

**To stop simulation:**
- Press `Ctrl+C`
- All sensors will stop gracefully

---

## 🎯 Key Points

1. **Simulation runs ON Raspbian**, not Windows
2. **Server runs ON Windows** (Flask/Apache)
3. **Network configuration matters:**
   - NAT mode: Use `10.0.2.2`
   - Bridged mode: Use Windows host IP
4. **Keys must match registered sensors:**
   - Structure: `sensor_keys/<user_id>/<device_id>/sensor_private.pem`
   - Keys must be generated for registered sensors
5. **Server must be running** before starting simulation

---

## 📚 Additional Resources

- **Single sensor simulation**: Use `raspberry_pi_client.py` (legacy)
- **Server configuration**: See `app.py` and Apache configuration
- **Key generation**: See `simulators/sensor/sensor_keygen.py`

---

## ✅ Checklist

Before running simulation:

- [ ] Raspbian VirtualBox is running
- [ ] Windows server is running (Apache/Flask on port 80)
- [ ] Files copied to `~/water-monitor/` on Raspbian
- [ ] Dependencies installed (`pip3 install requests pycryptodome`)
- [ ] Server public key exists: `~/water-monitor/keys/public.pem`
- [ ] Sensor private keys exist: `~/water-monitor/sensor_keys/<user_id>/<device_id>/sensor_private.pem`
- [ ] Sensors registered and active on server
- [ ] Network connectivity tested (`ping 10.0.2.2`)
- [ ] Server URL confirmed (NAT: `10.0.2.2`, Bridged: Windows IP)

---

**Ready to simulate? Run:**

```bash
cd ~/water-monitor
python3 multi_sensor_client.py --all http://10.0.2.2
```

