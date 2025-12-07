#!/usr/bin/env python3
"""
Test script for device session functionality.

This script demonstrates:
1. Requesting a session challenge
2. Establishing a session by signing the challenge
3. Submitting data with a session token
4. Testing error cases

Usage:
    python test_device_session.py <sensor_id> [server_url]
    
Example:
    python test_device_session.py pH01 http://localhost:5000
"""

import os
import sys
import json
import base64
import requests
import argparse
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Add project root to path
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from encryption_utils import encrypt_data


def sign_challenge(challenge: str, private_key_path: str) -> str:
    """Sign a challenge string with the device's private key."""
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Private key not found: {private_key_path}")
    
    private_key = RSA.import_key(open(private_key_path, "rb").read())
    h = SHA256.new(challenge.encode('utf-8'))
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()


def sign_payload_bytes(payload_bytes: bytes, private_key_path: str) -> str:
    """Sign payload bytes with the device's private key."""
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Private key not found: {private_key_path}")
    
    private_key = RSA.import_key(open(private_key_path, "rb").read())
    h = SHA256.new(payload_bytes)
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()


def request_session_challenge(device_id: str, server_url: str) -> dict:
    """Request a session challenge from the server."""
    url = f"{server_url}/api/device/session/request"
    params = {"device_id": device_id}
    
    print(f"\n[1] Requesting session challenge for device '{device_id}'...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Failed to request challenge: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ Challenge received:")
    print(f"   Challenge ID: {data.get('challenge_id')}")
    print(f"   Challenge: {data.get('challenge')[:50]}...")
    print(f"   Expires in: {data.get('expires_in_seconds')} seconds")
    return data


def establish_session(device_id: str, challenge_id: str, challenge: str, 
                     private_key_path: str, server_url: str) -> dict:
    """Establish a session by signing the challenge."""
    print(f"\n[2] Signing challenge and establishing session...")
    
    signature = sign_challenge(challenge, private_key_path)
    
    url = f"{server_url}/api/device/session/establish"
    payload = {
        "device_id": device_id,
        "challenge_id": challenge_id,
        "signature": signature
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to establish session: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ Session established:")
    print(f"   Session Token: {data.get('session_token')[:50]}...")
    print(f"   Device ID: {data.get('device_id')}")
    print(f"   Expires in: {data.get('expires_in_seconds')} seconds")
    return data


def submit_data_with_session(sensor_id: str, session_token: str, counter: int,
                             server_url: str, private_key_path: str) -> bool:
    """Submit sensor data with a session token."""
    print(f"\n[3] Submitting data with session token (counter={counter})...")
    
    # Create sample sensor data
    data = {
        "device_id": sensor_id,
        "device_type": "ph",  # Adjust based on your sensor type
        "ph": 7.2,
        "tds": 150,
        "turbidity": 0.5,
        "temperature": 25.0,
        "session_token": session_token,
        "counter": counter
    }
    
    # Encrypt data using server's public key
    public_key_path = os.path.join(PROJECT_ROOT, "keys", "public.pem")
    encrypted = encrypt_data(data, public_key_path)
    
    # Convert to base64 if needed
    encrypted_b64 = {
        key: base64.b64encode(value).decode() if isinstance(value, bytes) else value
        for key, value in encrypted.items()
    }
    
    # Add integrity hash
    import hashlib
    data_json = json.dumps(data, sort_keys=True).encode()
    sha256_hash = hashlib.sha256(data_json).hexdigest()
    encrypted_b64["sha256"] = sha256_hash
    
    # Sign the payload (must sign the bytes, not the string)
    signature = sign_payload_bytes(data_json, private_key_path)
    encrypted_b64["sensor_id"] = sensor_id
    encrypted_b64["signature"] = signature
    
    # Submit to server
    endpoint = f"{server_url}/submit-data"
    response = requests.post(endpoint, json=encrypted_b64)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Data submitted successfully:")
        print(f"   Status: {result.get('status')}")
        print(f"   Safe to drink: {result.get('safe_to_drink')}")
        if result.get('reasons'):
            print(f"   Issues: {result.get('reasons')}")
        return True
    else:
        print(f"❌ Failed to submit data: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_error_cases(device_id: str, server_url: str, private_key_path: str):
    """Test various error cases."""
    print(f"\n[4] Testing error cases...")
    
    # Test 1: Invalid device ID
    print("\n   Test 4a: Invalid device ID")
    response = requests.get(f"{server_url}/api/device/session/request", 
                          params={"device_id": "invalid_device_12345"})
    if response.status_code == 403:
        print("   ✅ Correctly rejected invalid device")
    else:
        print(f"   ❌ Unexpected response: {response.status_code}")
    
    # Test 2: Expired challenge (simulate by using old challenge)
    print("\n   Test 4b: Expired challenge")
    # Request a challenge
    challenge_data = request_session_challenge(device_id, server_url)
    if challenge_data:
        # Wait a moment, then try to establish with wrong challenge_id
        import time
        print("   Waiting 2 seconds...")
        time.sleep(2)
        # Use wrong challenge_id
        response = requests.post(
            f"{server_url}/api/device/session/establish",
            json={
                "device_id": device_id,
                "challenge_id": "invalid_challenge_id",
                "signature": sign_challenge(challenge_data['challenge'], private_key_path)
            }
        )
        if response.status_code in (400, 410):
            print("   ✅ Correctly rejected invalid/expired challenge")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description='Test device session functionality')
    parser.add_argument('sensor_id', help='Sensor device ID (e.g., pH01)')
    parser.add_argument('server_url', nargs='?', default='http://localhost:5000',
                       help='Server URL (default: http://localhost:5000)')
    parser.add_argument('--skip-errors', action='store_true',
                       help='Skip error case testing')
    
    args = parser.parse_args()
    
    sensor_id = args.sensor_id
    server_url = args.server_url.rstrip('/')
    
    # Check if private key exists
    private_key_path = os.path.join(PROJECT_ROOT, "sensor_keys", sensor_id, "sensor_private.pem")
    if not os.path.exists(private_key_path):
        print(f"❌ Error: Private key not found at {private_key_path}")
        print(f"   Generate keys first using: python simulators/sensor/sensor_keygen.py {sensor_id}")
        sys.exit(1)
    
    print("=" * 70)
    print("Device Session Test")
    print("=" * 70)
    print(f"Sensor ID: {sensor_id}")
    print(f"Server URL: {server_url}")
    print(f"Private Key: {private_key_path}")
    
    try:
        # Step 1: Request challenge
        challenge_data = request_session_challenge(sensor_id, server_url)
        if not challenge_data:
            print("\n❌ Failed to get challenge. Make sure:")
            print("   1. The sensor is registered and active in the database")
            print("   2. The server is running")
            print("   3. The sensor's public key is registered")
            sys.exit(1)
        
        # Step 2: Establish session
        session_data = establish_session(
            sensor_id,
            challenge_data['challenge_id'],
            challenge_data['challenge'],
            private_key_path,
            server_url
        )
        if not session_data:
            print("\n❌ Failed to establish session")
            sys.exit(1)
        
        session_token = session_data['session_token']
        
        # Step 3: Submit data with session (multiple times to test counter)
        print("\n" + "=" * 70)
        print("Submitting multiple readings with session...")
        print("=" * 70)
        
        for counter in range(1, 4):
            success = submit_data_with_session(
                sensor_id, session_token, counter, server_url, private_key_path
            )
            if not success:
                print(f"\n❌ Failed to submit data with counter={counter}")
                break
            import time
            time.sleep(1)  # Small delay between submissions
        
        # Step 4: Test error cases
        if not args.skip_errors:
            print("\n" + "=" * 70)
            print("Testing Error Cases")
            print("=" * 70)
            test_error_cases(sensor_id, server_url, private_key_path)
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

