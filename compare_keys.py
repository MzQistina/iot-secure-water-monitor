#!/usr/bin/env python3
"""
Compare public keys from database vs filesystem to find mismatches.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_pool

def compare_keys(device_id, user_id):
    pool = get_pool()
    if pool is None:
        print("❌ Cannot connect to database")
        return
    
    try:
        conn = pool.get_connection()
        cur = conn.cursor(dictionary=True)
        
        # Get sensor from database
        cur.execute(
            """
            SELECT device_id, user_id, public_key
            FROM sensors 
            WHERE device_id = %s AND user_id = %s
            LIMIT 1
            """,
            (device_id, user_id)
        )
        
        sensor = cur.fetchone()
        cur.close()
        conn.close()
        
        if not sensor:
            print(f"❌ Sensor {device_id} for user {user_id} not found in database")
            return
        
        db_key = sensor['public_key']
        if not db_key:
            print(f"❌ No public key in database for {device_id} (user {user_id})")
            return
        
        print(f"✅ Database public key found ({len(db_key)} chars)")
        print(f"   First 50 chars: {db_key[:50]}...")
        
        # Check filesystem keys
        base_dir = os.path.dirname(__file__)
        
        # Check user_keys
        user_key_path = os.path.join(base_dir, "user_keys", str(user_id), f"{device_id}_public.pem")
        if os.path.exists(user_key_path):
            with open(user_key_path, 'r') as f:
                file_key = f.read().strip()
            print(f"\n✅ Found user_keys file ({len(file_key)} chars)")
            print(f"   First 50 chars: {file_key[:50]}...")
            
            if db_key.strip() == file_key:
                print("\n✅ MATCH: Database key matches user_keys file")
            else:
                print("\n❌ MISMATCH: Database key does NOT match user_keys file")
                print("   This is the problem! The keys don't match.")
        
        # Check sensor_keys
        sensor_key_path = os.path.join(base_dir, "sensor_keys", str(user_id), device_id, "sensor_public.pem")
        if os.path.exists(sensor_key_path):
            with open(sensor_key_path, 'r') as f:
                file_key2 = f.read().strip()
            print(f"\n✅ Found sensor_keys file ({len(file_key2)} chars)")
            print(f"   First 50 chars: {file_key2[:50]}...")
            
            if db_key.strip() == file_key2:
                print("\n✅ MATCH: Database key matches sensor_keys file")
            else:
                print("\n❌ MISMATCH: Database key does NOT match sensor_keys file")
        
        # Check legacy location
        legacy_path = os.path.join(base_dir, "sensor_keys", device_id, "sensor_public.pem")
        if os.path.exists(legacy_path):
            with open(legacy_path, 'r') as f:
                file_key3 = f.read().strip()
            print(f"\n✅ Found legacy sensor_keys file ({len(file_key3)} chars)")
            print(f"   First 50 chars: {file_key3[:50]}...")
            
            if db_key.strip() == file_key3:
                print("\n✅ MATCH: Database key matches legacy file")
            else:
                print("\n❌ MISMATCH: Database key does NOT match legacy file")
        
        print("\n💡 Solution:")
        print("   The client's private key must match the public key in the database.")
        print("   If they don't match, you need to:")
        print("   1. Generate a new key pair (or use the existing one that matches)")
        print("   2. Upload the public key to the server")
        print("   3. Use the matching private key on the client")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    device_id = sys.argv[1] if len(sys.argv) > 1 else 'ph01'
    user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(f"Comparing keys for {device_id} (user {user_id})\n")
    compare_keys(device_id, user_id)

