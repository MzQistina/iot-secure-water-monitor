# Files to Update in Raspbian

This document lists which files need to be copied/updated on Raspbian VirtualBox after making changes to the codebase.

## Quick Reference

**After ANY code changes, update these files on Raspbian:**

### Required Files (Core Functionality)
1. ✅ `multi_sensor_client.py` - **MUST UPDATE** (main simulation client)
2. ✅ `encryption_utils.py` - Update if encryption logic changed
3. ✅ `requirements_pi.txt` - Update if dependencies changed

### Key Files (Authentication)
4. ✅ `keys/public.pem` - Server's public key (update if server keys regenerated)
5. ✅ `sensor_keys/<user_id>/<device_id>/sensor_private.pem` - Device private keys (add new ones as needed)

---

## Detailed File List

### 1. Core Python Scripts

#### `multi_sensor_client.py` ⚠️ **MUST UPDATE**
- **Purpose**: Main multi-sensor simulation client
- **When to update**: After any changes to sensor simulation logic, user_id handling, or session management
- **Recent changes**: Added user_id support for same device_id with different users
- **Location on Raspbian**: `~/water-monitor/multi_sensor_client.py`

#### `encryption_utils.py` ⚠️ **UPDATE IF CHANGED**
- **Purpose**: Encryption/decryption utilities (RSA, AES)
- **When to update**: Only if encryption logic is modified
- **Location on Raspbian**: `~/water-monitor/encryption_utils.py`

#### `raspberry_pi_client.py` (Optional)
- **Purpose**: Legacy single-sensor client
- **When to update**: Only if you use single-sensor simulation
- **Location on Raspbian**: `~/water-monitor/raspberry_pi_client.py`

#### `key_cleanup_agent.py` (Optional but Recommended)
- **Purpose**: Automated key cleanup agent - listens for device deletion events via MQTT
- **When to update**: Copy once, run as background service
- **Location on Raspbian**: `~/water-monitor/key_cleanup_agent.py`
- **Usage**: `python3 key_cleanup_agent.py` (run in background or as systemd service)
- **See**: `DELETE_DEVICE_KEY_CLEANUP.md` for setup instructions

### 2. Configuration Files

#### `requirements_pi.txt`
- **Purpose**: Python package dependencies
- **When to update**: When adding/removing Python packages
- **Location on Raspbian**: `~/water-monitor/requirements_pi.txt`
- **Current dependencies**:
  ```
  requests>=2.31.0
  pycryptodome>=3.19.0
  paho-mqtt>=2.0.0
  ```

#### `delete_device_keys.sh` (Optional but Recommended)
- **Purpose**: Helper script to delete device keys when a device is removed
- **When to update**: Copy once, use as needed
- **Location on Raspbian**: `~/water-monitor/delete_device_keys.sh`
- **Usage**: `./delete_device_keys.sh <user_id> <device_id>`
- **See**: `DELETE_DEVICE_KEY_CLEANUP.md` for details

### 3. Key Files

#### `keys/public.pem`
- **Purpose**: Server's public RSA key (for encrypting sensor data)
- **When to update**: Only if server keys are regenerated
- **Location on Raspbian**: `~/water-monitor/keys/public.pem`
- **How to copy**: `scp -r keys/ pi@<raspbian_ip>:~/water-monitor/`

#### `sensor_keys/<user_id>/<device_id>/sensor_private.pem`
- **Purpose**: Device private keys for authentication
- **When to update**: When registering new sensors or adding sensors for new users
- **Location on Raspbian**: `~/water-monitor/sensor_keys/<user_id>/<device_id>/sensor_private.pem`
- **Structure**:
  ```
  sensor_keys/
  ├── 1/              (user_id)
  │   ├── pH01/
  │   │   └── sensor_private.pem
  │   └── tds01/
  │       └── sensor_private.pem
  └── 2/              (another user_id)
      └── pH01/       (same device_id, different user)
          └── sensor_private.pem
  ```

---

## Update Commands

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

**Update core files:**
```powershell
# Update main client script (MOST IMPORTANT)
scp multi_sensor_client.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Update encryption utilities (if changed)
scp encryption_utils.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Update requirements (if changed)
scp requirements_pi.txt $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
```

**Update keys (if needed):**
```powershell
# Update server public key (only if server keys regenerated)
scp -r keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Update/add sensor private keys (for new sensors)
scp -r sensor_keys/1/pH01 $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/sensor_keys/1/
scp -r sensor_keys/2/pH01 $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/sensor_keys/2/
```

**Update all at once:**
```powershell
# Copy all core files
scp multi_sensor_client.py encryption_utils.py requirements_pi.txt $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Copy helper script (optional)
scp delete_device_keys.sh $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/

# Copy all keys (if needed)
scp -r keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
scp -r sensor_keys/ $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
```

**Make script executable on Raspbian:**
```bash
# On Raspbian
chmod +x ~/water-monitor/delete_device_keys.sh
```

---

## When to Update

### After Code Changes

| Change Type | Files to Update |
|------------|----------------|
| Modified `multi_sensor_client.py` | ✅ `multi_sensor_client.py` |
| Modified `encryption_utils.py` | ✅ `encryption_utils.py` |
| Added new Python dependency | ✅ `requirements_pi.txt` |
| Regenerated server keys | ✅ `keys/public.pem` |
| Registered new sensor | ✅ `sensor_keys/<user_id>/<device_id>/sensor_private.pem` |
| Added sensor for new user | ✅ `sensor_keys/<new_user_id>/<device_id>/sensor_private.pem` |

### After Recent Updates (User ID Support)

**If you updated `multi_sensor_client.py` to support same device_id with different users:**

1. ✅ **MUST UPDATE**: `multi_sensor_client.py`
   - New user_id handling in `DeviceSessionManager`
   - Updated logging to show `[device_id (user:user_id)]`
   - Enhanced sensor detection with user_id support

2. ✅ **Verify**: `sensor_keys/` structure
   - Ensure keys are in `sensor_keys/<user_id>/<device_id>/` format
   - Check that all sensors have keys in correct user folders

---

## Verification Steps

After updating files on Raspbian, verify:

### 1. Check Files Exist
```bash
cd ~/water-monitor
ls -la multi_sensor_client.py
ls -la encryption_utils.py
ls -la requirements_pi.txt
ls -la keys/public.pem
```

### 2. Check Key Structure
```bash
# Check user-specific keys
ls -R sensor_keys/

# Verify specific sensor keys
ls -la sensor_keys/1/pH01/sensor_private.pem
ls -la sensor_keys/2/pH01/sensor_private.pem  # If same device_id for different user
```

### 3. Test Python Imports
```bash
python3 -c "import requests; import Crypto; print('✅ Dependencies OK')"
python3 -c "from encryption_utils import encrypt_data; print('✅ encryption_utils OK')"
```

### 4. Test Client Script
```bash
# Check script runs (will fail without server, but should show help)
python3 multi_sensor_client.py --help
```

---

## Quick Update Checklist

After making code changes:

- [ ] Updated `multi_sensor_client.py` on Raspbian
- [ ] Updated `encryption_utils.py` (if changed)
- [ ] Updated `requirements_pi.txt` (if dependencies changed)
- [ ] Installed new dependencies: `pip3 install -r requirements_pi.txt`
- [ ] Verified files exist: `ls -la ~/water-monitor/`
- [ ] Verified keys exist: `ls -R ~/water-monitor/sensor_keys/`
- [ ] Tested client: `python3 multi_sensor_client.py --help`

---

## File Structure on Raspbian

```
~/water-monitor/
├── multi_sensor_client.py      ← UPDATE THIS after code changes
├── encryption_utils.py          ← UPDATE if encryption changed
├── raspberry_pi_client.py        ← Optional (legacy)
├── requirements_pi.txt           ← UPDATE if dependencies changed
├── delete_device_keys.sh          ← Optional helper script
├── keys/
│   └── public.pem               ← UPDATE if server keys regenerated
└── sensor_keys/
    ├── 1/                       ← User ID folder
    │   ├── pH01/
    │   │   └── sensor_private.pem
    │   └── tds01/
    │       └── sensor_private.pem
    └── 2/                       ← Another user
        └── pH01/                ← Same device_id, different user
            └── sensor_private.pem
```

---

## Notes

1. **Most Common Update**: `multi_sensor_client.py` - Update this whenever simulation logic changes
2. **Keys Rarely Change**: Server public key and sensor private keys only need updating when:
   - Server keys are regenerated (rare)
   - New sensors are registered
   - Sensors are added for new users
3. **Dependencies**: Only update `requirements_pi.txt` if you add/remove Python packages
4. **No Server Files Needed**: `app.py`, `db.py`, etc. stay on Windows - only client files go to Raspbian
5. **Key Cleanup**: When deleting devices, remember to delete keys on Raspbian - see `DELETE_DEVICE_KEY_CLEANUP.md`

---

## Troubleshooting

### "No module named 'encryption_utils'"
- **Fix**: Copy `encryption_utils.py` to Raspbian

### "Private key not found"
- **Fix**: Copy sensor keys: `scp -r sensor_keys/<user_id>/<device_id> pi@<ip>:~/water-monitor/sensor_keys/<user_id>/`

### "AttributeError" or "NameError" in multi_sensor_client.py
- **Fix**: Update `multi_sensor_client.py` with latest version

### "ImportError: No module named 'requests'"
- **Fix**: Install dependencies: `pip3 install -r requirements_pi.txt`

