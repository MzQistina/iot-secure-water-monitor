#!/usr/bin/env python3
"""
Test database connection and check for users
"""
import sys
import os

# Set environment variables to match app.wsgi
os.environ.setdefault('DB_HOST', 'ilmuwanutara.my')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'ilmuwanutara_e2eewater')
os.environ.setdefault('DB_PASSWORD', 'e2eeWater@2025')
os.environ.setdefault('DB_NAME', 'ilmuwanutara_e2eewater')

print("=" * 60)
print("Testing Database Connection and User Credentials")
print("=" * 60)
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")
print(f"DB_PASSWORD: {'*' * len(os.environ.get('DB_PASSWORD', ''))}")
print("=" * 60)

try:
    # Try using connect.py first
    print("\n[1] Testing connection using connect.py...")
    import connect
    if connect.test_connection():
        print("✅ Connection successful using connect.py")
        
        # Get connection and check users
        conn = connect.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user_cred table exists
        cursor.execute("SHOW TABLES LIKE 'user_cred'")
        table_exists = cursor.fetchone()
        if table_exists:
            print("✅ user_cred table exists")
            
            # Get all users
            cursor.execute("SELECT sr_no, username, email, name FROM user_cred LIMIT 10")
            users = cursor.fetchall()
            print(f"\n[2] Found {len(users)} user(s) in database:")
            for user in users:
                print(f"   - ID: {user['sr_no']}, Username: {user['username']}, Email: {user['email']}, Name: {user['name']}")
            
            # Test get_user_by_username function
            print("\n[3] Testing get_user_by_username function...")
            from db import get_user_by_username
            if users:
                test_username = users[0]['username']
                print(f"   Testing with username: {test_username}")
                user = get_user_by_username(test_username)
                if user:
                    print(f"   ✅ Found user: {user.get('username')} (ID: {user.get('sr_no')})")
                    print(f"   Password hash exists: {bool(user.get('password'))}")
                else:
                    print(f"   ❌ User not found using get_user_by_username()")
        else:
            print("❌ user_cred table does not exist!")
        
        cursor.close()
        connect.close_connection(conn)
    else:
        print("❌ Connection failed using connect.py")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)

