#!/usr/bin/env python3
"""
MySQL Connection Diagnostic Tool
This script helps diagnose MySQL connection issues.
"""

import os
import sys

# Import MySQL connector
try:
    import mysql.connector
    from mysql.connector import Error, errorcode
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("Install it with: pip install mysql-connector-python")
    sys.exit(1)

# Get database configuration from environment or use defaults
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')

def test_connection():
    """Test MySQL connection with detailed error reporting."""
    print("=" * 60)
    print("MySQL Connection Diagnostic Tool")
    print("=" * 60)
    print(f"\nConnection Parameters:")
    print(f"  Host:     {DB_HOST}")
    print(f"  Port:     {DB_PORT}")
    print(f"  User:     {DB_USER}")
    print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(empty)'}")
    print(f"  Database: {DB_NAME}")
    print("\n" + "-" * 60)
    
    # Test 1: Check if MySQL service is running
    print("\n[1] Testing basic connection to MySQL server...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connection_timeout=5
        )
        print("✓ Successfully connected to MySQL server!")
        
        # Get MySQL version
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"  MySQL Version: {version[0] if version else 'Unknown'}")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"✗ Failed to connect to MySQL server!")
        print(f"  Error Code: {e.errno}")
        print(f"  Error Message: {e.msg}")
        
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("\n  → SOLUTION: Wrong username or password.")
            print("    1. Check your MySQL root password")
            print("    2. Try resetting MySQL root password if needed")
            print("    3. Or set DB_USER and DB_PASSWORD environment variables")
        elif e.errno == 2003:  # Can't connect to MySQL server
            print("\n  → SOLUTION: MySQL service is not running or not accessible.")
            print("    On Windows:")
            print("    1. Open Services (services.msc)")
            print("    2. Find 'MySQL' service")
            print("    3. Right-click and select 'Start'")
            print("    4. Or run: net start MySQL (as Administrator)")
        elif e.errno == 2005:  # Unknown MySQL server host
            print("\n  → SOLUTION: Hostname cannot be resolved.")
            print("    Try using '127.0.0.1' instead of 'localhost'")
        else:
            print(f"\n  → Check MySQL error logs for more details")
        return False
    
    # Test 2: Check if database exists
    print("\n[2] Checking if database exists...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connection_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"✓ Database '{DB_NAME}' exists!")
        else:
            print(f"✗ Database '{DB_NAME}' does not exist.")
            print(f"  → SOLUTION: The database will be created automatically when you run the app.")
            print(f"     Or create it manually: CREATE DATABASE {DB_NAME};")
    except Error as e:
        print(f"✗ Error checking database: {e.msg}")
        return False
    
    # Test 3: Test connection to specific database
    print("\n[3] Testing connection to specific database...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=5
        )
        print(f"✓ Successfully connected to database '{DB_NAME}'!")
        
        # List tables
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if tables:
            print(f"  Found {len(tables)} table(s):")
            for table in tables:
                print(f"    - {table[0]}")
        else:
            print("  No tables found (database is empty)")
            print("  → The app will create tables automatically on first run")
    except Error as e:
        print(f"✗ Failed to connect to database '{DB_NAME}'!")
        print(f"  Error: {e.msg}")
        if e.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"  → SOLUTION: Database '{DB_NAME}' does not exist.")
            print(f"     It will be created automatically when you run the app.")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All connection tests passed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

