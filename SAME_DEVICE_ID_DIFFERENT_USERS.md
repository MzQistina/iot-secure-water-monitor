# Running Sensors with Same Device ID but Different Users

## Overview

The system supports having multiple sensors with the **same device_id** but belonging to **different users**. This is useful for:
- Testing scenarios where the same physical device is registered under multiple user accounts
- Simulating shared devices across different user accounts
- Multi-tenant deployments

## How It Works

### Database Schema

The `sensors` table has a composite unique constraint:
```sql
UNIQUE KEY unique_user_device (user_id, device_id)
```

This means:
- ✅ **Same device_id + Different user_id** = **ALLOWED**
- ❌ **Same device_id + Same user_id** = **NOT ALLOWED** (duplicate)

### Key Storage Structure

Each sensor's private key is stored in a user-specific location:
```
sensor_keys/
  ├── <user_id_1>/
  │   └── <device_id>/
  │       └── sensor_private.pem
  └── <user_id_2>/
      └── <device_id>/          # Same device_id, different user
          └── sensor_private.pem
```

## Setup Steps

### 1. Register Sensors with Same Device ID for Different Users

**For User 1:**
1. Log in as User 1
2. Register sensor with device_id: `pH01`
3. Upload or generate public key
4. Key stored in: `sensor_keys/<user_id_1>/pH01/sensor_private.pem`

**For User 2:**
1. Log in as User 2
2. Register sensor with device_id: `pH01` (same device_id!)
3. Upload or generate public key
4. Key stored in: `sensor_keys/<user_id_2>/pH01/sensor_private.pem`

### 2. Generate Private Keys for Both Users

**Option A: Using MQTT Provision Agent**

Send MQTT messages for each user:

```bash
# For User 1
mosquitto_pub -h localhost -t "keys/pH01/public" -m '{"device_id": "pH01", "action": "generate_and_publish_key", "user_id": "1"}'

# For User 2 (same device_id, different user_id)
mosquitto_pub -h localhost -t "keys/pH01/public" -m '{"device_id": "pH01", "action": "generate_and_publish_key", "user_id": "2"}'
```

**Option B: Manual Key Generation**

```bash
# For User 1
python simulators/sensor/sensor_keygen.py --device-id pH01 --user-id 1

# For User 2
python simulators/sensor/sensor_keygen.py --device-id pH01 --user-id 2
```

### 3. Copy Keys to Raspbian

Copy both user-specific keys to your Raspbian VirtualBox:

```bash
# From Windows PowerShell
$RASPBIAN_IP = "10.0.2.15"
$RASPBIAN_USER = "pi"

# Copy User 1's key
scp -r sensor_keys/1/pH01 $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/sensor_keys/1/

# Copy User 2's key
scp -r sensor_keys/2/pH01 $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/sensor_keys/2/
```

## Running Simulation

### Simulate All Sensors (Including Same Device ID)

The `multi_sensor_client.py` automatically detects and simulates all active sensors, including those with the same device_id but different users:

```bash
cd ~/water-monitor
python3 multi_sensor_client.py --all http://10.0.2.2
```

**Output Example:**
```
======================================================================
Multi-Sensor Secure Water Monitor Client
======================================================================
Server URL: http://10.0.2.2
Sensors: pH01 (user:1), pH01 (user:2), tds01 (user:1)
Locations: Building A, Building B
Interval: 60 seconds
Total sensors: 3
======================================================================

[pH01 (user:1)] Starting simulation (type: ph, interval: 60s, location: Building A, user_id: 1)
[pH01 (user:2)] Starting simulation (type: ph, interval: 60s, location: Building B, user_id: 2)
[tds01 (user:1)] Starting simulation (type: tds, interval: 60s, location: Building A, user_id: 1)

[pH01 (user:1)] ✅ Reading #1 submitted - ✅ Safe
[pH01 (user:2)] ✅ Reading #1 submitted - ✅ Safe
[tds01 (user:1)] ✅ Reading #1 submitted - ✅ Safe
```

### Simulate Specific Sensors

You can simulate specific sensors by device_id (will simulate all users with that device_id):

```bash
# Simulate all pH01 sensors (from all users)
python3 multi_sensor_client.py --ids pH01 http://10.0.2.2
```

### Filter by Location

If sensors with the same device_id are at different locations:

```bash
# Simulate only sensors from Building A
python3 multi_sensor_client.py --all --location "Building A" http://10.0.2.2
```

## How the Client Distinguishes Sensors

The client uses the following logic:

1. **Fetches active sensors** from `/api/public/active_sensors` (includes `user_id`)
2. **Finds private keys** using: `sensor_keys/<user_id>/<device_id>/sensor_private.pem`
3. **Creates separate sessions** for each sensor (even with same device_id)
4. **Displays with user_id** in logs: `[device_id (user:user_id)]`

## Important Notes

### Session Management

- Each sensor (even with same device_id) gets its **own session token**
- Sessions are managed independently per sensor
- The server identifies sensors by **device_id + signature** (which includes user_id via private key)

### Data Isolation

- Each user's dashboard shows **only their own sensors**
- Data from `pH01 (user:1)` appears on User 1's dashboard
- Data from `pH01 (user:2)` appears on User 2's dashboard
- No data mixing between users

### Key Requirements

- ✅ Each sensor **must** have its own private key in `sensor_keys/<user_id>/<device_id>/`
- ✅ Private keys **must** match the public key registered on the server
- ✅ Both sensors must be **active** on the server

## Troubleshooting

### "No private key found" Warning

If you see:
```
⚠️  Warning: pH01 is active on server but no private key found locally
   Check: sensor_keys/1/pH01/sensor_private.pem or sensor_keys/pH01/sensor_private.pem
```

**Solution:**
1. Verify the key exists: `ls -la sensor_keys/<user_id>/<device_id>/sensor_private.pem`
2. Check user_id matches the server's user_id
3. Ensure key was copied correctly from Windows

### "Failed to establish session" Error

If a sensor fails to establish a session:

1. **Check key matches**: The private key must match the public key registered on the server
2. **Verify sensor is active**: Check the server dashboard to ensure sensor status is "active"
3. **Check user_id**: Ensure the user_id in the key path matches the server's user_id

### Multiple Sensors Not Starting

If sensors with the same device_id don't start:

1. **Check server response**: `curl http://10.0.2.2/api/public/active_sensors`
2. Verify both sensors appear in the response with different `user_id` values
3. Ensure both have private keys in the correct locations

## Example Scenario

**Setup:**
- User 1 (ID: 1) registers `pH01` at "Building A"
- User 2 (ID: 2) registers `pH01` at "Building B" (same device_id!)

**Keys:**
- `sensor_keys/1/pH01/sensor_private.pem` (User 1)
- `sensor_keys/2/pH01/sensor_private.pem` (User 2)

**Run Simulation:**
```bash
python3 multi_sensor_client.py --all http://10.0.2.2
```

**Result:**
- Both `pH01` sensors run simultaneously
- Each sends data to its respective user's dashboard
- Logs show: `[pH01 (user:1)]` and `[pH01 (user:2)]` to distinguish them

## Summary

✅ **Same device_id + Different user_id** = **Supported**
✅ Each sensor needs its own private key in user-specific folder
✅ Client automatically detects and simulates all sensors
✅ Logs include user_id to distinguish sensors
✅ Data is isolated per user on the dashboard

