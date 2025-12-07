# LiteSpeed Web Server Deployment Guide

## Problem: Seeing Directory Listing Instead of Web App

If you're seeing a file directory listing (like the one shown) instead of your Flask application, it means **LiteSpeed is not configured to run your Flask WSGI application**.

## Solution: Configure LiteSpeed for Flask/WSGI

### Option 1: Using cPanel (Recommended - Easiest)

If your hosting provider uses cPanel:

1. **Log into cPanel**
2. **Find "Python App" or "Setup Python App"**
   - Look in Software section
   - Or search for "Python" in cPanel search bar
3. **Create a Python Application:**
   - **Application Root:** `/home/username/public_html/e2eewater` (or your domain path)
   - **Application URL:** `/` (or your subdomain)
   - **Application Startup File:** `app.wsgi`
   - **Application Entry Point:** `application` (this is the variable name in app.wsgi)
   - **Python Version:** Select Python 3.x (preferably 3.8+)
4. **Install Dependencies:**
   - After creating the app, cPanel will show a terminal or "Install Requirements" option
   - Run: `pip install -r requirements_pi.txt`
   - Or manually install: `pip install flask mysql-connector-python paho-mqtt pycryptodome`
5. **Set Environment Variables:**
   - In cPanel Python App settings, add environment variables:
     ```
     DB_HOST=127.0.0.1
     DB_PORT=3306
     DB_USER=your_db_user
     DB_PASSWORD=your_db_password
     DB_NAME=ilmuwanutara_e2eewater
     MQTT_HOST=your_mqtt_host
     MQTT_PORT=1883
     FLASK_ENV=production
     SECRET_KEY=your-secret-key-here
     ```
6. **Restart the Application:**
   - Click "Restart" button in cPanel Python App

### Option 2: Manual LiteSpeed Configuration

If you have SSH access and can edit LiteSpeed configuration:

1. **SSH into your server**

2. **Create Virtual Host Configuration:**
   ```bash
   sudo nano /usr/local/lsws/conf/vhosts/e2eewater/vhost.conf
   ```

3. **Add WSGI Configuration:**
   ```xml
   <VirtualHost e2eewater.ilmuwanutara.my:443>
       # SSL Configuration (if using HTTPS)
       keyFile                 /path/to/ssl/key.pem
       certFile                /path/to/ssl/cert.pem
       
       # Document Root
       docRoot                 /home/username/public_html/e2eewater
       
       # WSGI Configuration
       extprocessor e2eewater {
           type                    python
           address                  UDS://tmp/lshttpd/e2eewater.sock
           maxConns                10
           initTimeout             60
           retryTimeout            0
           pcKeepAliveTimeout      60
           respBuffer              0
           autoStart               1
           path                    /usr/local/lsws/fcgi-bin/lsphp
           memLimit                256M
           env                     PYTHONHOME=/home/username/public_html/e2eewater/venv
           env                     PYTHONPATH=/home/username/public_html/e2eewater
       }
       
       # Map WSGI application
       rewrite {
           RewriteRule ^(.*)$  extprocessor:e2eewater/$1
       }
   }
   ```

4. **Create .htaccess file** (if LiteSpeed supports it):
   ```apache
   RewriteEngine On
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteCond %{REQUEST_FILENAME} !-d
   RewriteRule ^(.*)$ app.wsgi/$1 [QSA,L]
   ```

5. **Restart LiteSpeed:**
   ```bash
   sudo /usr/local/lsws/bin/lswsctrl restart
   ```

### Option 3: Using .htaccess (If LiteSpeed Supports mod_rewrite)

Create a `.htaccess` file in your project root:

```apache
RewriteEngine On
RewriteBase /

# Don't rewrite files or directories
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d

# Rewrite everything else to app.wsgi
RewriteRule ^(.*)$ app.wsgi/$1 [L]

# Set environment variables
SetEnv DB_HOST 127.0.0.1
SetEnv DB_PORT 3306
SetEnv DB_USER your_db_user
SetEnv DB_PASSWORD your_db_password
SetEnv DB_NAME ilmuwanutara_e2eewater
SetEnv MQTT_HOST your_mqtt_host
SetEnv MQTT_PORT 1883
SetEnv FLASK_ENV production
```

### Option 4: Using Passenger (If Available)

Some hosting providers offer Phusion Passenger for Python:

1. **Create `passenger_wsgi.py`** in your project root:
   ```python
   import sys
   import os
   
   # Add project directory to path
   sys.path.insert(0, os.path.dirname(__file__))
   
   # Activate virtual environment
   activate_this = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate_this.py')
   if os.path.exists(activate_this):
       exec(open(activate_this).read(), {'__file__': activate_this})
   
   # Import Flask app
   from app import app as application
   ```

2. **Create `.htaccess`:**
   ```apache
   PassengerEnabled On
   PassengerPython /home/username/public_html/e2eewater/venv/bin/python
   ```

## Post-Deployment Steps

### 1. Create Virtual Environment on Server

SSH into server and run:
```bash
cd /home/username/public_html/e2eewater  # or your path
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_pi.txt
```

### 2. Set File Permissions

```bash
chmod 755 app.wsgi
chmod 644 *.py
chmod -R 755 templates/
chmod -R 755 static/
chmod 600 keys/private.pem
```

### 3. Verify Database Connection

Update `app.wsgi` with correct database credentials:
```python
os.environ.setdefault('DB_HOST', '127.0.0.1')
os.environ.setdefault('DB_USER', 'your_actual_db_user')
os.environ.setdefault('DB_PASSWORD', 'your_actual_db_password')
os.environ.setdefault('DB_NAME', 'ilmuwanutara_e2eewater')
```

### 4. Test the Application

Visit: `https://e2eewater.ilmuwanutara.my`

You should see your Flask application, not a directory listing.

## Troubleshooting

### Still Seeing Directory Listing?

1. **Check if WSGI is enabled:**
   - LiteSpeed must have Python/WSGI support enabled
   - Contact your hosting provider if unsure

2. **Check Error Logs:**
   ```bash
   tail -f /usr/local/lsws/logs/error.log
   # Or
   tail -f /home/username/public_html/e2eewater/error.log
   ```

3. **Verify app.wsgi is accessible:**
   - Check file permissions: `ls -la app.wsgi`
   - Ensure it's executable: `chmod +x app.wsgi`

4. **Test Python import:**
   ```bash
   cd /home/username/public_html/e2eewater
   source venv/bin/activate
   python3 -c "from app import app; print('OK')"
   ```

### "Module not found" Errors

- Ensure virtual environment is created and activated
- Install dependencies: `pip install -r requirements_pi.txt`
- Check Python path in WSGI configuration

### "Permission denied" Errors

- Check file permissions: `chmod 755` for directories, `chmod 644` for files
- Ensure web server user has read access

### Database Connection Errors

- Verify database credentials in `app.wsgi`
- Ensure database exists and user has permissions
- Check if database server is accessible from web server

## Quick Checklist

- [ ] Files uploaded via FileZilla ✓
- [ ] Virtual environment created on server
- [ ] Dependencies installed (`pip install -r requirements_pi.txt`)
- [ ] WSGI configured (cPanel Python App or manual config)
- [ ] Environment variables set (database, MQTT, etc.)
- [ ] File permissions set correctly
- [ ] Application restarted
- [ ] Tested in browser (should see Flask app, not directory listing)

## Contact Your Hosting Provider

If you're unsure about LiteSpeed configuration, contact your hosting provider and ask:
- "How do I deploy a Python Flask WSGI application?"
- "Do you support Python/WSGI applications?"
- "Is there a cPanel Python App feature?"

Most shared hosting providers with cPanel have a "Python App" or "Setup Python App" feature that makes this much easier!

