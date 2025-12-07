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
import urllib3
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

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


def publish_mqtt_payload(data: dict, mqtt_host: str = "localhost") -> None:
    data_json = json.dumps(data, sort_keys=True).encode()
    sha256_hash = hashlib.sha256(data_json).hexdigest()

    hashed = hash_data(data)
    encrypted = aes_encrypt(data, AES_KEY)

    payload = {
        "data": encrypted,
        "hash": hashed,
        "sha256": sha256_hash,
    }

    publish.single("secure/sensor", json.dumps(payload), hostname=mqtt_host)
    print("Published encrypted data to MQTT.")


def sign_payload(sensor_id: str, private_key_path: Optional[str], payload_bytes: bytes) -> Optional[str]:
    if not private_key_path or not os.path.exists(private_key_path):
        return None
    private_key = RSA.import_key(open(private_key_path, "rb").read())
    h = SHA256.new(payload_bytes)
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()


def post_to_server(data: dict, sensor_id: str, server_url: str) -> None:
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
    private_key_path = os.path.join(PROJECT_ROOT, "sensor_keys", sensor_id, "sensor_private.pem")
    signature_b64 = sign_payload(sensor_id, private_key_path, data_json)
    if not signature_b64:
        print(f"Missing private key for sensor '{sensor_id}'. Generate keys and register its public key.")
        return
    encrypted_b64["sensor_id"] = sensor_id
    encrypted_b64["signature"] = signature_b64

    endpoint = f"{(server_url or '').rstrip('/')}/submit-data"
    response = requests.post(
        endpoint,
        json=encrypted_b64,
    )
    print("Server response:", response.text)


def get_active_sensors() -> List[dict]:
    sensors = list_sensors()
    return [s for s in (sensors or []) if (s.get('status') == 'active')]

def pick_active_sensor():
    active_sensors = get_active_sensors()
    if not active_sensors:
        return None
    return random.choice(active_sensors)

def simulate_one(sensor: dict, generator_func, server_url: str, mqtt_host: str) -> None:
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
    print("Client JSON string:", json.dumps(data, sort_keys=True).encode())
    print("SHA-256 hash:", hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest())
    publish_mqtt_payload(data, mqtt_host=mqtt_host)
    post_to_server(data, sensor_id, server_url=server_url)

def simulate_many(target_sensors: List[dict], repeat: int, interval_seconds: float, parallel: bool, generator_func=None, server_url: str = "http://127.0.0.1:5000", mqtt_host: str = "localhost") -> None:
    if not target_sensors:
        print("No active sensors selected.")
        return
    for i in range(int(repeat)):
        if parallel and len(target_sensors) > 1:
            with ThreadPoolExecutor(max_workers=len(target_sensors)) as executor:
                for s in target_sensors:
                    executor.submit(simulate_one, s, generator_func, server_url, mqtt_host)
        else:
            for s in target_sensors:
                simulate_one(s, generator_func, server_url, mqtt_host)
        if i < (int(repeat) - 1):
            time.sleep(float(interval_seconds))


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-sensor simulator for water monitoring")
    parser.add_argument("--all", action="store_true", help="Simulate all active sensors")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated device_ids to simulate (must be active)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to send per selected sensor")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between repeats")
    parser.add_argument("--parallel", action="store_true", help="Simulate selected sensors in parallel")
    parser.add_argument("--mode", type=str, choices=["safe", "unsafe", "mixed"], default="mixed", help="Reading profile: safe (within thresholds), unsafe (outside), or mixed (original ranges)")
    parser.add_argument("--server-url", type=str, default=os.environ.get("SERVER_URL", "http://127.0.0.1:5000"), help="Base URL of Flask server, e.g., http://192.168.1.10:5000")
    parser.add_argument("--mqtt-host", type=str, default=os.environ.get("MQTT_HOST", "localhost"), help="MQTT broker host (default: localhost)")
    args = parser.parse_args()

    active_sensors = get_active_sensors()
    if not active_sensors:
        print("No active sensors found. Please register or activate a sensor first.")
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
                print(f"Skipping '{sid}': not found or not active.")
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
    else:
        gen = generate_sensor_reading_for_type

    simulate_many(
        target_sensors,
        repeat=args.repeat,
        interval_seconds=args.interval,
        parallel=args.parallel,
        generator_func=gen,
        server_url=args.server_url,
        mqtt_host=args.mqtt_host,
    )


if __name__ == "__main__":
    main()


