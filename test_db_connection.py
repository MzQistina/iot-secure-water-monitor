#!/usr/bin/env python3
"""Test database connection and display connection status."""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from db import get_pool, DB_HOST, DB_PORT, DB_USER, DB_NAME

def test_db_connection():
    """Test database connection and display results."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', '')) if os.getenv('DB_PASSWORD') else '(empty)'}")
    print("-" * 60)
    
    try:
        print("Attempting to connect to database...")
        pool = get_pool()
        
        if pool is None:
            print("❌ FAILED: Connection pool is None")
            print("\nPossible issues:")
            print("1. MySQL server is not running")
            print("2. Incorrect database credentials")
            print("3. Database does not exist and could not be created")
            print("4. Network connectivity issues")
            return False
        
        print("✅ Connection pool created successfully")
        
        # Test getting a connection from the pool
        print("\nTesting connection from pool...")
        conn = pool.get_connection()
        print("✅ Successfully obtained connection from pool")
        
        # Test a simple query
        print("\nTesting database query...")
        cur = conn.cursor()
        cur.execute("SELECT DATABASE(), VERSION()")
        result = cur.fetchone()
        if result:
            current_db, version = result
            print(f"✅ Query successful!")
            print(f"   Current database: {current_db}")
            print(f"   MySQL version: {version}")
        
        # Check if tables exist
        print("\nChecking database tables...")
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()
        if tables:
            print(f"✅ Found {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No tables found (database may be empty)")
        
        cur.close()
        conn.close()
        print("\n✅ Connection test completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        return False

if __name__ == '__main__':
    success = test_db_connection()
    sys.exit(0 if success else 1)

