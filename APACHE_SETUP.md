# Apache Server Setup Guide for IoT Secure Water Monitor

Complete guide for deploying your Flask application using Apache HTTP Server with mod_wsgi on Windows, Linux, and macOS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Windows Quick Start](#windows-quick-start)
4. [mod_wsgi Installation](#mod_wsgi-installation)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Port 80 Conflicts](#port-80-conflicts)

## Prerequisites

1. **Apache HTTP Server** installed on your system
2. **mod_wsgi** module for Apache
3. **Python** (same version as your virtual environment)
4. **Virtual environment** with all required packages installed

## Installation

### On Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi-py3
sudo a2enmod wsgi
```

### On Windows:
1. Download Apache HTTP Server from [Apache Lounge](https://www.apachelounge.com/download/)
   - Choose the version matching your system (32-bit or 64-bit)
   - Extract to `C:\Apache24` (or your preferred location)
2. Install Apache as a Windows Service:
   ```cmd
   cd C:\Apache24\bin
   httpd.exe -k install
   ```

### On macOS:
```bash
brew install apache2
pip install mod_wsgi
mod_wsgi-express module-config
```

## Windows Quick Start

### Step 1: Install Apache HTTP Server

1. Download from [Apache Lounge](https://www.apachelounge.com/download/)
2. Extract to `C:\Apache24`
3. Install as service:
   ```cmd
   cd C:\Apache24\bin
   httpd.exe -k install
   ```

### Step 2: Install mod_wsgi

See [mod_wsgi Installation](#mod_wsgi-installation) section below.

### Step 3: Configure Apache

1. **Edit httpd.conf:**
   - Open `C:\Apache24\conf\httpd.conf` (as Administrator)
   - Add mod_wsgi configuration (from `mod_wsgi-express module-config`)
   - Uncomment: `Include conf/extra/httpd-vhosts.conf`

2. **Edit httpd-vhosts.conf:**
   - Open `C:\Apache24\conf\extra\httpd-vhosts.conf`
   - Copy contents from `apache-config-windows.conf`
   - Update `PROJECT_DIR` path:
     ```apache
     Define PROJECT_DIR "C:/Users/YOUR_USERNAME/Desktop/fyp/iot-secure-water-monitor"
     ```

3. **Test configuration:**
   ```cmd
   cd C:\Apache24\bin
   httpd.exe -t
   ```
   Should output: "Syntax OK"

4. **Start Apache:**
   ```cmd
   httpd.exe -k start
   ```

5. **Test:** Open `http://localhost` in browser

## mod_wsgi Installation

### On Linux/macOS:
```bash
pip install mod_wsgi
mod_wsgi-express module-config
```

### On Windows:

**Problem:** mod_wsgi requires compilation, which needs Microsoft Visual C++ Build Tools.

#### Solution 1: Install Visual C++ Build Tools (Recommended)

1. **Download Build Tools:**
   - Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Click "Download Build Tools"
   - Run the installer

2. **Install Components:**
   - Select **"Desktop development with C++"** workload
   - Ensure these are checked:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 10/11 SDK
     - C++ CMake tools
   - Click **"Install"** (takes 10-20 minutes)

3. **Restart terminal** after installation

4. **Install mod_wsgi:**
   ```powershell
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   
   # Install mod_wsgi
   pip install mod_wsgi
   ```

5. **Get configuration:**
   ```cmd
   mod_wsgi-express module-config
   ```
   Copy the output (will look like):
   ```
   LoadFile "C:/Python312/python312.dll"
   LoadModule wsgi_module "C:/path/to/mod_wsgi/server/mod_wsgi.cp312-win_amd64.pyd"
   ```

6. **Add to httpd.conf:**
   - Open `C:\Apache24\conf\httpd.conf` (as Administrator)
   - Find LoadModule section (around line 180-200)
   - Add the two lines from step 5
   - Save file

7. **Verify:**
   ```cmd
   httpd.exe -t
   httpd.exe -M | findstr wsgi
   ```
   Should show: `wsgi_module (shared)`

#### Solution 2: Use Pre-built Binary (Alternative)

```powershell
pip install --only-binary :all: mod_wsgi
```

#### Solution 3: Use Alternative WSGI Server

If mod_wsgi installation fails, use **Waitress** (Windows-friendly):

```powershell
pip install waitress
```

Then modify `app.py`:
```python
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
```

## Configuration

### 1. Configure the WSGI File

The `app.wsgi` file is already created. Make sure to update the paths if your project structure differs.

### 2. Configure Apache Virtual Host

#### On Linux:
```bash
# Copy the configuration file
sudo cp apache-config.conf /etc/apache2/sites-available/iot-water-monitor.conf

# Edit the file and update paths
sudo nano /etc/apache2/sites-available/iot-water-monitor.conf

# Enable the site
sudo a2ensite iot-water-monitor.conf

# Test configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
```

#### On Windows:
1. Edit `httpd-vhosts.conf` or `httpd.conf`
2. Copy contents of `apache-config-windows.conf` and update paths
3. Restart Apache service

#### On macOS:
```bash
# Copy configuration
sudo cp apache-config.conf /usr/local/etc/apache2/2.4/extra/httpd-vhosts.conf

# Edit and update paths
sudo nano /usr/local/etc/apache2/2.4/extra/httpd-vhosts.conf

# Restart Apache
sudo brew services restart httpd
```

### 3. Update Configuration Paths

In `apache-config.conf` or `apache-config-windows.conf`, replace:

- `/path/to/iot-secure-water-monitor` → Your actual project path
- `your-domain.com` → Your domain name or IP address
- `/path/to/ssl/` → Your SSL certificate paths (if using HTTPS)

**Windows Example:**
```
C:/Users/YOUR_USERNAME/Desktop/fyp/iot-secure-water-monitor
```

**Linux Example:**
```
/home/username/iot-secure-water-monitor
```

### 4. Set File Permissions (Linux/macOS)

```bash
# Make WSGI file executable
chmod +x app.wsgi

# Set proper ownership (replace www-data with your Apache user)
sudo chown -R www-data:www-data /path/to/iot-secure-water-monitor
sudo chmod -R 755 /path/to/iot-secure-water-monitor
```

### 5. Environment Variables

Set environment variables in Apache configuration:

```apache
# Add to VirtualHost section
SetEnv MQTT_HOST your_mqtt_host
SetEnv MQTT_PORT 8883
SetEnv MQTT_USE_TLS true
SetEnv MQTT_CA_CERTS /path/to/ca-cert.pem
SetEnv MQTT_USER your_mqtt_username
SetEnv MQTT_PASSWORD your_mqtt_password
SetEnv SECRET_KEY your_secret_key
SetEnv DB_HOST your_database_host
SetEnv DB_PORT 3306
SetEnv DB_USER your_db_user
SetEnv DB_PASSWORD your_db_password
SetEnv DB_NAME your_db_name
```

Or create a `.env` file in your project directory (ensure Apache can read it).

### 6. Test the Configuration

1. **Check Apache configuration:**
   ```bash
   # Linux
   sudo apache2ctl configtest
   
   # Windows
   httpd.exe -t
   ```

2. **Check Apache error logs:**
   ```bash
   # Linux
   sudo tail -f /var/log/apache2/error.log
   
   # Windows
   # Check logs in Apache/logs/error.log
   ```

3. **Access your application:**
   - Open browser: `http://your-domain.com` or `http://localhost`

## Port 80 Conflicts

### Problem
Apache reports: `(OS 10048)Only one usage of each socket address (protocol/network address/port) is normally permitted`

### Solutions

#### Solution 1: Check if IIS is Running (Most Common on Windows)

**Check if IIS is installed:**
```cmd
dism /online /get-featureinfo /featurename:IIS-WebServerRole
```

**If IIS is installed, stop it:**
```cmd
# Stop IIS service
net stop w3svc

# Or disable it permanently
sc config w3svc start= disabled
```

**Or uninstall IIS:**
1. Open "Turn Windows features on or off"
2. Uncheck "Internet Information Services"
3. Restart computer

#### Solution 2: Check Windows HTTP.sys Port Reservations

**Check reservations:**
```cmd
netsh http show urlacl
```

**Remove reservation if found:**
```cmd
netsh http delete urlacl url=http://+:80/
```

#### Solution 3: Check if Apache Service is Already Running

**Check Apache service status:**
```cmd
sc query Apache2.4
```

**If running, stop it:**
```cmd
httpd -k stop
# Or
net stop Apache2.4
```

#### Solution 4: Use a Different Port (Quick Fix)

If you can't free port 80, configure Apache to use port 8080:

**Edit `C:\Apache24\conf\httpd.conf`:**
```apache
# Change from:
Listen 80

# To:
Listen 8080

# Also add ServerName:
ServerName localhost:8080
```

Then access your site at `http://localhost:8080`

#### Solution 5: Check for Other Services Using Port 80

**Check what's using port 80:**
```cmd
netstat -ano | findstr :80
```

**Check specific process:**
```cmd
# Find PID from netstat, then:
tasklist /FI "PID eq <PID_NUMBER>"
```

### Recommended Steps

1. Check if Apache service is running: `sc query Apache2.4`
2. Check for IIS: `net stop w3svc`
3. Check HTTP.sys reservations: `netsh http show urlacl`
4. Try starting Apache: `httpd -k start`
5. If still failing, use port 8080 (see Solution 4)

## Troubleshooting

### Common Issues

1. **403 Forbidden Error:**
   - Check file permissions
   - Verify Directory permissions in Apache config
   - Ensure `Require all granted` is set

2. **500 Internal Server Error:**
   - Check Apache error logs
   - Verify Python path in WSGIDaemonProcess
   - Ensure all Python dependencies are installed in virtual environment
   - Check that `app.wsgi` file is executable

3. **Module not found errors:**
   - Verify virtual environment path in Apache config
   - Ensure all packages are installed: `pip install -r requirements.txt`
   - Check Python path includes project directory

4. **WSGI daemon process errors:**
   - Verify Python version matches virtual environment
   - Check `python-home` path in Apache config
   - Ensure mod_wsgi is properly installed

5. **"Cannot load module" error (Windows):**
   - Verify mod_wsgi installation: `pip show mod_wsgi`
   - Check that the LoadModule path in httpd.conf is correct
   - Ensure Python version matches (32-bit vs 64-bit)

6. **"cl.exe not found" (Windows):**
   - Visual C++ Build Tools not installed correctly
   - Restart terminal after installation
   - Verify installation in "Add or remove programs"

### Debugging Tips

1. **Enable detailed error messages:**
   ```apache
   WSGIPythonDebug On
   ```

2. **Check WSGI process:**
   ```bash
   ps aux | grep wsgi
   ```

3. **Test WSGI file directly:**
   ```bash
   python app.wsgi
   ```

4. **View Apache error logs:**
   ```bash
   # Linux
   sudo tail -f /var/log/apache2/error.log
   
   # Windows
   type C:\Apache24\logs\error.log
   ```

### Useful Commands (Windows)

```cmd
# Stop Apache
httpd.exe -k stop

# Restart Apache
httpd.exe -k restart

# Test configuration
httpd.exe -t

# View Apache version
httpd.exe -v

# View loaded modules
httpd.exe -M
```

## Production Recommendations

1. **Use HTTPS:** Configure SSL certificates and enable HTTPS virtual host
2. **Set proper SECRET_KEY:** Use a strong, random secret key
3. **Disable debug mode:** Set `FLASK_DEBUG=False` in environment
4. **Configure firewall:** Only allow necessary ports (80, 443)
5. **Set up log rotation:** Configure Apache log rotation
6. **Monitor resources:** Use tools like `htop` or Apache status module
7. **Backup regularly:** Backup your database and configuration files

## Additional Resources

- [mod_wsgi Documentation](https://modwsgi.readthedocs.io/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)
- [Apache HTTP Server Documentation](https://httpd.apache.org/docs/)

## Support

If you encounter issues, check:
1. Apache error logs
2. Application logs (if configured)
3. System logs
4. mod_wsgi documentation
