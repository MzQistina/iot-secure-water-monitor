# How to Delete Old Sensor Readings

## ⚠️ WARNING: Backup First!

Before deleting data, consider backing up:

```sql
-- Create backup table
CREATE TABLE sensor_data_backup AS SELECT * FROM sensor_data;
```

## Option 1: Delete Records Older Than X Days

```sql
-- Delete readings older than 30 days
DELETE FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

```sql
-- Delete readings older than 7 days
DELETE FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

```sql
-- Delete readings older than 1 day
DELETE FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 1 DAY);
```

## Option 2: Delete Records Before a Specific Date

```sql
-- Delete all readings before December 1, 2025
DELETE FROM sensor_data 
WHERE recorded_at < '2025-12-01 00:00:00';
```

```sql
-- Delete all readings before today
DELETE FROM sensor_data 
WHERE recorded_at < CURDATE();
```

## Option 3: Keep Only the Most Recent N Records

```sql
-- Keep only the most recent 1000 records
-- First, find the ID of the 1000th newest record
SET @keep_id = (
    SELECT id FROM sensor_data 
    ORDER BY recorded_at DESC 
    LIMIT 1 OFFSET 999
);

-- Then delete everything older
DELETE FROM sensor_data 
WHERE id < @keep_id;
```

## Option 4: Delete by Date Range

```sql
-- Delete readings between two dates
DELETE FROM sensor_data 
WHERE recorded_at BETWEEN '2025-11-01 00:00:00' AND '2025-11-30 23:59:59';
```

## Option 5: Delete All Records (⚠️ DANGEROUS!)

```sql
-- Delete ALL sensor_data records
DELETE FROM sensor_data;

-- Or reset the table completely
TRUNCATE TABLE sensor_data;
```

## Safe Approach: Preview Before Deleting

**Step 1: Check what will be deleted**

```sql
-- See how many records will be deleted (older than 30 days)
SELECT COUNT(*) as records_to_delete
FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

**Step 2: See the records that will be deleted**

```sql
-- Preview records that will be deleted
SELECT id, sensor_id, value, recorded_at 
FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY recorded_at DESC
LIMIT 10;
```

**Step 3: Delete if satisfied**

```sql
-- Delete after confirming
DELETE FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

## Recommended: Keep Recent Data Only

```sql
-- Keep only last 7 days of data
DELETE FROM sensor_data 
WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

## Check Results

After deleting, verify:

```sql
-- Count remaining records
SELECT COUNT(*) as total_records FROM sensor_data;

-- See date range of remaining records
SELECT 
    MIN(recorded_at) as oldest_record,
    MAX(recorded_at) as newest_record,
    COUNT(*) as total_records
FROM sensor_data;
```

## Quick Commands

**Delete readings older than 7 days:**
```sql
DELETE FROM sensor_data WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

**Delete readings older than 1 day:**
```sql
DELETE FROM sensor_data WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 1 DAY);
```

**Delete all readings before today:**
```sql
DELETE FROM sensor_data WHERE recorded_at < CURDATE();
```

