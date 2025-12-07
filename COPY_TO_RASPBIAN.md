# Files to Copy to Raspbian for Multi-Sensor Client

## Required Files

Copy these files to your Raspbian system (Raspberry Pi):

### 1. Main Client Script
- `multi_sensor_client.py` - The updated simulator client

### 2. Dependencies
- `encryption_utils.py` - Encryption utilities (required by multi_sensor_client.py)

### 3. Server Public Key
- `keys/public.pem` - Server's public key for encrypting sensor data

### 4. Sensor Private Keys
- `sensor_keys/<user_id>/<device_id>/sensor_private.pem` - Private keys for each sensor
  - Example: `sensor_keys/5/amm03/sensor_private.pem`
  - Example: `sensor_keys/5/tds05/sensor_private.pem`

### 5. Python Requirements
- `requirements_pi.txt` - Python dependencies

## Directory Structure on Raspbian

```
/home/pi/iot-secure-water-monitor/
├── multi_sensor_client.py
├── encryption_utils.py
├── requirements_pi.txt
├── keys/
│   └── public.pem
└── sensor_keys/
    └── <user_id>/
        └── <device_id>/
            └── sensor_private.pem
```

## Copy Commands

### Option 1: Using SCP (from Windows PowerShell)

```powershell
# Set variables
$RASPBIAN_IP = "192.168.1.XXX"  # Replace with your Raspbian IP
$RASPBIAN_USER = "pi"  # Replace with your username
$RASPBIAN_PATH = "/home/pi/iot-secure-water-monitor"

# Copy main files
scp iot-secure-water-monitor/multi_sensor_client.py ${RASPBIAN_USER}@${RASPBIAN_IP}:${RASPBIAN_PATH}/
scp iot-secure-water-monitor/encryption_utils.py ${RASPBIAN_USER}@${RASPBIAN_IP}:${RASPBIAN_PATH}/
scp iot-secure-water-monitor/requirements_pi.txt ${RASPBIAN_USER}@${RASPBIAN_IP}:${RASPBIAN_PATH}/

# Copy server public key
scp -r iot-secure-water-monitor/keys ${RASPBIAN_USER}@${RASPBIAN_IP}:${RASPBIAN_PATH}/

# Copy sensor keys (replace user_id and device_id as needed)
scp -r iot-secure-water-monitor/sensor_keys ${RASPBIAN_USER}@${RASPBIAN_IP}:${RASPBIAN_PATH}/
```

### Option 2: Using FileZilla or WinSCP

1. Connect to your Raspbian IP address
2. Navigate to `/home/pi/iot-secure-water-monitor/` (create if doesn't exist)
3. Copy the files maintaining the directory structure

### Option 3: Using Git (if you have a repository)

```bash
# On Raspbian
cd /home/pi
git clone <your-repo-url> iot-secure-water-monitor
cd iot-secure-water-monitor
```

## Setup on Raspbian

After copying files, run these commands on Raspbian:

```bash
cd /home/pi/iot-secure-water-monitor

# Install Python dependencies
pip3 install -r requirements_pi.txt

# Make script executable
chmod +x multi_sensor_client.py

# Test connection (replace with your server IP)
python3 multi_sensor_client.py --all http://192.168.1.100:5000
```

## Usage Examples

```bash
# Simulate all sensors
python3 multi_sensor_client.py --all http://192.168.1.100:5000

# Simulate specific sensors
python3 multi_sensor_client.py --ids amm03,tds05,ph01 http://192.168.1.100:5000

# Simulate sensors from specific location
python3 multi_sensor_client.py --all --location "Tank A" http://192.168.1.100:5000

# Simulate with custom interval (30 seconds)
python3 multi_sensor_client.py --all --interval 30 http://192.168.1.100:5000

# Simulate for specific user
python3 multi_sensor_client.py --all --user-id 5 http://192.168.1.100:5000
```

## Troubleshooting

### Error: "encryption_utils.py not found"
- Make sure `encryption_utils.py` is in the same directory as `multi_sensor_client.py`

### Error: "Server public key not found"
- Make sure `keys/public.pem` exists
- Check the path: `keys/public.pem` relative to `multi_sensor_client.py`

### Error: "Private key not found"
- Verify sensor keys exist: `sensor_keys/<user_id>/<device_id>/sensor_private.pem`
- Check user_id matches your sensor's user_id

### Error: "500 Internal Server Error"
- Check server logs: `C:\Apache24\logs\error.log`
- Restart Apache: `Restart-Service Apache2.4` (as Administrator)

### Error: "device not active or not found"
- Make sure sensors are registered and active on the server
- Check sensor status in the dashboard

## Important Notes

1. **Keep private keys secure** - Never commit `sensor_private.pem` files to version control
2. **Update regularly** - When you update `multi_sensor_client.py`, copy the new version to Raspbian
3. **Check server URL** - Make sure the server URL is accessible from Raspbian
4. **Firewall** - Ensure port 5000 (or your Flask port) is open on the server

