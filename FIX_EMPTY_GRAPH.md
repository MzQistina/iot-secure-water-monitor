# Fix Empty Dashboard Graph

## Most Likely Issue: user_id Mismatch

The dashboard filters data by your logged-in `user_id`. If sensors have `user_id = NULL` or a different user_id, you'll see an empty graph.

## Quick Diagnosis

### Step 1: Check Your User ID

1. Log into your dashboard
2. Check browser console or session (you can also check in database)

### Step 2: Check Sensor user_id

Run this SQL:

```sql
-- Check user_id of sensors that have data
SELECT DISTINCT 
    s.user_id,
    s.device_id,
    s.device_type,
    s.location,
    COUNT(sd.id) as reading_count
FROM sensors s
JOIN sensor_data sd ON s.id = sd.sensor_id
GROUP BY s.user_id, s.device_id, s.device_type, s.location
ORDER BY reading_count DESC;
```

**If `user_id` is NULL or doesn't match your logged-in user**, that's the problem!

## Solution 1: Update Sensors to Your User ID

```sql
-- Find your user_id first
SELECT sr_no, username FROM user_cred WHERE username = 'your-username';

-- Then update sensors (replace YOUR_USER_ID with your actual user_id)
UPDATE sensors 
SET user_id = YOUR_USER_ID 
WHERE user_id IS NULL OR user_id != YOUR_USER_ID;
```

## Solution 2: Temporarily Remove User Filter (Testing)

To test if this is the issue, temporarily modify `app.py`:

```python
# Line 1125, change from:
rows = list_recent_sensor_data(limit=200, user_id=user_id)

# To:
rows = list_recent_sensor_data(limit=200, user_id=None)  # Show all users
```

If the graph appears, it confirms it's a user_id issue.

## Solution 3: Check Decryption

After restarting Apache, check logs:

```powershell
Get-Content C:\Apache24\logs\error.log -Tail 100 | Select-String "decrypt|WARNING|DEBUG.*dashboard"
```

Look for decryption errors.

## Most Common Fix

**Update sensors to match your user_id:**

```sql
-- Replace YOUR_USER_ID with your actual user ID from user_cred table
UPDATE sensors SET user_id = YOUR_USER_ID WHERE user_id IS NULL;
```

Then refresh your dashboard!

