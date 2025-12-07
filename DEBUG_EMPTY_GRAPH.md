# Debug Empty Dashboard Graph

## Step 1: Check Browser Console

1. **Open dashboard** in browser
2. **Press F12** to open Developer Tools
3. **Go to Console tab**
4. **Look for errors or warnings**

You should see:
- `Loading initial location: Tank A` (or your location)
- `API response status: 200`
- `API data received: {...}`
- `Labels count: X`
- `Datasets count: Y`

If you see errors, note them down!

## Step 2: Check Network Tab

1. **Go to Network tab** in Developer Tools
2. **Refresh dashboard**
3. **Look for request to** `/api/dashboard/location/...`
4. **Click on it** and check:
   - **Status**: Should be 200
   - **Response**: Should have `labels` and `datasets`

## Step 3: Check Server Logs

```powershell
Get-Content C:\Apache24\logs\error.log -Tail 100 | Select-String "DEBUG.*api_dashboard_location|Retrieved.*rows|Returning chart data"
```

Look for:
- `DEBUG: api_dashboard_location - Retrieved X rows`
- `DEBUG: api_dashboard_location - Returning chart data: X labels, Y datasets`

## Step 4: Verify Data Exists

Run this SQL query (replace YOUR_USER_ID and LOCATION):

```sql
-- Check if sensor_data exists for your user and location
SELECT 
    COUNT(*) as total_readings,
    COUNT(DISTINCT DATE(recorded_at)) as days_with_data,
    MIN(recorded_at) as oldest,
    MAX(recorded_at) as newest
FROM sensor_data sd
JOIN sensors s ON s.id = sd.sensor_id
WHERE s.location = 'Tank A'  -- Replace with your location
AND s.user_id = YOUR_USER_ID
AND sd.user_id = YOUR_USER_ID;
```

If `total_readings` is 0, that's why the graph is empty!

## Step 5: Check Location Dropdown

1. **Is location dropdown populated?**
   - Should show locations like "Tank A (3 sensors)"
   - If empty, no locations found for your user

2. **Is a location selected?**
   - Check if dropdown has a selected value
   - If not, graph won't load

## Common Issues

### Issue 1: No Data in Database
**Symptom:** Graph empty, API returns empty datasets
**Fix:** Check if sensor_data has records for your user_id and location

### Issue 2: Location Not Selected
**Symptom:** Graph shows "No location selected"
**Fix:** Select a location from dropdown

### Issue 3: API Returns 403
**Symptom:** Console shows "Location not accessible"
**Fix:** Check if sensors have correct user_id assigned

### Issue 4: API Returns Empty Data
**Symptom:** API returns 200 but labels/datasets are empty
**Fix:** Check if sensor_data has records with valid dates and values

## Quick Test

Open browser console and run:

```javascript
// Check if location is selected
console.log('Selected location:', document.getElementById('locationSelect').value);

// Manually trigger load
loadLocationData(document.getElementById('locationSelect').value);
```

This will help identify if it's a data issue or JavaScript issue.
