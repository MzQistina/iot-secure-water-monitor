# Files to Copy to Raspbian - Quick Checklist

## Required Files (Must Copy)

### 1. Core Python Scripts
- ✅ **`multi_sensor_client.py`** - Main simulation client (MOST IMPORTANT)
- ✅ **`encryption_utils.py`** - Encryption/decryption utilities
- ✅ **`requirements_pi.txt`** - Python dependencies list

### 2. Key Files (Authentication)
- ✅ **`keys/public.pem`** - Server's public key (for encrypting data)
- ✅ **`sensor_keys/<user_id>/<device_id>/sensor_private.pem`** - Device private keys

## Optional Files (Recommended)

- ⚙️ **`key_cleanup_agent.py`** - Automated key cleanup agent (for MQTT-based deletion)
- ⚙️ **`delete_device_keys.sh`** - Helper script for manual key deletion
- ⚙️ **`raspberry_pi_client.py`** - Legacy single-sensor client (if needed)

---

## Quick Copy Commands

### From Windows PowerShell

**Navigate to project directory:**
```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
```

**Set variables:**
```powershell
$RASPBIAN_IP = "10.0.2.15"  # Change to your Raspbian IP
$RASPBIAN_USER = "pi"        # Change if different
```

**Copy all required files:**
```powershell
# Create directory on Raspbian
ssh $RASPBIAN_USER@$RASPBIAN_IP "mkdir -p ~/water-monitor"

# Copy core Python scripts
scp multi_sensor_client.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp encryption_utils.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp requirements_pi.txt $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Copy server public key
scp -r keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Copy sensor private keys (all users)
scp -r sensor_keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Copy optional files
scp simulators/sensor/key_cleanup_agent.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp delete_device_keys.sh $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
```

---

## File Structure on Raspbian

After copying, your Raspbian should have:

```
~/water-monitor/
├── multi_sensor_client.py      ✅ Required
├── encryption_utils.py          ✅ Required
├── requirements_pi.txt          ✅ Required
├── key_cleanup_agent.py         ⚙️ Optional
├── delete_device_keys.sh        ⚙️ Optional
├── keys/
│   └── public.pem               ✅ Required
└── sensor_keys/
    ├── 1/                       ✅ User ID folder
    │   ├── pH01/
    │   │   └── sensor_private.pem
    │   └── tds01/
    │       └── sensor_private.pem
    └── 2/                       ✅ Another user
        └── pH01/
            └── sensor_private.pem
```

---

## After Copying - Setup Steps

### 1. Install Python Dependencies
```bash
cd ~/water-monitor
pip3 install -r requirements_pi.txt
```

### 2. Set Permissions
```bash
chmod +x multi_sensor_client.py
chmod +x key_cleanup_agent.py
chmod +x delete_device_keys.sh
find sensor_keys -name "sensor_private.pem" -exec chmod 600 {} \;
```

### 3. Verify Files
```bash
ls -la ~/water-monitor/
ls -R ~/water-monitor/sensor_keys/
ls -la ~/water-monitor/keys/public.pem
```

---

## Summary

**Minimum Required:**
1. `multi_sensor_client.py`
2. `encryption_utils.py`
3. `requirements_pi.txt`
4. `keys/public.pem`
5. `sensor_keys/<user_id>/<device_id>/sensor_private.pem` (for each sensor)

**Recommended Additional:**
- `key_cleanup_agent.py` (for automated key cleanup)
- `delete_device_keys.sh` (for manual key deletion)

**Total Files:** ~5-7 files + key directories

