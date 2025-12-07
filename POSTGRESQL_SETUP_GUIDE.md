# PostgreSQL Setup Guide for Render

This guide will help you set up PostgreSQL as a backup database option when MySQL access is not available.

## Step 1: Create PostgreSQL Database on Render

1. **Go to Render Dashboard:**
   - Log in to [render.com](https://render.com)
   - Click **"New +"** button (top right)
   - Select **"PostgreSQL"**

2. **Configure Database:**
   - **Name:** `iot-water-monitor-db` (or any name you prefer)
   - **Database:** `ilmuwanutara_e2eewater` (or your preferred database name)
   - **User:** Auto-generated (or you can set custom)
   - **Region:** Choose closest to you (e.g., Singapore, Oregon)
   - **Plan:** **Free** (for testing) or **Starter** ($7/month for production)
   - Click **"Create Database"**

3. **Wait for Database Creation:**
   - Takes about 1-2 minutes
   - You'll see "Available" status when ready

4. **Get Connection Details:**
   - Click on your database name
   - You'll see:
     - **Internal Database URL:** `postgresql://user:password@host:5432/dbname`
     - **External Database URL:** (if you need external access)
   - **Copy the Internal Database URL** - you'll need it!

## Step 2: Update requirements.txt

Add PostgreSQL driver to your `requirements.txt`:

```txt
# Flask Web Server Dependencies
Flask>=3.0.0
Werkzeug>=3.0.0
mysql-connector-python>=8.0.0  # Keep for MySQL option
psycopg2-binary>=2.9.0  # Add this for PostgreSQL
paho-mqtt>=1.6.0
pycryptodome>=3.19.0
cryptography>=41.0.0
gunicorn>=21.2.0
```

## Step 3: Set Environment Variables in Render

In your **Web Service** (not the database), go to **Environment** tab:

### Option A: Use Individual Variables

```
DB_TYPE=postgresql
DB_HOST=dpg-xxxxx-a.oregon-postgres.render.com  # From your PostgreSQL dashboard
DB_PORT=5432
DB_USER=your_db_user  # From PostgreSQL dashboard
DB_PASSWORD=your_db_password  # From PostgreSQL dashboard
DB_NAME=ilmuwanutara_e2eewater
```

### Option B: Use Database URL (Easier)

```
DB_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:5432/dbname  # Copy from PostgreSQL dashboard
```

**Note:** The code will automatically parse `DATABASE_URL` if provided.

## Step 4: Update Code to Support PostgreSQL

The code has been updated to support both MySQL and PostgreSQL automatically based on `DB_TYPE` environment variable.

**If `DB_TYPE=postgresql`:** Uses PostgreSQL
**If `DB_TYPE=mysql` or not set:** Uses MySQL (default)

## Step 5: Deploy and Test

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add PostgreSQL support"
   git push
   ```

2. **Redeploy on Render:**
   - Go to your Web Service
   - Click **"Manual Deploy"** → **"Deploy latest commit"**

3. **Check Logs:**
   - Go to **Logs** tab
   - Look for: `DEBUG: Using PostgreSQL database`
   - Should see: `PostgreSQL connection pool created successfully`
   - Should see: `Database connection pool initialized successfully`

4. **Test Registration:**
   - Visit your Render URL
   - Try registering a new user
   - Should work! ✅

## Troubleshooting

### "Module not found: psycopg2"

**Fix:** Make sure `psycopg2-binary>=2.9.0` is in `requirements.txt` and you've redeployed.

### "Connection refused"

**Check:**
- `DB_HOST` is correct (from PostgreSQL dashboard)
- `DB_PORT` is `5432` (PostgreSQL default)
- Using **Internal Database URL** (not external) if both services are on Render

### "Database does not exist"

**Fix:** The database name in `DB_NAME` must match the database name you created in Render.

### "Authentication failed"

**Check:**
- `DB_USER` and `DB_PASSWORD` are correct
- Copy from PostgreSQL dashboard (Internal Database URL)

## Switching Between MySQL and PostgreSQL

You can easily switch by changing the `DB_TYPE` environment variable:

**For MySQL:**
```
DB_TYPE=mysql
DB_HOST=ilmuwanutara.my
DB_PORT=3306
...
```

**For PostgreSQL:**
```
DB_TYPE=postgresql
DB_HOST=dpg-xxxxx-a.oregon-postgres.render.com
DB_PORT=5432
...
```

## Advantages of PostgreSQL on Render

✅ **Free tier available** - Great for testing
✅ **Managed service** - Render handles backups, updates
✅ **No external access needed** - Works automatically with Render services
✅ **Automatic SSL** - Secure connections
✅ **Easy scaling** - Upgrade plan when needed

## Next Steps

1. ✅ Create PostgreSQL database on Render
2. ✅ Update requirements.txt
3. ✅ Set environment variables
4. ✅ Deploy and test
5. ✅ Register a test user to verify it works

---

**Your app now supports both MySQL and PostgreSQL!** 🎉

