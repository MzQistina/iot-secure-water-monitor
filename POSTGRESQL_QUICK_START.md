# PostgreSQL Quick Start Guide

## ✅ What's Already Done

1. ✅ `requirements.txt` updated with `psycopg2-binary`
2. ✅ `db.py` updated to detect `DB_TYPE` environment variable
3. ✅ Connection pool supports both MySQL and PostgreSQL

## 🚀 Quick Setup Steps

### Step 1: Create PostgreSQL Database on Render

1. Render Dashboard → **New +** → **PostgreSQL**
2. Name: `iot-water-monitor-db`
3. Plan: **Free**
4. Click **Create Database**
5. **Copy the Internal Database URL** (you'll need it!)

### Step 2: Set Environment Variables

In your **Web Service** → **Environment** tab, add:

```
DB_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**OR** use individual variables:

```
DB_TYPE=postgresql
DB_HOST=dpg-xxxxx-a.oregon-postgres.render.com
DB_PORT=5432
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=ilmuwanutara_e2eewater
```

### Step 3: Deploy

1. Push code to GitHub
2. Redeploy on Render
3. Check logs - should see: `DEBUG: Initializing POSTGRESQL database connection pool...`

## ⚠️ Important Note

The `_ensure_schema()` function currently uses MySQL syntax. For full PostgreSQL support, the schema needs to be converted. However, the connection will work and you can manually create tables via Render's PostgreSQL dashboard or update the schema function.

## 🔧 Manual Table Creation (If Needed)

If automatic schema creation doesn't work, you can create tables manually in Render's PostgreSQL dashboard:

1. Go to your PostgreSQL database
2. Click **"Connect"** → **"psql"** or use **"Query"** tab
3. Run the PostgreSQL-compatible SQL (see below)

## 📝 Next Steps

The code is ready for PostgreSQL connection. The main remaining task is converting the schema SQL from MySQL to PostgreSQL syntax. This can be done incrementally.

---

**For now, try creating the database and setting the environment variables. The connection should work!** 🎉

