import os
import sys
import json
import base64
import random
import hashlib
import time
import argparse
import requests
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import urllib3
import re
import ssl
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Ensure project root is on sys.path to import shared utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from encryption_utils import encrypt_data, aes_encrypt, hash_data  # noqa: E402
from Crypto.Signature import pkcs1_15  # noqa: E402
from Crypto.Hash import SHA256  # noqa: E402
from Crypto.PublicKey import RSA  # noqa: E402
from db import list_sensors, list_sensor_types  # noqa: E402

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 16-byte AES key for MQTT payload simulation
AES_KEY = b'my16bytepassword'


def _build_type_defaults_map() -> dict:
    """Return {'ph': {'min': x, 'max': y}, ...} from sensor_type table.

    Falls back to empty mapping on DB errors.
    """
    try:
        result = {}
        for t in list_sensor_types() or []:
            type_name = (t.get('type_name') or '').lower()
            result[type_name] = {
                'min': t.get('default_min'),
                'max': t.get('default_max'),
            }
        return result
    except Exception:
        return {}


def generate_sensor_reading_for_type(sensor_type: str) -> dict:
    """Return measurement dict containing only the field for the given type.

    This aligns with server-side threshold evaluation which expects values keyed
    by the sensor's device_type, e.g., {'ph': 7.2} for a pH sensor.
    Uses wider ranges for mixed/unsafe mode.
    """
    st = (sensor_type or "").strip().lower()
    if st == "ph":
        return {"ph": round(random.uniform(4.0, 9.5), 2)}
    if st == "tds":
        return {"tds": random.randint(0, 2000)}
    if st == "turbidity":
        return {"turbidity": round(random.uniform(0.0, 10.0), 2)}
    if st == "temperature":
        return {"temperature": round(random.uniform(0.0, 50.0), 2)}
    if st == "dissolved_oxygen":
        return {"dissolved_oxygen": round(random.uniform(0.5, 20.0), 2)}
    if st == "conductivity":
        return {"conductivity": round(random.uniform(0.0, 2000.0), 1)}
    if st == "ammonia":
        return {"ammonia": round(random.uniform(0.0, 2.0), 2)}
    if st == "pressure":
        return {"pressure": round(random.uniform(0.0, 800.0), 2)}
    if st == "nitrate" or st == "nitrite":
        return {st: round(random.uniform(0.0, 50.0), 2)}
    if st == "orp":
        return {"orp": random.randint(0, 500)}
    if st == "chlorine":
        return {"chlorine": round(random.uniform(0.0, 2.0), 2)}
    if st == "salinity":
        return {"salinity": round(random.uniform(0.0, 50.0), 2)}
    if st == "flow":
        return {"flow": round(random.uniform(0.0, 150.0), 2)}
    # Fallback: send pH as a sane default if unknown type
    return {"ph": round(random.uniform(4.0, 9.5), 2)}


def generate_sensor_reading_for_type_safe(sensor_type: str) -> dict:
    """Generate values biased within configured safe thresholds (DB defaults).

    If thresholds are missing for a given type, use conservative safe-ish fallbacks.
    """
    st = (sensor_type or "").strip().lower()
    tmap = _build_type_defaults_map()
    th = tmap.get(st) or {}
    min_v = th.get('min')
    max_v = th.get('max')

    def _uniform_with_margin(a, b, margin_ratio=0.05):
        # Pull in the bounds slightly to avoid edge rounding issues
        span = b - a
        a2 = a + span * margin_ratio
        b2 = b - span * margin_ratio
        return random.uniform(a2, b2)

    if st == "ph":
        if min_v is not None and max_v is not None:
            return {"ph": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"ph": round(random.uniform(6.5, 8.5), 2)}  # Default: 6.5-8.5
    if st == "tds":
        if min_v is not None and max_v is not None:
            return {"tds": int(_uniform_with_margin(float(min_v), float(max_v)))}
        return {"tds": random.randint(0, 500)}  # Default: 0-500
    if st == "turbidity":
        if min_v is not None and max_v is not None:
            return {"turbidity": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"turbidity": round(random.uniform(0.0, 5.0), 2)}  # Default: 0-5
    if st == "temperature":
        hi = 35.0 if (max_v is None) else float(max_v)
        lo = 0.0 if (min_v is None) else float(min_v)
        if hi <= lo:
            hi = lo + 5.0
        return {"temperature": round(_uniform_with_margin(lo, hi), 2)}  # Default: 0-35
    if st == "dissolved_oxygen":
        lo = 5.0 if (min_v is None) else float(min_v)
        hi = 14.0 if (max_v is None) else float(max_v)
        if hi <= lo:
            hi = lo + 1.0
        return {"dissolved_oxygen": round(_uniform_with_margin(lo, hi), 2)}  # Default: 5-14
    if st == "conductivity":
        if min_v is not None and max_v is not None:
            return {"conductivity": round(_uniform_with_margin(float(min_v), float(max_v)), 1)}
        return {"conductivity": round(random.uniform(0.0, 500.0), 1)}  # Default: 0-500
    if st == "ammonia":
        if min_v is not None and max_v is not None:
            return {"ammonia": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"ammonia": round(random.uniform(0.0, 0.5), 2)}  # Default: 0-0.5
    if st == "pressure":
        if min_v is not None and max_v is not None:
            return {"pressure": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"pressure": round(random.uniform(0.0, 700.0), 2)}  # Default: 0-700
    if st == "nitrate" or st == "nitrite":
        if min_v is not None and max_v is not None:
            return {st: round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {st: round(random.uniform(0.0, 10.0), 2)}  # Default: 0-10
    if st == "orp":
        if min_v is not None and max_v is not None:
            return {"orp": int(_uniform_with_margin(float(min_v), float(max_v)))}
        return {"orp": random.randint(250, 400)}  # Default: 250-400
    if st == "chlorine":
        if min_v is not None and max_v is not None:
            return {"chlorine": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"chlorine": round(random.uniform(0.2, 1.0), 2)}  # Default: 0.2-1.0
    if st == "salinity":
        if min_v is not None and max_v is not None:
            return {"salinity": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"salinity": round(random.uniform(0.0, 35.0), 2)}  # Default: 0-35
    if st == "flow":
        if min_v is not None and max_v is not None:
            return {"flow": round(_uniform_with_margin(float(min_v), float(max_v)), 2)}
        return {"flow": round(random.uniform(0.0, 100.0), 2)}  # Default: 0-100
    # Fallback: safe-ish pH
    return {"ph": round(random.uniform(6.5, 8.5), 2)}


def generate_sensor_reading_for_type_unsafe(sensor_type: str) -> dict:
    """Generate values intentionally outside the configured thresholds.

    If both bounds are None, fall back to obviously out-of-norm ranges.
    """
    st = (sensor_type or "").strip().lower()
    tmap = _build_type_defaults_map()
    th = tmap.get(st) or {}
    min_v = th.get('min')
    max_v = th.get('max')

    def _below(min_value, span=0.2):
        return float(min_value) - random.uniform(0.01, max(0.05, span))

    def _above(max_value, span=0.2):
        return float(max_value) + random.uniform(0.01, max(0.05, span))

    if st == "ph":
        if min_v is not None and max_v is not None:
            # Randomly choose below-min or above-max
            if random.random() < 0.5:
                return {"ph": round(_below(min_v, 1.0), 2)}
            return {"ph": round(_above(max_v, 1.0), 2)}
        # Force very low/high
        return {"ph": round(random.choice([random.uniform(2.0, 6.0), random.uniform(9.0, 12.0)]), 2)}
    if st == "tds":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"tds": int(_below(min_v, 50.0))}
            return {"tds": int(_above(max_v, 500.0))}
        return {"tds": random.randint(1200, 3000)}
    if st == "turbidity":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"turbidity": round(_below(min_v, 1.0), 2)}
            return {"turbidity": round(_above(max_v, 2.0), 2)}
        return {"turbidity": round(random.uniform(6.0, 15.0), 2)}
    if st == "temperature":
        # Above max temperature if defined, else push high
        if max_v is not None:
            return {"temperature": round(_above(max_v, 5.0), 2)}
        return {"temperature": round(random.uniform(36.0, 50.0), 2)}
    if st == "dissolved_oxygen":
        # Below min if defined, else push low
        if min_v is not None:
            return {"dissolved_oxygen": round(_below(min_v, 1.0), 2)}
        return {"dissolved_oxygen": round(random.uniform(0.1, 4.5), 2)}
    if st == "conductivity":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"conductivity": round(_below(min_v, 10.0), 1)}
            return {"conductivity": round(_above(max_v, 200.0), 1)}
        return {"conductivity": round(random.uniform(750.0, 2500.0), 1)}
    if st == "ammonia":
        if min_v is not None and max_v is not None:
            # Usually unsafe means above max (ammonia should be low)
            return {"ammonia": round(_above(max_v, 1.0), 2)}
        return {"ammonia": round(random.uniform(1.0, 10.0), 2)}
    if st == "pressure":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"pressure": round(_below(min_v, 10.0), 2)}
            return {"pressure": round(_above(max_v, 50.0), 2)}
        return {"pressure": round(random.uniform(750.0, 1000.0), 2)}
    if st == "nitrate" or st == "nitrite":
        if min_v is not None and max_v is not None:
            return {st: round(_above(max_v, 10.0), 2)}
        return {st: round(random.uniform(15.0, 50.0), 2)}
    if st == "orp":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"orp": int(_below(min_v, 50.0))}
            return {"orp": int(_above(max_v, 100.0))}
        return {"orp": random.choice([random.randint(0, 200), random.randint(450, 600)])}
    if st == "chlorine":
        if min_v is not None and max_v is not None:
            if random.random() < 0.5:
                return {"chlorine": round(_below(min_v, 0.1), 2)}
            return {"chlorine": round(_above(max_v, 0.5), 2)}
        return {"chlorine": round(random.choice([random.uniform(0.0, 0.1), random.uniform(1.5, 3.0)]), 2)}
    if st == "salinity":
        if min_v is not None and max_v is not None:
            return {"salinity": round(_above(max_v, 10.0), 2)}
        return {"salinity": round(random.uniform(40.0, 50.0), 2)}
    if st == "flow":
        if min_v is not None and max_v is not None:
            return {"flow": round(_above(max_v, 20.0), 2)}
        return {"flow": round(random.uniform(120.0, 200.0), 2)}
    # Fallback: extreme pH
    return {"ph": round(random.choice([random.uniform(2.0, 6.0), random.uniform(9.0, 12.0)]), 2)}


def generate_sensor_reading_for_type_random(sensor_type: str) -> dict:
    """Randomly generate either safe or unsafe values (50/50 chance).
    
    This alternates between safe and unsafe readings for testing purposes.
    """
    if random.random() < 0.5:
        return generate_sensor_reading_for_type_safe(sensor_type)
    else:
        return generate_sensor_reading_for_type_unsafe(sensor_type)


def generate_safe_payload_all_metrics(prefer_type: Optional[str] = None) -> dict:
    """Return a payload containing safe values for all known metrics.

    This ensures server-wide aggregate safety regardless of which sensor
    is submitting the reading.
    """
    metrics = [
        'ph', 'tds', 'turbidity', 'temperature', 'dissolved_oxygen', 'conductivity'
    ]
    payload: dict = {}
    for m in metrics:
        try:
            payload.update(generate_sensor_reading_for_type_safe(m))
        except Exception:
            # Best-effort: ignore one metric if generation fails
            pass
    # Ensure the preferred device_type is present (may overwrite with same-safe value)
    if prefer_type:
        try:
            payload.update(generate_sensor_reading_for_type_safe(prefer_type))
        except Exception:
            pass
    return payload


def publish_mqtt_payload(data: dict, mqtt_host: str = "localhost", mqtt_port: int = 1883, 
                         mqtt_user: Optional[str] = None, mqtt_password: Optional[str] = None,
                         mqtt_use_tls: bool = False, mqtt_ca_certs: Optional[str] = None,
                         mqtt_tls_insecure: bool = False) -> None:
    """Publish sensor data to MQTT topic 'secure/sensor'."""
    data_json = json.dumps(data, sort_keys=True).encode()
    sha256_hash = hashlib.sha256(data_json).hexdigest()

    hashed = hash_data(data)
    encrypted = aes_encrypt(data, AES_KEY)

    payload = {
        "data": encrypted,
        "hash": hashed,
        "sha256": sha256_hash,
    }

    # Build publish kwargs
    publish_kwargs = {
        "hostname": mqtt_host,
        "port": mqtt_port,
    }
    
    if mqtt_user and mqtt_password:
        publish_kwargs["auth"] = {"username": mqtt_user, "password": mqtt_password}
    
    if mqtt_use_tls:
        tls_config = {}
        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
            tls_config["ca_certs"] = mqtt_ca_certs
        if mqtt_tls_insecure:
            tls_config["cert_reqs"] = ssl.CERT_NONE
        if tls_config:
            publish_kwargs["tls"] = tls_config

    publish.single("secure/sensor", json.dumps(payload), **publish_kwargs)
    
    # Compact output: [timestamp] device_id | metric=value
    device_id = data.get('device_id', 'unknown')
    timestamp = datetime.now().strftime("%H:%M:%S")
    metric_keys = ['ph', 'tds', 'turbidity', 'temperature', 'dissolved_oxygen', 'conductivity', 
                   'ammonia', 'pressure', 'nitrate', 'nitrite', 'orp', 'chlorine', 'salinity', 'flow']
    reading_value = next((f"{k}={v}" for k, v in data.items() if k in metric_keys), None)
    if reading_value:
        print(f"[{timestamp}] {device_id:8} | {reading_value}")
    else:
        print(f"[{timestamp}] {device_id:8} | sent")


def find_private_key(sensor_id: str, user_id: Optional[int] = None) -> Optional[str]:
    """Find private key file, checking both user-specific and global locations."""
    # Try user-specific location first (if user_id provided)
    if user_id:
        user_key_path = os.path.join(PROJECT_ROOT, "sensor_keys", str(user_id), sensor_id, "sensor_private.pem")
        if os.path.exists(user_key_path):
            return user_key_path
    
    # Try scanning all user_id directories
    sensor_keys_dir = os.path.join(PROJECT_ROOT, "sensor_keys")
    if os.path.exists(sensor_keys_dir):
        for item in os.listdir(sensor_keys_dir):
            item_path = os.path.join(sensor_keys_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a user_id folder (numeric) or direct device_id folder
                try:
                    # Try as user_id folder
                    user_id_test = int(item)
                    device_key_path = os.path.join(item_path, sensor_id, "sensor_private.pem")
                    if os.path.exists(device_key_path):
                        return device_key_path
                except ValueError:
                    # Not a user_id, treat as direct device_id folder (legacy)
                    if item == sensor_id:
                        device_key_path = os.path.join(item_path, "sensor_private.pem")
                        if os.path.exists(device_key_path):
                            return device_key_path
    
    # Try global location (legacy/fallback)
    global_key_path = os.path.join(PROJECT_ROOT, "sensor_keys", sensor_id, "sensor_private.pem")
    if os.path.exists(global_key_path):
        return global_key_path
    
    return None


def sign_payload(sensor_id: str, private_key_path: Optional[str], payload_bytes: bytes) -> Optional[str]:
    if not private_key_path or not os.path.exists(private_key_path):
        return None
    private_key = RSA.import_key(open(private_key_path, "rb").read())
    h = SHA256.new(payload_bytes)
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()


def post_to_server(data: dict, sensor_id: str, server_url: str, user_id: Optional[int] = None) -> None:
    # Hybrid RSA+AES envelope using server's public key
    public_key_path = os.path.join(PROJECT_ROOT, "keys", "public.pem")
    encrypted = encrypt_data(data, public_key_path)

    # encryption_utils already returns base64 strings, but keep guard for bytes
    encrypted_b64 = {
        key: base64.b64encode(value).decode() if isinstance(value, bytes) else value
        for key, value in encrypted.items()
    }

    # Integrity hash of plaintext
    data_json = json.dumps(data, sort_keys=True).encode()
    sha256_hash = hashlib.sha256(data_json).hexdigest()
    encrypted_b64["sha256"] = sha256_hash

    # Required signing with per-sensor keys to satisfy server validation
    # Auto-find private key path (checks user-specific and legacy locations)
    private_key_path = find_private_key(sensor_id, user_id)
    if not private_key_path:
        print(f"❌ Missing private key: {sensor_id}")
        return
    
    signature_b64 = sign_payload(sensor_id, private_key_path, data_json)
    if not signature_b64:
        print(f"❌ Sign failed: {sensor_id}")
        return
    encrypted_b64["sensor_id"] = sensor_id
    encrypted_b64["signature"] = signature_b64

    endpoint = f"{(server_url or '').rstrip('/')}/submit-data"
    response = requests.post(
        endpoint,
        json=encrypted_b64,
    )
    # Show sensor value in server response with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    metric_keys = ['ph', 'tds', 'turbidity', 'temperature', 'dissolved_oxygen', 'conductivity', 'ammonia', 'pressure', 'nitrate', 'nitrite', 'orp', 'chlorine', 'salinity', 'flow']
    reading_value = next((f"{k}={v}" for k, v in data.items() if k in metric_keys), None)
    if response.status_code == 200:
        if reading_value:
            print(f"[{timestamp}] ✅ Server: {sensor_id} | {reading_value}")
        else:
            print(f"[{timestamp}] ✅ Server: {sensor_id}")
    else:
        if reading_value:
            print(f"[{timestamp}] ⚠️  Server: {sensor_id} ({response.status_code}) | {reading_value}")
        else:
            print(f"[{timestamp}] ⚠️  Server: {sensor_id} ({response.status_code})")


def get_active_sensors() -> List[dict]:
    try:
        import mysql.connector
        DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
        DB_PORT = int(os.getenv('DB_PORT', '3306'))
        DB_USER = os.getenv('DB_USER', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')
        
        # Try using db module first
        try:
            from db import list_sensors
    sensors = list_sensors()
            if sensors and len(sensors) > 0:
                active_sensors = [s for s in sensors if (s.get('status') == 'active')]
                return active_sensors
        except Exception as db_module_err:
            print(f"⚠️  db.list_sensors() failed: {db_module_err}, trying direct connection...")
        
        # Fallback: direct database query
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=5
        )
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM sensors WHERE status = 'active' ORDER BY registered_at DESC")
        sensors = cur.fetchall()
        cur.close()
        conn.close()
        
        return sensors or []
    except Exception as e:
        print(f"❌ Error getting sensors: {e}")
        import traceback
        traceback.print_exc()
        return []

def pick_active_sensor():
    active_sensors = get_active_sensors()
    if not active_sensors:
        return None
    return random.choice(active_sensors)

# Per-sensor session token cache
_sensor_sessions = {}  # device_id -> {'token': str, 'counter': int, 'expires_at': datetime}

def _get_device_session(device_id: str, server_url: str) -> Optional[dict]:
    """Get or refresh device session token for a sensor."""
    global _sensor_sessions
    
    # Check if we have a valid cached session
    if device_id in _sensor_sessions:
        session = _sensor_sessions[device_id]
        expires_at = session.get('expires_at')
        if expires_at and datetime.now() < expires_at:
            return session
    
    # Request new session from server (use skip_challenge=true for simulators)
    try:
        endpoint = f"{(server_url or '').rstrip('/')}/api/device/session/request"
        params = {'device_id': device_id, 'skip_challenge': 'true'}
        response = requests.get(endpoint, params=params, timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            token = session_data.get('session_token')
            expires_in = session_data.get('expires_in_seconds', 900)
            if token:
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                session = {
                    'token': token,
                    'counter': 0,
                    'expires_at': expires_at
                }
                _sensor_sessions[device_id] = session
                return session
    except Exception:
        pass
    
    return None

def simulate_one(sensor: dict, generator_func, server_url: str, mqtt_host: str, 
                 mqtt_port: int = 1883, mqtt_user: Optional[str] = None, 
                 mqtt_password: Optional[str] = None, mqtt_use_tls: bool = False,
                 mqtt_ca_certs: Optional[str] = None, mqtt_tls_insecure: bool = False) -> None:
    if generator_func is None:
        generator_func = generate_sensor_reading_for_type
    sensor_id = sensor.get("device_id")
    device_type = sensor.get("device_type")
    # In safe mode, submit safe readings for all key metrics to guarantee
    # aggregate safety across the system regardless of other sensors.
    if getattr(generator_func, "__name__", "") == "generate_sensor_reading_for_type_safe":
        data = generate_safe_payload_all_metrics(device_type)
    else:
        data = generator_func(device_type)
    data.update({
        "device_id": sensor_id,
        "device_type": device_type,
        "location": sensor.get("location"),
    })
    
    # Get device session token if available
    session = _get_device_session(sensor_id, server_url)
    if session:
        session['counter'] += 1
        data['session_token'] = session['token']
        data['counter'] = session['counter']
    
    # Send to MQTT only (secure/sensor topic)
    publish_mqtt_payload(data, mqtt_host=mqtt_host, mqtt_port=mqtt_port, 
                        mqtt_user=mqtt_user, mqtt_password=mqtt_password,
                        mqtt_use_tls=mqtt_use_tls, mqtt_ca_certs=mqtt_ca_certs,
                        mqtt_tls_insecure=mqtt_tls_insecure)

def simulate_many(target_sensors: List[dict], repeat: int, interval_seconds: float, parallel: bool, 
                  generator_func=None, server_url: str = "http://127.0.0.1:5000", mqtt_host: str = "localhost",
                  mqtt_port: int = 1883, mqtt_user: Optional[str] = None, mqtt_password: Optional[str] = None,
                  mqtt_use_tls: bool = False, mqtt_ca_certs: Optional[str] = None, 
                  mqtt_tls_insecure: bool = False) -> None:
    if not target_sensors:
        print("❌ No sensors selected")
        return
    
    from datetime import datetime
    
    try:
        print(f"📡 {len(target_sensors)} sensor(s) | {repeat} readings | {interval_seconds}s interval\n")
        for i in range(int(repeat)):
            
            if parallel and len(target_sensors) > 1:
                with ThreadPoolExecutor(max_workers=len(target_sensors)) as executor:
                    for s in target_sensors:
                        executor.submit(simulate_one, s, generator_func, server_url, mqtt_host, 
                                       mqtt_port, mqtt_user, mqtt_password, mqtt_use_tls, 
                                       mqtt_ca_certs, mqtt_tls_insecure)
            else:
                for s in target_sensors:
                    simulate_one(s, generator_func, server_url, mqtt_host, mqtt_port, 
                               mqtt_user, mqtt_password, mqtt_use_tls, mqtt_ca_certs, mqtt_tls_insecure)
            if i < (int(repeat) - 1):
                try:
                    time.sleep(float(interval_seconds))
                except KeyboardInterrupt:
                    raise
    except KeyboardInterrupt:
        print("\n⏹️  Stopped")
        return


def run_reading_request_listener(mqtt_host: str = "localhost", mqtt_port: int = 1883,
                                  mqtt_user: Optional[str] = None, mqtt_password: Optional[str] = None,
                                  mqtt_use_tls: bool = False, mqtt_ca_certs: Optional[str] = None,
                                  mqtt_tls_insecure: bool = False, mode: str = "safe") -> None:
    """Run MQTT listener that responds to reading requests."""
    reading_request_topic_base = os.environ.get('MQTT_READING_REQUEST_TOPIC_BASE', 'reading_request')
    request_topic = f"{reading_request_topic_base}/+/request"
    
    # Select generator function based on mode
    if mode == "safe":
        gen = generate_sensor_reading_for_type_safe
    elif mode == "unsafe":
        gen = generate_sensor_reading_for_type_unsafe
    elif mode == "random":
        gen = generate_sensor_reading_for_type_random
    else:
        gen = generate_sensor_reading_for_type
    
    def on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        if reason_code == 0:
            client.subscribe(request_topic)
            print(f"✅ Connected: {mqtt_host}:{mqtt_port} | Topic: {request_topic}")
        else:
            print(f"❌ Connect failed: rc={reason_code}")
    
    def on_message(client, userdata, msg):
        """Handle incoming reading requests."""
        try:
            # Extract device_id from topic: reading_request/{device_id}/request
            topic_match = re.match(r'^' + re.escape(reading_request_topic_base) + r'/([^/]+)/request$', msg.topic or '')
            if not topic_match:
                print(f"⚠️  Invalid topic: {msg.topic}")
                return
            
            device_id = (topic_match.group(1) or '').strip()
            if not device_id:
                print("⚠️  Missing device_id")
                return
            
            # Parse request payload
            payload_str = msg.payload.decode('utf-8', errors='replace') if msg.payload else '{}'
            try:
                request_data = json.loads(payload_str)
            except json.JSONDecodeError:
                request_data = {}
            
            location = request_data.get('location', '')
            print(f"📥 Request: {device_id}" + (f" ({location})" if location else ""))
            
            # Find sensor in database
            sensors = list_sensors()
            sensor = None
            for s in sensors or []:
                if s.get('device_id') == device_id and s.get('status') == 'active':
                    sensor = s
                    break
            
            if not sensor:
                print(f"  ⚠️  {device_id} not found/inactive")
                return
            
            device_type = sensor.get('device_type', 'ph')
            sensor_location = sensor.get('location', '')
            
            # Generate sensor reading
            if getattr(gen, "__name__", "") == "generate_sensor_reading_for_type_safe":
                data = generate_safe_payload_all_metrics(device_type)
            else:
                data = gen(device_type)
            
            data.update({
                "device_id": device_id,
                "device_type": device_type,
                "location": sensor_location,
            })
            
            # Publish sensor data
            publish_mqtt_payload(data, mqtt_host=mqtt_host, mqtt_port=mqtt_port,
                                mqtt_user=mqtt_user, mqtt_password=mqtt_password,
                                mqtt_use_tls=mqtt_use_tls, mqtt_ca_certs=mqtt_ca_certs,
                                mqtt_tls_insecure=mqtt_tls_insecure)
            
            print(f"  ✅ Published: {device_id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Create MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Configure authentication
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
    
    # Configure TLS if enabled
    if mqtt_use_tls:
        try:
            if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
                client.tls_set(
                    ca_certs=mqtt_ca_certs,
                    cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLS
                )
                if mqtt_tls_insecure:
                    client.tls_insecure_set(True)
                    print(f"⚠️  TLS: {mqtt_ca_certs} (INSECURE)")
                else:
                    print(f"✅ TLS: {mqtt_ca_certs}")
            else:
                client.tls_set(
                    cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
                if mqtt_tls_insecure:
                    client.tls_insecure_set(True)
                print(f"✅ TLS: system certs")
        except Exception as tls_err:
            print(f"⚠️  TLS error: {tls_err}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Connecting: {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})")
    try:
        client.connect(mqtt_host, mqtt_port, keepalive=60)
        print("Listening... (Ctrl+C to stop)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-sensor simulator for water monitoring")
    parser.add_argument("--all", action="store_true", help="Simulate all active sensors")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated device_ids to simulate (must be active)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to send per selected sensor")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between repeats")
    parser.add_argument("--parallel", action="store_true", help="Simulate selected sensors in parallel")
    parser.add_argument("--mode", type=str, choices=["safe", "unsafe", "mixed", "random"], default="mixed", help="Reading profile: safe (within thresholds), unsafe (outside), mixed (original ranges), or random (alternates safe/unsafe)")
    parser.add_argument("--server-url", type=str, default=os.environ.get("SERVER_URL", "http://127.0.0.1:5000"), help="Base URL of Flask server, e.g., http://192.168.1.10:5000")
    parser.add_argument("--mqtt-host", type=str, default=os.environ.get("MQTT_HOST", "localhost"), help="MQTT broker host (default: localhost)")
    parser.add_argument("--mqtt-port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")), help="MQTT broker port (default: 1883)")
    parser.add_argument("--mqtt-user", type=str, default=os.environ.get("MQTT_USER"), help="MQTT username")
    parser.add_argument("--mqtt-password", type=str, default=os.environ.get("MQTT_PASSWORD"), help="MQTT password")
    parser.add_argument("--mqtt-use-tls", action="store_true", default=os.environ.get("MQTT_USE_TLS", "false").lower() in ("true", "1", "yes"), help="Enable TLS/SSL for MQTT")
    parser.add_argument("--mqtt-ca-certs", type=str, default=os.environ.get("MQTT_CA_CERTS"), help="Path to CA certificate file for TLS")
    parser.add_argument("--mqtt-tls-insecure", action="store_true", default=os.environ.get("MQTT_TLS_INSECURE", "false").lower() in ("true", "1", "yes"), help="Disable certificate verification (insecure)")
    parser.add_argument("--listen", action="store_true", help="Run in listener mode: subscribe to reading requests and respond automatically")
    args = parser.parse_args()
    
    # If --listen flag is set, run in listener mode
    if args.listen:
        run_reading_request_listener(
            mqtt_host=args.mqtt_host,
            mqtt_port=args.mqtt_port,
            mqtt_user=args.mqtt_user,
            mqtt_password=args.mqtt_password,
            mqtt_use_tls=args.mqtt_use_tls,
            mqtt_ca_certs=args.mqtt_ca_certs,
            mqtt_tls_insecure=args.mqtt_tls_insecure,
            mode=args.mode
        )
        return

    active_sensors = get_active_sensors()
    if not active_sensors:
        print("❌ No active sensors")
        return

    target_sensors: List[dict] = []
    if args.all:
        target_sensors = active_sensors
    elif args.ids:
        requested = [x.strip() for x in args.ids.split(",") if x.strip()]
        id_to_sensor = {s.get("device_id"): s for s in active_sensors}
        for sid in requested:
            s = id_to_sensor.get(sid)
            if s:
                target_sensors.append(s)
            else:
                print(f"⚠️  '{sid}' not found/inactive")
    else:
        # Backward-compat: pick one random active sensor
        pick = pick_active_sensor()
        if pick:
            target_sensors = [pick]

    # Select generator function based on mode
    if args.mode == "safe":
        gen = generate_sensor_reading_for_type_safe
    elif args.mode == "unsafe":
        gen = generate_sensor_reading_for_type_unsafe
    elif args.mode == "random":
        gen = generate_sensor_reading_for_type_random
    else:
        gen = generate_sensor_reading_for_type

    try:
        simulate_many(
            target_sensors,
            repeat=args.repeat,
            interval_seconds=args.interval,
            parallel=args.parallel,
            generator_func=gen,
            server_url=args.server_url,
            mqtt_host=args.mqtt_host,
            mqtt_port=args.mqtt_port,
            mqtt_user=args.mqtt_user,
            mqtt_password=args.mqtt_password,
            mqtt_use_tls=args.mqtt_use_tls,
            mqtt_ca_certs=args.mqtt_ca_certs,
            mqtt_tls_insecure=args.mqtt_tls_insecure,
        )
    except KeyboardInterrupt:
        print("\n⏹️  Stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()


