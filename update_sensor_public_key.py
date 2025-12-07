#!/usr/bin/env python3
"""
Update sensor's public key in database from user_keys file.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_pool

def update_sensor_public_key(device_id, user_id, public_key_file):
    """Update sensor's public key in database."""
    if not os.path.exists(public_key_file):
        print(f"❌ Public key file not found: {public_key_file}")
        return False
    
    # Read public key
    with open(public_key_file, 'r') as f:
        public_key = f.read().strip()
    
    print(f"✅ Read public key from: {public_key_file}")
    print(f"   Key length: {len(public_key)} characters")
    
    # Update database
    pool = get_pool()
    if pool is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn = pool.get_connection()
        cur = conn.cursor()
        
        # Update the sensor's public key
        cur.execute(
            """
            UPDATE sensors
            SET public_key = %s
            WHERE device_id = %s AND user_id = %s
            """,
            (public_key, device_id, user_id)
        )
        
        if cur.rowcount == 0:
            print(f"❌ No sensor found with device_id='{device_id}' and user_id={user_id}")
            conn.rollback()
            cur.close()
            conn.close()
            return False
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Successfully updated public key for {device_id} (user {user_id}) in database")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python update_sensor_public_key.py <device_id> <user_id> <public_key_file>")
        print("\nExample:")
        print("  python update_sensor_public_key.py ph01 5 user_keys/5/ph01_public.pem")
        sys.exit(1)
    
    device_id = sys.argv[1]
    user_id = int(sys.argv[2])
    public_key_file = sys.argv[3]
    
    print(f"Updating public key for {device_id} (user {user_id})")
    print(f"Using key from: {public_key_file}\n")
    
    success = update_sensor_public_key(device_id, user_id, public_key_file)
    
    if success:
        print("\n✅ Database updated successfully!")
        print("   ph01 should now be able to establish a session.")
    else:
        print("\n❌ Failed to update database.")
        sys.exit(1)

