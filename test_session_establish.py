#!/usr/bin/env python3
"""
Test script to simulate session establishment for ph01.
This helps diagnose why ph01 fails to establish a session.
"""

import sys
import os
import requests
import base64
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

def test_session_establish(device_id, server_url, private_key_path):
    """Test session establishment process."""
    server_url = server_url.rstrip('/')
    
    print(f"Testing session establishment for {device_id}")
    print(f"Server: {server_url}")
    print(f"Private key: {private_key_path}\n")
    
    # Check if private key exists
    if not os.path.exists(private_key_path):
        print(f"❌ Private key not found: {private_key_path}")
        return False
    
    # Load private key
    try:
        with open(private_key_path, 'rb') as f:
            private_key = RSA.import_key(f.read())
        print("✅ Private key loaded")
    except Exception as e:
        print(f"❌ Failed to load private key: {e}")
        return False
    
    # Step 1: Request challenge
    print("\n1. Requesting challenge...")
    try:
        response = requests.get(
            f"{server_url}/api/device/session/request",
            params={"device_id": device_id},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to request challenge: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        challenge_data = response.json()
        challenge_id = challenge_data.get('challenge_id')
        challenge = challenge_data.get('challenge')
        
        print(f"✅ Challenge received")
        print(f"   Challenge ID: {challenge_id}")
        print(f"   Challenge: {challenge[:50]}...")
    except Exception as e:
        print(f"❌ Error requesting challenge: {e}")
        return False
    
    # Step 2: Sign challenge
    print("\n2. Signing challenge...")
    try:
        h = SHA256.new(challenge.encode('utf-8'))
        signature = pkcs1_15.new(private_key).sign(h)
        signature_b64 = base64.b64encode(signature).decode()
        print(f"✅ Challenge signed")
        print(f"   Signature length: {len(signature_b64)} chars")
    except Exception as e:
        print(f"❌ Error signing challenge: {e}")
        return False
    
    # Step 3: Establish session
    print("\n3. Establishing session...")
    try:
        payload = {
            "device_id": device_id,
            "challenge_id": challenge_id,
            "signature": signature_b64
        }
        
        response = requests.post(
            f"{server_url}/api/device/session/establish",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            session_data = response.json()
            print(f"✅ Session established successfully!")
            print(f"   Session token: {session_data.get('session_token')[:50]}...")
            print(f"   Expires in: {session_data.get('expires_in_seconds')} seconds")
            return True
        else:
            print(f"❌ Failed to establish session: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Try to parse error message
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"\n   Error details: {error_msg}")
            except:
                pass
            
            return False
    except Exception as e:
        print(f"❌ Error establishing session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python test_session_establish.py <device_id> <server_url> <private_key_path>")
        print("\nExample:")
        print("  python test_session_establish.py ph01 http://10.0.2.2 sensor_keys/5/ph01/sensor_private.pem")
        sys.exit(1)
    
    device_id = sys.argv[1]
    server_url = sys.argv[2]
    private_key_path = sys.argv[3]
    
    success = test_session_establish(device_id, server_url, private_key_path)
    
    if not success:
        print("\n💡 Troubleshooting:")
        print("   1. Check server logs for detailed error messages")
        print("   2. Verify the public key is stored in the database")
        print("   3. Ensure the private key matches the public key on the server")
        print("   4. Check that the sensor is active in the database")
        sys.exit(1)

