# Test Dashboard Access

## Important: You Need to Actually Access the Dashboard Page!

The logs show no dashboard DEBUG messages, which means **the dashboard route hasn't been called yet**.

## Steps to Test:

### 1. Make Sure You're Logged In

- Go to: `http://localhost/login` (or your login URL)
- Log in with your credentials

### 2. Access the Dashboard

- Go to: `http://localhost/dashboard` (or your dashboard URL)
- **Wait for the page to load completely**

### 3. Immediately Check Logs

**While the dashboard page is loading**, run this command:

```powershell
Get-Content C:\Apache24\logs\error.log -Tail 50 | Select-String "dashboard|DEBUG|ERROR"
```

You should now see:
- `DEBUG: dashboard route called`
- `DEBUG: dashboard - user_id from session: X`
- `DEBUG: dashboard - list_recent_sensor_data returned X rows`
- `DEBUG: dashboard - Retrieved X rows from database`
- `DEBUG: dashboard - Created X tank buckets`

### 4. If Still No Messages

Check if there's a Python error preventing the route:

```powershell
Get-Content C:\Apache24\logs\error.log -Tail 200 | Select-String "Traceback|Error|Exception"
```

### 5. Check Browser Console

1. Open dashboard page
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Look for JavaScript errors (red text)

### 6. Verify Data Exists

Run this SQL to check if you have data:

```sql
-- Check your user_id
SELECT sr_no as user_id, username FROM user_cred;

-- Check data for your user_id (replace YOUR_USER_ID)
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT s.location) as locations,
    COUNT(DISTINCT s.device_type) as device_types
FROM sensor_data sd
LEFT JOIN sensors s ON s.id = sd.sensor_id
WHERE sd.user_id = YOUR_USER_ID;
```

If `total_rows` is 0, that's why the graph is empty!

## Quick Test

1. **Open browser**
2. **Navigate to:** `http://localhost/dashboard` (or your URL)
3. **While page loads**, run:
   ```powershell
   Get-Content C:\Apache24\logs\error.log -Tail 100
   ```
4. **Look for** `DEBUG: dashboard` messages

If you see the messages, share them with me!
If you DON'T see messages, there might be a routing or authentication issue.

