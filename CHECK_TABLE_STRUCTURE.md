# How to Check sensor_data Table Structure

## Method 1: phpMyAdmin (Easiest)

1. **Open phpMyAdmin** in your browser (usually `http://localhost/phpmyadmin`)

2. **Select your database** from the left sidebar (e.g., `water_monitor`)

3. **Click on `sensor_data` table** in the list

4. **Click "Structure" tab** - This automatically shows the table structure

   OR

5. **Click "SQL" tab** and run:
   ```sql
   DESCRIBE sensor_data;
   ```
   Then click "Go"

## Method 2: MySQL Command Line

1. **Open Command Prompt or PowerShell**

2. **Navigate to MySQL bin directory** (if not in PATH):
   ```powershell
   cd C:\Program Files\MySQL\MySQL Server 8.0\bin
   ```

3. **Login to MySQL**:
   ```powershell
   mysql -u root -p
   ```
   (Enter your MySQL password when prompted)

4. **Select your database**:
   ```sql
   USE water_monitor;
   ```

5. **Describe the table**:
   ```sql
   DESCRIBE sensor_data;
   ```

6. **Or use SHOW COLUMNS**:
   ```sql
   SHOW COLUMNS FROM sensor_data;
   ```

## Method 3: Check via Python Script

Create a file `check_table.py`:

```python
import mysql.connector
import os

# Get database credentials from environment or set directly
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
DB_NAME = os.environ.get('DB_NAME', 'water_monitor')

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor()
    
    # Get table structure
    cur.execute("DESCRIBE sensor_data")
    columns = cur.fetchall()
    
    print("\n" + "="*70)
    print("sensor_data Table Structure")
    print("="*70)
    print(f"{'Field':<20} {'Type':<25} {'Null':<8} {'Key':<8} {'Default':<15} {'Extra'}")
    print("-"*70)
    
    for col in columns:
        field, type_, null, key, default, extra = col
        default_str = str(default) if default is not None else 'NULL'
        print(f"{field:<20} {type_:<25} {null:<8} {key:<8} {default_str:<15} {extra or ''}")
    
    print("="*70)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
```

Run it:
```powershell
python check_table.py
```

## Expected Output

You should see columns like:
- `id` (INT, PRIMARY KEY)
- `sensor_id` (INT)
- `user_id` (INT) ← **NEW**
- `device_id` (VARCHAR) ← **NEW**
- `recorded_at` (DATETIME)
- `value` (TEXT)
- `status` (ENUM)

## Quick Check Query

To verify the new columns exist:

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'sensor_data' 
AND TABLE_SCHEMA = 'water_monitor'
ORDER BY ORDINAL_POSITION;
```

This shows all columns with their data types.

