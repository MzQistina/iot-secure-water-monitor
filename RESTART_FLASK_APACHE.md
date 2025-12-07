# How to Restart Flask with Apache

## Important: Set Environment Variable for Apache First!

Since you're using Apache/mod_wsgi, you need to set `DB_ENCRYPTION_KEY` in your Apache configuration or `app.wsgi` file, not just in your terminal.

### Option 1: Add to app.wsgi (Recommended)

Edit `app.wsgi` and add the environment variable:

```python
# Around line 58, add this:
os.environ.setdefault('DB_ENCRYPTION_KEY', 'T468PZiZfDtJDQEjxlzMMJqIDOSHJ4Pp3exMQtedD50=')
```

### Option 2: Add to Apache Config

In your Apache virtual host configuration, add:

```apache
<VirtualHost *:80>
    # ... other config ...
    
    # Set environment variable for mod_wsgi
    SetEnv DB_ENCRYPTION_KEY "T468PZiZfDtJDQEjxlzMMJqIDOSHJ4Pp3exMQtedD50="
    
    # ... rest of config ...
</VirtualHost>
```

## Restart Apache to Apply Changes

### Windows (Run as Administrator):

**Method 1: Using Services**
1. Press `Win + R`, type `services.msc`, press Enter
2. Find "Apache2.4" or "Apache HTTP Server"
3. Right-click → Restart

**Method 2: Using Command Prompt (as Administrator)**
```cmd
# Stop Apache
net stop Apache2.4

# Start Apache
net start Apache2.4
```

**Method 3: Using Apache Monitor**
- Look for Apache icon in system tray
- Right-click → Restart

### Linux:
```bash
# Ubuntu/Debian
sudo systemctl restart apache2

# Or
sudo service apache2 restart

# CentOS/RHEL
sudo systemctl restart httpd
```

## Verify Flask is Running

After restarting Apache:

1. **Check Apache error logs** for any errors:
   ```bash
   # Windows
   C:\Apache24\logs\error.log
   
   # Linux
   tail -f /var/log/apache2/error.log
   ```

2. **Test your Flask app** in browser:
   - Visit `http://localhost` or your domain
   - Check if dashboard loads correctly

3. **Verify encryption is working**:
   - Submit sensor data
   - Check database - values should be encrypted
   - View dashboard - values should display correctly (decrypted)

## Quick Restart Sequence

```powershell
# 1. Set environment variable in app.wsgi (one-time setup)
# Edit app.wsgi, add: os.environ.setdefault('DB_ENCRYPTION_KEY', 'your-key')

# 2. Restart Apache (as Administrator)
net stop Apache2.4
net start Apache2.4

# 3. Check logs
Get-Content C:\Apache24\logs\error.log -Tail 20
```

## Troubleshooting

### "DB_ENCRYPTION_KEY must be set" Error

**Solution:** Make sure you added the environment variable to `app.wsgi` or Apache config, then restarted Apache.

### Changes Not Taking Effect

**Solution:** 
- Restart Apache (not just reload)
- Clear browser cache
- Check Apache error logs

### Apache Won't Start

**Solution:**
- Check error logs for syntax errors
- Verify mod_wsgi is installed
- Check Python path in Apache config

## Development vs Production

**For Development (Direct Flask):**
```powershell
# Just run directly
.\venv\Scripts\Activate.ps1
python app.py
```

**For Production (Apache):**
- Set environment variable in `app.wsgi` or Apache config
- Restart Apache service

