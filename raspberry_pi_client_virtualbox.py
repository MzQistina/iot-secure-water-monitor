#!/usr/bin/env python3
"""
Raspberry Pi Client for Secure Water Monitor - VirtualBox Version

This version uses realistic sensor simulation instead of random data,
perfect for testing in VirtualBox where physical sensors cannot be connected.

Usage:
    python raspberry_pi_client_virtualbox.py <device_id> <server_url>
    
Example:
    python raspberry_pi_client_virtualbox.py pH01 http://10.0.2.2:5000
"""

import os
import sys
import json
import base64
import hashlib
import time
import math
import random
import requests
import argparse
from typing import Optional
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Import encryption utilities
try:
    from encryption_utils import encrypt_data
except ImportError:
    print("Error: encryption_utils.py not found. Copy it to the Raspberry Pi.")
    sys.exit(1)


def find_key_file(device_id: str, key_type: str = "public") -> Optional[str]:
    """Find a key file for a device, checking both old structure and user folders."""
    base_dir = os.path.dirname(__file__)
    sensor_keys_dir = os.path.join(base_dir, "sensor_keys")
    
    # Try old structure first
    possible_paths = [
        os.path.join(base_dir, "sensor_keys", device_id, f"sensor_{key_type}.pem"),
        os.path.join("sensor_keys", device_id, f"sensor_{key_type}.pem"),
        os.path.join(os.getcwd(), "sensor_keys", device_id, f"sensor_{key_type}.pem"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Check user folders
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
    
    public_key_path = find_key_file(device_id, "public")
    
    if not public_key_path:
        print(f"❌ Error: Public key not found!")
        return False
    
    print(f"✅ Found public key at: {public_key_path}")
    print(f"[Key Upload] Uploading public key for device '{device_id}' to {server_url}...")
    
    try:
        token_url = f"{server_url}/api/key_upload_token_open"
        token_response = requests.post(
            token_url,
            json={"device_id": device_id},
            timeout=10
        )
        
        if not token_response.ok:
            print(f"❌ Failed to get upload token: {token_response.status_code}")
            return False
        
        token_data = token_response.json()
        upload_url = token_data.get('upload_url')
        if not upload_url:
            print(f"❌ No upload_url in token response")
            return False
        
        with open(public_key_path, 'rb') as f:
            files = {
                'public_key_file': (os.path.basename(public_key_path), f, 'application/octet-stream')
            }
            data = {'device_id': device_id}
            upload_response = requests.post(upload_url, data=data, files=files, timeout=15)
        
        if upload_response.ok:
            print(f"✅ SUCCESS! Public key uploaded successfully!")
            return True
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading key: {e}")
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
        self.counter = 0
        
        print(f"[Session] ✅ Session established (expires in {expires_in}s)")
        return data
    
    def ensure_session(self) -> bool:
        """Ensure we have a valid session, establishing one if needed."""
        if self.session_token and self.session_expires_at:
            if time.time() < self.session_expires_at - 60:
                return True
        
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
        
        self.counter += 1
        
        sensor_data['session_token'] = self.session_token
        sensor_data['counter'] = self.counter
        
        server_public_key_path = os.path.join(os.path.dirname(__file__), "keys", "public.pem")
        if not os.path.exists(server_public_key_path):
            print(f"[Error] Server public key not found at {server_public_key_path}")
            return False
        
        encrypted = encrypt_data(sensor_data, server_public_key_path)
        
        encrypted_b64 = {
            key: base64.b64encode(value).decode() if isinstance(value, bytes) else value
            for key, value in encrypted.items()
        }
        
        data_json = json.dumps(sensor_data, sort_keys=True).encode()
        sha256_hash = hashlib.sha256(data_json).hexdigest()
        encrypted_b64["sha256"] = sha256_hash
        
        signature_b64 = self.sign_data(data_json)
        encrypted_b64["sensor_id"] = self.device_id
        encrypted_b64["signature"] = signature_b64
        
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
                if response.status_code == 401:
                    self.session_token = None
                    self.session_expires_at = None
                return False
        except Exception as e:
            print(f"[Submit] ❌ Error: {e}")
            return False


# Global state for realistic simulation
sensor_state = {}


def read_sensor_data_realistic(device_id: str, device_type: str = "ph") -> dict:
    """
    Generate realistic sensor readings with proper patterns.
    
    Features:
    - Gradual changes (not random jumps)
    - Daily temperature cycles
    - Correlations between sensors (temperature affects TDS)
    - Realistic value ranges
    """
    global sensor_state
    
    # Initialize state on first call
    if device_id not in sensor_state:
        sensor_state[device_id] = {
            'ph_base': random.uniform(6.8, 7.5),
            'ph_trend': 0.0,
            'tds_base': random.randint(150, 300),
            'temperature': random.uniform(22.0, 26.0),
            'turbidity_base': random.uniform(1.0, 2.5),
            'last_update': time.time(),
            'cycle_offset': random.uniform(0, 24)  # Random start time for daily cycle
        }
    
    state = sensor_state[device_id]
    current_time = time.time()
    elapsed = current_time - state['last_update']
    
    # Simulate realistic pH (slow drift with small variations)
    state['ph_trend'] += random.uniform(-0.003, 0.003)
    state['ph_trend'] = max(-0.2, min(0.2, state['ph_trend']))
    ph_value = state['ph_base'] + state['ph_trend'] + random.uniform(-0.05, 0.05)
    ph_value = max(6.5, min(8.5, ph_value))
    
    # Temperature with daily cycle (warmer during day, cooler at night)
    hour = ((current_time / 3600) % 24) + state['cycle_offset']
    temp_variation = 2.5 * math.sin((hour - 6) * math.pi / 12)
    temperature = 24.0 + temp_variation + random.uniform(-0.3, 0.3)
    state['temperature'] = temperature
    
    # TDS varies with temperature and has some natural variation
    temp_factor = (temperature - 24.0) * 1.2
    tds_value = state['tds_base'] + temp_factor + random.randint(-5, 5)
    tds_value = max(100, min(400, tds_value))
    
    # Turbidity correlates with TDS and has slow changes
    turbidity = state['turbidity_base'] + (tds_value - state['tds_base']) / 200 + random.uniform(-0.1, 0.1)
    turbidity = max(0.5, min(4.0, turbidity))
    
    state['last_update'] = current_time
    
    # Build data dict based on device type
    data = {
        "device_id": device_id,
        "device_type": device_type,
    }
    
    # Add readings based on device type
    if device_type == "ph":
        data["ph"] = round(ph_value, 2)
        data["temperature"] = round(temperature, 2)
    elif device_type == "tds":
        data["tds"] = round(tds_value, 0)
        data["temperature"] = round(temperature, 2)
    elif device_type == "turbidity":
        data["turbidity"] = round(turbidity, 2)
        data["temperature"] = round(temperature, 2)
    elif device_type == "temperature":
        data["temperature"] = round(temperature, 2)
    else:
        # Multi-sensor device - include all readings
        data["ph"] = round(ph_value, 2)
        data["tds"] = round(tds_value, 0)
        data["turbidity"] = round(turbidity, 2)
        data["temperature"] = round(temperature, 2)
    
    return data


def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi client for secure water monitor (VirtualBox version)')
    parser.add_argument('device_id', help='Device ID (e.g., pH01)')
    parser.add_argument('server_url', help='Server URL (e.g., http://10.0.2.2:5000)')
    parser.add_argument('--private-key', help='Path to private key file', default=None)
    parser.add_argument('--interval', type=int, default=60, help='Reading interval in seconds (default: 60)')
    parser.add_argument('--once', action='store_true', help='Submit one reading and exit')
    parser.add_argument('--upload-key', action='store_true', help='Upload public key only and exit')
    parser.add_argument('--device-type', default='ph', help='Device type: ph, tds, turbidity, temperature (default: ph)')
    
    args = parser.parse_args()
    
    device_id = args.device_id
    server_url = args.server_url
    
    if args.upload_key:
        success = upload_public_key(device_id, server_url)
        sys.exit(0 if success else 1)
    
    if args.private_key:
        private_key_path = args.private_key
    else:
        private_key_path = find_key_file(device_id, "private")
        if not private_key_path:
            private_key_path = os.path.join(
                os.path.dirname(__file__),
                "sensor_keys",
                device_id,
                "sensor_private.pem"
            )
    
    if not os.path.exists(private_key_path):
        print(f"❌ Error: Private key not found!")
        print(f"   Searched in: sensor_keys/{device_id}/sensor_private.pem")
        print(f"   Generate keys first or specify with --private-key")
        sys.exit(1)
    
    session_mgr = DeviceSessionManager(device_id, server_url, private_key_path)
    
    print("=" * 70)
    print("Raspberry Pi Secure Water Monitor Client (VirtualBox - Realistic Simulation)")
    print("=" * 70)
    print(f"Device ID: {device_id}")
    print(f"Device Type: {args.device_type}")
    print(f"Server URL: {server_url}")
    print(f"Private Key: {private_key_path}")
    print(f"Interval: {args.interval} seconds")
    print("=" * 70)
    print("⚠️  Using realistic simulation (VirtualBox cannot access physical sensors)")
    print("=" * 70)
    
    try:
        if args.once:
            data = read_sensor_data_realistic(device_id, args.device_type)
            print(f"\n[Reading] Generated: {data}")
            session_mgr.submit_reading(data)
        else:
            print("\n[Mode] Continuous readings (Ctrl+C to stop)\n")
            while True:
                data = read_sensor_data_realistic(device_id, args.device_type)
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

