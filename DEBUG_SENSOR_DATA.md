# Debugging sensor_data Insert Issues

## Step 1: Submit Sensor Data and Check Logs Immediately

1. **Submit sensor data** via your simulator or API
2. **Immediately check logs**:
```powershell
Get-Content C:\Apache24\logs\error.log -Tail 100 | Select-String "insert_sensor_data|ERROR|WARNING|DEBUG"
```

## Step 2: Check if Data is Actually Being Inserted

Run this SQL query to check recent inserts:

```sql
SELECT * FROM sensor_data 
ORDER BY recorded_at DESC 
LIMIT 10;
```

## Step 3: Check Table Structure

Verify the table exists and has correct structure:

```sql
DESCRIBE sensor_data;
```

Should show:
- `id` INT AUTO_INCREMENT PRIMARY KEY
- `sensor_id` INT NOT NULL
- `recorded_at` DATETIME
- `value` TEXT NOT NULL  ← Should be TEXT (for encryption)
- `status` ENUM

## Step 4: Check if Sensor Exists

Verify your sensor is registered:

```sql
SELECT id, device_id, device_type, status 
FROM sensors 
WHERE device_id = 'your-device-id';
```

The `id` column is what's used as `sensor_db_id` in `insert_sensor_data()`.

## Step 5: Test Encryption Directly

Run this Python script to test if encryption works:

```python
# test_encryption_direct.py
import os
os.environ['DB_ENCRYPTION_KEY'] = 'T468PZiZfDtJDQEjxlzMMJqIDOSHJ4Pp3exMQtedD50='

from db_encryption import get_db_encryption
from db import insert_sensor_data, get_pool

# Test encryption
encryption = get_db_encryption()
test_value = 7.5
encrypted = encryption.encrypt_value(test_value)
decrypted = encryption.decrypt_value(encrypted)
print(f"Encryption test: {test_value} → {encrypted[:50]}... → {decrypted}")

# Test database insert (replace 1 with actual sensor_id)
# result = insert_sensor_data(sensor_db_id=1, value=7.5, status='normal')
# print(f"Insert result: {result}")
```

## Common Issues

### Issue 1: Python print() not showing in Apache logs
- Python `print()` statements go to stdout/stderr
- Check if they appear in error.log
- If not, they might be buffered

### Issue 2: Transaction not committed
- Check if `conn.commit()` is being called
- Verify MySQL autocommit settings

### Issue 3: Wrong sensor_id
- `sensor_db_id` must be the `id` from `sensors` table, not `device_id`
- Check: `SELECT id FROM sensors WHERE device_id = 'your-device-id'`

### Issue 4: Encryption failing silently
- Check if `DB_ENCRYPTION_KEY` is set correctly in app.wsgi
- Test encryption module directly

## Quick Test Query

After submitting data, run:

```sql
-- Check latest sensor_data entries
SELECT 
    sd.id,
    sd.sensor_id,
    sd.value,
    sd.status,
    sd.recorded_at,
    s.device_id,
    s.device_type
FROM sensor_data sd
JOIN sensors s ON s.id = sd.sensor_id
ORDER BY sd.recorded_at DESC
LIMIT 5;
```

If `value` shows encrypted strings (long base64), encryption is working!

