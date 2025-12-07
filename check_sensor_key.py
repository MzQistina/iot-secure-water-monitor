#!/usr/bin/env python3
"""
Diagnostic script to check if a sensor's public key exists on the server.
This helps diagnose why ph01 (or any sensor) might fail to establish a session.

Usage:
    python check_sensor_key.py ph01 http://10.0.2.2
"""

import sys
import requests
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python check_sensor_key.py <device_id> <server_url>")
        print("Example: python check_sensor_key.py ph01 http://10.0.2.2")
        sys.exit(1)
    
    device_id = sys.argv[1]
    server_url = sys.argv[2].rstrip('/')
    
    print(f"Checking public key status for sensor: {device_id}")
    print(f"Server: {server_url}\n")
    
    # Check if we can access the diagnostic endpoint (requires login)
    # For now, check local filesystem
    print("Checking local filesystem for public keys...")
    
    base_dir = os.path.dirname(__file__)
    
    # Check user_keys directory
    user_keys_dir = os.path.join(base_dir, "user_keys")
    if os.path.exists(user_keys_dir):
        for user_id_dir in os.listdir(user_keys_dir):
            user_path = os.path.join(user_keys_dir, user_id_dir)
            if os.path.isdir(user_path):
                key_file = os.path.join(user_path, f"{device_id}_public.pem")
                if os.path.exists(key_file):
                    print(f"✅ Found: user_keys/{user_id_dir}/{device_id}_public.pem")
                    with open(key_file, 'r') as f:
                        key_content = f.read()
                        print(f"   Key length: {len(key_content)} characters")
    
    # Check sensor_keys directory
    sensor_keys_dir = os.path.join(base_dir, "sensor_keys")
    if os.path.exists(sensor_keys_dir):
        # Check user-specific folders
        for item in os.listdir(sensor_keys_dir):
            item_path = os.path.join(sensor_keys_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a user_id folder with device subfolder
                device_path = os.path.join(item_path, device_id)
                if os.path.isdir(device_path):
                    key_file = os.path.join(device_path, "sensor_public.pem")
                    if os.path.exists(key_file):
                        print(f"✅ Found: sensor_keys/{item}/{device_id}/sensor_public.pem")
                        with open(key_file, 'r') as f:
                            key_content = f.read()
                            print(f"   Key length: {len(key_content)} characters")
        
        # Check legacy location
        legacy_path = os.path.join(sensor_keys_dir, device_id, "sensor_public.pem")
        if os.path.exists(legacy_path):
            print(f"✅ Found: sensor_keys/{device_id}/sensor_public.pem")
            with open(legacy_path, 'r') as f:
                key_content = f.read()
                print(f"   Key length: {len(key_content)} characters")
    
    print("\n💡 If no keys found, you need to:")
    print("   1. Generate keys: python simulators/sensor/sensor_keygen.py --device-id ph01 --user-id 5")
    print("   2. Upload public key to server (via web interface or MQTT)")
    print("   3. Ensure the private key exists on the client: sensor_keys/5/ph01/sensor_private.pem")

if __name__ == '__main__':
    main()

