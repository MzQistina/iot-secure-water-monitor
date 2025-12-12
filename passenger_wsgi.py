# Passenger WSGI file for hosting providers that support Passenger (like cPanel)
# This file is used when deploying Flask apps on shared hosting

import sys
import os

# Add your project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask app
from app import app as application

# Optional: Set environment variables if not set in hosting control panel
if not os.getenv('DB_HOST'):
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_USER'] = 'ilmuwanutara_e2eewater'
    os.environ['DB_PASSWORD'] = 'e2eeWater@2025'
    os.environ['DB_NAME'] = 'ilmuwanutara_e2eewater'
    os.environ['DB_TYPE'] = 'mysql'
    os.environ['FLASK_ENV'] = 'production'

if __name__ == "__main__":
    application.run()

