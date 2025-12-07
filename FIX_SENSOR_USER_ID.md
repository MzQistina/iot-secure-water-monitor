# Fix Sensor user_id Assignment

## Step 1: Find Your User ID

Run this query to find your user_id:

```sql
SELECT sr_no as user_id, username, email FROM user_cred;
```

Find your username and note the `user_id` (sr_no column).

## Step 2: Update All Sensors to Your User ID

Replace `YOUR_USER_ID` with your actual user_id from Step 1:

```sql
-- Update all sensors in Tank A, B, C to your user_id
UPDATE sensors 
SET user_id = YOUR_USER_ID 
WHERE location IN ('Tank A', 'Tank B', 'Tank C');
```

## Step 3: Verify Update

```sql
SELECT device_id, location, user_id, status 
FROM sensors 
WHERE location IN ('Tank A', 'Tank B', 'Tank C')
ORDER BY location, device_id;
```

All sensors should now show your `user_id`.

## Step 4: Check Locations Are Visible

```sql
SELECT DISTINCT location 
FROM sensors 
WHERE user_id = YOUR_USER_ID 
AND location IS NOT NULL 
AND location != '';
```

Should show: Tank A, Tank B, Tank C

## Step 5: Refresh Dashboard

After updating, refresh your dashboard - all three locations should appear!

