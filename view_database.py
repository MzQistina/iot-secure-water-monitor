#!/usr/bin/env python3
"""
View Database Data on PythonAnywhere
Run this script from Bash console: python3.10 view_database.py
"""
import os
import sys

# Add project directory to path if needed
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Import database connection
try:
    from connect import get_connection, close_connection
    USE_CONNECT = True
    print("Using connect.py for database connection")
except ImportError:
    USE_CONNECT = False
    try:
        import mysql.connector
        print("Using mysql.connector directly")
    except ImportError:
        print("ERROR: mysql.connector not available. Install with: pip install mysql-connector-python")
        sys.exit(1)

def get_conn():
    """Get database connection."""
    if USE_CONNECT:
        return get_connection()
    else:
        # Get credentials from environment or use defaults
        DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
        DB_USER = os.getenv('DB_USER', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')
        DB_PORT = int(os.getenv('DB_PORT', '3306'))
        
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

def close_conn(conn):
    """Close database connection."""
    if USE_CONNECT:
        close_connection(conn)
    else:
        conn.close()

def view_tables():
    """View all tables in database."""
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("\n" + "="*60)
    print("DATABASE TABLES")
    print("="*60)
    for table in tables:
        print(f"  • {table[0]}")
    
    cursor.close()
    close_conn(conn)
    return [t[0] for t in tables]

def view_table_structure(table_name):
    """View table structure."""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        print(f"\n{'='*60}")
        print(f"TABLE STRUCTURE: {table_name.upper()}")
        print("="*60)
        print(f"{'Field':<20} {'Type':<20} {'Null':<6} {'Key':<6} {'Default'}")
        print("-" * 60)
        for col in columns:
            field, type_, null, key, default, extra = col[:6]
            default_str = str(default) if default is not None else 'NULL'
            print(f"{field:<20} {type_:<20} {null:<6} {key:<6} {default_str}")
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        cursor.close()
        close_conn(conn)

def view_table_data(table_name, limit=10):
    """View data from a specific table."""
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        print(f"\n{'='*60}")
        print(f"TABLE: {table_name.upper()} (showing {len(rows)} rows)")
        print("="*60)
        
        if rows:
            # Print column headers
            columns = list(rows[0].keys())
            header = " | ".join(col[:15].ljust(15) for col in columns)
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in rows:
                values = [str(row.get(col, ''))[:15].ljust(15) for col in columns]
                print(" | ".join(values))
        else:
            print("  (No data)")
            
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        cursor.close()
        close_conn(conn)

def view_counts():
    """View record counts for all tables."""
    conn = get_conn()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("RECORD COUNTS")
    print("="*60)
    
    # Get all tables first
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:25} : {count:,} records")
        except Exception as e:
            print(f"  {table:25} : (error: {str(e)[:30]})")
    
    cursor.close()
    close_conn(conn)

def view_database_info():
    """View database connection information."""
    print("\n" + "="*60)
    print("DATABASE CONNECTION INFO")
    print("="*60)
    
    if USE_CONNECT:
        from connect import DB_HOST, DB_PORT, DB_USER, DB_NAME
        print(f"  Host     : {DB_HOST}")
        print(f"  Port     : {DB_PORT}")
        print(f"  User     : {DB_USER}")
        print(f"  Database : {DB_NAME}")
        print(f"  Method   : Using connect.py")
    else:
        DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
        DB_PORT = os.getenv('DB_PORT', '3306')
        DB_USER = os.getenv('DB_USER', 'root')
        DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')
        print(f"  Host     : {DB_HOST}")
        print(f"  Port     : {DB_PORT}")
        print(f"  User     : {DB_USER}")
        print(f"  Database : {DB_NAME}")
        print(f"  Method   : Direct mysql.connector")

def main():
    """Main function."""
    print("\n" + "="*60)
    print("DATABASE VIEWER")
    print("="*60)
    
    try:
        # Show database info
        view_database_info()
        
        # View all tables
        tables = view_tables()
        
        if not tables:
            print("\n⚠️  No tables found in database.")
            print("   Run your database initialization script to create tables.")
            return
        
        # View counts
        view_counts()
        
        # Ask user which table to view (optional - can be automated)
        print("\n" + "="*60)
        print("TABLE DATA PREVIEW")
        print("="*60)
        print("Showing first 10 rows from each table:\n")
        
        # View data from each table
        for table in tables:
            view_table_structure(table)
            view_table_data(table, limit=10)
            print()
        
        print("="*60)
        print("✅ Done!")
        print("="*60)
        print("\nTip: Run this script anytime to view your database data.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  1. Check database credentials in environment variables")
        print("  2. Ensure database exists")
        print("  3. Verify network connectivity to database host")

if __name__ == "__main__":
    main()





