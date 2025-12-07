#!/usr/bin/env python3
"""
WSGI entry point for Apache/mod_wsgi deployment
"""
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Activate virtual environment if it exists
# Note: Modern virtual environments may not have activate_this.py
# If using WSGIDaemonProcess with python-home, this may not be necessary
venv_path = os.path.join(project_dir, 'venv')
if os.path.exists(venv_path):
    # Try Windows path first
    activate_this = os.path.join(venv_path, 'Scripts', 'activate_this.py')
    if not os.path.exists(activate_this):
        # Try Linux/Mac path
        activate_this = os.path.join(venv_path, 'bin', 'activate_this.py')
    
    if os.path.exists(activate_this):
        try:
            with open(activate_this) as f:
                exec(f.read(), {'__file__': activate_this})
        except Exception as e:
            # If activate_this.py fails, try adding venv site-packages to path
            if sys.platform == 'win32':
                site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
            else:
                site_packages = os.path.join(venv_path, 'lib', 'python{}.{}'.format(
                    sys.version_info.major, sys.version_info.minor), 'site-packages')
            
            if os.path.exists(site_packages) and site_packages not in sys.path:
                sys.path.insert(0, site_packages)
    else:
        # Fallback: add venv site-packages to path directly
        if sys.platform == 'win32':
            site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
        else:
            site_packages = os.path.join(venv_path, 'lib', 'python{}.{}'.format(
                sys.version_info.major, sys.version_info.minor), 'site-packages')
        
        if os.path.exists(site_packages) and site_packages not in sys.path:
            sys.path.insert(0, site_packages)

# Set environment variables for the application
# These are set here because mod_wsgi doesn't automatically pick up SetEnv from Apache config
os.environ.setdefault('MQTT_HOST', '192.168.56.101')
os.environ.setdefault('MQTT_PORT', '1883')
os.environ.setdefault('DB_HOST', '127.0.0.1')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'root')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_NAME', 'ilmuwanutara_e2eewater')
os.environ.setdefault('FLASK_APP', 'app.py')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DB_ENCRYPTION_KEY', 'rxyJ__s_iQzXo49e-3Cju-Vh7nnNdlFW2KK-1c_0xKo=')

# Import the Flask application
try:
    # Log WSGI loading
    print(f"[WSGI] Loading app from {project_dir}", file=sys.stderr)
    print(f"[WSGI] MQTT_HOST env: {os.environ.get('MQTT_HOST', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] MQTT_PORT env: {os.environ.get('MQTT_PORT', 'NOT SET')}", file=sys.stderr)
    
    from app import app as application, start_mqtt_key_subscriber
    
    # Start MQTT key subscriber for Apache/mod_wsgi deployment
    # This is needed because the if __name__ == '__main__' block doesn't run under mod_wsgi
    print("[WSGI] Starting MQTT key subscriber...", file=sys.stderr)
    try:
        start_mqtt_key_subscriber()
        print("[WSGI] MQTT key subscriber started successfully", file=sys.stderr)
    except Exception as mqtt_err:
        # Log but don't fail - MQTT is optional
        import traceback
        print(f"[WSGI] MQTT subscriber start error (non-fatal): {mqtt_err}", file=sys.stderr)
        print(f"[WSGI] Traceback: {traceback.format_exc()}", file=sys.stderr)
    
except Exception as e:
    # Log error for debugging (check Apache error logs)
    import traceback
    error_msg = f"[WSGI] Failed to import app: {str(e)}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    raise

