# How to Check Apache Errors on Windows

When using Apache with Flask/mod_wsgi, errors are logged to specific locations. Here's how to find them:

## 1. Apache Error Log Location

The Apache error log location depends on your Apache installation. Common locations:

- **XAMPP**: `C:\xampp\apache\logs\error.log`
- **WAMP**: `C:\wamp64\logs\apache_error.log` or `C:\wamp\logs\apache_error.log`
- **Custom Apache**: Usually in `C:\Apache24\logs\error.log` or check your `httpd.conf` file

If your Apache config uses a custom error log (as configured in `apache-config-windows.conf`), check:
- `C:\Apache24\logs\iot-water-monitor-error.log` (or wherever your Apache logs directory is)

## 2. Flask Error Log File

I've also created a separate Flask error log file in your project directory:
- `C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\flask_error.log`

## 3. How to View Error Logs

### Option A: Using Notepad
1. Open File Explorer
2. Navigate to the log file location
3. Right-click the log file → Open with → Notepad
4. Scroll to the bottom to see recent errors

### Option B: Using PowerShell
```powershell
# View last 50 lines of Apache error log (adjust path as needed)
Get-Content C:\xampp\apache\logs\error.log -Tail 50

# Or for the Flask error log
Get-Content "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\flask_error.log" -Tail 50
```

### Option C: Using Command Prompt
```cmd
# View last lines (Windows 10/11)
powershell "Get-Content C:\xampp\apache\logs\error.log -Tail 50"

# Or use type command (shows entire file)
type "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\flask_error.log"
```

## 4. After Getting the 500 Error

1. **Reproduce the error** - Visit the page that gives the 500 error
2. **Check the logs immediately** - Errors appear in real-time
3. **Look for the error message** - It should show:
   - The route that failed
   - The exception type
   - Full traceback showing exactly where it failed

## 5. Example Error Format

You should see something like:
```
[2025-12-06 10:30:45] ERROR: Unhandled exception in route /sensors [GET]: 'NoneType' object has no attribute 'get'
Exception type: AttributeError
Traceback (most recent call last):
  File "...", line 1234, in sensors
    ...
```

## 6. Restart Apache After Changes

After fixing code, restart Apache to reload the application:
- **XAMPP**: Open XAMPP Control Panel → Stop Apache → Start Apache
- **WAMP**: Click WAMP icon → Restart All Services
- **Windows Service**: Open Services → Find Apache → Restart

## 7. Enable More Verbose Logging (Optional)

To see more details, you can edit `app.wsgi` and add:
```python
os.environ['FLASK_DEBUG'] = '1'
```

**Note**: Only enable this in development, not production!

