# Update Apache Environment Variables for MQTT

Your Apache server is using old MQTT configuration. Update it to use the new TLS settings.

## Problem

Apache logs show:
- `MQTT_HOST env: 192.168.56.101` ❌ (old IP)
- `MQTT_PORT env: 1883` ❌ (old port, not TLS)
- Connection refused errors

## Solution

### Step 1: Edit Apache Virtual Host Configuration

**Open the Apache configuration file:**
```
C:\Apache24\conf\extra\httpd-vhosts.conf
```

**Or if you have a custom config, find where your VirtualHost is defined.**

### Step 2: Add/Update MQTT Environment Variables

**Find the section with `SetEnv` directives and add/update these lines:**

```apache
# MQTT Configuration (for TLS/SSL connection to Raspbian broker)
SetEnv MQTT_HOST 192.168.56.102
SetEnv MQTT_PORT 8883
SetEnv MQTT_USE_TLS true
SetEnv MQTT_CA_CERTS C:/Users/NURMIZAN QISTINA/Desktop/fyp/iot-secure-water-monitor/certs/ca-cert.pem
SetEnv MQTT_TLS_INSECURE true
SetEnv MQTT_KEYS_TOPIC keys/+/public
SetEnv MQTT_PROVISION_TOPIC_BASE provision
```

**Important Notes:**
- Use forward slashes `/` in the path (not backslashes `\`)
- The path must be absolute (full path from C: drive)
- Remove any old `SetEnv MQTT_HOST 192.168.56.101` lines
- Remove any old `SetEnv MQTT_PORT 1883` lines

### Step 3: Verify Certificate Path

**Make sure the CA certificate exists:**
```powershell
Test-Path "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
```

If it doesn't exist, copy it from Raspbian:
```powershell
# From Raspbian (if you have SSH access):
# scp raspberry@192.168.56.102:/etc/mosquitto/certs/ca-cert.pem "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\"
```

### Step 4: Test Apache Configuration

**Test the configuration syntax:**
```cmd
cd C:\Apache24\bin
httpd.exe -t
```

Should output: `Syntax OK`

### Step 5: Restart Apache

**Restart Apache service:**
```cmd
# Stop Apache
net stop Apache2.4

# Start Apache
net start Apache2.4
```

**Or use the Apache Monitor:**
- Right-click Apache icon in system tray
- Click "Restart"

### Step 6: Verify Environment Variables

**Check Apache error log:**
```powershell
Get-Content C:\Apache24\logs\error.log -Tail 20
```

**Look for:**
```
[WSGI] MQTT_HOST env: 192.168.56.102  ✅
[WSGI] MQTT_PORT env: 8883  ✅
```

**And check for successful MQTT connection:**
```
MQTT: Connecting to 192.168.56.102:8883 (TLS)
MQTT: connected rc=0; subscribed to 'keys/+/public'
```

## Example Complete VirtualHost Section

```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAlias 127.0.0.1
    
    Define PROJECT_DIR "C:/Users/NURMIZAN QISTINA/Desktop/fyp/iot-secure-water-monitor"
    
    WSGIDaemonProcess iot-water-monitor python-home=${PROJECT_DIR}/venv python-path=${PROJECT_DIR}
    WSGIProcessGroup iot-water-monitor
    WSGIScriptAlias / ${PROJECT_DIR}/app.wsgi
    
    <Directory "${PROJECT_DIR}">
        Require all granted
        Options -Indexes +FollowSymLinks
        AllowOverride None
    </Directory>
    
    Alias /static "${PROJECT_DIR}/static"
    <Directory "${PROJECT_DIR}/static">
        Require all granted
        Options -Indexes
    </Directory>
    
    ErrorLog "logs/iot-water-monitor-error.log"
    CustomLog "logs/iot-water-monitor-access.log" combined
    
    # Environment variables
    SetEnv FLASK_APP app.py
    SetEnv FLASK_ENV production
    
    # MQTT Configuration
    SetEnv MQTT_HOST 192.168.56.102
    SetEnv MQTT_PORT 8883
    SetEnv MQTT_USE_TLS true
    SetEnv MQTT_CA_CERTS C:/Users/NURMIZAN QISTINA/Desktop/fyp/iot-secure-water-monitor/certs/ca-cert.pem
    SetEnv MQTT_TLS_INSECURE true
    SetEnv MQTT_KEYS_TOPIC keys/+/public
    SetEnv MQTT_PROVISION_TOPIC_BASE provision
    
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

## Troubleshooting

### Still seeing old IP/port in logs?
- Make sure you edited the correct config file
- Check for multiple VirtualHost sections
- Restart Apache after changes
- Clear browser cache if testing via web interface

### Certificate path not found?
- Verify the path uses forward slashes `/`
- Check that the file exists at that location
- Make sure the path is absolute (starts with `C:/`)

### Connection still refused?
- Verify MQTT broker is running on Raspbian: `sudo systemctl status mosquitto`
- Test network connectivity: `Test-NetConnection -ComputerName 192.168.56.102 -Port 8883`
- Check Raspbian firewall (if enabled)

### MQTT connection works but no messages?
- Verify provision agent is running on Raspbian
- Check MQTT topics match: `keys/+/public`
- Check Apache logs for MQTT subscription messages

