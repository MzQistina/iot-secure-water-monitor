#!/usr/bin/env python3
"""
Multi-Sensor Client for Secure Water Monitor

This script simulates multiple sensors simultaneously, sending data from all
specified sensors at regular intervals.

Usage:
    # Simulate all registered sensors
    python multi_sensor_client.py --all http://192.168.1.100:5000

    # Simulate specific sensors
    python multi_sensor_client.py --ids pH01,tds01,turb01 http://192.168.1.100:5000

    # Simulate with custom interval
    python multi_sensor_client.py --ids pH01,tds01 --interval 30 http://192.168.1.100:5000
"""

import os
import sys
import json
import base64
import hashlib
import time
import requests
import argparse
import random
import threading
from typing import Optional, List
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Import encryption utilities
try:
    from encryption_utils import encrypt_data
except ImportError:
    print("Error: encryption_utils.py not found. Copy it to the Raspberry Pi.")
    sys.exit(1)


class DeviceSessionManager:
    """Manages device session lifecycle."""
    
    def __init__(self, device_id: str, server_url: str, private_key_path: str, user_id: Optional[str] = None):
        self.device_id = device_id
        self.user_id = user_id
        self.server_url = server_url.rstrip('/')
        self.private_key_path = private_key_path
        self.session_token: Optional[str] = None
        self.counter = 0
        self.session_expires_at: Optional[float] = None
        self.lock = threading.Lock()  # Thread-safe session management
    
    def _get_display_id(self) -> str:
        """Get display identifier for logging (includes user_id if available)."""
        if self.user_id:
            return f"{self.device_id} (user:{self.user_id})"
        return self.device_id
        
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
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"Failed to request challenge: {response.status_code} - {response.text}")
            
            return response.json()
        except requests.exceptions.ConnectTimeout:
            raise Exception(f"Connection timeout: Server at {self.server_url} is not responding. Check if server is running and accessible.")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: Cannot reach server at {self.server_url}. Error: {e}")
    
    def establish_session(self, challenge_id: str, challenge: str) -> dict:
        """Establish a session by signing the challenge."""
        signature = self.sign_data(challenge.encode('utf-8'))
        
        url = f"{self.server_url}/api/device/session/establish"
        payload = {
            "device_id": self.device_id,
            "challenge_id": challenge_id,
            "signature": signature
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"Failed to establish session: {response.status_code} - {response.text}")
            
            data = response.json()
            with self.lock:
                self.session_token = data.get('session_token')
                expires_in = data.get('expires_in_seconds', 900)
                self.session_expires_at = time.time() + expires_in
                self.counter = 0
            
            return data
        except requests.exceptions.ConnectTimeout:
            raise Exception(f"Connection timeout: Server at {self.server_url} is not responding.")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: Cannot reach server at {self.server_url}. Error: {e}")
    
    def ensure_session(self) -> bool:
        """Ensure we have a valid session, establishing one if needed."""
        with self.lock:
            if self.session_token and self.session_expires_at:
                if time.time() < self.session_expires_at - 60:  # Renew if expires in < 1 minute
                    return True
        
        # Need to establish new session - retry with exponential backoff
        max_retries = 3
        base_delay = 0.5  # Start with 0.5 seconds
        
        for attempt in range(max_retries):
            try:
                challenge_data = self.request_challenge()
                self.establish_session(
                    challenge_data['challenge_id'],
                    challenge_data['challenge']
                )
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 0.5s, 1s, 2s
                    delay = base_delay * (2 ** attempt)
                    print(f"[{self._get_display_id()}] ⚠️  Session establishment failed (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    # Last attempt failed
                    print(f"[{self._get_display_id()}] ❌ Failed to establish session after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def submit_reading(self, sensor_data: dict) -> bool:
        """Submit sensor reading with session token."""
        if not self.ensure_session():
            return False
        
        with self.lock:
            self.counter += 1
            current_token = self.session_token
            current_counter = self.counter
        
        # Add session info to data
        sensor_data['session_token'] = current_token
        sensor_data['counter'] = current_counter
        
        # Encrypt data using server's public key
        server_public_key_path = os.path.join(os.path.dirname(__file__), "keys", "public.pem")
        if not os.path.exists(server_public_key_path):
            print(f"[{self._get_display_id()}] Error: Server public key not found at {server_public_key_path}")
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
                safe_status = "✅ Safe" if result.get('safe_to_drink') else "⚠️ Unsafe"
                print(f"[{self._get_display_id()}] ✅ Reading #{current_counter} submitted - {safe_status}")
                return True
            else:
                error_text = response.text[:200] if response.text else "No error message"
                print(f"[{self._get_display_id()}] ❌ Failed: {response.status_code} - {error_text}")
                # Check for device_type mismatch error specifically
                if "device_type mismatch" in error_text.lower():
                    print(f"[{self._get_display_id()}] 💡 Tip: Check that device_type in database matches the sensor type")
                    print(f"[{self._get_display_id()}]    Payload device_type: {sensor_data.get('device_type', 'N/A')}")
                # If session error, clear session to force re-establishment
                if response.status_code == 401:
                    with self.lock:
                        self.session_token = None
                        self.session_expires_at = None
                return False
        except Exception as e:
            print(f"[{self._get_display_id()}] ❌ Error: {e}")
            return False


def read_sensor_data(device_id: str, device_type: str, location: Optional[str] = None, mode: str = "safe") -> dict:
    """Generate simulated sensor data based on device type.
    
    Modes:
    - "safe": Values within safe thresholds (default)
    - "unsafe": Values outside safe thresholds (dangerous/unsafe)
    
    Safe thresholds:
    - pH: 6.5-8.5
    - TDS: 0-500 mg/L
    - Turbidity: 0-5 NTU
    - Temperature: 0-35 °C
    - Dissolved Oxygen: 5-14 mg/L
    - Conductivity: 0-500 µS/cm
    - Ammonia: 0-0.5 mg/L
    - Pressure: 0-700 kPa
    - Nitrate/Nitrite: 0-10 mg/L
    - ORP: 250-400 mV
    - Chlorine: 0.2-1.0 mg/L
    - Salinity: 0-35 ppt
    - Flow: 0-100 L/min
    """
    import random
    
    # Base data structure
    # Normalize device_type to lowercase and strip whitespace to match server validation
    normalized_device_type = str(device_type).lower().strip()
    data = {
        "device_id": device_id,
        "device_type": normalized_device_type,
    }
    
    # Add location if provided (from server)
    if location:
        data["location"] = location
    
    # Generate values based on device type
    device_type_lower = device_type.lower()
    
    if mode == "unsafe":
        # Generate unsafe values (outside thresholds)
        if device_type_lower == "ph":
            # Very low or very high pH
            data["ph"] = round(random.choice([random.uniform(2.0, 6.0), random.uniform(9.0, 12.0)]), 2)
        elif device_type_lower == "tds":
            data["tds"] = random.randint(1200, 3000)  # Very high TDS
        elif device_type_lower == "turbidity":
            data["turbidity"] = round(random.uniform(6.0, 15.0), 2)  # Very high turbidity
        elif device_type_lower == "temperature":
            data["temperature"] = round(random.uniform(36.0, 50.0), 2)  # Very high temperature
        elif device_type_lower == "dissolved_oxygen":
            data["dissolved_oxygen"] = round(random.uniform(0.1, 4.5), 2)  # Very low DO
        elif device_type_lower == "conductivity":
            data["conductivity"] = round(random.uniform(750.0, 2500.0), 1)  # Very high conductivity
        elif device_type_lower == "ammonia":
            data["ammonia"] = round(random.uniform(1.0, 10.0), 2)  # Very high ammonia
        elif device_type_lower == "pressure":
            data["pressure"] = round(random.uniform(750.0, 1000.0), 2)  # Very high pressure
        elif device_type_lower == "nitrate":
            data["nitrate"] = round(random.uniform(15.0, 50.0), 2)  # Very high nitrate
        elif device_type_lower == "nitrite":
            data["nitrite"] = round(random.uniform(15.0, 50.0), 2)  # Very high nitrite
        elif device_type_lower == "orp":
            # Very low or very high ORP
            data["orp"] = random.choice([random.randint(0, 200), random.randint(450, 600)])
        elif device_type_lower == "chlorine":
            # Very low or very high chlorine
            data["chlorine"] = round(random.choice([random.uniform(0.0, 0.1), random.uniform(1.5, 3.0)]), 2)
        elif device_type_lower == "salinity":
            data["salinity"] = round(random.uniform(40.0, 50.0), 2)  # Very high salinity
        elif device_type_lower == "flow":
            data["flow"] = round(random.uniform(120.0, 200.0), 2)  # Very high flow
        else:
            # Default: extreme pH
            data["ph"] = round(random.choice([random.uniform(2.0, 6.0), random.uniform(9.0, 12.0)]), 2)
    else:
        # Generate safe values (within thresholds)
        if device_type_lower == "ph":
            data["ph"] = round(random.uniform(6.5, 8.5), 2)
        elif device_type_lower == "tds":
            data["tds"] = random.randint(0, 500)
        elif device_type_lower == "turbidity":
            data["turbidity"] = round(random.uniform(0.0, 5.0), 2)
        elif device_type_lower == "temperature":
            data["temperature"] = round(random.uniform(0.0, 35.0), 2)
        elif device_type_lower == "dissolved_oxygen":
            data["dissolved_oxygen"] = round(random.uniform(5.0, 14.0), 2)
        elif device_type_lower == "conductivity":
            data["conductivity"] = round(random.uniform(0.0, 500.0), 1)
        elif device_type_lower == "ammonia":
            data["ammonia"] = round(random.uniform(0.0, 0.5), 2)
        elif device_type_lower == "pressure":
            data["pressure"] = round(random.uniform(0.0, 700.0), 2)
        elif device_type_lower == "nitrate":
            data["nitrate"] = round(random.uniform(0.0, 10.0), 2)
        elif device_type_lower == "nitrite":
            data["nitrite"] = round(random.uniform(0.0, 10.0), 2)
        elif device_type_lower == "orp":
            data["orp"] = random.randint(250, 400)
        elif device_type_lower == "chlorine":
            data["chlorine"] = round(random.uniform(0.2, 1.0), 2)
        elif device_type_lower == "salinity":
            data["salinity"] = round(random.uniform(0.0, 35.0), 2)
        elif device_type_lower == "flow":
            data["flow"] = round(random.uniform(0.0, 100.0), 2)
        else:
            # Default: include common metrics (safe ranges)
            data["ph"] = round(random.uniform(6.5, 8.5), 2)
            data["tds"] = random.randint(0, 500)
            data["turbidity"] = round(random.uniform(0.0, 5.0), 2)
            data["temperature"] = round(random.uniform(0.0, 35.0), 2)
    
    return data


def find_private_key(device_id: str, base_dir: str, user_id: Optional[str] = None) -> Optional[str]:
    """Find private key file, checking both user-specific and global locations."""
    # Try user-specific location first (if user_id provided)
    if user_id:
        user_key_path = os.path.join(base_dir, "sensor_keys", str(user_id), device_id, "sensor_private.pem")
        if os.path.exists(user_key_path):
            return user_key_path
    
    # Try global location (legacy/fallback)
    global_key_path = os.path.join(base_dir, "sensor_keys", device_id, "sensor_private.pem")
    if os.path.exists(global_key_path):
        return global_key_path
    
    return None


def normalize_device_type(device_type: str) -> str:
    """Normalize device_type to match database format (lowercase, no spaces)."""
    if not device_type:
        return "ph"  # default
    normalized = str(device_type).lower().strip()
    # Handle common variations
    type_mapping = {
        "cond": "conductivity",
        "nitr": "nitrate",  # Will be handled by inference logic
        "chlor": "chlorine",
        "sal": "salinity",
    }
    # Check if it's a partial match that should be expanded
    for partial, full in type_mapping.items():
        if normalized.startswith(partial) and len(normalized) <= len(partial) + 2:
            return full
    return normalized


def get_device_info(device_id: str, base_dir: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get device information by checking for private key."""
    private_key_path = find_private_key(device_id, base_dir, user_id)
    
    if not private_key_path:
        return None
    
    # Try to infer device type from device_id
    device_type = "ph"  # default
    device_id_lower = device_id.lower()
    
    # Check for more specific patterns first to avoid false matches
    # Handle both full names and common abbreviations (e.g., "nit01", "con01", "ch01")
    # Order matters: check most specific/shortest patterns first
    
    # Check for nitrate/nitrite first (before other checks that might match "nit")
    if device_id_lower.startswith("nit"):
        # Short form like "nit01" - assume nitrate (more common than nitrite)
        if "nitrite" in device_id_lower:
            device_type = "nitrite"
        else:
            device_type = "nitrate"
    # Check for conductivity (before other checks that might match "con")
    elif device_id_lower.startswith("con"):
        # Short form like "con01" - assume conductivity
        device_type = "conductivity"
    # Check for chlorine (before "ph" check to avoid false matches)
    elif device_id_lower.startswith("ch") and len(device_id_lower) <= 4:
        # Short form like "ch01" - assume chlorine
        device_type = "chlorine"
    elif "chlor" in device_id_lower or "chlorine" in device_id_lower:
        device_type = "chlorine"
    # Check for pH (but not if it's chlorine)
    elif "ph" in device_id_lower and "chlor" not in device_id_lower and not device_id_lower.startswith("ch"):
        device_type = "ph"
    elif "tds" in device_id_lower:
        device_type = "tds"
    elif "turb" in device_id_lower:
        device_type = "turbidity"
    elif "temp" in device_id_lower:
        device_type = "temperature"
    elif "do" in device_id_lower or "oxygen" in device_id_lower or "dissolved" in device_id_lower:
        device_type = "dissolved_oxygen"
    elif "cond" in device_id_lower:
        device_type = "conductivity"
    elif "amm" in device_id_lower or "ammonia" in device_id_lower:
        device_type = "ammonia"
    elif "pres" in device_id_lower or "pressure" in device_id_lower:
        device_type = "pressure"
    elif "nitr" in device_id_lower:
        # Full form like "nitrate" or "nitrite"
        if "nitrite" in device_id_lower:
            device_type = "nitrite"
        else:
            device_type = "nitrate"
    elif "orp" in device_id_lower:
        device_type = "orp"
    elif "sal" in device_id_lower or "salinity" in device_id_lower:
        device_type = "salinity"
    elif "flow" in device_id_lower:
        device_type = "flow"
    
    # Normalize the inferred device_type
    normalized_type = normalize_device_type(device_type)
    
    return {
        "device_id": device_id,
        "device_type": normalized_type,
        "private_key_path": private_key_path
    }


def check_server_connectivity(server_url: str) -> bool:
    """Check if server is reachable and provide helpful diagnostics."""
    try:
        # Try to connect to a simple endpoint
        url = f"{server_url}/api/public/active_sensors"
        response = requests.get(url, timeout=5)
        return True  # Even if 404, server is reachable
    except requests.exceptions.ConnectTimeout:
        print(f"\n❌ Connection timeout: Cannot reach server at {server_url}")
        print("\n🔍 Troubleshooting steps:")
        print(f"   1. Verify the server is running: Open {server_url} in a browser")
        print(f"   2. Check the IP address is correct (not 10.0.2.2 for physical Pi)")
        print(f"   3. Test connectivity: ping <server_ip>")
        print(f"   4. Check firewall settings on the server")
        print(f"   5. Verify server is listening on the correct port (default: 5000)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error: Cannot reach server at {server_url}")
        print(f"   Error: {e}")
        print("\n🔍 Troubleshooting steps:")
        print(f"   1. Verify the server is running: Open {server_url} in a browser")
        print(f"   2. Check the IP address is correct")
        if "10.0.2.2" in server_url:
            print(f"   ⚠️  Note: 10.0.2.2 is typically a VirtualBox NAT IP.")
            print(f"      For a physical Raspberry Pi, use your Windows server's actual IP")
            print(f"      (e.g., 192.168.43.196 or your network's server IP)")
        print(f"   3. Test connectivity: ping <server_ip>")
        print(f"   4. Check firewall settings on the server")
        return False
    except Exception as e:
        print(f"⚠️  Warning: Could not verify server connectivity: {e}")
        return False


def fetch_active_sensors_from_server(server_url: str) -> List[dict]:
    """Fetch active sensors from server API."""
    try:
        # Try public endpoint first (if available)
        url = f"{server_url}/api/public/active_sensors"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sensors = data.get('active_sensors', [])
            if sensors:
                print(f"✅ Fetched {len(sensors)} sensors from server (public endpoint)")
            return sensors
        elif response.status_code == 404:
            # Public endpoint doesn't exist - that's okay, we'll use local keys
            pass
    except Exception as e:
        # Public endpoint might not be available - that's okay
        pass
    
    # Public endpoint returns empty or doesn't exist
    # This is expected - we'll infer device_type from device_id or use local keys
    return []


def find_available_sensors(base_dir: str, server_url: Optional[str] = None, location_filter: Optional[str] = None, user_id_filter: Optional[int] = None) -> List[dict]:
    """Find available sensors by checking server and local keys."""
    sensors = []
    
    # First, try to fetch active sensors from server
    server_sensors = []
    if server_url:
        server_sensors = fetch_active_sensors_from_server(server_url)
    
    # Map server sensors by device_id for quick lookup
    server_sensor_map = {s.get('device_id'): s for s in server_sensors}
    
    # If we have server sensors, use them to find matching local keys
    if server_sensors:
        for server_sensor in server_sensors:
            device_id = server_sensor.get('device_id')
            user_id = server_sensor.get('user_id')  # Get user_id from server if available
            
            if not device_id:
                continue
            
            # Filter by user_id if specified
            if user_id_filter is not None and user_id != user_id_filter:
                continue
            
            # Try to find private key (checks both user-specific and global locations)
            private_key_path = find_private_key(device_id, base_dir, user_id)
            
            if private_key_path:
                device_info = get_device_info(device_id, base_dir, user_id)
                if device_info:
                    # Merge server data - ALWAYS use server's device_type if provided
                    # This ensures we match what's in the database
                    server_device_type = server_sensor.get("device_type")
                    if server_device_type:
                        # Normalize device_type to match database format
                        normalized_server_type = normalize_device_type(server_device_type)
                        device_info["device_type"] = normalized_server_type
                        print(f"   Using server device_type '{normalized_server_type}' for {device_id}")
                    else:
                        # If server doesn't provide device_type, normalize the inferred one
                        inferred_type = device_info.get("device_type", "ph")
                        normalized_inferred = normalize_device_type(inferred_type)
                        device_info["device_type"] = normalized_inferred
                        print(f"   ⚠️  Server didn't provide device_type for {device_id}, using inferred: '{normalized_inferred}'")
                        print(f"   💡 Tip: Ensure device_type in database matches '{normalized_inferred}' for {device_id}")
                    device_info["location"] = server_sensor.get("location")
                    device_info["status"] = "active"
                    if user_id:
                        device_info["user_id"] = user_id
                    
                    # Filter by location if specified
                    if location_filter:
                        device_location = device_info.get("location", "")
                        if not device_location or device_location.lower() != location_filter.lower():
                            continue
                    
                    print(f"✅ Found sensor: {device_id} (user:{user_id}, location:{device_info.get('location')}, key:{private_key_path})")
                    sensors.append(device_info)
            else:
                print(f"⚠️  Warning: {device_id} (user:{user_id}) is active on server but no private key found locally")
                print(f"   Expected: sensor_keys/{user_id}/{device_id}/sensor_private.pem or sensor_keys/{device_id}/sensor_private.pem")
    else:
        # Fallback: scan local sensor_keys directory (legacy mode)
        sensor_keys_dir = os.path.join(base_dir, "sensor_keys")
        
        if not os.path.exists(sensor_keys_dir):
            print("⚠️  Warning: No local sensor keys found and could not fetch from server.")
            print("   Ensure sensor_keys/<user_id>/<device_id>/sensor_private.pem files exist.")
            return []
        
        # Check for user-specific folders first
        for item in os.listdir(sensor_keys_dir):
            item_path = os.path.join(sensor_keys_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a user_id folder (contains numeric subdirectories with device_ids)
                # or a direct device_id folder
                try:
                    # Try as user_id folder
                    user_id_test = int(item)
                    # Scan user folder for device folders
                    for device_folder in os.listdir(item_path):
                        device_path = os.path.join(item_path, device_folder)
                        if os.path.isdir(device_path):
                            private_key = os.path.join(device_path, "sensor_private.pem")
                            if os.path.exists(private_key):
                                device_info = get_device_info(device_folder, base_dir, item)
                                if device_info:
                                    sensors.append(device_info)
                except ValueError:
                    # Not a user_id, treat as direct device_id folder (legacy)
                    private_key = os.path.join(item_path, "sensor_private.pem")
                    if os.path.exists(private_key):
                        device_info = get_device_info(item, base_dir)
                        if device_info:
                            sensors.append(device_info)
    
    return sensors


def simulate_sensor(device_info: dict, server_url: str, interval: int, stop_event: threading.Event, mode: str = "safe"):
    """Simulate a single sensor in a separate thread."""
    device_id = device_info["device_id"]
    device_type = device_info["device_type"]
    private_key_path = device_info["private_key_path"]
    location = device_info.get("location")
    user_id = device_info.get("user_id")
    
    session_mgr = DeviceSessionManager(device_id, server_url, private_key_path, user_id)
    
    display_id = f"{device_id} (user:{user_id})" if user_id else device_id
    location_str = f", location: {location}" if location else ""
    user_str = f", user_id: {user_id}" if user_id else ""
    mode_str = f", mode: {mode}" if mode != "safe" else ""
    # Normalize device_type for display and ensure consistency
    normalized_type = str(device_type).lower().strip()
    print(f"[{display_id}] Starting simulation (type: {normalized_type}, interval: {interval}s{location_str}{user_str}{mode_str})")
    
    while not stop_event.is_set():
        try:
            # Ensure device_type is normalized before generating data
            normalized_type = str(device_type).lower().strip()
            sensor_data = read_sensor_data(device_id, normalized_type, location, mode=mode)
            session_mgr.submit_reading(sensor_data)
        except Exception as e:
            print(f"[{device_id}] ❌ Error: {e}")
            import traceback
            print(f"[{device_id}] Error details: {traceback.format_exc()}")
        
        # Wait for interval or until stop event
        stop_event.wait(timeout=interval)


def main():
    parser = argparse.ArgumentParser(
        description='Multi-sensor client for secure water monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simulate all active sensors from server (one location at a time recommended)
  python multi_sensor_client.py --all http://192.168.1.100:5000

  # Simulate sensors from a specific location only
  python multi_sensor_client.py --all --location "Building A" http://192.168.1.100:5000

  # Simulate specific sensors
  python multi_sensor_client.py --ids pH01,tds01,turb01 http://192.168.1.100:5000

  # Simulate specific sensor for a specific user (when multiple users have same device_id)
  python multi_sensor_client.py --ids ph01 --user-id 5 http://192.168.1.100:5000

  # Simulate with custom interval
  python multi_sensor_client.py --ids pH01,tds01 --interval 30 http://192.168.1.100:5000

  # Simulate with unsafe mode (values outside safe thresholds)
  python multi_sensor_client.py --all --mode unsafe http://192.168.1.100:5000
        """
    )
    
    parser.add_argument('server_url', help='Server URL (e.g., http://192.168.1.100:5000)')
    parser.add_argument('--ids', type=str, default='',
                       help='Comma-separated device IDs to simulate (e.g., pH01,tds01,turb01)')
    parser.add_argument('--all', action='store_true',
                       help='Simulate all available sensors')
    parser.add_argument('--interval', type=int, default=60,
                       help='Reading interval in seconds (default: 60)')
    parser.add_argument('--location', type=str, default='',
                       help='Simulate sensors from this location only (one location at a time)')
    parser.add_argument('--user-id', type=int, default=None,
                       help='Filter sensors by user ID (useful when multiple users have same device_id)')
    parser.add_argument('--mode', type=str, choices=['safe', 'unsafe'], default='safe',
                       help='Simulation mode: safe (within thresholds) or unsafe (outside thresholds)')
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(__file__)
    server_url = args.server_url.rstrip('/')
    
    # Check server connectivity first
    print(f"🔍 Checking server connectivity: {server_url}...")
    if not check_server_connectivity(server_url):
        print("\n❌ Cannot connect to server. Please fix the connection issue and try again.")
        sys.exit(1)
    print(f"✅ Server is reachable\n")
    
    # Find available sensors (checks server for active sensors)
    location_filter = args.location.strip() if args.location else None
    user_id_filter = args.user_id
    available_sensors = find_available_sensors(base_dir, server_url, location_filter, user_id_filter)
    
    if not available_sensors:
        if location_filter:
            print(f"❌ No active sensors found at location '{location_filter}'.")
            print("   Available locations can be checked on the server dashboard.")
        else:
            print("❌ No active sensors found.")
            print("   Ensure:")
            print("   1. Sensors are registered and active on the server")
            print("   2. sensor_keys/<device_id>/sensor_private.pem files exist")
        sys.exit(1)
    
    # Select sensors to simulate
    if args.all:
        selected_sensors = available_sensors
    elif args.ids:
        requested_ids = [x.strip() for x in args.ids.split(',') if x.strip()]
        # If user_id filter is specified, match by device_id AND user_id
        # Otherwise, match by device_id only (may get multiple if same device_id for different users)
        if user_id_filter is not None:
            id_to_sensor = {s["device_id"]: s for s in available_sensors if s.get("user_id") == user_id_filter}
        else:
            id_to_sensor = {s["device_id"]: s for s in available_sensors}
        
        selected_sensors = []
        for device_id in requested_ids:
            matching = [s for s in available_sensors if s["device_id"].lower() == device_id.lower()]
            if matching:
                if user_id_filter is not None:
                    # Filter by user_id if specified
                    matching = [s for s in matching if s.get("user_id") == user_id_filter]
                if matching:
                    # If multiple matches and no user_id filter, warn user
                    if len(matching) > 1 and user_id_filter is None:
                        print(f"⚠️  Warning: Multiple sensors found for '{device_id}':")
                        for m in matching:
                            print(f"   - {m['device_id']} (user:{m.get('user_id')}, location:{m.get('location')})")
                        print(f"   Using first match: {matching[0]['device_id']} (user:{matching[0].get('user_id')})")
                        print(f"   Tip: Use --user-id <id> to specify which one to use")
                    selected_sensors.extend(matching)
                else:
                    print(f"⚠️  Warning: Sensor '{device_id}' not found for user_id {user_id_filter}, skipping")
            else:
                print(f"⚠️  Warning: Sensor '{device_id}' not found, skipping")
        if not selected_sensors:
            print("❌ No valid sensors selected.")
            sys.exit(1)
    else:
        print("❌ Error: Must specify --all or --ids")
        parser.print_help()
        sys.exit(1)
    
    # Group sensors by location
    sensors_by_location = {}
    for sensor in selected_sensors:
        loc = sensor.get("location") or "Unassigned"  # Handle None location
        if loc not in sensors_by_location:
            sensors_by_location[loc] = []
        sensors_by_location[loc].append(sensor["device_id"])
    
    print("=" * 70)
    print("Multi-Sensor Secure Water Monitor Client")
    print("=" * 70)
    print(f"Server URL: {server_url}")
    # Display sensors with user_id if available
    sensor_display = []
    for s in selected_sensors:
        display = s['device_id']
        if s.get('user_id'):
            display += f" (user:{s['user_id']})"
        sensor_display.append(display)
    print(f"Sensors: {', '.join(sensor_display)}")
    if location_filter:
        print(f"Location filter: {location_filter}")
    else:
        # Convert location keys to strings (handle None values)
        location_keys = [str(loc) if loc else "Unassigned" for loc in sensors_by_location.keys()]
        print(f"Locations: {', '.join(location_keys)}")
    print(f"Interval: {args.interval} seconds")
    print(f"Mode: {args.mode}")
    print(f"Total sensors: {len(selected_sensors)}")
    print("=" * 70)
    
    if not location_filter and len(sensors_by_location) > 1:
        print("\n⚠️  Note: Sensors from multiple locations detected.")
        print("   Use --location <location_name> to simulate one location at a time.")
        # Convert location keys to strings (handle None values)
        location_keys = [str(loc) if loc else "Unassigned" for loc in sensors_by_location.keys()]
        print(f"   Available locations: {', '.join(location_keys)}\n")
    print("\nStarting simulation (Press Ctrl+C to stop)...\n")
    
    # Create stop event for graceful shutdown
    stop_event = threading.Event()
    
    # Start a thread for each sensor with staggered delays to avoid connection storms
    threads = []
    for idx, device_info in enumerate(selected_sensors):
        thread = threading.Thread(
            target=simulate_sensor,
            args=(device_info, server_url, args.interval, stop_event, args.mode),
            daemon=True
        )
        thread.start()
        threads.append(thread)
        # Stagger thread starts by 0.2 seconds to reduce database/network contention
        # This helps prevent first-attempt failures when many sensors start simultaneously
        if idx < len(selected_sensors) - 1:  # Don't delay after the last sensor
            time.sleep(0.2)
    
    try:
        # Wait for all threads (they run until stop_event is set)
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopping all sensors...")
        stop_event.set()
        for thread in threads:
            thread.join(timeout=5)
        print("✅ All sensors stopped.")


if __name__ == '__main__':
    main()

