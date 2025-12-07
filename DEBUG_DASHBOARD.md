# Debugging Empty Dashboard Graph

## Step 1: Access Dashboard and Check Logs

1. **Open your dashboard** in browser: `http://localhost/dashboard` (or your URL)

2. **Immediately check logs**:
```powershell
Get-Content C:\Apache24\logs\error.log -Tail 100 | Select-String "dashboard|DEBUG|WARNING|ERROR"
```

Look for:
- `DEBUG: dashboard - Retrieved X rows from database`
- `DEBUG: dashboard - Created X tank buckets`
- `WARNING: dashboard - No rows retrieved`
- `WARNING: dashboard - No tank buckets created`

## Step 2: Check Browser Console

1. **Open browser Developer Tools** (F12)
2. **Go to Console tab**
3. **Look for JavaScript errors**

Common issues:
- `tank_series is undefined`
- `Chart.js not loaded`
- JSON parsing errors

## Step 3: Verify Data in Database

Run this SQL to check if data has location and device_type:

```sql
SELECT 
    sd.id,
    sd.user_id,
    sd.device_id,
    sd.recorded_at,
    s.device_type,
    s.location
FROM sensor_data sd
LEFT JOIN sensors s ON s.id = sd.sensor_id
WHERE sd.user_id = YOUR_USER_ID
ORDER BY sd.recorded_at DESC
LIMIT 10;
```

**Check:**
- Is `location` NULL or empty? → Graph won't show
- Is `device_type` NULL or empty? → Graph won't show
- Is `recorded_at` NULL? → Graph won't show

## Step 4: Check if Data Matches Your User

```sql
-- Find your user_id
SELECT sr_no as user_id, username FROM user_cred;

-- Check if sensor_data has records for your user_id
SELECT COUNT(*) 
FROM sensor_data 
WHERE user_id = YOUR_USER_ID;
```

If count is 0, that's why the graph is empty!

## Step 5: Test Data Retrieval Directly

Create a test file `test_dashboard_data.py`:

```python
import os
import sys
sys.path.insert(0, r'C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor')

# Set environment variables
os.environ['DB_ENCRYPTION_KEY'] = 'T468PZiZfDtJDQEjxlzMMJqIDOSHJ4Pp3exMQtedD50='
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = 'your_password'
os.environ['DB_NAME'] = 'water_monitor'

from db import list_recent_sensor_data

# Test with user_id = 1 (replace with your actual user_id)
rows = list_recent_sensor_data(limit=200, user_id=1)

print(f"Retrieved {len(rows)} rows")
if rows:
    print("\nFirst 5 rows:")
    for i, row in enumerate(rows[:5]):
        print(f"Row {i+1}:")
        print(f"  device_id: {row.get('device_id')}")
        print(f"  device_type: {row.get('device_type')}")
        print(f"  location: {row.get('location')}")
        print(f"  value: {row.get('value')}")
        print(f"  recorded_at: {row.get('recorded_at')}")
        print()
else:
    print("No rows returned!")
```

Run it:
```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
python test_dashboard_data.py
```

## Common Issues and Fixes

### Issue 1: No rows retrieved
**Cause:** user_id mismatch or no data
**Fix:** Update sensors to match your user_id

### Issue 2: Rows retrieved but no buckets created
**Cause:** Missing location or device_type
**Fix:** Update sensors table to set location and device_type

### Issue 3: JavaScript errors
**Cause:** Chart.js not loading or JSON parsing error
**Fix:** Check browser console and network tab

### Issue 4: Graph shows but no data points
**Cause:** All values are None after decryption
**Fix:** Check encryption key matches

## Quick Test Query

```sql
-- Check recent data with all required fields
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT s.location) as locations,
    COUNT(DISTINCT s.device_type) as device_types,
    MIN(sd.recorded_at) as oldest,
    MAX(sd.recorded_at) as newest
FROM sensor_data sd
JOIN sensors s ON s.id = sd.sensor_id
WHERE sd.user_id = YOUR_USER_ID
AND s.location IS NOT NULL
AND s.device_type IS NOT NULL;
```

If `total` is 0, you need to update your sensors!

