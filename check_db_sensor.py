#!/usr/bin/env python3
"""
Check sensor information in the database, including public key status.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from db import get_pool

def check_sensor(device_id):
    pool = get_pool()
    if pool is None:
        print("❌ Cannot connect to database")
        return
    
    try:
        conn = pool.get_connection()
        cur = conn.cursor(dictionary=True)
        
        # Get all sensors with this device_id
        cur.execute(
            """
            SELECT id, device_id, device_type, location, status, user_id, 
                   public_key IS NOT NULL as has_public_key,
                   LENGTH(public_key) as public_key_length,
                   registered_at
            FROM sensors 
            WHERE device_id = %s
            ORDER BY user_id
            """,
            (device_id,)
        )
        
        sensors = cur.fetchall()
        cur.close()
        conn.close()
        
        if not sensors:
            print(f"❌ No sensors found with device_id: {device_id}")
            return
        
        print(f"\n📊 Found {len(sensors)} sensor(s) with device_id: {device_id}\n")
        
        for sensor in sensors:
            print(f"  Sensor ID: {sensor['id']}")
            print(f"  Device Type: {sensor['device_type']}")
            print(f"  Location: {sensor['location']}")
            print(f"  Status: {sensor['status']}")
            print(f"  User ID: {sensor['user_id']}")
            print(f"  Has Public Key: {'✅ YES' if sensor['has_public_key'] else '❌ NO'}")
            if sensor['has_public_key']:
                print(f"  Public Key Length: {sensor['public_key_length']} characters")
            print(f"  Registered At: {sensor['registered_at']}")
            print()
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    device_id = sys.argv[1] if len(sys.argv) > 1 else 'ph01'
    print(f"Checking sensor: {device_id}")
    check_sensor(device_id)

