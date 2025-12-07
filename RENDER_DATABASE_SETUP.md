# Database Setup for Render + Docker

## Your Database Options

Since Render's free tier only offers **PostgreSQL** (not MySQL), you have 3 options:

### Option 1: Use Render PostgreSQL (Free) ⭐ Recommended
- ✅ **Free** - Included in Render free tier
- ✅ **Managed** - Render handles backups, updates
- ✅ **Easy setup** - One-click database creation
- ⚠️ **Need to modify code** - Change from MySQL to PostgreSQL

### Option 2: Use External MySQL (Your Existing)
- ✅ **No code changes** - Keep using MySQL
- ✅ **Use existing database** - From LiteSpeed hosting
- ⚠️ **Need to allow connections** - Firewall configuration
- ⚠️ **External dependency** - Relies on another service

### Option 3: Managed MySQL Service (Paid)
- ✅ **No code changes** - Keep using MySQL
- ✅ **Reliable** - AWS RDS, Google Cloud SQL, etc.
- ❌ **Costs money** - Usually $5-20/month

## Option 1: Render PostgreSQL (Recommended)

### Step 1: Create PostgreSQL Database on Render

1. **In Render Dashboard:**
   - Click **"New +"** → **"PostgreSQL"**
   - **Name:** `iot-water-monitor-db`
   - **Database:** `ilmuwanutara_e2eewater` (or your preferred name)
   - **User:** Auto-generated
   - **Plan:** Free (or paid for more resources)
   - Click **"Create Database"**

2. **Get Connection Details:**
   - **Internal Database URL:** `postgresql://user:password@host:5432/dbname`
   - **External Database URL:** (if you need external access)
   - Copy these - you'll need them!

### Step 2: Update db.py for PostgreSQL

**Current `db.py` uses MySQL. You need to modify it for PostgreSQL:**

**Install PostgreSQL driver:**
```txt
# Update requirements.txt
psycopg2-binary>=2.9.0  # Add this
# Remove or keep mysql-connector-python (if not using MySQL)
```

**Modify `db.py`:**

Create a new version that supports both MySQL and PostgreSQL, or create `db_postgresql.py`:

```python
import os
from datetime import datetime
import psycopg2
from psycopg2 import pool, Error, errorcode
import json

# Environment-driven PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')

_pool = None

def get_pool():
    """Get or create PostgreSQL connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min connections
                10,  # max connections
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            if _pool:
                print(f"PostgreSQL connection pool created successfully")
        except Exception as e:
            print(f"PostgreSQL pool creation error: {e}")
            _pool = None
    return _pool

# Rest of your database functions stay mostly the same
# Just change MySQL-specific syntax to PostgreSQL:
# - AUTO_INCREMENT → SERIAL
# - DATETIME → TIMESTAMP
# - VARCHAR → VARCHAR (same)
# - etc.
```

**Or use a database abstraction library** (easier):

**Update `requirements.txt`:**
```txt
Flask>=3.0.0
Werkzeug>=3.0.0
psycopg2-binary>=2.9.0  # PostgreSQL
SQLAlchemy>=2.0.0      # Database abstraction
paho-mqtt>=1.6.0
pycryptodome>=3.19.0
gunicorn>=21.2.0
```

**Use SQLAlchemy** - Works with both MySQL and PostgreSQL!

### Step 3: Set Environment Variables in Render

**In Render Dashboard → Environment:**

```
DB_HOST=dpg-xxxxx-a.oregon-postgres.render.com
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=ilmuwanutara_e2eewater
```

**Or use Render's Internal Database URL:**
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Step 4: Initialize Database Schema

**After deployment, run initialization:**

**Option A: Via Render Shell:**
1. Render Dashboard → Your service → **Shell**
2. Run Python script to create tables

**Option B: Add to app.py startup:**
```python
# In app.py, add database initialization
def init_db():
    """Initialize database tables if they don't exist."""
    # Your table creation SQL (converted to PostgreSQL)
    pass
```

## Option 2: Use External MySQL (Easier - No Code Changes)

### Step 1: Use Your Existing MySQL

**From your LiteSpeed hosting:**
- Host: `your-mysql-host.com` (or IP)
- Port: `3306`
- User: Your MySQL username
- Password: Your MySQL password
- Database: `ilmuwanutara_e2eewater`

### Step 2: Allow External Connections

**MySQL needs to allow connections from Render IPs:**

1. **Check MySQL user permissions:**
```sql
-- In MySQL
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* TO 'your_user'@'%' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
```

2. **Check firewall:**
- Allow port 3306 from Render IPs
- Or allow from anywhere (less secure, but easier)

3. **Check MySQL bind address:**
```sql
-- MySQL config should allow external connections
bind-address = 0.0.0.0  # or your server IP
```

### Step 3: Set Environment Variables in Render

**In Render Dashboard → Environment:**

```
DB_HOST=your-mysql-host.com
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=ilmuwanutara_e2eewater
```

### Step 4: Keep db.py as-is

**No code changes needed!** Your existing `db.py` with MySQL connector will work.

## Option 3: Managed MySQL Service

### Services Available:

**AWS RDS MySQL:**
- ✅ Reliable
- ✅ Managed backups
- ⚠️ Costs ~$15-30/month

**Google Cloud SQL:**
- ✅ Reliable
- ✅ Good integration
- ⚠️ Costs ~$10-25/month

**DigitalOcean Managed Database:**
- ✅ Simple pricing
- ⚠️ Costs ~$15/month

**For FYP:** Probably overkill unless you have budget.

## Recommendation for Your FYP

### Use Option 2: External MySQL (Easiest)

**Why:**
1. ✅ **No code changes** - Keep existing `db.py`
2. ✅ **Use existing database** - From LiteSpeed hosting
3. ✅ **Faster setup** - Just configure connection
4. ✅ **Same data** - Can migrate later if needed

**Steps:**
1. Get MySQL credentials from LiteSpeed hosting
2. Allow external connections (firewall)
3. Set environment variables in Render
4. Deploy Docker app
5. Done! ✅

## Quick Setup Guide: External MySQL

### Step 1: Get MySQL Credentials

**From your LiteSpeed hosting/cPanel:**
- Host: `e2eewater.ilmuwanutara.my` (or IP)
- Port: `3306`
- User: Your MySQL username
- Password: Your MySQL password
- Database: `ilmuwanutara_e2eewater`

### Step 2: Configure MySQL for External Access

**If you have SSH/phpMyAdmin access:**

```sql
-- Allow user to connect from anywhere
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* 
TO 'your_user'@'%' 
IDENTIFIED BY 'your_password';

FLUSH PRIVILEGES;
```

**Or allow specific IPs (more secure):**
```sql
-- Allow from Render IPs (check Render docs for IP ranges)
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* 
TO 'your_user'@'render-ip-range' 
IDENTIFIED BY 'your_password';
```

### Step 3: Set Environment Variables in Render

**In Render Dashboard → Your Web Service → Environment:**

```
DB_HOST=e2eewater.ilmuwanutara.my
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=ilmuwanutara_e2eewater
MQTT_HOST=your-mqtt-host
MQTT_PORT=1883
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=10000
```

### Step 4: Test Connection

**After deployment, check Render logs:**
- Should see: "Database connection: OK"
- Or errors if connection fails

## Troubleshooting Database Connection

### "Can't connect to MySQL server"

**Check:**
1. **MySQL allows external connections?**
   - Check `bind-address` in MySQL config
   - Should be `0.0.0.0` or your server IP

2. **Firewall allows port 3306?**
   - Check hosting firewall rules
   - Allow from Render IPs

3. **User has remote access?**
   - Check MySQL user permissions
   - Should allow `@'%'` or specific IPs

4. **Credentials correct?**
   - Verify host, user, password, database name

### "Access denied for user"

**Fix:**
```sql
-- Grant remote access
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* 
TO 'your_user'@'%' 
IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
```

### "Unknown database"

**Fix:**
- Verify database name matches
- Check if database exists
- Create database if missing

## Migration Path: MySQL → PostgreSQL (If Needed Later)

**If you want to switch to PostgreSQL later:**

1. **Export MySQL data:**
```bash
mysqldump -u user -p ilmuwanutara_e2eewater > backup.sql
```

2. **Convert to PostgreSQL:**
- Use `pgloader` or manual conversion
- Update SQL syntax differences

3. **Update db.py:**
- Change to PostgreSQL driver
- Update connection code

4. **Import to PostgreSQL:**
```bash
psql -U user -d dbname < converted_backup.sql
```

## Summary

### For Your FYP Project:

**Recommended: Use External MySQL (Option 2)**

**Why:**
- ✅ No code changes needed
- ✅ Use existing database
- ✅ Faster setup
- ✅ Works immediately

**Steps:**
1. Get MySQL credentials
2. Allow external connections
3. Set environment variables in Render
4. Deploy Docker app
5. Test connection

**Alternative: Use Render PostgreSQL (Option 1)**
- If you want managed database
- Need to modify `db.py`
- More setup work

---

**Bottom line: Use your existing MySQL database with Render Docker deployment. Just configure the connection!** 🐳

