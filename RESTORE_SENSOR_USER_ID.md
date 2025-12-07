# Restore Sensor user_id Values

## Option 1: Restore Based on Original Data

From your previous query, the original user_ids were:
- Tank A: user_id = 5 (amm03, tds05, ph01)
- Tank B: user_id = NULL (temp01, ph02), user_id = 5 (pres01), user_id = 6 (nit02, temp04)
- Tank C: user_id = NULL (amm01, flow02)

### Restore Query:

```sql
-- Restore Tank A sensors to user_id = 5
UPDATE sensors 
SET user_id = 5 
WHERE device_id IN ('amm03', 'tds05', 'ph01');

-- Restore Tank B sensors
UPDATE sensors 
SET user_id = NULL 
WHERE device_id IN ('temp01', 'ph02');

UPDATE sensors 
SET user_id = 5 
WHERE device_id = 'pres01';

UPDATE sensors 
SET user_id = 6 
WHERE device_id IN ('nit02', 'temp04');

-- Restore Tank C sensors to NULL
UPDATE sensors 
SET user_id = NULL 
WHERE device_id IN ('amm01', 'flow02');
```

## Option 2: Better Solution - Show All Locations

Instead of filtering by user_id, modify the dashboard to show all locations regardless of user_id.

This way, each user can see all locations, but the data filtering can still be done per user.

## Option 3: Only Update Your Own Sensors

If you want to keep multi-user support, only update sensors that should belong to you:

```sql
-- Only update sensors that are NULL or belong to you
UPDATE sensors 
SET user_id = YOUR_USER_ID 
WHERE location IN ('Tank A', 'Tank B', 'Tank C')
AND (user_id IS NULL OR user_id = YOUR_USER_ID);
```

This preserves other users' sensors.

