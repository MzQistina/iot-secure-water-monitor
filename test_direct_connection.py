#!/usr/bin/env python3
"""
Test direct connection to MySQL server
This tests if remote MySQL access is available
"""

import mysql.connector
import sys

print("=" * 60)
print("Testing Direct Connection to MySQL Server")
print("=" * 60)
print("Host: ilmuwanutara.my")
print("Port: 3306")
print("User: ilmuwanutara_e2eewater")
print("Database: ilmuwanutara_e2eewater")
print("-" * 60)
print("\n🔍 Attempting connection...\n")

try:
    conn = mysql.connector.connect(
        host='ilmuwanutara.my',
        port=3306,
        user='ilmuwanutara_e2eewater',
        password='e2eeWater@2025',
        database='ilmuwanutara_e2eewater',
        connection_timeout=10
    )
    
    print("✅ SUCCESS! Direct connection works!")
    print("\n📊 Database Information:")
    
    cursor = conn.cursor()
    
    # Get database info
    cursor.execute("SELECT DATABASE(), VERSION(), NOW()")
    result = cursor.fetchone()
    print(f"   Database: {result[0]}")
    print(f"   Version: {result[1]}")
    print(f"   Server Time: {result[2]}")
    
    # Get tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n📋 Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Remote MySQL access is available!")
    print("You can update Docker to use direct connection.")
    print("=" * 60)
    sys.exit(0)
    
except mysql.connector.Error as e:
    print(f"❌ MySQL Connection Failed: {e}")
    print("\n" + "=" * 60)
    print("⚠️  Remote MySQL access is NOT available")
    print("\nOptions:")
    print("1. Deploy to production server (recommended)")
    print("   - Upload via FTP to e2eewater.ilmuwanutara.my")
    print("   - Use localhost database connection")
    print("   - No Docker needed")
    print("\n2. Contact hosting to grant remote MySQL access")
    print("   - Ask them to allow connections from your IP")
    print("=" * 60)
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

