#!/usr/bin/env python3
"""
Quick script to check sensor_data table structure
"""
import mysql.connector
import os

# Get database credentials from environment variables
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'water_monitor')

def check_table_structure():
    try:
        print(f"Connecting to MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor()
        
        # Get table structure
        print("\n" + "="*80)
        print("sensor_data Table Structure")
        print("="*80)
        
        cur.execute("DESCRIBE sensor_data")
        columns = cur.fetchall()
        
        # Print header
        print(f"{'Field':<20} {'Type':<30} {'Null':<8} {'Key':<8} {'Default':<15} {'Extra'}")
        print("-"*80)
        
        # Print each column
        for col in columns:
            field, type_, null, key, default, extra = col
            default_str = str(default) if default is not None else 'NULL'
            key_str = key if key else ''
            extra_str = extra if extra else ''
            print(f"{field:<20} {type_:<30} {null:<8} {key_str:<8} {default_str:<15} {extra_str}")
        
        print("="*80)
        
        # Check for new columns
        column_names = [col[0] for col in columns]
        has_user_id = 'user_id' in column_names
        has_device_id = 'device_id' in column_names
        
        print("\nColumn Check:")
        print(f"  ✓ user_id column exists: {has_user_id}")
        print(f"  ✓ device_id column exists: {has_device_id}")
        
        if has_user_id and has_device_id:
            print("\n✅ Migration successful! Both user_id and device_id columns are present.")
        else:
            print("\n⚠️  Migration may not have run yet. Restart Apache to trigger migration.")
        
        # Check data
        cur.execute("SELECT COUNT(*) FROM sensor_data")
        total_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sensor_data WHERE user_id IS NOT NULL")
        with_user_id = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sensor_data WHERE device_id IS NOT NULL")
        with_device_id = cur.fetchone()[0]
        
        print(f"\nData Statistics:")
        print(f"  Total records: {total_count}")
        print(f"  Records with user_id: {with_user_id}")
        print(f"  Records with device_id: {with_device_id}")
        
        cur.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_table_structure()

