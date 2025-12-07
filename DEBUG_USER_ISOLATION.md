# Debug User Isolation Issues

## Step 1: Check Logs After Accessing Dashboard

After logging in and accessing dashboard, check logs:

```powershell
Get-Content C:\Apache24\logs\error.log -Tail 100 | Select-String "DEBUG.*dashboard|DEBUG.*api_dashboard_location|user_id|username|WARNING"
```

Look for:
- `DEBUG: dashboard - username: X, user_id: Y`
- `DEBUG: api_dashboard_location - User Y has X sensors in location 'Z'`
- `WARNING: Row has user_id X but expected Y` ← This means data leak!

## Step 2: Verify Session user_id

Check what user_id is in session:

1. **Login as User1**
2. **Check logs** - should show `user_id: 5` (or User1's ID)
3. **Login as User2**  
4. **Check logs** - should show `user_id: 6` (or User2's ID)

If both show the same user_id, session is not working!

## Step 3: Check Database user_id Values

Run these queries:

```sql
-- Check sensors user_id distribution
SELECT user_id, COUNT(*) as count, GROUP_CONCAT(DISTINCT location) as locations
FROM sensors
WHERE location IN ('Tank A', 'Tank B', 'Tank C')
GROUP BY user_id;

-- Check sensor_data user_id distribution  
SELECT user_id, COUNT(*) as count
FROM sensor_data
GROUP BY user_id;
```

**Expected:**
- Each user should have different user_id values
- No NULL user_ids (or they should be assigned)

## Step 4: Test Isolation

1. **Login as User1** (user_id = 5)
2. **Access dashboard** - should only see locations where sensors have `user_id = 5`
3. **Check logs** - verify `user_id: 5` in all queries
4. **Logout**
5. **Login as User2** (user_id = 6)
6. **Access dashboard** - should only see locations where sensors have `user_id = 6`
7. **Check logs** - verify `user_id: 6` in all queries

## Common Issues

### Issue 1: Session Not Maintaining user_id
**Symptom:** Both users see same user_id in logs
**Fix:** Check login function sets `session['user_id']` correctly

### Issue 2: Sensors Have NULL user_id
**Symptom:** Locations show up for all users
**Fix:** Update sensors: `UPDATE sensors SET user_id = X WHERE user_id IS NULL`

### Issue 3: sensor_data Has Wrong user_id
**Symptom:** Data from one user shows for another
**Fix:** Check `insert_sensor_data` is setting correct user_id

### Issue 4: Browser Cache
**Symptom:** Old data persists after logout/login
**Fix:** Clear browser cache (Ctrl+Shift+Delete) or use incognito mode

## Quick Test Query

```sql
-- See which user owns which sensors
SELECT 
    s.user_id,
    s.location,
    s.device_id,
    s.device_type,
    COUNT(sd.id) as reading_count
FROM sensors s
LEFT JOIN sensor_data sd ON s.id = sd.sensor_id AND sd.user_id = s.user_id
WHERE s.location IN ('Tank A', 'Tank B', 'Tank C')
GROUP BY s.user_id, s.location, s.device_id, s.device_type
ORDER BY s.user_id, s.location;
```

This shows which user owns which sensors and how many readings they have.

