# PythonAnywhere WSGI Configuration File
# Copy this content to your WSGI file in PythonAnywhere
# File location: /var/www/yourusername_pythonanywhere_com_wsgi.py

import sys
import os

# Add your project directory to Python path
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

# ============================================
# DATABASE CONFIGURATION
# ============================================
# Replace these with your PythonAnywhere MySQL details
# You can find these in the "Databases" tab after creating a database

os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_PASSWORD'] = 'your-database-password-here'
os.environ['DB_NAME'] = 'yourusername$ilmuwanutara_e2eewater'
os.environ['DB_TYPE'] = 'mysql'

# ============================================
# FLASK CONFIGURATION
# ============================================
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'
os.environ['PYTHONUNBUFFERED'] = '1'

# ============================================
# ENCRYPTION KEY (if needed)
# ============================================
# Uncomment and set if you use db_encryption.py
# os.environ['DB_ENCRYPTION_KEY'] = 'your-encryption-key-here'

# ============================================
# MQTT CONFIGURATION (if needed)
# ============================================
# Uncomment and set if you use MQTT
# os.environ['MQTT_HOST'] = 'your-mqtt-host'
# os.environ['MQTT_PORT'] = '1883'
# os.environ['MQTT_USERNAME'] = 'your-mqtt-username'
# os.environ['MQTT_PASSWORD'] = 'your-mqtt-password'

# ============================================
# CHANGE WORKING DIRECTORY
# ============================================
os.chdir(path)

# ============================================
# IMPORT FLASK APP
# ============================================
from app import app as application

# ============================================
# OPTIONAL: START MQTT SUBSCRIBER
# ============================================
# Uncomment if you need MQTT listener to start automatically
# try:
#     from mqtt_listener import start_mqtt_key_subscriber
#     start_mqtt_key_subscriber()
# except Exception as e:
#     print(f"MQTT subscriber error (non-fatal): {e}")

# ============================================
# NOTES:
# ============================================
# 1. Replace 'yourusername' with your actual PythonAnywhere username
# 2. Replace 'your-database-password-here' with your MySQL database password
# 3. The database name format is: username$database_name
# 4. After making changes, click "Reload" in the Web tab
# 5. Check "Error log" if you encounter issues

