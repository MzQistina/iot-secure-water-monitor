#!/usr/bin/env python3
"""
Raspberry Pi Client for Secure Water Monitor

This script handles:
1. Session establishment (challenge-response authentication)
2. Secure data submission with session tokens
3. Automatic session renewal
4. Public key upload for registration

Usage:
    python raspberry_pi_client.py <device_id> <server_url>
    
    # Upload public key only:
    python raspberry_pi_client.py <device_id> <server_url> --upload-key

Example:
    python raspberry_pi_client.py pH01 http://192.168.1.100:5000
    python raspberry_pi_client.py pH01 http://192.168.1.100:5000 --upload-key
"""

import os
import sys
import json
import base64
import hashlib
import time
import requests
import argparse
from typing import Optional
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Import encryption utilities (adjust path as needed)
# If running on Pi, copy encryption_utils.py to the same directory
try:
    from encryption_utils import encrypt_data
except ImportError:
    print("Error: encryption_utils.py not found. Copy it to the Raspberry Pi.")
    sys.exit(1)


def find_key_file(device_id: str, key_type: str = "public") -> Optional[str]:
    """Find a key file for a device, checking both old structure and user folders.
    
    Args:
        device_id: Device/sensor ID
        key_type: "public" or "private"
    
    Returns:
        Path to key file if found, None otherwise
    """
    base_dir = os.path.dirname(__file__)
    sensor_keys_dir = os.path.join(base_dir, "sensor_keys")
    
    # Try old structure first: sensor_keys/{device_id}/sensor_{key_type}.pem
    possible_paths = [
        os.path.join(base_dir, "sensor_keys", device_id, f"sensor_{key_type}.pem"),
        os.path.join("sensor_keys", device_id, f"sensor_{key_type}.pem"),
        os.path.join(os.getcwd(), "sensor_keys", device_id, f"sensor_{key_type}.pem"),
    ]
    
    # Check old structure paths
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Check user folders: sensor_keys/{user_id}/{device_id}/sensor_{key_type}.pem
    if os.path.exists(sensor_keys_dir):
        try:
            for user_folder in os.listdir(sensor_keys_dir):
                user_path = os.path.join(sensor_keys_dir, user_folder)
                if os.path.isdir(user_path):
                    device_path = os.path.join(user_path, device_id, f"sensor_{key_type}.pem")
                    if os.path.exists(device_path):
                        return device_path
        except Exception:
            pass
    
    return None


def upload_public_key(device_id: str, server_url: str) -> bool:
    """Upload the public key to the server for registration."""
    server_url = server_url.rstrip('/')
    
    # Find public key file (checks both old structure and user folders)
    public_key_path = find_key_file(device_id, "public")
    
    if not public_key_path:
        print(f"❌ Error: Public key not found!")
        print(f"   Searched in:")
        print(f"     - sensor_keys/{device_id}/sensor_public.pem (old structure)")
        print(f"     - sensor_keys/*/{device_id}/sensor_public.pem (user folders)")
        print(f"\n   Make sure the file exists in one of these locations")
        return False
    
    print(f"✅ Found public key at: {public_key_path}")
    print(f"[Key Upload] Uploading public key for device '{device_id}' to {server_url}...")
    
    try:
        # Step 1: Get upload token
        print("[Step 1] Getting upload token...")
        token_url = f"{server_url}/api/key_upload_token_open"
        token_response = requests.post(
            token_url,
            json={"device_id": device_id},
            timeout=10
        )
        
        if not token_response.ok:
            print(f"❌ Failed to get upload token: {token_response.status_code}")
            print(f"   Response: {token_response.text}")
            print(f"   Check:")
            print(f"   - Server is running at {server_url}")
            print(f"   - Network connectivity")
            return False
        
        token_data = token_response.json()
        upload_url = token_data.get('upload_url')
        if not upload_url:
            print(f"❌ No upload_url in token response: {token_data}")
            return False
        
        print(f"✅ Token obtained")
        print(f"[Step 2] Uploading key file...")
        
        # Step 2: Upload the public key file
        with open(public_key_path, 'rb') as f:
            files = {
                'public_key_file': (os.path.basename(public_key_path), f, 'application/octet-stream')
            }
            data = {
                'device_id': device_id
            }
            upload_response = requests.post(upload_url, data=data, files=files, timeout=15)
        
        if upload_response.ok:
            result = upload_response.json()
            print(f"✅ SUCCESS! Public key uploaded successfully!")
            print(f"   Response: {result}")
            print(f"\n📝 Next steps:")
            print(f"   1. Go to the sensor registration page")
            print(f"   2. Enter device_id: {device_id}")
            print(f"   3. The key should auto-fill in the textarea")
            return True
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: Cannot reach server at {server_url}")
        print(f"   Check:")
        print(f"   - Server is running")
        print(f"   - Network connectivity")
        print(f"   - Server URL is correct")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Server did not respond in time")
        return False
    except Exception as e:
        print(f"❌ Error uploading key: {e}")
        import traceback
        traceback.print_exc()
        return False


class DeviceSessionManager:
    """Manages device session lifecycle."""
    
    def __init__(self, device_id: str, server_url: str, private_key_path: str):
        self.device_id = device_id
        self.server_url = server_url.rstrip('/')
        self.private_key_path = private_key_path
        self.session_token: Optional[str] = None
        self.counter = 0
        self.session_expires_at: Optional[float] = None
        
    def sign_data(self, data_bytes: bytes) -> str:
        """Sign data bytes with device's private key."""
        if not os.path.exists(self.private_key_path):
            raise FileNotFoundError(f"Private key not found: {self.private_key_path}")
        
        private_key = RSA.import_key(open(self.private_key_path, "rb").read())
        h = SHA256.new(data_bytes)
        signature = pkcs1_15.new(private_key).sign(h)
        return base64.b64encode(signature).decode()
    
    def request_challenge(self) -> dict:
        """Request a session challenge from the server."""
        url = f"{self.server_url}/api/device/session/request"
        params = {"device_id": self.device_id}
        
        print(f"[Session] Requesting challenge for device '{self.device_id}'...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Failed to request challenge: {response.status_code} - {response.text}")
        
        return response.json()
    
    def establish_session(self, challenge_id: str, challenge: str) -> dict:
        """Establish a session by signing the challenge."""
        print(f"[Session] Signing challenge and establishing session...")
        
        # Sign the challenge
        signature = self.sign_data(challenge.encode('utf-8'))
        
        url = f"{self.server_url}/api/device/session/establish"
        payload = {
            "device_id": self.device_id,
            "challenge_id": challenge_id,
            "signature": signature
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Failed to establish session: {response.status_code} - {response.text}")
        
        data = response.json()
        self.session_token = data.get('session_token')
        expires_in = data.get('expires_in_seconds', 900)
        self.session_expires_at = time.time() + expires_in
        self.counter = 0  # Reset counter for new session
        
        print(f"[Session] ✅ Session established (expires in {expires_in}s)")
        return data
    
    def ensure_session(self) -> bool:
        """Ensure we have a valid session, establishing one if needed."""
        # Check if session exists and is not expired
        if self.session_token and self.session_expires_at:
            if time.time() < self.session_expires_at - 60:  # Renew if expires in < 1 minute
                return True
        
        # Need to establish new session
        try:
            challenge_data = self.request_challenge()
            self.establish_session(
                challenge_data['challenge_id'],
                challenge_data['challenge']
            )
            return True
        except Exception as e:
            print(f"[Session] ❌ Failed to establish session: {e}")
            return False
    
    def submit_reading(self, sensor_data: dict) -> bool:
        """Submit sensor reading with session token."""
        if not self.ensure_session():
            return False
        
        # Increment counter for this submission
        self.counter += 1
        
        # Add session info to data
        sensor_data['session_token'] = self.session_token
        sensor_data['counter'] = self.counter
        
        # Encrypt data using server's public key
        server_public_key_path = os.path.join(os.path.dirname(__file__), "keys", "public.pem")
        if not os.path.exists(server_public_key_path):
            print(f"[Error] Server public key not found at {server_public_key_path}")
            return False
        
        encrypted = encrypt_data(sensor_data, server_public_key_path)
        
        # Convert to base64 if needed
        encrypted_b64 = {
            key: base64.b64encode(value).decode() if isinstance(value, bytes) else value
            for key, value in encrypted.items()
        }
        
        # Add integrity hash
        data_json = json.dumps(sensor_data, sort_keys=True).encode()
        sha256_hash = hashlib.sha256(data_json).hexdigest()
        encrypted_b64["sha256"] = sha256_hash
        
        # Sign the payload
        signature_b64 = self.sign_data(data_json)
        encrypted_b64["sensor_id"] = self.device_id
        encrypted_b64["signature"] = signature_b64
        
        # Submit to server
        endpoint = f"{self.server_url}/submit-data"
        try:
            response = requests.post(endpoint, json=encrypted_b64, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[Submit] ✅ Reading submitted (counter={self.counter})")
                if result.get('safe_to_drink'):
                    print(f"         Water is safe to drink")
                else:
                    print(f"         ⚠️  Safety issues: {result.get('reasons', [])}")
                return True
            else:
                print(f"[Submit] ❌ Failed: {response.status_code} - {response.text}")
                # If session error, clear session to force re-establishment
                if response.status_code == 401:
                    self.session_token = None
                    self.session_expires_at = None
                return False
        except Exception as e:
            print(f"[Submit] ❌ Error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi client for secure water monitor')
    parser.add_argument('device_id', help='Device ID (e.g., pH01)')
    parser.add_argument('server_url', help='Server URL (e.g., http://192.168.1.100:5000)')
    parser.add_argument('--private-key', help='Path to private key file', 
                       default=None)
    parser.add_argument('--interval', type=int, default=60,
                       help='Reading interval in seconds (default: 60)')
    parser.add_argument('--once', action='store_true',
                       help='Submit one reading and exit')
    parser.add_argument('--upload-key', action='store_true',
                       help='Upload public key only and exit')
    
    args = parser.parse_args()
    
    device_id = args.device_id
    server_url = args.server_url
    
    # If upload-key flag is set, just upload and exit
    if args.upload_key:
        success = upload_public_key(device_id, server_url)
        sys.exit(0 if success else 1)
    
    # Determine private key path
    if args.private_key:
        private_key_path = args.private_key
    else:
        # Search for private key (checks both old structure and user folders)
        private_key_path = find_key_file(device_id, "private")
        if not private_key_path:
            # Fallback to old default path for error message
            private_key_path = os.path.join(
                os.path.dirname(__file__),
                "sensor_keys",
                device_id,
                "sensor_private.pem"
            )
    
    if not os.path.exists(private_key_path):
        print(f"❌ Error: Private key not found!")
        print(f"   Searched in:")
        print(f"     - sensor_keys/{device_id}/sensor_private.pem (old structure)")
        print(f"     - sensor_keys/*/{device_id}/sensor_private.pem (user folders)")
        print(f"   Generate keys first or specify with --private-key")
        sys.exit(1)
    
    # Create session manager
    session_mgr = DeviceSessionManager(device_id, server_url, private_key_path)
    
    print("=" * 70)
    print("Raspberry Pi Secure Water Monitor Client")
    print("=" * 70)
    print(f"Device ID: {device_id}")
    print(f"Server URL: {server_url}")
    print(f"Private Key: {private_key_path}")
    print(f"Interval: {args.interval} seconds")
    print("=" * 70)
    
    # Example: Read sensor data (replace with actual sensor reading code)
    def read_sensor_data():
        """Read actual sensor data - REPLACE THIS with your sensor reading code."""
        # This is a placeholder - replace with actual sensor reading
        import random
        return {
            "device_id": device_id,
            "device_type": "ph",  # Adjust based on your sensor
            "ph": round(random.uniform(6.5, 8.5), 2),
            "tds": random.randint(50, 500),
            "turbidity": round(random.uniform(0.0, 5.0), 2),
            "temperature": round(random.uniform(20.0, 30.0), 2),
        }
    
    try:
        if args.once:
            # Submit one reading
            data = read_sensor_data()
            session_mgr.submit_reading(data)
        else:
            # Continuous mode
            print("\n[Mode] Continuous readings (Ctrl+C to stop)\n")
            while True:
                data = read_sensor_data()
                session_mgr.submit_reading(data)
                time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
