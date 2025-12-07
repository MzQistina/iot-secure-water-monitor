# VirtualBox Raspbian Simulation Setup Guide

> **📘 For detailed step-by-step instructions, see [RASPBIAN_SIMULATION_GUIDE.md](RASPBIAN_SIMULATION_GUIDE.md)**

This guide helps you set up sensor data simulation in a Raspbian VirtualBox environment.

**⚠️ IMPORTANT: All simulation commands are run ON the Raspbian VirtualBox, NOT on Windows!**

- **Windows Host**: Runs the Flask server (`app.py`) on Apache (port 80)
- **Raspbian VirtualBox**: Runs the sensor simulation clients (`multi_sensor_client.py` or `raspberry_pi_client.py`)

## Files Required in VirtualBox

Copy these files to your Raspbian VirtualBox (create a directory like `~/water-monitor/`):

### 1. Core Python Files
```
water-monitor/
├── raspberry_pi_client.py    # Main client script
├── encryption_utils.py        # Encryption utilities
├── requirements_pi.txt       # Python dependencies (optional but recommended)
```

### 2. Key Files (Required for Authentication)
```
water-monitor/
├── keys/
│   └── public.pem            # Server's public key (for encryption)
└── sensor_keys/
                                                                                          ├── <user_id>/             # User-specific folder (NEW structure)
    │   └── <device_id>/       # e.g., pH01, tds01, turb01, etc.
    │       └── sensor_private.pem
    └── <device_id>/            # Legacy structure (still supported)
        └── sensor_private.pem
```

**Example structure:**
```
water-monitor/
├── raspberry_pi_client.py
├── multi_sensor_client.py
├── encryption_utils.py
├── requirements_pi.txt       # Optional: for easy dependency installation
├── keys/
│   └── public.pem
└── sensor_keys/
    ├── 5/                    # User ID folder (NEW)
    │   ├── pH01/
    │   │   └── sensor_private.pem
    │   └── tds01/
    │       └── sensor_private.pem
    ├── 6/                    # Another user
    │   └── turb01/
    │       └── sensor_private.pem
    └── pH01/                 # Legacy structure (still works)
        └── sensor_private.pem
```

**Note:** Keys are now organized by `user_id`. The client automatically finds keys in both:
- `sensor_keys/<user_id>/<device_id>/sensor_private.pem` (preferred)
- `sensor_keys/<device_id>/sensor_private.pem` (legacy, still supported)

## Step-by-Step Setup

### Step 1: Transfer Files to VirtualBox

**Option A: Using Shared Folder**
1. Set up a shared folder between Windows host and VirtualBox
2. Copy files from Windows to shared folder
3. Copy files from shared folder to `~/water-monitor/` in Raspbian

**Option B: Using SCP (if network is configured)**
```bash
# From Windows PowerShell (in your project directory)
scp raspberry_pi_client.py encryption_utils.py pi@<virtualbox_ip>:~/water-monitor/
scp -r keys/ pi@<virtualbox_ip>:~/water-monitor/
scp -r sensor_keys/ pi@<virtualbox_ip>:~/water-monitor/
```

**Option C: Manual Copy**
1. Copy files to USB drive or use VirtualBox's drag-and-drop feature
2. Move files to `~/water-monitor/` directory

### Step 2: Install Python Dependencies

SSH into your Raspbian VirtualBox or open terminal:

```bash
# Update package list
sudo apt-get update

# Install Python 3 and pip if not already installed
sudo apt-get install -y python3 python3-pip

# Option A: Install using requirements file (recommended)
cd ~/water-monitor
pip3 install -r requirements_pi.txt

# Option B: Install packages individually
pip3 install requests pycryptodome

# Option C: Use virtual environment (recommended for isolation)
python3 -m venv ~/water-monitor/venv
source ~/water-monitor/venv/bin/activate
pip install -r requirements_pi.txt
```

### Step 3: Set File Permissions

```bash
cd ~/water-monitor

# Make scripts executable
chmod +x raspberry_pi_client.py

# Secure private keys (important!)
chmod 600 sensor_keys/*/sensor_private.pem
```

### Step 4: Verify Server Connection

Before running the client, ensure:
1. **Server is running** on your host machine (Windows)
2. **Device is registered** on the server with `active` status
3. **Network connectivity** - VirtualBox can reach the host machine

**Test connectivity:**
```bash
# Replace with your host machine's IP address
ping <host_machine_ip>

# Test server endpoint
curl http://<host_machine_ip>:5000/api/device/session/request?device_id=pH01
```

**Find your host machine IP:**
- Windows: Open PowerShell and run `ipconfig`
- Look for IPv4 address (e.g., 192.168.1.100)

**Configure VirtualBox Network:**
- Use **NAT** or **Bridged Adapter** mode
- For NAT: Use `10.0.2.2` to access host machine
- For Bridged: Use your host's actual IP address

### Step 5: Run Sensor Simulation

**⚠️ All commands below are run INSIDE the Raspbian VirtualBox terminal/SSH session!**

You have two options for simulating sensors:

#### Option A: Multi-Sensor Simulation (Recommended)

Simulate **multiple sensors simultaneously** using `multi_sensor_client.py`:

**Simulate ALL active sensors from server:**

**Run this command INSIDE Raspbian VirtualBox:**
```bash
# SSH into Raspbian or open terminal in VirtualBox
cd ~/water-monitor
# Replace <host_ip> with your Windows server IP (see FINDING_SERVER_IP.md)
python3 multi_sensor_client.py --all http://<host_ip>:5000 --interval 60
```

**Simulate sensors from ONE location (recommended):**

**Run this command INSIDE Raspbian VirtualBox:**
```bash
# Only simulate sensors at a specific location
python3 multi_sensor_client.py --all --location "Building A" http://<host_ip>:5000 --interval 60
```

**Simulate specific sensors:**
```bash
# Simulate pH01, tds01, and turb01 together
python3 multi_sensor_client.py --ids pH01,tds01,turb01 http://<host_ip>:5000 --interval 60
```

**Simulate with custom interval:**
```bash
python3 multi_sensor_client.py --ids pH01,tds01 --interval 30 http://<host_ip>:5000
```

**How it works:**
- The client automatically fetches active sensors from the server
- Gets location information from server registration
- Only simulates sensors that are active on the server
- Use `--location` to simulate one location at a time

**Benefits:**
- ✅ All sensors run simultaneously in parallel
- ✅ Single command to start all sensors
- ✅ Each sensor maintains its own session independently
- ✅ Easy to manage and stop (Ctrl+C stops all)

#### Option B: Single Sensor Simulation

Simulate **one sensor at a time** using `raspberry_pi_client.py`:

**Single reading test:**
```bash
cd ~/water-monitor
python3 raspberry_pi_client.py pH01 http://<host_ip>:5000 --once
```

**Continuous simulation (every 60 seconds):**
```bash
python3 raspberry_pi_client.py pH01 http://<host_ip>:5000 --interval 60
```

**To simulate multiple sensors, open multiple terminals:**
```bash
# Terminal 1
python3 raspberry_pi_client.py pH01 http://<host_ip>:5000 --interval 60

# Terminal 2
python3 raspberry_pi_client.py tds01 http://<host_ip>:5000 --interval 60

# Terminal 3
python3 raspberry_pi_client.py turb01 http://<host_ip>:5000 --interval 60
```

**⚠️ Important:** Replace `<host_ip>` with your actual server IP address:
- **NAT mode:** Use `10.0.2.2`
- **Bridged mode:** Use your Windows IP (find with `ipconfig` on Windows)
- **Host-Only:** Use `192.168.56.1`

See `FINDING_SERVER_IP.md` for detailed instructions.

**Press Ctrl+C to stop**

## Simulated Sensor Data

The current `read_sensor_data()` function generates:
- **pH**: Random value between 6.5 - 8.5
- **TDS**: Random value between 50 - 500 ppm
- **Turbidity**: Random value between 0.0 - 5.0 NTU
- **Temperature**: Random value between 20.0 - 30.0 °C

**For detailed simulation instructions and customization examples, see:** `HOW_TO_SIMULATE_READINGS.md`

## Customizing Simulated Data

To modify the simulated sensor values, edit the `read_sensor_data()` function in `raspberry_pi_client.py` (around line 227):

```python
def read_sensor_data():
    """Read actual sensor data - REPLACE THIS with your sensor reading code."""
    import random
    return {
        "device_id": device_id,
        "device_type": "ph",  # Change based on sensor type: "ph", "tds", "turbidity", "temperature"
        "ph": round(random.uniform(6.5, 8.5), 2),      # Adjust range as needed
        "tds": random.randint(50, 500),                 # Adjust range as needed
        "turbidity": round(random.uniform(0.0, 5.0), 2), # Adjust range as needed
        "temperature": round(random.uniform(20.0, 30.0), 2), # Adjust range as needed
    }
```

## Troubleshooting

### "Private key not found"
- Verify the path: `sensor_keys/<device_id>/sensor_private.pem`
- Check file exists: `ls -la sensor_keys/pH01/sensor_private.pem`
- Ensure device_id matches exactly (case-sensitive)

### "Server public key not found"
- Verify `keys/public.pem` exists
- Check path in script matches your directory structure

### "device not active or not found"
- Register device on server first: Visit `http://<host_ip>:5000/sensors`
- Ensure device_id matches exactly
- Set status to `active`

### "Connection refused" or "Failed to connect"
- Check server is running on host machine
- Verify IP address and port (default: 5000)
- Check VirtualBox network settings
- Try `ping <host_ip>` to test connectivity

### "Invalid signature"
- Ensure private key matches the public key registered on server
- Verify you're using the correct device_id

## Quick Test Checklist

- [ ] Files copied to `~/water-monitor/` in VirtualBox
- [ ] Python dependencies installed (`requests`, `pycryptodome`)
- [ ] Private key exists: `sensor_keys/<device_id>/sensor_private.pem`
- [ ] Server public key exists: `keys/public.pem`
- [ ] Device registered on server with `active` status
- [ ] Network connectivity verified (can ping host machine)
- [ ] Server is running on host machine
- [ ] Single reading test successful (`--once` flag)
- [ ] Continuous simulation working

## Example Usage

```bash
# Simulate pH sensor sending data every 30 seconds
python3 raspberry_pi_client.py pH01 http://192.168.1.100:5000 --interval 30

# Simulate TDS sensor sending data every 60 seconds
python3 raspberry_pi_client.py tds01 http://192.168.1.100:5000 --interval 60

# Simulate turbidity sensor - single reading
python3 raspberry_pi_client.py turb01 http://192.168.1.100:5000 --once
```

## Next Steps

1. Test with different device IDs
2. Monitor data on server dashboard: `http://<host_ip>:5000`
3. Check server logs for received data
4. Verify data appears in database
5. Test with multiple simulated sensors simultaneously



