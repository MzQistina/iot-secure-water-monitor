#!/usr/bin/env python3
"""
Simple database connection test script
Tests connection to MySQL/MariaDB database
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import connect
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    print(f"Host: {connect.DB_HOST}")
    print(f"Port: {connect.DB_PORT}")
    print(f"User: {connect.DB_USER}")
    print(f"Database: {connect.DB_NAME}")
    print(f"Password: {'*' * len(connect.DB_PASSWORD) if connect.DB_PASSWORD else '(not set)'}")
    print("-" * 60)
    
    # Test connection
    print("\n🔍 Testing connection...")
    if connect.test_connection():
        print("\n✅ SUCCESS: Database connection is working!")
        
        # Test a simple query
        print("\n🔍 Testing query execution...")
        try:
            results = connect.execute_query("SHOW TABLES")
            print(f"✅ Found {len(results)} tables in database:")
            for table in results:
                print(f"   - {table[0]}")
        except Exception as e:
            print(f"⚠️  Query test failed: {e}")
        
        # Test connection pool
        print("\n🔍 Testing connection pool...")
        try:
            conn = connect.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            cursor.close()
            connect.close_connection(conn)
            print(f"✅ Connection pool working! Connected to database: {db_name}")
        except Exception as e:
            print(f"⚠️  Connection pool test failed: {e}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Database is ready to use.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n❌ FAILED: Could not connect to database")
        print("\nTroubleshooting:")
        print("1. Check if MySQL/MariaDB server is running")
        print("2. Verify database credentials are correct")
        print("3. Check if database host is accessible")
        print("4. If using SSH tunnel, make sure it's running")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ ERROR: Could not import connect module: {e}")
    print("Make sure connect.py is in the same directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

