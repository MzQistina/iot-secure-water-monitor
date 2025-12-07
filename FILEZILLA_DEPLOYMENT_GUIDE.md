# FileZilla Deployment Guide

## Files to Upload to Server

When deploying your IoT Secure Water Monitor application via FileZilla, upload the following files and folders:

### ✅ **MUST UPLOAD** (Essential Application Files)

#### Core Application Files
- `app.py` - Main Flask application
- `app.wsgi` - WSGI entry point for Apache/mod_wsgi
- `db.py` - Database connection and operations
- `encryption_utils.py` - Encryption utilities
- `mqtt_listener.py` - MQTT listener service
- `default_thresholds.json` - Default sensor thresholds

#### Templates (HTML files)
- `templates/` folder (all HTML files):
  - `dashboard.html`
  - `history.html`
  - `landing.html`
  - `login.html`
  - `profile.html`
  - `readings.html`
  - `register.html`
  - `sensors_register.html`
  - `sensors.html`
  - `sidebar.html`

#### Static Files (CSS, JS, Images)
- `static/` folder:
  - `favicon.ico`
  - `landing.png`
  - Any other CSS/JS/image files

#### Configuration Files
- `apache-config.conf` - Apache configuration (if deploying with Apache)
- `apache-config-windows.conf` - Windows Apache config (if applicable)
- `config.inc.php` - phpMyAdmin config (if using phpMyAdmin)

#### Keys and Certificates
- `keys/` folder - **REQUIRED** - Server's encryption key pair:
  - `keys/public.pem` - Server's public key (used by Raspberry Pi to encrypt data)
  - `keys/private.pem` - Server's private key (used by server to decrypt data)
  
**Important:** `sensor_keys/` folder is **NOT needed on the server**. Sensor keys are generated on the Raspberry Pi device. The Pi uploads its public keys to the server, which are then stored in the `user_keys/` folder (created automatically).

#### Simulators (Optional - only if needed on server)
- `simulators/` folder - If you need to run simulators on the server
- `raspberry_pi_client.py` - Raspberry Pi client script
- `multi_sensor_client.py` - Multi-sensor client script

#### Requirements File
- `requirements_pi.txt` - Python dependencies (or create a `requirements.txt` with all dependencies)

---

### ❌ **DO NOT UPLOAD** (Exclude These)

#### Virtual Environment
- `venv/` folder - **NEVER upload this!** Create a new virtual environment on the server
- Virtual environments are platform-specific and will cause errors

#### Python Cache
- `__pycache__/` folders - Python bytecode cache (auto-generated)
- `*.pyc` files - Compiled Python files
- `*.pyo` files - Optimized Python files

#### IDE/Editor Files
- `.vscode/` folder
- `.idea/` folder
- `*.swp`, `*.swo` files

#### OS Files
- `.DS_Store` (Mac)
- `Thumbs.db` (Windows)

#### Log Files
- `*.log` files

#### Test Files (Optional - usually not needed in production)
- `test_mysql_connection.py`
- `test_device_session.py`
- `check_phpmyadmin.py`
- `find_apache_phpmyadmin.py`
- `configure_apache_phpmyadmin.py`

#### Documentation Files (Optional - not needed for deployment)
- `*.md` files (all markdown documentation files)
- `VIRTUALBOX_FILES_CHECKLIST.txt`

#### User Keys (Auto-generated on server)
- `user_keys/` folder - **DO NOT upload** - This folder is created automatically on the server when Raspberry Pi devices register and upload their public keys. If you're migrating from another server, you may need to copy this folder, but for fresh deployment, leave it empty.

---

## Step-by-Step FileZilla Upload Process

### 1. **Connect to Server**
   - Open FileZilla
   - Enter your domain name or IP address
   - Enter FTP username and password
   - Connect

### 2. **Navigate to Target Directory**
   - On the server side (right panel), navigate to your web root directory
   - Common locations:
     - `/var/www/html/` (Linux)
     - `/home/username/public_html/` (Shared hosting)
     - `/var/www/yourdomain.com/` (VPS)

### 3. **Upload Files**
   
   **Method 1: Selective Upload (Recommended)**
   - On local side (left panel), navigate to your project folder
   - Select and drag these folders/files:
     - `app.py`
     - `app.wsgi`
     - `db.py`
     - `encryption_utils.py`
     - `mqtt_listener.py`
     - `default_thresholds.json`
     - `templates/` folder
     - `static/` folder
     - `keys/` folder (if needed)
     - `sensor_keys/` folder
     - `requirements_pi.txt` or `requirements.txt`
     - `apache-config.conf` (if using Apache)

   **Method 2: Upload All Then Delete**
   - Upload entire project folder
   - Delete `venv/` folder on server
   - Delete `__pycache__/` folders
   - Delete documentation files (`*.md`)

### 4. **Set Permissions** (Linux/Unix servers)
   After uploading, SSH into your server and set proper permissions:
   ```bash
   chmod 755 app.py
   chmod 755 app.wsgi
   chmod 644 *.py
   chmod -R 755 templates/
   chmod -R 755 static/
   chmod 600 keys/*  # Secure key files
   ```

### 5. **Create Virtual Environment on Server**
   ```bash
   cd /path/to/your/project
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate  # Windows
   pip install -r requirements_pi.txt
   ```

---

## Quick Checklist

Before uploading, verify you have:

- [ ] `app.py`
- [ ] `app.wsgi`
- [ ] `db.py`
- [ ] `encryption_utils.py`
- [ ] `mqtt_listener.py`
- [ ] `default_thresholds.json`
- [ ] `templates/` folder (all HTML files)
- [ ] `static/` folder (CSS, images, etc.)
- [ ] `keys/` folder (server's public.pem and private.pem)
- [ ] **NOT** `sensor_keys/` folder (these are on Raspberry Pi, not server)
- [ ] `requirements_pi.txt` or `requirements.txt`
- [ ] Configuration files (`apache-config.conf`, etc.)

After uploading, verify you did NOT upload:

- [ ] `venv/` folder
- [ ] `__pycache__/` folders
- [ ] `*.md` documentation files
- [ ] Test files (`test_*.py`)
- [ ] `sensor_keys/` folder (these are generated on Raspberry Pi)
- [ ] `user_keys/` folder (created automatically on server)

---

## Post-Upload Steps

1. **SSH into your server** (if you have SSH access)
2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_pi.txt
   ```

3. **Configure environment variables** (edit `app.wsgi` or set in Apache config):
   - Database credentials
   - MQTT settings
   - Flask secret key

4. **Set up Apache/mod_wsgi** (if using Apache):
   - Copy `apache-config.conf` to Apache sites directory
   - Update paths in configuration
   - Enable site and restart Apache

5. **Test the application:**
   - Visit your domain in a browser
   - Check Apache error logs if issues occur

---

## FileZilla Filter Settings (Optional)

To make uploading easier, you can set up filters in FileZilla:

1. Go to **View → Filename Filters**
2. Add filters to exclude:
   - `venv`
   - `__pycache__`
   - `*.pyc`
   - `*.md`
   - `.git`

This will hide these files/folders from view, making it easier to select only what you need.

---

## Understanding Keys Architecture

### Server Keys (`keys/` folder) - **REQUIRED on Server**
- **Purpose:** Server's encryption key pair for receiving encrypted data from sensors
- **Files needed:**
  - `keys/public.pem` - Public key (sensors use this to encrypt data)
  - `keys/private.pem` - Private key (server uses this to decrypt data)
- **Location:** Must be on the server
- **Action:** Upload `keys/` folder via FileZilla

### Sensor Keys (`sensor_keys/` folder) - **NOT on Server**
- **Purpose:** Each Raspberry Pi device has its own key pair for signing data
- **Location:** Generated and stored on the Raspberry Pi device (in Raspbian)
- **How it works:**
  1. Keys are generated on the Raspberry Pi using `sensor_keygen.py`
  2. Pi stores private key locally (never shared)
  3. Pi uploads public key to server via `/api/register-device` endpoint
  4. Server stores public key in `user_keys/` folder automatically
- **Action:** Do NOT upload `sensor_keys/` folder to server

### User Keys (`user_keys/` folder) - **Auto-generated on Server**
- **Purpose:** Stores public keys uploaded from Raspberry Pi devices
- **Location:** Created automatically on server when devices register
- **Structure:** `user_keys/{user_id}/{device_id}_public.pem`
- **Action:** Do NOT upload this folder (will be created automatically)

### Summary
- ✅ **Upload:** `keys/` folder (server's key pair)
- ❌ **Don't upload:** `sensor_keys/` folder (belongs on Raspberry Pi)
- ❌ **Don't upload:** `user_keys/` folder (auto-created on server)

## Important Notes

- **Never upload `venv/`** - Virtual environments are platform-specific
- **Upload `requirements.txt`** - Install dependencies on the server
- **Keep folder structure** - Maintain the same directory structure
- **Check file permissions** - Some files may need execute permissions
- **Backup before upload** - Always backup existing files on server first
- **Test after upload** - Verify the application works after deployment
- **Server keys are critical** - Make sure `keys/` folder with both public.pem and private.pem is uploaded

---

## Troubleshooting

### Common Upload Issues

#### Problem 1: File Size Mismatch (Most Common)

**Symptoms:**
- Files upload but sizes don't match (local vs remote)
- Files are incomplete or corrupted
- Import errors or syntax errors

**Fix:**
1. **Check file sizes in FileZilla:**
   - Compare local vs remote file sizes
   - They must match exactly!

2. **Fix FileZilla settings:**
   - **Edit** → **Settings** → **Connection** → **Timeout:** `300` seconds
   - **Edit** → **Settings** → **Transfers** → **Maximum retries:** `10`
   - **Transfer** → **Transfer Type** → **Auto**

3. **Re-upload files:**
   - Delete corrupted files on server
   - Re-upload with correct settings
   - Verify sizes match after upload

#### Problem 2: Wrong Transfer Mode

**Symptoms:**
- Files upload but don't work
- Syntax errors after upload
- Encoding issues

**Fix:**
- **Transfer** → **Transfer Type** → **Auto** (recommended) or **ASCII**
- **NOT Binary** (for Python/text files)

#### Problem 3: File Permissions

**Symptoms:**
- "Permission denied" errors
- Files can't be executed

**Fix:**
- Set permissions: `chmod 755 app.py app.wsgi`
- Set permissions: `chmod 644 *.py` (for other Python files)
- Or use FileZilla: Right-click → **File Permissions** → Set to `755` or `644`

#### Problem 4: Directory Listing Instead of Flask App

**Symptoms:**
- See file directory listing instead of web app
- Flask app not running

**Causes:**
1. Files incomplete (file size mismatch)
2. WSGI not configured
3. Flask app not starting

**Fix:**
1. **Fix file size mismatch first** (see Problem 1)
2. **Verify `app.wsgi` exists** and is correct
3. **Configure WSGI** (cPanel or `.htaccess`)
4. **Check error logs** for specific errors
5. **Set file permissions** correctly

#### Problem 5: Line Endings (Windows vs Unix)

**Symptoms:**
- "bad interpreter" errors
- Files work locally but not on server

**Fix:**
- Configure FileZilla: **Edit** → **Settings** → **Transfers** → **ASCII/Binary**
- Check **"Treat files without extension as ASCII files"**
- Or fix on server: `dos2unix *.py`

### Other Common Issues

**"Module not found" errors:**
- Ensure virtual environment is created and activated
- Install requirements: `pip install -r requirements.txt`

**"Database connection failed":**
- Verify database credentials in `app.wsgi` or environment variables
- Ensure database server is accessible from web server

**"Template not found":**
- Verify `templates/` folder is uploaded
- Check Flask template folder path in `app.py`

### PythonAnywhere + FileZilla FAQ

**Can I use FileZilla with PythonAnywhere?**
- ❌ **NO** - PythonAnywhere does NOT support FTP/FileZilla
- Use web interface, Git, or Bash console instead
- See `PYTHONANYWHERE_DEPLOYMENT_GUIDE.md` for details

### Recommended FileZilla Settings

**For Python/Flask projects:**
```
Transfer Type: Auto
Timeout: 300 seconds
Max Retries: 10
ASCII Files: *.py, *.txt, *.html, *.css, *.js, *.json, *.md, *.conf, *.wsgi
Binary Files: *.jpg, *.png, *.gif, *.pdf, *.zip, *.pem, *.key
```

### Alternative: Use Git Instead

If FileZilla keeps causing issues:
1. Push to GitHub: `git push`
2. Pull on server: `git pull`
3. Git handles transfers correctly and avoids size mismatch issues!

