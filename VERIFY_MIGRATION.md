# Verify Migration Success

## ✅ What We Know

- **user_id column exists** ✓
- **1075 records have user_id populated** ✓

## Next: Check device_id

Run this query in phpMyAdmin:

```sql
SELECT COUNT(*) FROM sensor_data WHERE device_id IS NOT NULL;
```

Expected: Should also show 1075 (or close to it)

## Verify Both Columns Exist

```sql
DESCRIBE sensor_data;
```

Should show:
- `user_id` INT NULL
- `device_id` VARCHAR(100) NULL

## Check Recent Records

```sql
SELECT 
    id,
    sensor_id,
    user_id,
    device_id,
    recorded_at,
    LEFT(value, 50) as encrypted_value_preview,
    status
FROM sensor_data 
ORDER BY recorded_at DESC 
LIMIT 10;
```

All recent records should have:
- `user_id` = your user ID (not NULL)
- `device_id` = device identifier (not NULL)
- `value` = encrypted string

## Test Dashboard

1. **Restart Apache** (if you haven't already):
   ```powershell
   Restart-Service Apache2.4
   ```

2. **Open dashboard** in browser

3. **Check if graph shows data** - Should now display sensor readings!

## If Graph Still Empty

Check if your logged-in user_id matches:

```sql
-- Find your user_id
SELECT sr_no as user_id, username FROM user_cred WHERE username = 'your-username';

-- Check if sensor_data has records for your user_id
SELECT COUNT(*) 
FROM sensor_data 
WHERE user_id = YOUR_USER_ID_HERE;
```

If count is 0, update sensors:
```sql
UPDATE sensors SET user_id = YOUR_USER_ID WHERE user_id IS NULL;
```

Then backfill sensor_data:
```sql
UPDATE sensor_data sd
JOIN sensors s ON s.id = sd.sensor_id
SET sd.user_id = s.user_id, sd.device_id = s.device_id
WHERE sd.user_id IS NULL OR sd.device_id IS NULL;
```

