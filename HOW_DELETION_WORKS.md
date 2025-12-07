# How Device Deletion Works

This document explains the complete flow of device deletion, from user action to automatic key cleanup.

## Overview

When a device is deleted, the system performs:
1. **Server-side deletion** - Removes device from database
2. **MQTT notification** - Publishes deletion event (if MQTT configured)
3. **Automatic key cleanup** - Raspbian agent deletes keys automatically
4. **Manual cleanup** - Fallback if MQTT is not configured

---

## Complete Deletion Flow

### Step 1: User Initiates Deletion

**Location:** Web Dashboard (`/sensors` page)

**Action:**
- User clicks "Delete" button for a device
- Form submits POST request to `/sensors/delete`
- Includes `device_id` in form data

**Code:** `templates/sensors.html`
```html
<form method="post" action="{{ url_for('sensors_delete') }}" 
      onsubmit="return confirmDelete('{{ s.device_id }}')">
    <input type="hidden" name="device_id" value="{{ s.device_id }}">
    <button type="submit" class="btn">Delete</button>
</form>
```

---

### Step 2: Server Validates and Deletes

**Location:** `app.py` - `sensors_delete()` function

**Process:**

1. **Extract device_id** from form data
2. **Get user_id** from session (ensures user owns the device)
3. **Verify ownership** - Check device belongs to current user
4. **Delete from database** - Call `delete_sensor_by_device_id()`
5. **Notify Raspbian** - Attempt MQTT notification
6. **Show success message** - Display result to user

**Code Flow:**
```python
@app.route('/sensors/delete', methods=['POST'])
@login_required
def sensors_delete():
    # 1. Get device_id from form
    device_id = request.form.get('device_id', '').strip()
    
    # 2. Get user_id from session
    user_id = session.get('user_id')
    
    # 3. Verify ownership
    sensor = get_sensor_by_device_id(device_id, user_id)
    if not sensor:
        flash('Sensor not found or no permission', 'error')
        return redirect(url_for('sensors'))
    
    # 4. Delete from database
    ok = delete_sensor_by_device_id(device_id)
    
    if ok:
        # 5. Try MQTT notification
        cleanup_notified = notify_raspbian_key_cleanup(device_id, user_id)
        
        if cleanup_notified:
            flash('Sensor deleted. ✅ Key cleanup notification sent.', 'success')
        else:
            flash('Sensor deleted. ⚠️ Remember to delete keys on Raspbian.', 'success')
    
    return redirect(url_for('sensors'))
```

---

### Step 3: Database Deletion

**Location:** `db.py` - `delete_sensor_by_device_id()` function

**Process:**

1. **Get database connection** from connection pool
2. **Execute DELETE query** - Removes sensor record
3. **Commit transaction** - Makes deletion permanent
4. **Return success status** - True if row was deleted

**SQL Query:**
```sql
DELETE FROM sensors WHERE device_id = %s
```

**Code:**
```python
def delete_sensor_by_device_id(device_id: str) -> bool:
    conn = pool.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sensors WHERE device_id = %s", (device_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    return deleted
```

**What Gets Deleted:**
- ✅ Sensor record from `sensors` table
- ✅ All sensor metadata (device_type, location, thresholds, etc.)
- ✅ Public key stored in database
- ❌ **NOT deleted**: Historical sensor data (stays in `sensor_data` table)
- ❌ **NOT deleted**: Keys on Raspbian (handled separately)

---

### Step 4: MQTT Notification (Automated)

**Location:** `app.py` - `notify_raspbian_key_cleanup()` function

**Process:**

1. **Check MQTT configuration** - Verify `MQTT_HOST` is set
2. **Connect to MQTT broker** - Establish connection
3. **Publish deletion event** - Send message to `devices/delete` topic
4. **Disconnect** - Close MQTT connection
5. **Return status** - True if notification sent successfully

**MQTT Message Format:**
```json
{
    "action": "delete",
    "device_id": "pH01",
    "user_id": "1",
    "timestamp": "2024-01-15T10:30:00"
}
```

**Code:**
```python
def notify_raspbian_key_cleanup(device_id: str, user_id: int) -> bool:
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        return False  # MQTT not configured
    
    client = mqtt.Client()
    client.connect(mqtt_host, mqtt_port, 60)
    
    payload = json.dumps({
        'action': 'delete',
        'device_id': device_id,
        'user_id': str(user_id),
        'timestamp': datetime.now().isoformat()
    })
    
    result = client.publish('devices/delete', payload, qos=1)
    client.disconnect()
    
    return result.rc == mqtt.MQTT_ERR_SUCCESS
```

**Requirements:**
- ✅ `MQTT_HOST` environment variable must be set
- ✅ MQTT broker must be running and accessible
- ✅ `paho-mqtt` Python package installed

**If MQTT fails:**
- System continues normally
- User sees manual cleanup reminder
- Keys must be deleted manually

---

### Step 5: Raspbian Receives Notification

**Location:** `key_cleanup_agent.py` - `on_message()` callback

**Process:**

1. **Agent listens** - Continuously listening on `devices/delete` topic
2. **Receives message** - MQTT broker delivers deletion event
3. **Parse JSON** - Extract `device_id` and `user_id`
4. **Delete keys** - Call `delete_device_keys()` function
5. **Log result** - Show success/failure in logs

**Code Flow:**
```python
def on_message(client, userdata, msg):
    # 1. Parse message
    payload = msg.payload.decode('utf-8')
    data = json.loads(payload)
    
    device_id = data.get('device_id')
    user_id = data.get('user_id')
    action = data.get('action', 'delete')
    
    # 2. Validate action
    if action != 'delete':
        return
    
    # 3. Delete keys
    success = delete_device_keys(user_id, device_id)
    
    # 4. Log result
    if success:
        print(f"✅ Successfully deleted keys for device '{device_id}'")
```

---

### Step 6: Key Deletion on Raspbian

**Location:** `key_cleanup_agent.py` - `delete_device_keys()` function

**Process:**

1. **Try user-specific location** - `sensor_keys/<user_id>/<device_id>/`
2. **If found, delete** - Remove entire directory
3. **Try legacy location** - `sensor_keys/<device_id>/` (fallback)
4. **If found, delete** - Remove legacy directory
5. **Return status** - True if any keys were deleted

**Code:**
```python
def delete_device_keys(user_id: str, device_id: str) -> bool:
    deleted = False
    
    # Try user-specific location
    user_key_path = f"sensor_keys/{user_id}/{device_id}"
    if os.path.exists(user_key_path):
        shutil.rmtree(user_key_path)
        deleted = True
    
    # Try legacy location
    legacy_key_path = f"sensor_keys/{device_id}"
    if os.path.exists(legacy_key_path):
        shutil.rmtree(legacy_key_path)
        deleted = True
    
    return deleted
```

**What Gets Deleted:**
- ✅ `sensor_keys/<user_id>/<device_id>/sensor_private.pem`
- ✅ `sensor_keys/<user_id>/<device_id>/sensor_public.pem` (if exists)
- ✅ Entire device directory

**What Stays:**
- ✅ Other devices' keys (unaffected)
- ✅ Server public key (`keys/public.pem`)

---

## Deletion Scenarios

### Scenario 1: Automated Deletion (MQTT Configured)

```
User clicks Delete
    ↓
Server deletes from database ✅
    ↓
Server publishes MQTT message ✅
    ↓
Raspbian agent receives message ✅
    ↓
Keys automatically deleted ✅
    ↓
User sees: "Sensor deleted. ✅ Key cleanup notification sent."
```

**Result:** Fully automated, no manual steps needed

---

### Scenario 2: Manual Deletion (MQTT Not Configured)

```
User clicks Delete
    ↓
Server deletes from database ✅
    ↓
MQTT notification fails (not configured) ❌
    ↓
User sees: "Sensor deleted. ⚠️ Remember to delete keys on Raspbian: sensor_keys/1/pH01/"
    ↓
Admin manually deletes keys on Raspbian
```

**Result:** Database cleaned, but keys must be deleted manually

---

### Scenario 3: Partial Failure

```
User clicks Delete
    ↓
Server deletes from database ✅
    ↓
Server publishes MQTT message ✅
    ↓
Raspbian agent not running ❌
    ↓
Keys remain on Raspbian ⚠️
```

**Result:** Database cleaned, but keys remain (agent must be restarted)

---

## Security Considerations

### What Happens to Data?

1. **Sensor Record:** ✅ Deleted from `sensors` table
2. **Historical Data:** ❌ **NOT deleted** - Stays in `sensor_data` table for audit trail
3. **Public Key:** ✅ Deleted from database
4. **Private Key:** ✅ Deleted from Raspbian (if automated) or must be deleted manually

### Why Keep Historical Data?

- **Audit trail** - Track what happened in the past
- **Compliance** - May be required for regulatory purposes
- **Analytics** - Historical trends and analysis
- **Forensics** - Investigate past incidents

### Security Implications

**If keys are NOT deleted:**
- ⚠️ Device can still authenticate (if keys exist)
- ⚠️ Device can still send data (if simulation running)
- ⚠️ Data will be rejected (device not in database)
- ✅ **No security breach** - Device can't access other users' data

**Best Practice:**
- ✅ Always delete keys when device is deleted
- ✅ Use automated cleanup agent
- ✅ Verify keys are gone after deletion
- ✅ Stop any running simulations

---

## Troubleshooting

### Keys Not Being Deleted Automatically

**Check 1: MQTT Configuration**
```bash
# On Windows (server)
echo $env:MQTT_HOST  # Should show broker IP
```

**Check 2: Cleanup Agent Running**
```bash
# On Raspbian
ps aux | grep key_cleanup_agent
```

**Check 3: MQTT Broker Running**
```bash
# Test connection
mosquitto_sub -h <broker_ip> -t devices/delete -v
```

**Check 4: Agent Logs**
```bash
# On Raspbian
tail -f cleanup_agent.log
```

### Manual Cleanup Required

If automated cleanup fails, delete keys manually:

```bash
# On Raspbian
cd ~/water-monitor
rm -rf sensor_keys/<user_id>/<device_id>/

# Verify deletion
ls sensor_keys/<user_id>/<device_id>/  # Should show "No such file"
```

---

## Summary

**Deletion Process:**
1. ✅ User clicks Delete → Server validates ownership
2. ✅ Database record deleted → Sensor removed from system
3. ✅ MQTT notification sent → (if configured)
4. ✅ Raspbian agent receives → Listens for deletion events
5. ✅ Keys automatically deleted → Cleanup complete

**Key Points:**
- Database deletion is **immediate** and **permanent**
- Key cleanup can be **automated** (MQTT) or **manual**
- Historical data is **preserved** for audit trail
- Multiple deletion paths ensure **flexibility** and **reliability**









