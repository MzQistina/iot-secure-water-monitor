# Deploying to PythonAnywhere - Complete Guide

PythonAnywhere is a cloud-based Python development and hosting environment that's **perfect for Flask applications**. It's especially popular for Python developers because it provides a full Python environment in your browser.

## Why Use PythonAnywhere?

✅ **Python-focused** - Built specifically for Python applications  
✅ **Free tier available** - Great for testing and small projects  
✅ **Easy Flask deployment** - One-click Flask app setup  
✅ **Built-in console** - Access Python shell, bash, and MySQL console  
✅ **No Git required** - Upload files directly via web interface  
✅ **MySQL included** - Free MySQL database on free tier  
✅ **Always-on** - Free tier doesn't spin down (unlike Render)  
✅ **Simple file management** - Web-based file browser  

## Prerequisites

1. **PythonAnywhere account** - Sign up at [pythonanywhere.com](https://www.pythonanywhere.com) (free)
2. **Your project files** - Ready to upload

## Step 1: Sign Up and Log In

1. **Go to [pythonanywhere.com](https://www.pythonanywhere.com)**
2. **Click "Pricing" → "Beginner" (Free)**
3. **Sign up** with email or GitHub account
4. **Log into your dashboard**

## Step 2: Upload Your Files

PythonAnywhere provides a web-based file browser. You can upload files directly without Git.

### Option 1: Upload via Web Interface (Easiest)

1. **Open Files tab** in PythonAnywhere dashboard
2. **Navigate to:** `/home/yourusername/mysite/` (or create this folder)
3. **Click "Upload a file"**
4. **Upload these files:**
   - `app.py`
   - `db.py`
   - `encryption_utils.py`
   - `mqtt_listener.py`
   - `default_thresholds.json`
   - `app.wsgi` (or create new one, see below)
   - `requirements.txt`

5. **Create folders:**
   - `templates/` - Upload all HTML files
   - `static/` - Upload CSS, images, etc.
   - `keys/` - Upload your server keys (public.pem and private.pem)

### Option 2: Upload via Bash Console

1. **Open Bash console** in PythonAnywhere dashboard
2. **Create project directory:**
   ```bash
   mkdir -p ~/mysite
   cd ~/mysite
   ```

3. **Upload files using wget or curl** (if files are hosted somewhere):
   ```bash
   # Example: Download from GitHub
   wget https://raw.githubusercontent.com/yourusername/repo/main/app.py
   ```

4. **Or use PythonAnywhere's file uploader** in the Files tab

## Step 3: Create WSGI Configuration File

PythonAnywhere uses WSGI files to configure Flask apps.

1. **Go to Files tab**
2. **Navigate to:** `/var/www/yourusername_pythonanywhere_com_wsgi.py`
   - This file is automatically created for your domain
   - Or create: `/var/www/yourusername_pythonanywhere_com_wsgi.py`

3. **Edit the WSGI file** and replace with:

```python
import sys
import os

# Add your project directory to Python path
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_PASSWORD'] = 'your_db_password'
os.environ['DB_NAME'] = 'yourusername$ilmuwanutara_e2eewater'
os.environ['MQTT_HOST'] = 'your-mqtt-host'
os.environ['MQTT_PORT'] = '1883'
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'your-secret-key-here'

# Change working directory to your project
os.chdir(path)

# Import Flask app
from app import app as application

# Start MQTT subscriber if needed
try:
    from app import start_mqtt_key_subscriber
    start_mqtt_key_subscriber()
except Exception as e:
    print(f"MQTT subscriber error (non-fatal): {e}")
```

**Important:** Replace `yourusername` with your actual PythonAnywhere username!

## Step 4: Install Dependencies

1. **Open Bash console** in PythonAnywhere dashboard
2. **Navigate to your project:**
   ```bash
   cd ~/mysite
   ```

3. **Install dependencies:**
   ```bash
   pip3.10 install --user flask mysql-connector-python paho-mqtt pycryptodome werkzeug gunicorn
   ```
   
   Or if you have `requirements.txt`:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

**Note:** PythonAnywhere uses Python 3.10 by default. Use `pip3.10` to install packages.

## Step 5: Set Up MySQL Database

PythonAnywhere includes a free MySQL database!

### 5.1 Create Database

1. **Go to Databases tab** in PythonAnywhere dashboard
2. **Click "Create database"**
3. **Database name:** `ilmuwanutara_e2eewater` (or your preferred name)
   - **Note:** PythonAnywhere prefixes database names with your username
   - Full name will be: `yourusername$ilmuwanutara_e2eewater`
4. **Click "Create"**

### 5.2 Get Database Credentials

In the Databases tab, you'll see:
- **Host:** `yourusername.mysql.pythonanywhere-services.com`
- **Username:** `yourusername`
- **Password:** (shown in dashboard)
- **Database name:** `yourusername$ilmuwanutara_e2eewater`

### 5.3 Initialize Database Schema

1. **Open MySQL console** in PythonAnywhere dashboard
2. **Run your database initialization script** or create tables manually:

```sql
USE yourusername$ilmuwanutara_e2eewater;

-- Create your tables here
-- (Copy your database schema from your local setup)
```

Or use Python script:

1. **Open Bash console**
2. **Run:**
   ```bash
   cd ~/mysite
   python3.10
   ```
3. **In Python:**
   ```python
   from db import get_pool
   # This will create tables if they don't exist
   pool = get_pool()
   ```

## Step 6: Configure Web App

1. **Go to Web tab** in PythonAnywhere dashboard
2. **Click "Add a new web app"** (if first time) or edit existing
3. **Choose domain:**
   - Free tier: `yourusername.pythonanywhere.com`
   - Paid tier: Can use custom domain
4. **Select "Manual configuration"** → **Python 3.10**
5. **Set WSGI configuration file:**
   - Path: `/var/www/yourusername_pythonanywhere_com_wsgi.py`
6. **Click "Next"** → **"All done!"**

## Step 7: Update WSGI File with Correct Paths

1. **Go to Files tab**
2. **Open:** `/var/www/yourusername_pythonanywhere_com_wsgi.py`
3. **Update the file** with correct paths and database credentials:

```python
import sys
import os

# Add your project directory to Python path
path = '/home/yourusername/mysite'  # Update with your actual path
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_PASSWORD'] = 'your_actual_db_password'  # From Databases tab
os.environ['DB_NAME'] = 'yourusername$ilmuwanutara_e2eewater'  # Note the $ prefix
os.environ['MQTT_HOST'] = 'your-mqtt-host'
os.environ['MQTT_PORT'] = '1883'
os.environ['MQTT_USER'] = 'your_mqtt_username'  # If using MQTT authentication
os.environ['MQTT_PASSWORD'] = 'your_mqtt_password'  # If using MQTT authentication
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'generate-a-random-secret-key-here'

# Change working directory
os.chdir(path)

# Import Flask app
from app import app as application

# Start MQTT subscriber
try:
    from app import start_mqtt_key_subscriber
    start_mqtt_key_subscriber()
except Exception as e:
    print(f"MQTT subscriber error (non-fatal): {e}")
```

## Step 8: Reload Web App

1. **Go to Web tab**
2. **Click the green "Reload" button** (or the URL of your web app)
3. **Wait a few seconds** for the app to reload
4. **Visit your app:** `https://yourusername.pythonanywhere.com`

## Step 9: Configure Static Files (Optional)

PythonAnywhere can serve static files directly for better performance:

1. **Go to Web tab**
2. **Scroll to "Static files" section**
3. **Add static file mapping:**
   - **URL:** `/static/`
   - **Directory:** `/home/yourusername/mysite/static/`
4. **Click "Add"**
5. **Reload web app**

## Step 10: Set Up Scheduled Tasks (Optional)

If you need to run background tasks (like MQTT listener):

1. **Go to Tasks tab**
2. **Click "Create a task"**
3. **Set schedule** (e.g., every 5 minutes)
4. **Command:**
   ```bash
   cd /home/yourusername/mysite && python3.10 mqtt_listener.py
   ```

**Note:** For MQTT listener, it's better to start it in the WSGI file (already done above).

## Troubleshooting

### "Module not found" Error

- **Check Python version:** PythonAnywhere uses Python 3.10
- **Install packages:** Use `pip3.10 install --user package_name`
- **Check sys.path:** Ensure your project directory is in sys.path in WSGI file

### "Database connection failed"

- **Check database name:** PythonAnywhere prefixes with username (e.g., `yourusername$dbname`)
- **Verify credentials:** Check Databases tab for correct host, user, password
- **Check host:** Must use `yourusername.mysql.pythonanywhere-services.com`

### "500 Internal Server Error"

1. **Check error logs:**
   - Go to Web tab → **Error log** link
   - Look for specific error messages

2. **Common issues:**
   - Missing dependencies → Install with `pip3.10 install --user`
   - Wrong file paths → Check WSGI file paths
   - Database connection → Verify credentials

### "Keys not found" Error

- **Ensure `keys/` folder is uploaded** to `/home/yourusername/mysite/keys/`
- **Check file permissions:** Files should be readable
- **Verify paths in code:** Use relative paths or absolute paths

### Files Not Updating

- **Reload web app** after uploading new files
- **Check file paths** are correct
- **Clear browser cache** if CSS/JS not updating

## PythonAnywhere vs Render vs LiteSpeed Comparison

| Feature | PythonAnywhere | Render | LiteSpeed |
|--------|----------------|--------|-----------|
| **Setup Difficulty** | ⭐⭐ Easy | ⭐ Easy | ⭐⭐⭐ Hard |
| **Free Tier** | ✅ Yes (always-on) | ✅ Yes (spins down) | ❌ No |
| **MySQL Database** | ✅ Included free | ❌ PostgreSQL only | ✅ External |
| **File Upload** | ✅ Web interface | ❌ Git only | ✅ FTP/SSH |
| **FileZilla/FTP** | ❌ Not supported | ❌ Not supported | ✅ Supported |
| **Custom Domain** | ⚠️ Paid only ($5+) | ✅ Free | ✅ Yes |
| **Python Console** | ✅ Built-in | ❌ No | ✅ SSH |
| **Always-On** | ✅ Yes (free tier) | ❌ Spins down | ✅ Yes |
| **Custom Domain** | ⚠️ Paid only | ✅ Free | ✅ Yes |
| **SSL Certificate** | ✅ Automatic | ✅ Automatic | ⚠️ Manual |
| **Git Deployment** | ⚠️ Manual | ✅ Automatic | ❌ No |
| **Best For** | Python developers | Modern DevOps | Traditional hosting |

## Free Tier Limitations

### PythonAnywhere Free Tier:
- ✅ **Always-on** - Doesn't spin down
- ✅ **MySQL database** included
- ✅ **Python console** access
- ⚠️ **Limited CPU time** - 100 seconds/day
- ⚠️ **Custom domain** - Paid tier only
- ⚠️ **Limited file storage** - 512MB

### When to Upgrade:
- Need more CPU time
- Want custom domain
- Need more storage
- Production use

## Quick Start Checklist

- [ ] Sign up for PythonAnywhere account
- [ ] Upload project files to `/home/yourusername/mysite/`
- [ ] Create WSGI file at `/var/www/yourusername_pythonanywhere_com_wsgi.py`
- [ ] Install dependencies: `pip3.10 install --user -r requirements.txt`
- [ ] Create MySQL database in Databases tab
- [ ] Update WSGI file with database credentials
- [ ] Configure web app in Web tab
- [ ] Reload web app
- [ ] Test application at `yourusername.pythonanywhere.com`
- [ ] Upload `keys/` folder
- [ ] Configure static files (optional)
- [ ] Set up scheduled tasks (if needed)

## Tips for PythonAnywhere

1. **Use Bash console** for file operations (easier than web interface for many files)
2. **Check error logs** in Web tab when debugging
3. **Use MySQL console** for database operations
4. **Python console** is great for testing imports and code
5. **Always reload** web app after making changes
6. **Use `--user` flag** when installing packages (required on free tier)

## Next Steps

1. **Test your application** - Visit your PythonAnywhere URL
2. **Set up database tables** - Run initialization scripts
3. **Configure MQTT** - Update MQTT host/credentials
4. **Test full functionality** - User registration, sensor data, etc.
5. **Monitor logs** - Check error logs regularly
6. **Consider upgrade** - If you need custom domain or more resources

## Resources

- [PythonAnywhere Documentation](https://help.pythonanywhere.com/)
- [PythonAnywhere Flask Guide](https://help.pythonanywhere.com/pages/Flask/)
- [PythonAnywhere MySQL Guide](https://help.pythonanywhere.com/pages/MySQL/)
- [PythonAnywhere WSGI Configuration](https://help.pythonanywhere.com/pages/Flask/)

---

**PythonAnywhere is great for Python developers!** It provides a full Python environment with MySQL included, and the free tier is always-on (unlike Render). 🐍

