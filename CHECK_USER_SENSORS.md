# Check User Sensors

## Step 1: Find Your User ID

Run this SQL query:

```sql
SELECT sr_no as user_id, username, email FROM user_cred;
```

This will show all users. Find your username and note the `user_id` (sr_no column).

## Step 2: Check Sensors for Your User ID

Replace `YOUR_ACTUAL_USER_ID` with the number from Step 1:

```sql
SELECT COUNT(*) as sensor_count 
FROM sensors 
WHERE user_id = YOUR_ACTUAL_USER_ID;
```

If this returns 0, that's the problem!

## Step 3: Check All Sensors and Their user_id

```sql
SELECT 
    id,
    device_id,
    device_type,
    location,
    user_id,
    status
FROM sensors
ORDER BY location, device_id;
```

This shows which sensors have `user_id` set and which don't.

## Step 4: Fix Missing user_id

If sensors have `user_id = NULL`, update them:

```sql
-- Replace YOUR_ACTUAL_USER_ID with your actual user_id from Step 1
UPDATE sensors 
SET user_id = YOUR_ACTUAL_USER_ID 
WHERE user_id IS NULL;
```

## Step 5: Verify Locations Are Visible

After updating, check:

```sql
SELECT DISTINCT location 
FROM sensors 
WHERE user_id = YOUR_ACTUAL_USER_ID 
AND location IS NOT NULL 
AND location != '';
```

Should show: Tank A, Tank B, Tank C

