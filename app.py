from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from encryption_utils import decrypt_data, encrypt_data
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import traceback
from datetime import datetime, timedelta
import threading
import re
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from validation import (
    validate_email, validate_username, validate_password, validate_name,
    validate_device_id, validate_location, validate_public_key, validate_threshold,
    validate_status, sanitize_input, validate_device_type
)
from functools import wraps
from typing import Optional
from utils.auth import login_required
from utils.session_utils import _issue_device_challenge, _validate_device_session
from utils.mqtt_utils import _get_mqtt_publish_kwargs

from db import (
    insert_sensor_data,
    create_user,
    get_user_by_username,
    get_user_by_email,
    update_user_profile,
    update_user_password,
    create_sensor,
    get_sensor_by_device_id,
    list_sensors,
    list_sensor_types,
    get_sensor_type_by_type,
    update_sensor_by_device_id,
    delete_sensor_by_device_id,
    count_active_sensors,
    count_active_sensors_by_location,
    list_recent_sensor_data,
    list_recent_sensor_data_by_location,
    get_locations_with_status,
    create_device_session,
    get_device_session,
    update_device_session,
    delete_device_session,
    cleanup_expired_sessions,
    _get_connection,
    _return_connection,
    _get_cursor,
)

app = Flask(__name__)

# CRITICAL: Ensure MQTT environment variables are set at startup
# These should be set by start_flask.ps1, but set them here as a fallback
# to ensure they're ALWAYS available
import os
if not os.environ.get('MQTT_USER'):
    # Fallback: Set default values if not already set
    # These match what start_flask.ps1 sets
    os.environ.setdefault('MQTT_HOST', '192.168.43.214')
    os.environ.setdefault('MQTT_USER', 'admin_flask')
    os.environ.setdefault('MQTT_PASSWORD', 'flaske2ee25')
    os.environ.setdefault('MQTT_PORT', '8883')
    os.environ.setdefault('MQTT_USE_TLS', 'true')
    os.environ.setdefault('MQTT_TLS_INSECURE', 'true')
    print("[FLASK STARTUP] ⚠️  MQTT env vars NOT SET by PowerShell, using fallback defaults!", file=sys.stderr)
    sys.stderr.flush()

# Log environment variables at startup for debugging
print("=" * 80, file=sys.stderr)
print("[FLASK STARTUP] MQTT Environment Variables:", file=sys.stderr)
print(f"  MQTT_HOST: {os.environ.get('MQTT_HOST', 'NOT SET')}", file=sys.stderr)
print(f"  MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}", file=sys.stderr)
print(f"  MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'} (len: {len(os.environ.get('MQTT_PASSWORD', ''))})", file=sys.stderr)
print(f"  MQTT_PORT: {os.environ.get('MQTT_PORT', 'NOT SET')}", file=sys.stderr)
print("=" * 80, file=sys.stderr)
sys.stderr.flush()

# Global error handler to catch all unhandled exceptions
import logging

# Set up logging for Apache/mod_wsgi
log_file = os.path.join(os.path.dirname(__file__), 'flask_error.log')
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to stderr (goes to Apache error log)
    ]
)
app_logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    import sys
    import traceback
    from flask import request
    from werkzeug.exceptions import NotFound
    
    # Ignore 404 errors for favicon and Chrome DevTools requests (browsers auto-request these)
    if isinstance(e, NotFound):
        path_lower = request.path.lower()
        if 'favicon' in path_lower or 'favicon.ico' in path_lower:
            return '', 204  # No Content - silently ignore missing favicon
        if '.well-known' in path_lower or 'devtools' in path_lower:
            return '', 204  # No Content - silently ignore Chrome DevTools requests
    
    error_msg = f"ERROR: Unhandled exception in route {request.path} [{request.method}]: {str(e)}"
    exception_type = type(e).__name__
    full_traceback = traceback.format_exc()
    
    # Log to file
    app_logger.error(f"{error_msg}\nException type: {exception_type}\n{full_traceback}")
    
    # Also print to stderr (for console output - this is critical for debugging)
    print("=" * 80, file=sys.stderr)
    print(error_msg, file=sys.stderr)
    print(f"Exception type: {exception_type}", file=sys.stderr)
    print(full_traceback, file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    sys.stderr.flush()
    
    # For API endpoints, always return JSON
    if request.path.startswith('/api/'):
        debug_mode = str(os.environ.get('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
        response_data = {
            "error": "Internal Server Error",
            "message": str(e),
            "type": exception_type
        }
        if debug_mode:
            response_data["traceback"] = full_traceback
        else:
            response_data["hint"] = "Check Apache error log or flask_error.log file for details."
        return jsonify(response_data), 500
    
    # For non-API endpoints, return HTML/text
    debug_mode = str(os.environ.get('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
    if debug_mode:
        return f"Internal Server Error: {str(e)}\n\n{full_traceback}", 500
    return f"Internal Server Error: {str(e)}\n\nCheck Apache error log or flask_error.log file for details.", 500

# Request logging for debugging
@app.before_request
def log_request():
    """Log all incoming requests for debugging."""
    if '/provision/' in request.path:
        app.logger.error("=" * 80)
        app.logger.error(f"[BEFORE_REQUEST] {request.method} {request.path}")
        app.logger.error(f"[BEFORE_REQUEST] Remote: {request.remote_addr}")
        app.logger.error(f"[BEFORE_REQUEST] User-Agent: {request.headers.get('User-Agent', 'N/A')}")
        app.logger.error(f"[BEFORE_REQUEST] Content-Type: {request.headers.get('Content-Type', 'N/A')}")
        print("=" * 80, file=sys.stderr)
        print(f"[BEFORE_REQUEST] {request.method} {request.path}", file=sys.stderr)
        print(f"[BEFORE_REQUEST] Remote: {request.remote_addr}", file=sys.stderr)
        print(f"[BEFORE_REQUEST] User-Agent: {request.headers.get('User-Agent', 'N/A')}", file=sys.stderr)
        print(f"[BEFORE_REQUEST] Content-Type: {request.headers.get('Content-Type', 'N/A')}", file=sys.stderr)
        if request.is_json:
            try:
                body = request.get_json(silent=True)
                app.logger.error(f"[BEFORE_REQUEST] JSON body: {body}")
                print(f"[BEFORE_REQUEST] JSON body: {body}", file=sys.stderr)
            except Exception as e:
                app.logger.error(f"[BEFORE_REQUEST] Error parsing JSON: {e}")
                print(f"[BEFORE_REQUEST] Error parsing JSON: {e}", file=sys.stderr)
        else:
            app.logger.error(f"[BEFORE_REQUEST] Raw data: {request.get_data(as_text=True)[:200]}")
            print(f"[BEFORE_REQUEST] Raw data: {request.get_data(as_text=True)[:200]}", file=sys.stderr)
        sys.stderr.flush()

# User-specific data storage: user_id -> {latest_data, latest_by_metric, latest_by_sensor}
user_latest_data = {}  # user_id -> latest_data dict
user_latest_by_metric = {}  # user_id -> latest_by_metric dict
user_latest_by_sensor = {}  # user_id -> latest_by_sensor dict


# Legacy global variables (for backward compatibility, will be deprecated)
latest_data = {}
latest_by_metric = {}
latest_by_sensor = {}

key_upload_tokens = {}
pending_keys = {}  # Global pending keys (device_id -> key) for MQTT/uploads without user context
user_pending_keys = {}  # User-specific keys (user_id -> {device_id -> key})
mqtt_thread_started = False
mqtt_sensor_thread_started = False
provision_last_sent = {}
device_challenges = {}

# --- REPLAY ATTACK PROTECTION ---
# Store recent nonces and timestamps for each device_id (in-memory, resets on restart)
recent_nonces = {}  # device_id -> set of nonces
recent_timestamps = {}  # device_id -> last timestamp (ISO8601 string)
NONCE_CACHE_SIZE = 50  # How many nonces to remember per device
REPLAY_MAX_SKEW_SECONDS = 120  # Allow up to 2 minutes clock skew

# Directory for storing user-specific key files
USER_KEYS_DIR = os.path.join(os.path.dirname(__file__), 'user_keys')

def ensure_user_keys_dir():
    """Ensure the user_keys directory exists."""
    if not os.path.exists(USER_KEYS_DIR):
        os.makedirs(USER_KEYS_DIR, mode=0o755)

def get_user_keys_dir(user_id):
    """Get the directory path for storing a user's keys."""
    ensure_user_keys_dir()
    user_dir = os.path.join(USER_KEYS_DIR, str(user_id))
    os.makedirs(user_dir, mode=0o755, exist_ok=True)
    return user_dir

def get_user_key_file(user_id, device_id):
    """Get the file path for storing a user's device public key."""
    user_dir = get_user_keys_dir(user_id)
    return os.path.join(user_dir, f'{device_id}_public.pem')

def get_user_keys_file(user_id):
    """Get the legacy JSON file path for storing a user's keys (for migration)."""
    ensure_user_keys_dir()
    return os.path.join(USER_KEYS_DIR, f'user_{user_id}_keys.json')

def migrate_user_keys_from_json(user_id):
    """Migrate keys from old JSON format to new folder structure."""
    json_file = get_user_keys_file(user_id)
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                keys_dict = json.load(f)
            # Save each key as a separate PEM file
            for device_id, public_key in keys_dict.items():
                key_file = get_user_key_file(user_id, device_id)
                with open(key_file, 'w', encoding='utf-8') as kf:
                    kf.write(public_key)
            # Optionally remove the old JSON file after migration
            # os.remove(json_file)  # Uncomment if you want to delete old files
            print(f"Migrated keys for user {user_id} from JSON to folder structure")
            return True
        except Exception as e:
            print(f"Error migrating user keys for user_id {user_id}: {e}")
            return False
    return False

def load_user_keys(user_id):
    """Load keys for a specific user from folder structure."""
    user_dir = get_user_keys_dir(user_id)
    keys = {}
    
    # Check for legacy JSON file and migrate if exists
    migrate_user_keys_from_json(user_id)
    
    # Load keys from individual PEM files
    if os.path.exists(user_dir):
        try:
            for filename in os.listdir(user_dir):
                if filename.endswith('_public.pem'):
                    device_id = filename.replace('_public.pem', '')
                    key_file = os.path.join(user_dir, filename)
                    with open(key_file, 'r', encoding='utf-8') as f:
                        keys[device_id] = f.read()
        except Exception as e:
            print(f"Error loading user keys for user_id {user_id}: {e}")
    
    return keys

def save_user_keys(user_id, keys_dict):
    """Save keys for a specific user to folder structure (for backward compatibility)."""
    try:
        for device_id, public_key in keys_dict.items():
            key_file = get_user_key_file(user_id, device_id)
            with open(key_file, 'w', encoding='utf-8') as f:
                f.write(public_key)
        return True
    except Exception as e:
        print(f"Error saving user keys for user_id {user_id}: {e}")
        return False

def add_user_key(user_id, device_id, public_key):
    """Add a key for a user's device. Creates folder and file if needed."""
    # Ensure user folder exists
    user_dir = get_user_keys_dir(user_id)
    
    # Save key as individual PEM file
    key_file = get_user_key_file(user_id, device_id)
    try:
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(public_key)
    except Exception as e:
        print(f"Error saving key for user {user_id}, device {device_id}: {e}")
        return False
    
    # Also update in-memory cache
    if user_id not in user_pending_keys:
        user_pending_keys[user_id] = {}
    user_pending_keys[user_id][device_id] = public_key
    return True

def get_user_key(user_id, device_id):
    """Get a key for a user's device. Checks both file and in-memory cache."""
    # Check in-memory cache first
    if user_id in user_pending_keys and device_id in user_pending_keys[user_id]:
        return user_pending_keys[user_id][device_id]
    
    # Check file (individual PEM file)
    key_file = get_user_key_file(user_id, device_id)
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading key file for user {user_id}, device {device_id}: {e}")
    
    # Fallback: try loading from legacy JSON format
    keys = load_user_keys(user_id)
    return keys.get(device_id)


# _get_mqtt_publish_kwargs is now in utils/mqtt_utils.py


def notify_raspbian_key_cleanup(device_id: str, user_id: int) -> bool:
    """
    Notify Raspbian to delete device keys via MQTT.
    
    Args:
        device_id: Device ID to delete
        user_id: User ID
        
    Returns:
        True if notification was sent, False otherwise
    """
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        print(f"MQTT: MQTT_HOST not configured, skipping cleanup notification for '{device_id}'")
        return False
    
    try:
        import paho.mqtt.publish as publish
    except ImportError:
        print(f"MQTT: paho-mqtt not available, skipping cleanup notification for '{device_id}'")
        return False
    
    try:
        topic_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
        delete_topic = f"{topic_base}/{device_id}/delete"
        
        # Prepare payload dictionary
        payload_dict = {
            'action': 'delete',
            'device_id': device_id,
            'user_id': str(user_id),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Try to get public_key from database for E2EE encryption
        # This is important because the key will be deleted from DB after this call
        device_key_path = None
        try:
            sensor = get_sensor_by_device_id(device_id, user_id)
            if sensor and sensor.get('public_key'):
                public_key_value = sensor.get('public_key')
                if public_key_value and len(str(public_key_value).strip()) > 0:
                    # Create temporary key file for encryption
                    import tempfile
                    temp_key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
                    temp_key_file.write(str(public_key_value))
                    temp_key_file.close()
                    device_key_path = temp_key_file.name
                    print(f"[Delete Notification] ✅ Found public_key in DB, will encrypt message")
        except Exception as key_err:
            print(f"[Delete Notification] ⚠️  Could not get key from DB: {key_err}")
        
        # Apply E2EE if key was found
        if device_key_path and os.path.exists(device_key_path):
            try:
                from encryption_utils import encrypt_data
                encrypted_payload = encrypt_data(payload_dict, device_key_path)
                payload = json.dumps(encrypted_payload)
                print(f"[Delete Notification] 🔒 Message encrypted with E2EE")
            except Exception as e2ee_err:
                print(f"[Delete Notification] ⚠️  E2EE encryption failed: {e2ee_err}, using plaintext")
                payload = json.dumps(payload_dict)
        else:
            payload = json.dumps(payload_dict)
            print(f"[Delete Notification] ⚠️  No key found, sending plaintext")
        
        print(f"[Delete Notification] Sending MQTT message:")
        print(f"  Topic: {delete_topic}")
        
        # Use the same MQTT configuration as provision requests
        publish_kwargs = _get_mqtt_publish_kwargs()
        publish.single(delete_topic, payload, qos=1, **publish_kwargs)
        
        print(f"MQTT: ✅ Sent key cleanup notification for device '{device_id}' (user: {user_id})")
        return True
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"MQTT: ❌ Error sending cleanup notification for '{device_id}': {e}")
        print(f"MQTT: Error details:\n{error_details}")
        return False


def start_mqtt_key_subscriber():
    """Wrapper function for backward compatibility. Calls extracted utility."""
    global mqtt_thread_started
    if mqtt_thread_started:
        return
    mqtt_key_thread_ref = [mqtt_thread_started]
    from utils.mqtt_utils import start_mqtt_key_subscriber as _start_mqtt_key_subscriber
    _start_mqtt_key_subscriber(
        pending_keys,
        recent_nonces,
        recent_timestamps,
        add_user_key,
        get_sensor_by_device_id,
        update_sensor_by_device_id,
        mqtt_key_thread_ref,
        NONCE_CACHE_SIZE,
        REPLAY_MAX_SKEW_SECONDS
    )
    mqtt_thread_started = mqtt_key_thread_ref[0]
    return

# Original implementation removed - now in utils/mqtt_utils.py
def _old_start_mqtt_key_subscriber():
    """Old implementation - kept for reference only."""
    global mqtt_thread_started
    if mqtt_thread_started:
        return
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        return
    try:
        import paho.mqtt.client as mqtt
        import ssl
    except Exception:
        print("MQTT: paho-mqtt not installed; skipping key subscriber.")
        return

    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_topic = os.environ.get('MQTT_KEYS_TOPIC', 'keys/+/public')
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')  # Path to CA certificate file
    mqtt_certfile = os.environ.get('MQTT_CERTFILE')  # Client certificate file
    mqtt_keyfile = os.environ.get('MQTT_KEYFILE')  # Client private key file
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')  # Skip certificate validation (for self-signed certs)

    # Connection state tracking (nonlocal variable for nested functions)
    mqtt_connected = False
    
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        nonlocal mqtt_connected
        try:
            if reason_code == 0:
                result = client.subscribe(mqtt_topic)
                mqtt_connected = True
                print(f"MQTT: connected rc={reason_code}; subscribed to '{mqtt_topic}' (result: {result})", file=sys.stderr)
                sys.stderr.flush()
            else:
                mqtt_connected = False
                error_msg = f"MQTT: connection failed with rc={reason_code}"
                if reason_code == 5:
                    error_msg += " (Not authorized - check MQTT_USER and MQTT_PASSWORD, or ACL permissions)"
                print(f"MQTT: {error_msg}", file=sys.stderr)
                sys.stderr.flush()
        except Exception as e:
            mqtt_connected = False
            error_msg = f"MQTT subscribe error: {e}"
            print(f"MQTT: {error_msg}", file=sys.stderr)
            import traceback
            print(f"MQTT: Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()

    def _on_message(client, userdata, msg):
        try:
            payload_bytes = msg.payload or b''
            text = payload_bytes.decode('utf-8', errors='replace').strip()
            device_id = None
            # Attempt to parse device_id from topic
            try:
                m = re.match(r'^keys/([^/]+)/public$', msg.topic or '')
                if m:
                    device_id = m.group(1)
            except Exception:
                pass
            pem = None
            user_id_from_msg = None
            # Accept JSON {"device_id":"...","public_key":"PEM","user_id":"...", "nonce":..., "timestamp":...}
            if text.startswith('{'):
                try:
                    data = json.loads(text)
                    pem = (data.get('public_key') or '').strip()
                    device_id = (data.get('device_id') or device_id or '').strip()
                    # Extract user_id if provided
                    user_id_raw = data.get('user_id')
                    if user_id_raw is not None:
                        try:
                            user_id_from_msg = int(user_id_raw)
                        except (ValueError, TypeError):
                            user_id_from_msg = None
                    # --- REPLAY PROTECTION ---
                    nonce = data.get('nonce')
                    timestamp = data.get('timestamp')
                    if device_id and (nonce or timestamp):
                        # Check nonce replay
                        if nonce:
                            nonces = recent_nonces.setdefault(device_id, set())
                            if nonce in nonces:
                                print(f"[REPLAY BLOCKED] Duplicate nonce for device {device_id}: {nonce}")
                                return
                        # Check timestamp replay
                        if timestamp:
                            try:
                                from datetime import datetime, timezone
                                ts = datetime.fromisoformat(timestamp)
                                now = datetime.now(timezone.utc)
                                skew = abs((now - ts).total_seconds())
                                if skew > REPLAY_MAX_SKEW_SECONDS:
                                    print(f"[REPLAY BLOCKED] Timestamp too old or far in future for device {device_id}: {timestamp}")
                                    return
                                # Optionally, block if timestamp not newer than last
                                last_ts = recent_timestamps.get(device_id)
                                if last_ts:
                                    last_dt = datetime.fromisoformat(last_ts)
                                    if ts <= last_dt:
                                        print(f"[REPLAY BLOCKED] Timestamp not newer than previous for device {device_id}: {timestamp}")
                                        return
                                recent_timestamps[device_id] = timestamp
                            except Exception as ts_err:
                                print(f"[REPLAY WARNING] Could not parse timestamp for device {device_id}: {timestamp} ({ts_err})")
                        # Store nonce (limit cache size)
                        if nonce:
                            nonces.add(nonce)
                            if len(nonces) > NONCE_CACHE_SIZE:
                                # Remove oldest (not strictly ordered, but set pop is fine for small cache)
                                while len(nonces) > NONCE_CACHE_SIZE:
                                    nonces.pop()
                except Exception:
                    pem = None
            else:
                pem = text
            if not device_id or not pem:
                print("MQTT: missing device_id or public_key; ignoring message")
                return
            # Store as pending and update DB if sensor already exists
            pending_keys[device_id] = pem
            try:
                # Use user_id if provided to get the correct sensor (important when multiple users have same device_id)
                srow = get_sensor_by_device_id(device_id, user_id_from_msg)
            except Exception:
                srow = None
            
            # Determine user_id for key storage
            user_id_for_key = None
            if srow:
                sensor_user_id = srow.get('user_id')
                user_id_for_key = user_id_from_msg if user_id_from_msg is not None else sensor_user_id
            elif user_id_from_msg is not None:
                user_id_for_key = user_id_from_msg
            
            # Save key to filesystem (user_keys directory) for E2EE encryption
            if user_id_for_key:
                try:
                    if add_user_key(user_id_for_key, device_id, pem):
                        print(f"MQTT: saved public key to user_keys/{user_id_for_key}/{device_id}_public.pem for E2EE")
                    else:
                        print(f"MQTT: warning - failed to save key to user_keys/{user_id_for_key}/{device_id}_public.pem")
                except Exception as key_save_err:
                    print(f"MQTT: error saving key to filesystem: {key_save_err}")
                    import traceback
                    traceback.print_exc()
            
            if srow:
                try:
                    # Update sensor - use user_id if available to ensure we update the correct sensor
                    sensor_db_id = srow.get('id')
                    sensor_user_id = srow.get('user_id')
                    
                    # Use user_id_from_msg if available, otherwise use sensor_user_id from database
                    user_id_for_update = user_id_from_msg if user_id_from_msg is not None else sensor_user_id
                    
                    update_sensor_by_device_id(
                        device_id=device_id,
                        location=srow.get('location'),
                        status=srow.get('status'),
                        public_key=pem,
                        min_threshold=srow.get('min_threshold'),
                        max_threshold=srow.get('max_threshold'),
                        user_id=user_id_for_update,
                    )
                    user_info = f" (user_id={user_id_for_update}, db_id={sensor_db_id})" if user_id_for_update else f" (db_id={sensor_db_id})"
                    print(f"MQTT: updated public key in DB for sensor '{device_id}'{user_info}")
                except Exception as e:
                    print(f"MQTT DB update error for {device_id}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                user_info = f" (user_id={user_id_from_msg})" if user_id_from_msg else ""
                print(f"MQTT: received key for unregistered device '{device_id}'{user_info} (stored pending)")
        except Exception as e:
            print(f"MQTT message error: {e}")

    def _run():
        import time
        retry_count = 0
        max_retries = 10  # Maximum retry attempts before giving up
        base_delay = 5  # Base delay in seconds
        
        while retry_count < max_retries:
            try:
                # Create MQTT client with API v2 (fixes deprecation warning)
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                
                # Configure authentication
                if mqtt_user and mqtt_password:
                    client.username_pw_set(mqtt_user, mqtt_password)
                
                # Configure TLS/SSL if enabled
                if mqtt_use_tls:
                    try:
                        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
                            # Use CA certificate for validation
                            client.tls_set(
                                ca_certs=mqtt_ca_certs,
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                            print(f"MQTT: TLS enabled with CA cert: {mqtt_ca_certs}")
                        else:
                            # Use system CA certificates (default)
                            client.tls_set(
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                            print(f"MQTT: TLS enabled (using system CA certs)")
                        
                        if mqtt_tls_insecure:
                            client.tls_insecure_set(True)
                            print("MQTT: TLS insecure mode enabled (certificate validation disabled)")
                    except Exception as tls_err:
                        print(f"MQTT: TLS configuration error: {tls_err}")
                        print("MQTT: Continuing without TLS (insecure)")
                
                # Set callbacks
                client.on_connect = _on_connect
                client.on_message = _on_message
                
                # Add disconnect callback to handle reconnection
                def _on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
                    """Callback when MQTT client disconnects (API v2)."""
                    nonlocal mqtt_connected
                    mqtt_connected = False
                    if reason_code != 0:
                        print(f"MQTT: Unexpected disconnection (rc={reason_code})", file=sys.stderr)
                        sys.stderr.flush()
                
                client.on_disconnect = _on_disconnect
                
                # Enable automatic reconnection
                client.reconnect_delay_set(min_delay=1, max_delay=120)
                
                print(f"MQTT: Attempting to connect to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'}) (attempt {retry_count + 1}/{max_retries})")
                
                # Use async connection
                try:
                    client.connect_async(mqtt_host, mqtt_port, keepalive=60)
                    client.loop_start()
                    
                    # Wait up to 5 seconds to see if connection succeeds
                    for _ in range(10):  # Check 10 times over 5 seconds
                        time.sleep(0.5)
                        if mqtt_connected:
                            print(f"MQTT: Successfully connected to {mqtt_host}:{mqtt_port}")
                            # Keep the loop running - it will handle reconnections automatically
                            while True:
                                time.sleep(10)
                                # If we lose connection and it doesn't reconnect, break to retry
                                if not mqtt_connected:
                                    # Give it some time to reconnect automatically
                                    time.sleep(5)
                                    if not mqtt_connected:
                                        print("MQTT: Connection lost and auto-reconnect failed, will retry...")
                                        break
                            break
                    else:
                        # Connection failed within timeout
                        client.loop_stop()
                        client.disconnect()
                        raise ConnectionError("Connection attempt timed out")
                        
                except Exception as conn_err:
                    print(f"MQTT: Connection error: {conn_err}")
                    try:
                        client.loop_stop()
                        client.disconnect()
                    except:
                        pass
                    raise
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff: delay increases with each retry
                    delay = min(base_delay * (2 ** (retry_count - 1)), 60)  # Cap at 60 seconds
                    print(f"MQTT: Connection failed (attempt {retry_count}/{max_retries}). Retrying in {delay} seconds...")
                    print(f"MQTT error: {e}")
                    time.sleep(delay)
                else:
                    print(f"MQTT: Max retries ({max_retries}) reached. MQTT subscriber stopped.")
                    print(f"MQTT: Last error: {e}")
                    import traceback
                    traceback.print_exc()
                    break

    t = threading.Thread(target=_run, name='mqtt-key-subscriber', daemon=True)
    t.start()
    mqtt_thread_started = True


def start_mqtt_sensor_subscriber():
    """Wrapper function for backward compatibility. Calls extracted utility."""
    global mqtt_sensor_thread_started
    if mqtt_sensor_thread_started:
        return
    mqtt_sensor_thread_ref = [mqtt_sensor_thread_started]
    from utils.mqtt_utils import start_mqtt_sensor_subscriber as _start_mqtt_sensor_subscriber
    _start_mqtt_sensor_subscriber(
        list_sensors,
        insert_sensor_data,
        _validate_device_session,
        build_effective_thresholds_for_sensor,
        _build_type_defaults_map,
        compute_safety,
        latest_by_metric,
        latest_by_sensor,
        user_latest_by_metric,
        user_latest_by_sensor,
        user_latest_data,
        mqtt_sensor_thread_ref,
        REQUIRE_DEVICE_SESSION
    )
    mqtt_sensor_thread_started = mqtt_sensor_thread_ref[0]
    return


 

# Use a relative path to the private key
PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), 'keys', 'private.pem')

# Thresholds are sourced from DB: sensor_type defaults and sensor-level overrides

# Secret key for session management (override via environment for production)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Security headers middleware to protect against XSS and other attacks
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    # XSS Protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (CSP) - strict policy to prevent XSS
    # Allow inline scripts/styles only from same origin (for form validation)
    # Allow Chart.js CDN for dashboard graphs and source maps
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "  # Allow Chart.js and Intro.js CDN
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "   # Allow Intro.js CSS from CDN
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://cdn.jsdelivr.net; "  # Allow Chart.js source map connections
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "object-src 'none'; "
        "upgrade-insecure-requests;"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Permissions Policy (formerly Feature Policy)
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=()"
    )
    
    return response

# Legacy env-based admin fallback (optional). Prefer DB users created via /register.
ENV_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ENV_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

# Device session configuration
REQUIRE_DEVICE_SESSION = (os.environ.get('REQUIRE_DEVICE_SESSION', 'false') or 'false').strip().lower() in ('1', 'true', 'yes')
DEVICE_SESSION_TTL_SECONDS = int(os.environ.get('DEVICE_SESSION_TTL_SECONDS', '900'))
DEVICE_CHALLENGE_TTL_SECONDS = int(os.environ.get('DEVICE_CHALLENGE_TTL_SECONDS', '60'))

# login_required, _issue_device_challenge, and _validate_device_session are now imported from utils


@app.route('/api/device/session/request', methods=['GET'])
def api_device_session_request():
    """Request a device session. Returns challenge for secure flow, or direct token if skip_challenge=true."""
    try:
        device_id = sanitize_input(request.args.get('device_id') or '')
        skip_challenge = request.args.get('skip_challenge', 'false').lower() in ('true', '1', 'yes')
        
        device_id_valid, device_id_error = validate_device_id(device_id)
        if not device_id_valid:
            return jsonify({"error": device_id_error or "Invalid device_id."}), 400
        
        # Multiple users can have the same device_id, so check all active sensors
        try:
            all_sensors = list_sensors()
            print(f"DEBUG: session/request for device_id='{device_id}' - Found {len(all_sensors or [])} total sensors in database", file=sys.stderr)
            sys.stderr.flush()
        except Exception as db_err:
            print(f"ERROR: Database error in session request: {db_err}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": "Database error occurred"}), 500
        
        # Debug: show all sensors with matching device_id (case-insensitive)
        device_id_lower = device_id.lower()
        all_matching = [s for s in (all_sensors or []) if s.get('device_id', '').lower() == device_id_lower]
        print(f"DEBUG: session/request - Found {len(all_matching)} sensors with device_id='{device_id}' (case-insensitive)", file=sys.stderr)
        for s in all_matching:
            print(f"DEBUG:   - device_id='{s.get('device_id')}', status='{s.get('status')}', user_id={s.get('user_id')}", file=sys.stderr)
        sys.stderr.flush()
        
        matching_sensors = [s for s in all_matching if s.get('status') == 'active']
        print(f"DEBUG: session/request - Found {len(matching_sensors)} ACTIVE sensors with device_id='{device_id}'", file=sys.stderr)
        sys.stderr.flush()
        
        if not matching_sensors:
            # Provide more helpful error message
            if all_matching:
                inactive_statuses = [s.get('status') for s in all_matching]
                return jsonify({
                    "error": f"device '{device_id}' found but not active (status: {', '.join(set(inactive_statuses))})"
                }), 403
            else:
                return jsonify({
                    "error": f"device '{device_id}' not found in database"
                }), 403
        
        # If skip_challenge=true, directly issue session token (for simulators)
        if skip_challenge:
            # Direct session token generation (simpler flow for simulators)
            import secrets
            max_attempts = 10
            session_token = None
            expires_at_ttl = DEVICE_SESSION_TTL_SECONDS
            
            for _ in range(max_attempts):
                candidate = secrets.token_urlsafe(48)
                # Try to create session in database (pass TTL seconds, not datetime)
                if create_device_session(candidate, device_id, expires_at_ttl):
                    session_token = candidate
                    break
            
            if not session_token:
                return jsonify({"error": "failed to generate unique session token"}), 500
            
            return jsonify({
                "session_token": session_token,
                "device_id": device_id,
                "expires_in_seconds": DEVICE_SESSION_TTL_SECONDS,
            })
        
        # Default: Issue challenge - signature verification in establish will identify which sensor
        try:
            challenge_id, challenge = _issue_device_challenge(device_id, device_challenges)
        except Exception as challenge_err:
            print(f"ERROR: Challenge generation error: {challenge_err}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Failed to generate challenge"}), 500
        
        return jsonify({
            "challenge_id": challenge_id,
            "challenge": challenge,
            "expires_in_seconds": DEVICE_CHALLENGE_TTL_SECONDS,
        })
    except Exception as e:
        print(f"ERROR: Unexpected error in session request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/device/session/establish', methods=['POST'])
def api_device_session_establish():
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    device_id = sanitize_input(data.get('device_id') or '')
    challenge_id = sanitize_input(data.get('challenge_id') or '')
    signature_b64 = (data.get('signature') or '').strip()
    
    # Validate device_id
    device_id_valid, device_id_error = validate_device_id(device_id)
    if not device_id_valid:
        return jsonify({"error": device_id_error or "Invalid device_id."}), 400
    
    # Validate challenge_id and signature
    if not challenge_id or len(challenge_id) > 200:
        return jsonify({"error": "Invalid challenge_id."}), 400
    if not signature_b64 or len(signature_b64) > 2000:
        return jsonify({"error": "Invalid signature."}), 400
    # Multiple users can have the same device_id, match by signature
    try:
        all_sensors = list_sensors()
        if all_sensors is None:
            all_sensors = []
        print(f"DEBUG: session/establish - list_sensors() returned {len(all_sensors)} total sensors", file=sys.stderr)
    except Exception as db_err:
        print(f"ERROR: Database error in session/establish list_sensors(): {db_err}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": "Database error occurred"}), 500
    
    device_id_lower = device_id.lower()
    matching_sensors = [s for s in all_sensors if s.get('device_id', '').lower() == device_id_lower and s.get('status') == 'active']
    
    if not matching_sensors:
        # Debug: show what was found
        all_matching = [s for s in all_sensors if s.get('device_id', '').lower() == device_id_lower]
        print(f"DEBUG: session/establish for device_id='{device_id}' - Found {len(all_matching)} sensors, {len(matching_sensors)} active", file=sys.stderr)
        print(f"DEBUG: session/establish - Total sensors in database: {len(all_sensors)}", file=sys.stderr)
        if len(all_sensors) > 0:
            print(f"DEBUG: session/establish - Sample sensor device_ids: {[s.get('device_id') for s in all_sensors[:5]]}", file=sys.stderr)
        for s in all_matching:
            print(f"DEBUG:   - device_id='{s.get('device_id')}', status='{s.get('status')}', user_id={s.get('user_id')}", file=sys.stderr)
        sys.stderr.flush()
        
        if all_matching:
            inactive_statuses = [s.get('status') for s in all_matching]
            return jsonify({
                "error": f"device '{device_id}' found but not active (status: {', '.join(set(inactive_statuses))})"
            }), 403
        else:
            return jsonify({
                "error": f"device '{device_id}' not found in database"
            }), 403
    
    ch = device_challenges.get(challenge_id)
    if not ch or ch.get('device_id', '').lower() != device_id.lower():
        return jsonify({"error": "invalid challenge"}), 400
    if datetime.utcnow() > ch.get('expires_at', datetime.utcnow()):
        try:
            del device_challenges[challenge_id]
        except Exception:
            pass
        return jsonify({"error": "challenge expired"}), 410
    challenge = ch.get('challenge') or ''
    
    # Try to verify signature against each matching sensor's public key
    srow = None
    signature_verified = False
    verification_errors = []
    for candidate_sensor in matching_sensors:
        try:
            db_pub_key = candidate_sensor.get('public_key')
            sensor_user_id = candidate_sensor.get('user_id')
            key_source = "database"
            
            # If not in database, try multiple fallback locations
            if not db_pub_key:
                # Try user-specific locations first
                if sensor_user_id:
                    # Check user_keys/{user_id}/{device_id}_public.pem
                    user_key_path = get_user_key_file(sensor_user_id, device_id)
                    if os.path.exists(user_key_path):
                        db_pub_key = open(user_key_path, "rb").read().decode('utf-8')
                        key_source = f"user_keys/{sensor_user_id}/{device_id}_public.pem"
                    
                    # Also check sensor_keys/{user_id}/{device_id}/sensor_public.pem
                    if not db_pub_key:
                        sensor_pub_path_user = os.path.join(os.path.dirname(__file__), "sensor_keys", str(sensor_user_id), device_id, "sensor_public.pem")
                        if os.path.exists(sensor_pub_path_user):
                            db_pub_key = open(sensor_pub_path_user, "rb").read().decode('utf-8')
                            key_source = f"sensor_keys/{sensor_user_id}/{device_id}/sensor_public.pem"
                
                # Fallback to global location (legacy)
                if not db_pub_key:
                    sensor_pub_path = os.path.join(os.path.dirname(__file__), "sensor_keys", device_id, "sensor_public.pem")
                    if os.path.exists(sensor_pub_path):
                        db_pub_key = open(sensor_pub_path, "rb").read().decode('utf-8')
                        key_source = f"sensor_keys/{device_id}/sensor_public.pem"
            
            if not db_pub_key:
                verification_errors.append(f"user_id={sensor_user_id}: No public key found in database or filesystem")
                continue
            
            public_key = RSA.import_key(db_pub_key.encode('utf-8'))
            h = SHA256.new((challenge or '').encode('utf-8'))
            pkcs1_15.new(public_key).verify(h, base64.b64decode(signature_b64))
            # Signature verified! This is the correct sensor
            print(f"Session establish: Signature verified for {device_id} (user_id={sensor_user_id}, key_source={key_source})")
            srow = candidate_sensor
            signature_verified = True
            break
        except Exception as e:
            # Signature doesn't match this sensor's key, try next one
            verification_errors.append(f"user_id={candidate_sensor.get('user_id')}: {str(e)}")
            continue
    
    if not signature_verified or not srow:
        error_msg = f"invalid signature or no matching active sensor found for device_id '{device_id}'"
        if verification_errors:
            error_msg += f". Verification attempts: {'; '.join(verification_errors)}"
        print(f"Session establish failed: {error_msg}")
        return jsonify({"error": error_msg}), 400
    try:
        del device_challenges[challenge_id]
    except Exception:
        pass
    # Generate unique session token (ensure no collision in database)
    max_attempts = 10
    session_token = None
    # Pass TTL seconds instead of datetime to ensure timezone consistency with MySQL NOW()
    expires_at_ttl = DEVICE_SESSION_TTL_SECONDS
    
    for _ in range(max_attempts):
        candidate = secrets.token_urlsafe(48)
        # Check if token exists in database
        existing = get_device_session(candidate)
        if not existing:
            # Try to create session in database (pass TTL seconds, not datetime)
            if create_device_session(candidate, device_id, expires_at_ttl):
                session_token = candidate
                break
    
    if not session_token:
        return jsonify({"error": "failed to generate unique session token"}), 500
    return jsonify({
        "session_token": session_token,
        "device_id": device_id,
        "expires_in_seconds": DEVICE_SESSION_TTL_SECONDS,
    })


@app.route('/api/provision/request', methods=['POST'])
@login_required
def api_provision_request():
    """Request initial key generation (only if keys don't exist)."""
    return _send_provision_message('request')

@app.route('/api/provision/update', methods=['POST'])
@login_required
def api_provision_update():
    """Update/regenerate existing keys (force new keys)."""
    import sys
    import traceback
    import os
    
    # CRITICAL: Write to file immediately to ensure we see it
    with open('provision_debug.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{datetime.now()}] api_provision_update CALLED\n")
        f.write(f"Method: {request.method}\n")
        f.write(f"Path: {request.path}\n")
        f.write(f"User ID: {session.get('user_id')}\n")
        f.write(f"MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}\n")
        f.write(f"MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'}\n")
        f.flush()
    
    try:
        # Force immediate output with environment check - using BOTH logger and stderr
        app.logger.error("=" * 80)
        app.logger.error("[api_provision_update] ====== ENDPOINT CALLED ======")
        app.logger.error(f"[api_provision_update] Method: {request.method}")
        app.logger.error(f"[api_provision_update] Path: {request.path}")
        app.logger.error(f"[api_provision_update] User ID: {session.get('user_id')}")
        app.logger.error(f"[api_provision_update] ENV CHECK - MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}")
        app.logger.error(f"[api_provision_update] ENV CHECK - MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'} (len: {len(os.environ.get('MQTT_PASSWORD', ''))})")
        app.logger.error(f"[api_provision_update] ENV CHECK - MQTT_HOST: {os.environ.get('MQTT_HOST', 'NOT SET')}")
        print("=" * 80, file=sys.stderr)
        print("[api_provision_update] ====== ENDPOINT CALLED ======", file=sys.stderr)
        print(f"[api_provision_update] Method: {request.method}", file=sys.stderr)
        print(f"[api_provision_update] Path: {request.path}", file=sys.stderr)
        print(f"[api_provision_update] User ID: {session.get('user_id')}", file=sys.stderr)
        print(f"[api_provision_update] ENV CHECK - MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}", file=sys.stderr)
        print(f"[api_provision_update] ENV CHECK - MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'} (len: {len(os.environ.get('MQTT_PASSWORD', ''))})", file=sys.stderr)
        print(f"[api_provision_update] ENV CHECK - MQTT_HOST: {os.environ.get('MQTT_HOST', 'NOT SET')}", file=sys.stderr)
        sys.stderr.flush()
        
        result = _send_provision_message('update')
        
        app.logger.error(f"[api_provision_update] ====== _send_provision_message RETURNED ======")
        app.logger.error(f"[api_provision_update] Result type: {type(result)}")
        app.logger.error(f"[api_provision_update] Result value: {result}")
        print(f"[api_provision_update] ====== _send_provision_message RETURNED ======", file=sys.stderr)
        print(f"[api_provision_update] Result type: {type(result)}", file=sys.stderr)
        print(f"[api_provision_update] Result value: {result}", file=sys.stderr)
        sys.stderr.flush()
        
        app.logger.error("[api_provision_update] ====== ENDPOINT RETURNING ======")
        print("[api_provision_update] ====== ENDPOINT RETURNING ======", file=sys.stderr)
        sys.stderr.flush()
        
        # Ensure we always return a valid response
        if result is None:
            app.logger.error("[api_provision_update] ❌ WARNING: _send_provision_message returned None!")
            print("[api_provision_update] ❌ WARNING: _send_provision_message returned None!", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": "Internal server error", "message": "Provision function returned no response"}), 500
        
        return result
    except Exception as e:
        error_msg = f"Exception in api_provision_update: {str(e)}"
        
        # Write to file
        with open('provision_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"ERROR: {error_msg}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
            f.flush()
        
        app.logger.error("=" * 80)
        app.logger.error(f"[api_provision_update] ❌ {error_msg}")
        app.logger.error(f"[api_provision_update] Traceback:\n{traceback.format_exc()}")
        app.logger.error("=" * 80)
        print("=" * 80, file=sys.stderr)
        print(f"[api_provision_update] ❌ {error_msg}", file=sys.stderr)
        print(f"[api_provision_update] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": error_msg, "details": str(e)}), 500

def _send_provision_message(action: str):
    """Helper function to send provision messages (request or update).
    
    Args:
        action: 'request' for initial keys, 'update' for regenerating keys
    """
    # Validate action parameter
    if not action or not isinstance(action, str):
        error_msg = f"Invalid action parameter: {action}"
        app.logger.error(f"[_send_provision_message] ❌ {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    # Safely get action title for logging
    try:
        action_title = action.title()
    except Exception:
        action_title = str(action)
    
    import os
    try:
        app.logger.error("=" * 80)
        app.logger.error(f"[_send_provision_message] ====== FUNCTION CALLED ======")
        app.logger.error(f"[_send_provision_message] Action: {action}")
        app.logger.error(f"[_send_provision_message] ENV at start - MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}")
        app.logger.error(f"[_send_provision_message] ENV at start - MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'}")
        print("=" * 80, file=sys.stderr)
        print(f"[_send_provision_message] ====== FUNCTION CALLED ======", file=sys.stderr)
        print(f"[_send_provision_message] Action: {action}", file=sys.stderr)
        print(f"[_send_provision_message] ENV at start - MQTT_USER: {os.environ.get('MQTT_USER', 'NOT SET')}", file=sys.stderr)
        print(f"[_send_provision_message] ENV at start - MQTT_PASSWORD: {'SET' if os.environ.get('MQTT_PASSWORD') else 'NOT SET'}", file=sys.stderr)
        sys.stderr.flush()
    except Exception as log_err:
        # If logging fails, continue anyway
        print(f"[_send_provision_message] Warning: Logging failed: {log_err}", file=sys.stderr)
        sys.stderr.flush()
    
    # Wrap entire function body in try-except to catch any unhandled exceptions
    try:
        print(f"[_send_provision_message] Starting for action: {action}", file=sys.stderr)
        sys.stderr.flush()
        
        mqtt_host = os.environ.get('MQTT_HOST')
        print(f"[_send_provision_message] MQTT_HOST from env: {mqtt_host}", file=sys.stderr)
        sys.stderr.flush()
        
        if not mqtt_host:
            error_msg = "MQTT_HOST not configured on server. Please set MQTT_HOST environment variable (e.g., MQTT_HOST=192.168.43.214)"
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "hint": "Set MQTT_HOST environment variable to your MQTT broker address"}), 500
        
        # Get current user ID
        user_id = session.get('user_id')
        print(f"[_send_provision_message] User ID from session: {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        if not user_id:
            return jsonify({"error": "User session invalid"}), 401
    except Exception as e:
        import traceback
        error_msg = f"Exception at start of _send_provision_message: {str(e)}"
        print(f"[_send_provision_message] ❌ {error_msg}", file=sys.stderr)
        print(f"[_send_provision_message] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": error_msg, "details": str(e)}), 500
    
    try:
        print(f"[_send_provision_message] Getting JSON data from request...", file=sys.stderr)
        sys.stderr.flush()
        data = request.get_json(force=True, silent=True) or {}
        print(f"[_send_provision_message] Received data: {data}", file=sys.stderr)
        sys.stderr.flush()
    except Exception as json_err:
        import traceback
        print(f"[_send_provision_message] ❌ Error parsing JSON: {json_err}", file=sys.stderr)
        print(f"[_send_provision_message] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.stderr.flush()
        data = {}
    
    device_id = sanitize_input(data.get('device_id') or '')
    print(f"[_send_provision_message] Extracted device_id: '{device_id}'", file=sys.stderr)
    sys.stderr.flush()
    
    device_id_valid, device_id_error = validate_device_id(device_id)
    if not device_id_valid:
        error_msg = device_id_error or "Invalid device_id."
        print(f"[_send_provision_message] ❌ {error_msg}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": error_msg}), 400
    
    # Prevent duplicate requests within 5 seconds for the same device_id and action
    request_key = f"{device_id}:{action}"
    last_sent_time = provision_last_sent.get(request_key)
    if last_sent_time:
        time_since_last = (datetime.utcnow() - last_sent_time).total_seconds()
        if time_since_last < 5:
            print(f"[Provision {action_title}] ⏭️  Skipping duplicate request for '{device_id}' (last sent {time_since_last:.1f}s ago)")
            return jsonify({"status": "skipped", "reason": "duplicate_request", "device_id": device_id, "action": action})
    
    topic_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
    topic = f"{topic_base}/{device_id}/{action}"
    
    # Prepare payload dictionary
    payload_dict = {"device_id": device_id, "action": action, "user_id": str(user_id)}
    
    # Apply E2EE if device key exists (for ALL actions if key is available)
    # Note: "request" actions typically don't have keys yet (chicken-and-egg problem),
    # but we check anyway in case keys were pre-provisioned
    payload = None
    use_e2ee = False
    device_key_path = None
    key_source = None
    
    # Check for device public key for ALL actions (request, update, delete)
    # This allows E2EE for "request" if keys are pre-provisioned
    # Check multiple locations for device public key (same logic as session establishment)
    # Debug: Log all search paths
    app.logger.error(f"[Provision {action_title}] 🔍 Searching for key for device_id='{device_id}', user_id='{user_id}'")
    print(f"[Provision {action_title}] 🔍 Searching for key for device_id='{device_id}', user_id='{user_id}'", file=sys.stderr)
    
    # PRIORITY 1: Check database FIRST (since user confirmed key is stored in DB)
    # This is especially important for delete operations where filesystem keys may have been cleaned up
    if not device_key_path:
        app.logger.error(f"[Provision {action_title}]   [PRIORITY 1] Checking database for key...")
        print(f"[Provision {action_title}]   [PRIORITY 1] Checking database for key...", file=sys.stderr)
        try:
            # Ensure user_id is int for database query
            user_id_int = int(user_id) if user_id is not None else None
            srow = get_sensor_by_device_id(device_id, user_id_int)
            if srow:
                app.logger.error(f"[Provision {action_title}]   Database query: sensor found (id={srow.get('id')}, user_id={srow.get('user_id')}, status={srow.get('status')})")
                print(f"[Provision {action_title}]   Database query: sensor found (id={srow.get('id')}, user_id={srow.get('user_id')}, status={srow.get('status')})", file=sys.stderr)
                
                public_key_value = srow.get('public_key')
                has_key = public_key_value and len(str(public_key_value).strip()) > 0
                
                if public_key_value:
                    key_length = len(str(public_key_value))
                    app.logger.error(f"[Provision {action_title}]   Public key in DB: length={key_length} chars")
                    print(f"[Provision {action_title}]   Public key in DB: length={key_length} chars", file=sys.stderr)
                else:
                    app.logger.error(f"[Provision {action_title}]   Public key in DB: NULL or empty")
                    print(f"[Provision {action_title}]   Public key in DB: NULL or empty", file=sys.stderr)
                
                app.logger.error(f"[Provision {action_title}]   Database query result: sensor found={srow is not None}, has_key={has_key}")
                print(f"[Provision {action_title}]   Database query result: sensor found={srow is not None}, has_key={has_key}", file=sys.stderr)
                
                if has_key:
                    try:
                        # Create temporary key file for encryption
                        import tempfile
                        temp_key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
                        temp_key_file.write(str(public_key_value))
                        temp_key_file.close()
                        device_key_path = temp_key_file.name
                        key_source = f"database (temp file: {device_key_path})"
                        app.logger.error(f"[Provision {action_title}] ✅ Using database key for {device_id} (key length: {key_length})")
                        print(f"[Provision {action_title}] ✅ Using database key for {device_id} (key length: {key_length})", file=sys.stderr)
                    except Exception as temp_err:
                        app.logger.error(f"[Provision {action_title}] ❌ Failed to create temp key file from DB: {temp_err}")
                        print(f"[Provision {action_title}] ❌ Failed to create temp key file from DB: {temp_err}", file=sys.stderr)
                        import traceback
                        app.logger.error(f"[Provision {action_title}] Traceback: {traceback.format_exc()}")
                        print(f"[Provision {action_title}] Traceback: {traceback.format_exc()}", file=sys.stderr)
                else:
                    app.logger.error(f"[Provision {action_title}] ⚠️  Sensor found in DB but public_key is NULL or empty")
                    print(f"[Provision {action_title}] ⚠️  Sensor found in DB but public_key is NULL or empty", file=sys.stderr)
            else:
                app.logger.error(f"[Provision {action_title}]   Database query: sensor NOT found (device_id='{device_id}', user_id={user_id})")
                print(f"[Provision {action_title}]   Database query: sensor NOT found (device_id='{device_id}', user_id={user_id})", file=sys.stderr)
        except Exception as db_err:
                app.logger.error(f"[Provision {action_title}] ❌ Failed to query database for key: {db_err}")
                print(f"[Provision {action_title}] ❌ Failed to query database for key: {db_err}", file=sys.stderr)
                import traceback
                app.logger.error(f"[Provision {action_title}] Traceback: {traceback.format_exc()}")
                print(f"[Provision {action_title}] Traceback: {traceback.format_exc()}", file=sys.stderr)
    
    # PRIORITY 2: Check user_keys/{user_id}/{device_id}_public.pem (Flask's primary location)
    if not device_key_path:
        user_key_path = get_user_key_file(user_id, device_id)
        app.logger.error(f"[Provision {action_title}]   [PRIORITY 2] Checking: {user_key_path} (exists: {os.path.exists(user_key_path)})")
        print(f"[Provision {action_title}]   [PRIORITY 2] Checking: {user_key_path} (exists: {os.path.exists(user_key_path)})", file=sys.stderr)
        if os.path.exists(user_key_path):
            device_key_path = user_key_path
            key_source = f"user_keys/{user_id}/{device_id}_public.pem"
    
    # PRIORITY 3: Check sensor_keys/{user_id}/{device_id}/sensor_public.pem (provision agent location)
    if not device_key_path:
        sensor_pub_path_user = os.path.join(os.path.dirname(__file__), "sensor_keys", str(user_id), device_id, "sensor_public.pem")
        app.logger.error(f"[Provision {action_title}]   [PRIORITY 3] Checking: {sensor_pub_path_user} (exists: {os.path.exists(sensor_pub_path_user)})")
        print(f"[Provision {action_title}]   [PRIORITY 3] Checking: {sensor_pub_path_user} (exists: {os.path.exists(sensor_pub_path_user)})", file=sys.stderr)
        if os.path.exists(sensor_pub_path_user):
            device_key_path = sensor_pub_path_user
            key_source = f"sensor_keys/{user_id}/{device_id}/sensor_public.pem"
    
    # PRIORITY 4: Fallback to global sensor_keys/{device_id}/sensor_public.pem (legacy)
    if not device_key_path:
            sensor_pub_path = os.path.join(os.path.dirname(__file__), "sensor_keys", device_id, "sensor_public.pem")
            app.logger.error(f"[Provision {action_title}]   [PRIORITY 4] Checking: {sensor_pub_path} (exists: {os.path.exists(sensor_pub_path)})")
            print(f"[Provision {action_title}]   [PRIORITY 4] Checking: {sensor_pub_path} (exists: {os.path.exists(sensor_pub_path)})", file=sys.stderr)
            if os.path.exists(sensor_pub_path):
                device_key_path = sensor_pub_path
                key_source = f"sensor_keys/{device_id}/sensor_public.pem"
    
    # PRIORITY 5: Fallback to in-memory pending_keys (if key was just received via MQTT but not yet saved to file)
    # This is especially important for unregistered devices where key is only in pending_keys
    if not device_key_path:
        app.logger.error(f"[Provision {action_title}]   [PRIORITY 5] Checking pending_keys (device_id in pending_keys: {device_id in pending_keys})")
        print(f"[Provision {action_title}]   [PRIORITY 5] Checking pending_keys (device_id in pending_keys: {device_id in pending_keys})", file=sys.stderr)
        if device_id in pending_keys:
            try:
                # Create temporary key file for encryption
                import tempfile
                temp_key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
                temp_key_file.write(pending_keys[device_id])
                temp_key_file.close()
                device_key_path = temp_key_file.name
                key_source = f"pending_keys (in-memory, temp file: {device_key_path})"
                app.logger.error(f"[Provision {action_title}] ✅ Using in-memory pending key for {device_id}")
                print(f"[Provision {action_title}] ✅ Using in-memory pending key for {device_id}", file=sys.stderr)
            except Exception as temp_err:
                app.logger.error(f"[Provision {action_title}] ❌ Failed to create temp key file: {temp_err}")
                print(f"[Provision {action_title}] ❌ Failed to create temp key file: {temp_err}", file=sys.stderr)
    
    # Apply E2EE if key was found (for ALL actions: request, update, delete)
    if device_key_path:
            # Verify key file still exists and is readable
            if not os.path.exists(device_key_path):
                app.logger.error(f"[Provision {action_title}] ⚠️  Key file disappeared: {device_key_path} (was found but no longer exists)")
                print(f"[Provision {action_title}] ⚠️  Key file disappeared: {device_key_path} (was found but no longer exists)", file=sys.stderr)
                payload = json.dumps(payload_dict)
            else:
                try:
                    # Verify key file is readable and not empty
                    key_size = os.path.getsize(device_key_path)
                    app.logger.error(f"[Provision {action_title}]   Key file size: {key_size} bytes")
                    print(f"[Provision {action_title}]   Key file size: {key_size} bytes", file=sys.stderr)
                    
                    if key_size == 0:
                        app.logger.error(f"[Provision {action_title}] ⚠️  Key file is empty: {device_key_path}")
                        print(f"[Provision {action_title}] ⚠️  Key file is empty: {device_key_path}", file=sys.stderr)
                        payload = json.dumps(payload_dict)
                    else:
                        # Encrypt payload with E2EE
                        encrypted_payload = encrypt_data(payload_dict, device_key_path)
                        payload = json.dumps(encrypted_payload)
                        use_e2ee = True
                        app.logger.error(f"[Provision {action_title}] ✅ E2EE encryption applied (key found: {key_source}, size: {key_size} bytes)")
                        print(f"[Provision {action_title}] ✅ E2EE encryption applied (key found: {key_source}, size: {key_size} bytes)", file=sys.stderr)
                except Exception as e2ee_err:
                    # If encryption fails, fall back to plaintext
                    app.logger.error(f"[Provision {action_title}] ⚠️  E2EE encryption failed: {e2ee_err}, falling back to plaintext")
                    print(f"[Provision {action_title}] ⚠️  E2EE encryption failed: {e2ee_err}, falling back to plaintext", file=sys.stderr)
                    import traceback
                    app.logger.error(f"[Provision {action_title}] Traceback: {traceback.format_exc()}")
                    print(f"[Provision {action_title}] Traceback: {traceback.format_exc()}", file=sys.stderr)
                    payload = json.dumps(payload_dict)
    else:
        # Key doesn't exist in any location
        # For "request" actions: Use server public key for E2EE (provision agent has server private key)
        # For "update"/"delete" actions: Fall back to plaintext (key should exist)
        if action == 'request':
            # Try to use server public key for encrypting "request" messages
            server_public_key_path = os.path.join(os.path.dirname(__file__), 'keys', 'public.pem')
            if os.path.exists(server_public_key_path):
                try:
                    encrypted_payload = encrypt_data(payload_dict, server_public_key_path)
                    payload = json.dumps(encrypted_payload)
                    use_e2ee = True
                    key_source = "server public key (keys/public.pem)"
                    app.logger.error(f"[Provision {action_title}] ✅ E2EE encryption applied using server public key")
                    print(f"[Provision {action_title}] ✅ E2EE encryption applied using server public key", file=sys.stderr)
                except Exception as e2ee_err:
                    app.logger.error(f"[Provision {action_title}] ⚠️  Server key encryption failed: {e2ee_err}, using plaintext")
                    print(f"[Provision {action_title}] ⚠️  Server key encryption failed: {e2ee_err}, using plaintext", file=sys.stderr)
                    payload = json.dumps(payload_dict)
        else:
                payload = json.dumps(payload_dict)
                app.logger.error(f"[Provision {action_title}] ⚠️  E2EE not applied (server public key not found at {server_public_key_path}), using plaintext")
                print(f"[Provision {action_title}] ⚠️  E2EE not applied (server public key not found at {server_public_key_path}), using plaintext", file=sys.stderr)
        else:
            # For "update"/"delete": key should exist, but fall back to plaintext if not found
            payload = json.dumps(payload_dict)
            app.logger.error(f"[Provision {action_title}] ⚠️  E2EE not applied (key not found in any location), using plaintext")
            print(f"[Provision {action_title}] ⚠️  E2EE not applied (key not found in any location), using plaintext", file=sys.stderr)
        print(f"[Provision {action_title}]   Searched: database, user_keys/{user_id}/{device_id}_public.pem, sensor_keys/{user_id}/{device_id}/sensor_public.pem, sensor_keys/{device_id}/sensor_public.pem, pending_keys", file=sys.stderr)
    
    print(f"[Provision {action_title}] Sending MQTT message:", file=sys.stderr)
    print(f"  Topic: {topic}", file=sys.stderr)
    print(f"  E2EE: {'✅ Enabled' if use_e2ee else '❌ Disabled (plaintext)'}", file=sys.stderr)
    print(f"  Payload length: {len(payload)} bytes", file=sys.stderr)
    print(f"  User ID: {user_id}", file=sys.stderr)
    print(f"  Device ID: {device_id}", file=sys.stderr)
    sys.stderr.flush()
    
    # Initialize publish_kwargs to None to ensure it's always defined
    publish_kwargs = None
    
    try:
        print(f"[Provision {action_title}] Attempting to import paho.mqtt.publish...", file=sys.stderr)
        sys.stderr.flush()
        import paho.mqtt.publish as publish
        print(f"[Provision {action_title}] ✅ paho.mqtt.publish imported successfully", file=sys.stderr)
        sys.stderr.flush()
        
        app.logger.error("=" * 80)
        app.logger.error(f"[Provision {action_title}] ====== ABOUT TO CALL _get_mqtt_publish_kwargs() ======")
        print("=" * 80, file=sys.stderr)
        print(f"[Provision {action_title}] ====== ABOUT TO CALL _get_mqtt_publish_kwargs() ======", file=sys.stderr)
        sys.stderr.flush()
        try:
            app.logger.error(f"[Provision {action_title}] Calling _get_mqtt_publish_kwargs() NOW...")
            print(f"[Provision {action_title}] Calling _get_mqtt_publish_kwargs() NOW...", file=sys.stderr)
            sys.stderr.flush()
            publish_kwargs = _get_mqtt_publish_kwargs()
            app.logger.error(f"[Provision {action_title}] ====== _get_mqtt_publish_kwargs() RETURNED ======")
            print(f"[Provision {action_title}] ====== _get_mqtt_publish_kwargs() RETURNED ======", file=sys.stderr)
            sys.stderr.flush()
            app.logger.error(f"[Provision {action_title}] ✅ MQTT publish kwargs retrieved - keys: {list(publish_kwargs.keys())}")
            print(f"[Provision {action_title}] ✅ MQTT publish kwargs retrieved:", file=sys.stderr)
            # Log kwargs but hide password
            safe_kwargs = {k: (v if k != 'auth' else {'username': v.get('username', 'N/A'), 'password': '***'}) for k, v in publish_kwargs.items()}
            app.logger.error(f"[Provision {action_title}]   {safe_kwargs}")
            print(f"[Provision {action_title}]   {safe_kwargs}", file=sys.stderr)
            app.logger.error(f"[Provision {action_title}]   User: {publish_kwargs.get('auth', {}).get('username', 'NONE')}")
            print(f"[Provision {action_title}]   User: {publish_kwargs.get('auth', {}).get('username', 'NONE')}", file=sys.stderr)
            app.logger.error(f"[Provision {action_title}]   Has password: {bool(publish_kwargs.get('auth', {}).get('password'))}")
            print(f"[Provision {action_title}]   Has password: {bool(publish_kwargs.get('auth', {}).get('password'))}", file=sys.stderr)
            app.logger.error(f"[Provision {action_title}]   Has auth key: {'auth' in publish_kwargs}")
            print(f"[Provision {action_title}]   Has auth key: {'auth' in publish_kwargs}", file=sys.stderr)
            sys.stderr.flush()
            
            # CRITICAL: Force immediate write to file to bypass any buffering
            try:
                with open('provision_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] [Provision {action_title}] LINE 1: AFTER 'Has auth key' log\n")
                    f.flush()
                app.logger.error(f"[Provision {action_title}] ✅ File write 1 completed")
                print(f"[Provision {action_title}] ✅ File write 1 completed", file=sys.stderr)
                sys.stderr.flush()
            except Exception as file_err:
                app.logger.error(f"[Provision {action_title}] ❌ File write 1 failed: {file_err}")
                print(f"[Provision {action_title}] ❌ File write 1 failed: {file_err}", file=sys.stderr)
                sys.stderr.flush()
            
            app.logger.error(f"[Provision {action_title}] ====== KWARGS RETRIEVED SUCCESSFULLY ======")
            print(f"[Provision {action_title}] ====== KWARGS RETRIEVED SUCCESSFULLY ======", file=sys.stderr)
            sys.stderr.flush()
            
            try:
                with open('provision_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] [Provision {action_title}] LINE 2: AFTER 'KWARGS RETRIEVED SUCCESSFULLY'\n")
                    f.flush()
            except Exception as file_err:
                app.logger.error(f"[Provision {action_title}] ❌ File write 2 failed: {file_err}")
                print(f"[Provision {action_title}] ❌ File write 2 failed: {file_err}", file=sys.stderr)
                sys.stderr.flush()
            
            app.logger.error(f"[Provision {action_title}] ====== EXITING TRY BLOCK FOR KWARGS ======")
            print(f"[Provision {action_title}] ====== EXITING TRY BLOCK FOR KWARGS ======", file=sys.stderr)
            sys.stderr.flush()
        except Exception as kwargs_err:
            app.logger.error(f"[Provision {action_title}] ====== EXCEPTION IN KWARGS TRY BLOCK ======")
            print(f"[Provision {action_title}] ====== EXCEPTION IN KWARGS TRY BLOCK ======", file=sys.stderr)
            sys.stderr.flush()
            import traceback
            error_msg = f"Failed to get MQTT publish kwargs: {str(kwargs_err)}"
            app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
            app.logger.error(f"[Provision {action_title}] Traceback:\n{traceback.format_exc()}")
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            print(f"[Provision {action_title}] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "details": str(kwargs_err)}), 500
        
        app.logger.error(f"[Provision {action_title}] ====== OUTSIDE KWARGS TRY BLOCK, CONTINUING ======")
        print(f"[Provision {action_title}] ====== OUTSIDE KWARGS TRY BLOCK, CONTINUING ======", file=sys.stderr)
        sys.stderr.flush()
        
        app.logger.error(f"[Provision {action_title}] ====== AFTER GETTING KWARGS, BEFORE VALIDATION ======")
        print(f"[Provision {action_title}] ====== AFTER GETTING KWARGS, BEFORE VALIDATION ======", file=sys.stderr)
        sys.stderr.flush()
        
        # Log publish_kwargs status before validation
        try:
            app.logger.error(f"[Provision {action_title}] publish_kwargs type: {type(publish_kwargs)}, value: {publish_kwargs}")
            print(f"[Provision {action_title}] publish_kwargs type: {type(publish_kwargs)}, value: {publish_kwargs}", file=sys.stderr)
            sys.stderr.flush()
        except Exception as log_err:
            app.logger.error(f"[Provision {action_title}] Error logging publish_kwargs: {log_err}")
            print(f"[Provision {action_title}] Error logging publish_kwargs: {log_err}", file=sys.stderr)
            sys.stderr.flush()
        
        app.logger.error(f"[Provision {action_title}] ====== ABOUT TO ENTER VALIDATION TRY BLOCK ======")
        print(f"[Provision {action_title}] ====== ABOUT TO ENTER VALIDATION TRY BLOCK ======", file=sys.stderr)
        sys.stderr.flush()
        
        try:
            app.logger.error(f"[Provision {action_title}] ====== INSIDE VALIDATION TRY BLOCK ======")
            print(f"[Provision {action_title}] ====== INSIDE VALIDATION TRY BLOCK ======", file=sys.stderr)
            sys.stderr.flush()
            
            # Defensive check: ensure publish_kwargs was successfully retrieved and is a dict
            if publish_kwargs is None:
                error_msg = "Internal error: publish_kwargs not retrieved"
                app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
                print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
                sys.stderr.flush()
                return jsonify({"error": error_msg}), 500
            
            if not isinstance(publish_kwargs, dict):
                error_msg = f"Internal error: publish_kwargs is not a dict (type: {type(publish_kwargs)})"
                app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
                print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
                sys.stderr.flush()
                return jsonify({"error": error_msg}), 500
            
            # Validate MQTT configuration before attempting publish
            if 'hostname' not in publish_kwargs or not publish_kwargs.get('hostname'):
                error_msg = "MQTT_HOST not configured or invalid"
                app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
                print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
                sys.stderr.flush()
                return jsonify({"error": error_msg}), 500
            
            app.logger.error(f"[Provision {action_title}] ====== VALIDATION PASSED, ENTERING PUBLISH TRY BLOCK ======")
            print(f"[Provision {action_title}] ====== VALIDATION PASSED, ENTERING PUBLISH TRY BLOCK ======", file=sys.stderr)
            sys.stderr.flush()
        except Exception as validation_err:
            import traceback
            error_msg = f"Exception during validation: {str(validation_err)}"
            app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
            app.logger.error(f"[Provision {action_title}] Traceback:\n{traceback.format_exc()}")
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            print(f"[Provision {action_title}] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "details": str(validation_err)}), 500
        
        try:
            # Add keepalive and client_id to kwargs if not present
            if 'keepalive' not in publish_kwargs:
                publish_kwargs['keepalive'] = 60
            if 'client_id' not in publish_kwargs:
                publish_kwargs['client_id'] = f"flask_provision_{action}_{device_id}_{int(time.time())}"
            
            app.logger.error(f"[Provision {action_title}] ====== ABOUT TO CALL publish.single() ======")
            app.logger.error(f"[Provision {action_title}] Publishing to topic: {topic}")
            app.logger.error(f"[Provision {action_title}] Payload: {payload}")
            app.logger.error(f"[Provision {action_title}] MQTT Host: {publish_kwargs.get('hostname')}:{publish_kwargs.get('port')}")
            app.logger.error(f"[Provision {action_title}] MQTT User: {publish_kwargs.get('auth', {}).get('username', 'NONE')}")
            print(f"[Provision {action_title}] ====== ABOUT TO CALL publish.single() ======", file=sys.stderr)
            print(f"[Provision {action_title}] Publishing to topic: {topic}", file=sys.stderr)
            print(f"[Provision {action_title}] Payload: {payload}", file=sys.stderr)
            print(f"[Provision {action_title}] MQTT Host: {publish_kwargs.get('hostname')}:{publish_kwargs.get('port')}", file=sys.stderr)
            print(f"[Provision {action_title}] MQTT User: {publish_kwargs.get('auth', {}).get('username', 'NONE')}", file=sys.stderr)
            sys.stderr.flush()
            
            # Call publish.single() directly
            # Note: publish.single() doesn't return a value - it raises an exception on failure
            publish.single(topic, payload, qos=1, **publish_kwargs)
            
            app.logger.error(f"[Provision {action_title}] ====== publish.single() COMPLETED SUCCESSFULLY ======")
            app.logger.error(f"[Provision {action_title}] ✅ Message published to MQTT broker")
            app.logger.error(f"[Provision {action_title}] 💡 If provision agent doesn't receive it, check:")
            app.logger.error(f"[Provision {action_title}]    1. Provision agent is running and connected")
            app.logger.error(f"[Provision {action_title}]    2. Provision agent subscribed to: {topic_base}/+/{action}")
            app.logger.error(f"[Provision {action_title}]    3. MQTT broker ACL allows user to publish to this topic")
            print(f"[Provision {action_title}] ====== publish.single() COMPLETED SUCCESSFULLY ======", file=sys.stderr)
            print(f"[Provision {action_title}] ✅ Message published to MQTT broker", file=sys.stderr)
            print(f"[Provision {action_title}] 💡 If provision agent doesn't receive it, check:", file=sys.stderr)
            print(f"[Provision {action_title}]    1. Provision agent is running and connected", file=sys.stderr)
            print(f"[Provision {action_title}]    2. Provision agent subscribed to: {topic_base}/+/{action}", file=sys.stderr)
            print(f"[Provision {action_title}]    3. MQTT broker ACL allows user to publish to this topic", file=sys.stderr)
            sys.stderr.flush()
            
            # Success - update last sent time and return success response
            try:
                provision_last_sent[request_key] = datetime.utcnow()
            except Exception:
                pass
            
            app.logger.error(f"[Provision {action_title}] ====== RETURNING SUCCESS RESPONSE ======")
            print(f"[Provision {action_title}] ====== RETURNING SUCCESS RESPONSE ======", file=sys.stderr)
            sys.stderr.flush()
            
            return jsonify({
                "status": "sent", 
                "topic": topic, 
                "action": action, 
                "user_id": str(user_id),
                "message": "MQTT message published successfully",
                "troubleshooting": {
                    "check_provision_agent": "Ensure provision_agent.py is running on Raspberry Pi",
                    "check_subscription": f"Provision agent should be subscribed to: {topic_base}/+/{action}",
                    "check_mqtt_broker": f"Verify MQTT broker is accessible at {publish_kwargs.get('hostname')}:{publish_kwargs.get('port')}",
                    "check_acl": "Verify MQTT user has publish permission for provision topics",
                    "check_logs": "Check provision agent console output for received messages"
                }
            })
        except ConnectionRefusedError as conn_err:
            hostname = publish_kwargs.get('hostname') if publish_kwargs else 'unknown'
            port = publish_kwargs.get('port') if publish_kwargs else 'unknown'
            error_msg = f"MQTT broker connection refused. Is the broker running at {hostname}:{port}?"
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            print(f"[Provision {action_title}] Error: {conn_err}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "details": str(conn_err), "hint": "Check if MQTT broker is running and accessible"}), 500
        except TimeoutError as timeout_err:
            # This is now raised by our timeout wrapper
            hostname = publish_kwargs.get('hostname') if publish_kwargs else 'unknown'
            port = publish_kwargs.get('port') if publish_kwargs else 'unknown'
            error_msg = str(timeout_err) or f"MQTT publish timed out. Cannot reach broker at {hostname}:{port}"
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            print(f"[Provision {action_title}] Error: {timeout_err}", file=sys.stderr)
            print(f"[Provision {action_title}] 💡 Tip: Check network connectivity and MQTT broker status", file=sys.stderr)
            print(f"[Provision {action_title}] 💡 When running via SSH, this timeout prevents indefinite blocking", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "details": str(timeout_err), "hint": "Check network connectivity and MQTT broker status"}), 500
        except Exception as pub_err:
            # More specific error handling for publish failures
            error_str = str(pub_err)
            error_msg = f"Failed to publish MQTT message: {error_str}"
            
            # Check for "Not authorized" error specifically
            if "not authorized" in error_str.lower():
                error_msg = "MQTT broker rejected publish: Not authorized. Check MQTT_USER, MQTT_PASSWORD, and ACL permissions for 'provision/+/update' topic"
                hint = "Check MQTT_USER, MQTT_PASSWORD, and ACL permissions for the provision topic"
            else:
                error_msg = f"Failed to publish MQTT message: {error_str}"
                hint = "Check MQTT broker configuration and network connectivity"
            
            print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({"error": error_msg, "details": error_str, "hint": hint}), 500
    except KeyError as key_err:
        # Handle missing required parameters
        error_msg = f"Missing required parameter: {str(key_err)}"
        print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": error_msg}), 500
    except ImportError as e:
        error_msg = f"paho-mqtt library not available: {e}"
        print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_str = str(e)
        error_msg = f"MQTT publish failed: {error_str}"
        
        app.logger.error("=" * 80)
        app.logger.error(f"[Provision {action_title}] ====== OUTER EXCEPTION HANDLER CAUGHT ERROR ======")
        app.logger.error(f"[Provision {action_title}] Exception type: {type(e).__name__}")
        app.logger.error(f"[Provision {action_title}] Exception message: {error_str}")
        app.logger.error(f"[Provision {action_title}] Traceback:\n{error_details}")
        print("=" * 80, file=sys.stderr)
        print(f"[Provision {action_title}] ====== OUTER EXCEPTION HANDLER CAUGHT ERROR ======", file=sys.stderr)
        print(f"[Provision {action_title}] Exception type: {type(e).__name__}", file=sys.stderr)
        print(f"[Provision {action_title}] Exception message: {error_str}", file=sys.stderr)
        print(f"[Provision {action_title}] Traceback:\n{error_details}", file=sys.stderr)
        sys.stderr.flush()
        
        # Provide helpful hints based on error type
        hint = None
        if "not authorized" in error_str.lower():
            hint = "MQTT broker authentication/authorization failed. Check: 1) MQTT_USER and MQTT_PASSWORD environment variables, 2) ACL permissions for the user to publish to 'provision/+/update' topic"
        elif "connection refused" in error_str.lower():
            hint = "MQTT broker connection refused. Is the broker running?"
        elif "timeout" in error_str.lower():
            hint = "MQTT broker connection timeout. Check network connectivity and broker address."
        
        app.logger.error(f"[Provision {action_title}] ❌ {error_msg}")
        print(f"[Provision {action_title}] ❌ {error_msg}", file=sys.stderr)
        if hint:
            app.logger.error(f"[Provision {action_title}] 💡 Hint: {hint}")
            print(f"[Provision {action_title}] 💡 Hint: {hint}", file=sys.stderr)
        app.logger.error(f"[Provision {action_title}] Error details:\n{error_details}")
        print(f"[Provision {action_title}] Error details:\n{error_details}", file=sys.stderr)
        sys.stderr.flush()
        
        response_data = {"error": error_msg, "details": error_str}
        if hint:
            response_data["hint"] = hint
        
        app.logger.error(f"[Provision {action_title}] ====== RETURNING ERROR RESPONSE FROM OUTER EXCEPTION HANDLER ======")
        print(f"[Provision {action_title}] ====== RETURNING ERROR RESPONSE FROM OUTER EXCEPTION HANDLER ======", file=sys.stderr)
        sys.stderr.flush()
        
        return jsonify(response_data), 500
    except Exception as final_err:
        # Ultimate catch-all for any exception that escaped all other handlers
        import traceback
        error_details = traceback.format_exc()
        error_str = str(final_err)
        error_msg = f"Unexpected error in provision function: {error_str}"
        
        app.logger.error("=" * 80)
        app.logger.error(f"[Provision {action_title}] ====== FINAL CATCH-ALL EXCEPTION HANDLER ======")
        app.logger.error(f"[Provision {action_title}] Exception type: {type(final_err).__name__}")
        app.logger.error(f"[Provision {action_title}] Exception message: {error_str}")
        app.logger.error(f"[Provision {action_title}] Traceback:\n{error_details}")
        app.logger.error("=" * 80)
        print("=" * 80, file=sys.stderr)
        print(f"[Provision {action_title}] ====== FINAL CATCH-ALL EXCEPTION HANDLER ======", file=sys.stderr)
        print(f"[Provision {action_title}] Exception type: {type(final_err).__name__}", file=sys.stderr)
        print(f"[Provision {action_title}] Exception message: {error_str}", file=sys.stderr)
        print(f"[Provision {action_title}] Traceback:\n{error_details}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        sys.stderr.flush()
        
        return jsonify({
            "error": error_msg,
            "details": error_str,
            "hint": "An unexpected error occurred. Check server logs for details."
        }), 500
    
    # Safety fallback - should never reach here, but ensures we always return something
    app.logger.error(f"[Provision {action_title}] ❌ WARNING: Reached end of function without returning!")
    print(f"[Provision {action_title}] ❌ WARNING: Reached end of function without returning!", file=sys.stderr)
    sys.stderr.flush()
    return jsonify({"error": "Internal server error", "message": "Function completed without returning a response"}), 500

def _within_range(value, min_val, max_val):
    if value is None:
        return True
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True

def compute_safety(values: dict, thresholds: dict):
    reasons = []
    # Only check keys we have values for
    for key, val in values.items():
        if key not in thresholds:
            continue
        th = thresholds.get(key) or {}
        min_v = th.get('min')
        max_v = th.get('max')
        if not _within_range(val, min_v, max_v):
            # Human-friendly label
            label = key.replace('_', ' ').title()
            if min_v is not None and val < min_v:
                reasons.append(f"{label} below minimum: {val} < {min_v}")
            elif max_v is not None and val > max_v:
                reasons.append(f"{label} above maximum: {val} > {max_v}")
            else:
                reasons.append(f"{label} out of range: {val}")
    return len(reasons) == 0, reasons

def _build_type_defaults_map():
    """Return {'ph': {'min': x, 'max': y}, ...} from sensor_type table."""
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

def build_effective_thresholds_for_sensor(sensor_id: Optional[str]):
    """Resolve thresholds using sensor override if available, else type default.

    Returns a mapping suitable for compute_safety. If sensor is known and has
    device_type 'ph', returns {'ph': {'min': ..., 'max': ...}}. If sensor is
    unknown, falls back to all type defaults.
    """
    type_defaults = _build_type_defaults_map()
    if not sensor_id:
        return type_defaults
    try:
        sensor = get_sensor_by_device_id(sensor_id)
    except Exception:
        sensor = None
    if not sensor:
        return type_defaults
    device_type = sensor.get('device_type')
    if not device_type:
        return type_defaults
    device_type_key = (device_type or '').lower()
    default_for_type = (type_defaults.get(device_type_key) or {})
    min_eff = sensor.get('min_threshold')
    max_eff = sensor.get('max_threshold')
    if min_eff is None:
        min_eff = default_for_type.get('min')
    if max_eff is None:
        max_eff = default_for_type.get('max')
    # Return thresholds keyed by normalized metric name to match values keys
    return {device_type_key: {'min': min_eff, 'max': max_eff}}


@app.route('/submit-data', methods=['POST'])
def submit_data():
    global latest_data, latest_by_metric, latest_by_sensor, user_latest_data, user_latest_by_metric, user_latest_by_sensor
    # Safely parse JSON body; return 400 if missing or not an object to avoid 500s
    encrypted_payload = request.get_json(force=False, silent=True) or {}
    if not isinstance(encrypted_payload, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400
    try:
        # Extract and remove SHA-256 hash from payload
        sha256_hash = encrypted_payload.pop("sha256", None)
        decrypted_data = decrypt_data(encrypted_payload, PRIVATE_KEY_PATH)
        # Compute SHA-256 hash of decrypted data and compare
        if decrypted_data:
            data_json = json.dumps(decrypted_data, sort_keys=True).encode()
            print("Server JSON string:", data_json)
            computed_hash = hashlib.sha256(data_json).hexdigest()
            print("Computed SHA-256 hash:", computed_hash)
            if sha256_hash and computed_hash != sha256_hash:
                return jsonify({"status": "error", "message": "SHA-256 hash mismatch! Data integrity compromised."}), 400

            # Enforce: only registered ACTIVE sensors may submit, with valid signature
            sensor_id = encrypted_payload.get("sensor_id")
            signature_b64 = encrypted_payload.get("signature")
            if not sensor_id or not signature_b64:
                return jsonify({"status": "error", "message": "sensor_id and signature are required."}), 400

            # Look up sensor(s) in DB - multiple users can have the same device_id
            # We'll match by device_id + public_key signature
            all_sensors_with_id = list_sensors()
            matching_sensors = [s for s in all_sensors_with_id if s.get('device_id', '').lower() == sensor_id.lower()]
            
            if not matching_sensors:
                return jsonify({"status": "error", "message": f"Unregistered sensor_id '{sensor_id}'."}), 403
            
            # Cross-check payload identity
            payload_device_id = decrypted_data.get("device_id")
            if payload_device_id and payload_device_id.lower() != sensor_id.lower():
                return jsonify({"status": "error", "message": "device_id in payload does not match sensor_id."}), 400

            # Try to verify signature against each matching sensor's public key
            # This identifies which user's sensor this data belongs to
            sensor_row = None
            signature_verified = False
            
            for candidate_sensor in matching_sensors:
                if candidate_sensor.get('status') != 'active':
                    continue
                
                # Verify signature using this sensor's public key
                try:
                    db_pub_key = candidate_sensor.get('public_key')
                    sensor_user_id = candidate_sensor.get('user_id')
                    
                    # If not in database, try multiple fallback locations
                    if not db_pub_key:
                        # Try user-specific locations first
                        if sensor_user_id:
                            # Check user_keys/{user_id}/{device_id}_public.pem
                            user_key_path = get_user_key_file(sensor_user_id, sensor_id)
                            if os.path.exists(user_key_path):
                                db_pub_key = open(user_key_path, "rb").read().decode('utf-8')
                            
                            # Also check sensor_keys/{user_id}/{device_id}/sensor_public.pem
                            if not db_pub_key:
                                sensor_pub_path_user = os.path.join(os.path.dirname(__file__), "sensor_keys", str(sensor_user_id), sensor_id, "sensor_public.pem")
                                if os.path.exists(sensor_pub_path_user):
                                    db_pub_key = open(sensor_pub_path_user, "rb").read().decode('utf-8')
                        
                        # Fallback to global location (legacy)
                        if not db_pub_key:
                            sensor_pub_path = os.path.join(os.path.dirname(__file__), "sensor_keys", sensor_id, "sensor_public.pem")
                            if os.path.exists(sensor_pub_path):
                                db_pub_key = open(sensor_pub_path, "rb").read().decode('utf-8')
                    
                    if db_pub_key:
                        public_key = RSA.import_key(db_pub_key.encode('utf-8'))
                        h = SHA256.new(data_json)
                        pkcs1_15.new(public_key).verify(h, base64.b64decode(signature_b64))
                        # Signature verified! This is the correct sensor
                        sensor_row = candidate_sensor
                        signature_verified = True
                        break
                except Exception:
                    # Signature doesn't match this sensor's key, try next one
                    continue
            
            if not signature_verified or not sensor_row:
                return jsonify({"status": "error", "message": "Invalid sensor signature or no matching active sensor found."}), 400
            
            # Cross-check device_type (case-insensitive, and allow None/empty to pass)
            payload_device_type = decrypted_data.get("device_type")
            sensor_device_type = sensor_row.get('device_type', '').strip()
            if payload_device_type and sensor_device_type:
                # Normalize both to lowercase for comparison
                payload_type_lower = str(payload_device_type).lower().strip()
                sensor_type_lower = str(sensor_device_type).lower().strip()
                if payload_type_lower != sensor_type_lower:
                    # sys is imported at top of file, safe to use here
                    import sys
                    print(f"WARNING: device_type mismatch for {sensor_id}: payload='{payload_device_type}' vs db='{sensor_device_type}'", file=sys.stderr)
                    sys.stderr.flush()
                    return jsonify({
                        "status": "error", 
                        "message": f"device_type mismatch for sensor. Expected '{sensor_device_type}', got '{payload_device_type}'"
                    }), 400

            # Device session validation - validate and update session every time before storing
            session_token = decrypted_data.get('session_token')
            session_counter = decrypted_data.get('counter')
            if REQUIRE_DEVICE_SESSION:
                # Sessions are required - reject if invalid
                ok, reason = _validate_device_session(session_token, sensor_id, session_counter)
                if not ok:
                    return jsonify({"status": "error", "message": f"Device session error: {reason}"}), 401
            elif session_token:
                # Sessions are optional but provided - validate and update it
                ok, reason = _validate_device_session(session_token, sensor_id, session_counter)
                if not ok:
                    # Log warning but don't reject (sessions optional)
                    import sys
                    print(f"HTTP Sensor: Device session warning for {sensor_id}: {reason} (continuing anyway)", file=sys.stderr)

        # Get user_id from sensor_row to store data per user
        sensor_user_id = sensor_row.get('user_id')
        
        # Initialize user-specific dictionaries if needed
        if sensor_user_id:
            if sensor_user_id not in user_latest_by_metric:
                user_latest_by_metric[sensor_user_id] = {}
            if sensor_user_id not in user_latest_by_sensor:
                user_latest_by_sensor[sensor_user_id] = {}
            if sensor_user_id not in user_latest_data:
                user_latest_data[sensor_user_id] = {}
        
        # Update per-metric latest cache using this sensor's reading(s)
        updated_values = {}
        # Include all supported sensor types
        supported_metrics = [
            "tds", "ph", "turbidity", "temperature", "dissolved_oxygen", "conductivity",
            "ammonia", "pressure", "nitrate", "nitrite", "orp", "chlorine", "salinity", "flow"
        ]
        for k in supported_metrics:
            if k in decrypted_data and decrypted_data[k] not in (None, ""):
                try:
                    val = float(decrypted_data[k])
                    updated_values[k] = val
                    # Update user-specific cache
                    if sensor_user_id:
                        user_latest_by_metric[sensor_user_id][k] = {
                            "value": val,
                            "sensor_id": sensor_id,
                        }
                    # Also update global for backward compatibility
                    latest_by_metric[k] = {
                        "value": val,
                        "sensor_id": sensor_id,
                    }
                except Exception:
                    pass

        # Build aggregate values across metrics we have (snapshot to avoid concurrent mutation)
        # Use user-specific data if available, otherwise fall back to global
        if sensor_user_id and sensor_user_id in user_latest_by_metric:
            _lbm_snapshot = list(user_latest_by_metric[sensor_user_id].items())
        else:
            _lbm_snapshot = list(latest_by_metric.items())
        agg_values = {k: v.get("value") for k, v in _lbm_snapshot if v and v.get("value") is not None}

        # Build aggregate thresholds using the sensor id associated with each metric (snapshot)
        agg_thresholds = {}
        for metric, entry in _lbm_snapshot:
            sid = (entry or {}).get("sensor_id")
            tmap = build_effective_thresholds_for_sensor(sid)
            if tmap and metric in tmap:
                agg_thresholds[metric] = tmap[metric]
        # Fallback to defaults for any metric without sensor context
        for metric in agg_values.keys():
            if metric not in agg_thresholds:
                defaults = _build_type_defaults_map()
                if metric in defaults:
                    agg_thresholds[metric] = defaults[metric]

        # Evaluate safety across the available metrics
        safe, reasons = compute_safety(agg_values, agg_thresholds)

        # Persist the latest reading to MySQL
        # Note: Using sensor_data table only (water_readings table removed)
        # Aggregated readings are stored via individual sensor_data entries
        # try:
        #     tds_v = agg_values.get("tds")
        #     ph_v = agg_values.get("ph")
        #     turbidity_v = agg_values.get("turbidity")
        #     insert_reading(tds_v, ph_v, turbidity_v, safe, reasons)
        # except Exception as db_err:
        #     print(f"MySQL write error: {db_err}")

        # Update per-sensor latest map (stores the value for the sensor's type)
        try:
            device_type = sensor_row.get('device_type')
            value_for_type = None

            # Determine value corresponding to device_type (case-insensitive)
            if device_type:
                device_type_lower = str(device_type).lower().strip()
                # Try case-insensitive match first (handles both "Chlorine" and "chlorine")
                for key, val in updated_values.items():
                    if key and str(key).lower().strip() == device_type_lower:
                        value_for_type = val
                        break
                # If no match found, try exact match as fallback
                if value_for_type is None and device_type in updated_values:
                    value_for_type = updated_values.get(device_type)

            # Fallback: take the first available metric if still None
            if value_for_type is None and len(updated_values) > 0:
                value_for_type = next(iter(updated_values.values()))
                import sys
                msg = f"INFO: Using fallback value for device_id: {sensor_id}, device_type: {device_type}, available_keys: {list(updated_values.keys())}\n"
                print(msg, file=sys.stderr)
                sys.stderr.flush()

            # Map computed safety into table status enum
            status_label = 'normal'
            if not safe:
                status_label = 'warning' if reasons else 'warning'

            # Write one row to sensor_data for this sensor
            try:
                import sys
                sensor_db_id = sensor_row.get('id')
                if sensor_db_id is None:
                    msg = f"ERROR: sensor_row.get('id') is None for device_id: {sensor_id}. Cannot insert sensor data.\n"
                    print(msg, file=sys.stderr)
                    sys.stderr.flush()
                    app_logger.error(msg)
                elif value_for_type is None:
                    msg = f"ERROR: value_for_type is None for device_id: {sensor_id}, device_type: {device_type}, updated_values: {updated_values}\n"
                    print(msg, file=sys.stderr)
                    sys.stderr.flush()
                    app_logger.error(msg)
                else:
                    msg = f"DEBUG: Attempting insert_sensor_data - device_id: {sensor_id}, sensor_db_id: {sensor_db_id}, value: {value_for_type}, device_type: {device_type}\n"
                    print(msg, file=sys.stderr)
                    sys.stderr.flush()
                    app_logger.error(msg)  # Using error level so it appears in log file
                    
                    result = insert_sensor_data(
                        sensor_db_id=sensor_db_id, 
                        value=value_for_type, 
                        status=status_label,
                        user_id=sensor_user_id,
                        device_id=sensor_id
                    )
                    if not result:
                        msg = f"ERROR: insert_sensor_data returned False for device_id: {sensor_id}, sensor_db_id: {sensor_db_id}\n"
                        print(msg, file=sys.stderr)
                        sys.stderr.flush()
                        app_logger.error(msg)
                    else:
                        msg = f"SUCCESS: insert_sensor_data completed for device_id: {sensor_id}, sensor_db_id: {sensor_db_id}, value: {value_for_type}\n"
                        print(msg, file=sys.stderr)
                        sys.stderr.flush()
                        app_logger.error(msg)  # Using error level so it appears in log file
            except Exception as e:
                import sys
                import traceback
                msg = f"ERROR: Failed to insert sensor_data for device_id: {sensor_id}, sensor_db_id: {sensor_row.get('id')}\n"
                msg += f"ERROR: Exception: {e}\n"
                msg += traceback.format_exc()
                print(msg, file=sys.stderr)
                sys.stderr.flush()
                app_logger.error(msg)
            
            # Update user-specific cache
            if sensor_user_id:
                if sensor_user_id not in user_latest_by_sensor:
                    user_latest_by_sensor[sensor_user_id] = {}
                user_latest_by_sensor[sensor_user_id][sensor_id] = {
                    'device_id': sensor_id,
                    'device_type': device_type,
                    'location': sensor_row.get('location'),
                    'value': value_for_type,
                }
            # Also update global for backward compatibility
            latest_by_sensor[sensor_id] = {
                'device_id': sensor_id,
                'device_type': device_type,
                'location': sensor_row.get('location'),
                'value': value_for_type,
            }
        except Exception as e:
            import sys
            import traceback
            msg = f"ERROR: Exception in sensor data processing for device_id: {sensor_id}\n"
            msg += f"ERROR: {e}\n"
            msg += traceback.format_exc()
            print(msg, file=sys.stderr)
            sys.stderr.flush()

        # Update live latest_data only after successful verification and processing (aggregate view)
        # Include all supported metrics
        latest_data_dict = {
            "tds": agg_values.get("tds"),
            "ph": agg_values.get("ph"),
            "turbidity": agg_values.get("turbidity"),
            "temperature": agg_values.get("temperature"),
            "dissolved_oxygen": agg_values.get("dissolved_oxygen"),
            "conductivity": agg_values.get("conductivity"),
            "ammonia": agg_values.get("ammonia"),
            "pressure": agg_values.get("pressure"),
            "nitrate": agg_values.get("nitrate"),
            "nitrite": agg_values.get("nitrite"),
            "orp": agg_values.get("orp"),
            "chlorine": agg_values.get("chlorine"),
            "salinity": agg_values.get("salinity"),
            "flow": agg_values.get("flow"),
        }
        # Update user-specific data
        if sensor_user_id:
            user_latest_data[sensor_user_id] = latest_data_dict
        # Also update global for backward compatibility
        latest_data = latest_data_dict

        return jsonify({
            "status": "success",
            "safe_to_drink": safe,
            **({"reasons": reasons} if not safe else {"note": "Water meets safety standards."})
        })
    except Exception as e:
        import traceback
        error_msg = f"Decryption error: {str(e)}"
        # Log full traceback for debugging
        print(f"ERROR in submit_data: {error_msg}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"status": "error", "message": error_msg}), 400
@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 500 errors."""
    return '', 204  # No Content

@app.route('/static/favicon.ico')
def static_favicon():
    """Handle static favicon requests to prevent 404 errors."""
    return '', 204  # No Content

# Dashboard routes (landing, dashboard, readings) are now in routes/dashboard.py
from routes.dashboard import register_dashboard_routes
register_dashboard_routes(app, user_latest_by_metric)

@app.route('/api/dashboard/location/<location>')
@login_required
def api_dashboard_location(location):
    """API endpoint to get sensor data for a specific location with date range filtering."""
    import sys
    from datetime import datetime, timedelta
    user_id = session.get('user_id')
    username = session.get('user')
    
    # Get date range parameters
    date_from_str = request.args.get('from', '')
    date_to_str = request.args.get('to', '')
    
    print(f"DEBUG: api_dashboard_location - username: {username}, user_id: {user_id}, location: {location}, from: {date_from_str}, to: {date_to_str}", file=sys.stderr)
    sys.stderr.flush()
    
    if not user_id:
        print("ERROR: api_dashboard_location - user_id not found in session!", file=sys.stderr)
        sys.stderr.flush()
        response = jsonify({'error': 'User session not found'})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 401
    
    # STRICT: Verify that this location AND sensors belong to the user
    # Check if user has any sensors in this location (handle "Unassigned" for NULL locations)
    from db import get_pool, _get_connection, _return_connection, _get_cursor
    pool = get_pool()
    if pool:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        location_filter = None if location == 'Unassigned' else location
        
        if location_filter:
            cur.execute("""
                SELECT COUNT(*) as count
                FROM sensors s
                WHERE s.location = %s AND s.user_id = %s
            """, (location_filter, int(user_id)))
        else:
            # Handle "Unassigned" - sensors with NULL/empty location
            cur.execute("""
                SELECT COUNT(*) as count
                FROM sensors s
                WHERE (s.location IS NULL OR s.location = '') AND s.user_id = %s
            """, (int(user_id),))
        
        result = cur.fetchone()
        sensor_count = result['count'] if result else 0
        cur.close()
        _return_connection(pool, conn)
        
        print(f"DEBUG: api_dashboard_location - User {user_id} has {sensor_count} sensors in location '{location}'", file=sys.stderr)
        sys.stderr.flush()
        
        if sensor_count == 0:
            print(f"ERROR: api_dashboard_location - User {user_id} has NO sensors in location '{location}' - ACCESS DENIED", file=sys.stderr)
            sys.stderr.flush()
            response = jsonify({'error': 'Location not accessible - no sensors found for this user'})
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response, 403
    
    # Parse date range - handle multiple formats
    date_from = None
    date_to = None
    try:
        if date_from_str:
            # Try multiple date formats
            for fmt in ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    date_from = datetime.strptime(date_from_str, fmt)
                    break
                except ValueError:
                    continue
            if not date_from:
                # Try ISO format
                date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
            # Remove timezone for MySQL comparison
            if date_from and date_from.tzinfo:
                date_from = date_from.replace(tzinfo=None)
        
        if date_to_str:
            # Try multiple date formats
            for fmt in ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    date_to = datetime.strptime(date_to_str, fmt)
                    break
                except ValueError:
                    continue
            if not date_to:
                # Try ISO format
                date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
            # Remove timezone for MySQL comparison
            if date_to and date_to.tzinfo:
                date_to = date_to.replace(tzinfo=None)
    except Exception as e:
        print(f"WARNING: api_dashboard_location - Invalid date format: {e}, from: {date_from_str}, to: {date_to_str}", file=sys.stderr)
        # Fallback: if date parsing fails, don't filter by date
        date_from = None
        date_to = None
    
    # Get sensor data for this location, filtered by user_id and date range
    # Calculate limit based on time range
    if date_from and date_to:
        time_diff = (date_to - date_from).total_seconds() / 3600  # hours
        if time_diff <= 1:
            limit = 200  # 1 hour: up to 200 points
        elif time_diff <= 24:
            limit = 500  # 1 day: up to 500 points
        elif time_diff <= 168:
            limit = 1000  # 7 days: up to 1000 points
        else:
            limit = 2000  # 30+ days: up to 2000 points
    else:
        # No date range - get ALL available historical data (increase limit significantly)
        limit = 5000  # Get more historical data when no date filter
    
    print(f"DEBUG: api_dashboard_location - Query params: location='{location}', user_id={user_id}, date_from={date_from}, date_to={date_to}, limit={limit}", file=sys.stderr)
    sys.stderr.flush()
    
    rows = list_recent_sensor_data_by_location(
        location=location, 
        limit=limit, 
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )
    
    print(f"DEBUG: api_dashboard_location - Retrieved {len(rows) if rows else 0} rows from database", file=sys.stderr)
    sys.stderr.flush()
    
    # If no rows with date filter, try without date filter as fallback
    if not rows and (date_from or date_to):
        print(f"WARNING: api_dashboard_location - No rows with date filter (from={date_from}, to={date_to}), trying without date filter", file=sys.stderr)
        sys.stderr.flush()
        rows = list_recent_sensor_data_by_location(
            location=location, 
            limit=500, 
            user_id=user_id,
            date_from=None,
            date_to=None
        )
        print(f"DEBUG: api_dashboard_location - Fallback query returned {len(rows) if rows else 0} rows", file=sys.stderr)
        sys.stderr.flush()
        
        # If we got data without date filter, adjust the date range to include it
        if rows and len(rows) > 0:
            # Find the actual date range of the data
            all_timestamps = []
            for r in rows:
                ts = r.get('recorded_at')
                if ts:
                    if isinstance(ts, str):
                        try:
                            ts_dt = datetime.strptime(ts[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            continue
                    elif isinstance(ts, datetime):
                        ts_dt = ts.replace(tzinfo=None) if ts.tzinfo else ts
                    else:
                        continue
                    all_timestamps.append(ts_dt)
            
            if all_timestamps:
                actual_from = min(all_timestamps)
                actual_to = max(all_timestamps)
                # Update date range to match actual data
                date_from = actual_from
                date_to = actual_to
                print(f"DEBUG: api_dashboard_location - Adjusted date range to match data: {date_from} to {date_to}", file=sys.stderr)
                sys.stderr.flush()
    # If still no rows, return empty response with success status
    if not rows:
        return jsonify({
            "location": location,
            "labels": [],
            "datasets": [],
            "safety_status": [],
            "is_live": False,
            "user_id": user_id,
            "username": username,
            "row_count": 0,
            "point_count": 0
        })
    
    import sys
    print(f"DEBUG: api_dashboard_location - Retrieved {len(rows) if rows else 0} rows from database", file=sys.stderr)
    if rows and len(rows) > 0:
        sample_row = rows[0]
        print(f"DEBUG: api_dashboard_location - Sample row keys: {list(sample_row.keys())}", file=sys.stderr)
        print(f"DEBUG: api_dashboard_location - Sample recorded_at: {sample_row.get('recorded_at')} (type: {type(sample_row.get('recorded_at'))})", file=sys.stderr)
    sys.stderr.flush()
    
    # Determine time interval based on date range
    if date_from and date_to:
        # Remove timezone for comparison
        if date_from.tzinfo:
            date_from = date_from.replace(tzinfo=None)
        if date_to.tzinfo:
            date_to = date_to.replace(tzinfo=None)
        time_diff_hours = (date_to - date_from).total_seconds() / 3600
        if time_diff_hours <= 1:
            interval_minutes = 1  # 1-minute intervals for 1 hour
            label_format = '%H:%M'
        elif time_diff_hours <= 24:
            interval_minutes = 15  # 15-minute intervals for today
            label_format = '%H:%M'
        elif time_diff_hours <= 168:
            interval_minutes = 60  # 1-hour intervals for 7 days
            label_format = '%m/%d %H:%M'
        else:
            interval_minutes = 1440  # Daily intervals for 30+ days
            label_format = '%Y-%m-%d'
    else:
        # No date range - use default intervals based on data
        interval_minutes = 15  # Default: 15-minute intervals
        label_format = '%Y-%m-%d %H:%M'
    
    # Group by time intervals
    time_buckets = {}
    latest_timestamp = None
    
    import sys
    print(f"DEBUG: api_dashboard_location - Processing {len(rows) if rows else 0} rows", file=sys.stderr)
    sys.stderr.flush()
    
    for r in rows or []:
        recorded_at = r.get('recorded_at')
        if not recorded_at:
            continue
        
        # Parse timestamp - handle MySQL datetime objects and strings
        parsed_dt = None
        if isinstance(recorded_at, str):
            try:
                # Try ISO format first
                parsed_dt = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
            except:
                try:
                    # Try MySQL datetime format: YYYY-MM-DD HH:MM:SS
                    parsed_dt = datetime.strptime(recorded_at[:19], '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"WARNING: api_dashboard_location - Could not parse timestamp '{recorded_at}': {e}", file=sys.stderr)
                    continue
        elif isinstance(recorded_at, datetime):
            # MySQL datetime objects are naive (no timezone), treat as local time
            parsed_dt = recorded_at
            if parsed_dt.tzinfo is not None:
                # Convert to naive local time
                parsed_dt = parsed_dt.replace(tzinfo=None)
        else:
            print(f"WARNING: api_dashboard_location - Unexpected timestamp type: {type(recorded_at)}, value: {recorded_at}", file=sys.stderr)
            continue
        
        if not parsed_dt:
            continue
        
        # Track latest timestamp for is_live check
        if not latest_timestamp or parsed_dt > latest_timestamp:
            latest_timestamp = parsed_dt
        
        # Round to interval (handle naive datetime)
        interval_seconds = interval_minutes * 60
        ts = parsed_dt.timestamp()
        rounded_ts = (ts // interval_seconds) * interval_seconds
        rounded_timestamp = datetime.fromtimestamp(rounded_ts)
        
        metric = (r.get('device_type') or '').lower()
        val = r.get('value')
        
        if not metric:
            print(f"WARNING: api_dashboard_location - Row missing device_type, keys: {list(r.keys())}", file=sys.stderr)
            continue
        
        try:
            val = None if val is None else float(val)
        except (ValueError, TypeError) as e:
            print(f"WARNING: api_dashboard_location - Could not convert value '{val}' to float: {e}", file=sys.stderr)
            val = None
        
        if val is None:
            continue
        
        if rounded_timestamp not in time_buckets:
            time_buckets[rounded_timestamp] = {}
        
        # Store sum and count for averaging
        if metric not in time_buckets[rounded_timestamp]:
            time_buckets[rounded_timestamp][metric] = {'sum': 0.0, 'count': 0}
        
        time_buckets[rounded_timestamp][metric]['sum'] += val
        time_buckets[rounded_timestamp][metric]['count'] += 1
    
    # Check if data is live (within last 5 minutes based on database timestamp)
    is_live = False
    
    # Get sensors at this location for this user (needed for other processing)
    if user_id:
        # Get sensors at this location for this user
        location_filter_check = None if location == 'Unassigned' else location
        user_sensors_at_location = []
        all_user_sensors = list_sensors()
        for s in all_user_sensors:
            if s.get('user_id') == user_id and s.get('status') == 'active':
                s_location = s.get('location') or 'Unassigned'
                if location_filter_check:
                    if s_location == location_filter_check:
                        user_sensors_at_location.append(s.get('device_id'))
                else:
                    if s_location == 'Unassigned':
                        user_sensors_at_location.append(s.get('device_id'))
        
        # Note: Cache check removed - we only check database timestamps for is_live status
        # to avoid false positives when simulation/data feed stops but cache still has old data
    
    # Check database timestamp to determine if data is live
    if latest_timestamp:
        # Ensure both are naive datetimes for comparison
        now = datetime.now()
        if latest_timestamp.tzinfo is not None:
            latest_timestamp = latest_timestamp.replace(tzinfo=None)
        time_since_latest = (now - latest_timestamp).total_seconds()
        # Use 5 minutes threshold (data is considered live if within last 5 minutes)
        is_live = time_since_latest < 300  # 5 minutes
        print(f"DEBUG: api_dashboard_location - Latest DB timestamp: {latest_timestamp}, time since: {time_since_latest:.1f}s, is_live: {is_live}", file=sys.stderr)
    else:
        # No database timestamp means no data, so not live
        is_live = False
        print(f"DEBUG: api_dashboard_location - No DB timestamp, is_live: False", file=sys.stderr)
    sys.stderr.flush()
    
    # Sort timestamps
    sorted_timestamps = sorted(time_buckets.keys())
    labels = [ts.strftime(label_format) for ts in sorted_timestamps]
    
    # Get metrics present and calculate averages + safety in one pass
    metrics_present = set()
    safety_status = []
    default_thresholds = _build_type_defaults_map()
    
    # Pre-calculate averages and safety
    timestamp_averages = {}  # {timestamp: {metric: avg_value}}
    for timestamp in sorted_timestamps:
        timestamp_data = time_buckets[timestamp]
        timestamp_values = {}
        
        for metric, stats in timestamp_data.items():
            if stats['count'] > 0:
                avg_val = stats['sum'] / stats['count']
                timestamp_values[metric] = avg_val
                metrics_present.add(metric)
        
        timestamp_averages[timestamp] = timestamp_values
        
        # Calculate safety using default thresholds
        try:
            safe, reasons = compute_safety(timestamp_values, default_thresholds)
            safety_status.append(1 if safe else 0)
        except Exception:
            safety_status.append(0)
    
    # Build datasets for each metric
    known_order = ['tds', 'ph', 'turbidity', 'temperature', 'dissolved_oxygen', 'conductivity', 'ammonia', 'pressure', 'nitrate', 'nitrite', 'orp', 'chlorine', 'salinity', 'flow']
    metrics_sorted = sorted(metrics_present, key=lambda m: (known_order.index(m) if m in known_order else 999, m))
    
    def display_label(metric: str) -> str:
        mapping = {
            'tds': 'TDS',
            'ph': 'pH',
            'turbidity': 'Turbidity',
            'temperature': 'Temperature',
            'dissolved_oxygen': 'Dissolved Oxygen',
            'conductivity': 'Conductivity',
            'ammonia': 'Ammonia',
            'pressure': 'Pressure',
            'nitrate': 'Nitrate',
            'nitrite': 'Nitrite',
            'orp': 'ORP',
            'chlorine': 'Chlorine',
            'salinity': 'Salinity',
            'flow': 'Flow',
        }
        return mapping.get(metric, metric.replace('_', ' ').title())
    
    def color_for_metric(metric: str) -> str:
        palette = {
            'tds': '#0ea5e9',
            'ph': '#22c55e',
            'turbidity': '#f59e0b',
            'temperature': '#ef4444',
            'dissolved_oxygen': '#6366f1',
            'conductivity': '#14b8a6',
        }
        default_cycle = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#6366f1', '#14b8a6', '#8b5cf6', '#10b981']
        return palette.get(metric) or default_cycle[hash(metric) % len(default_cycle)]
    
    # Build datasets efficiently using pre-calculated averages
    datasets = []
    for m in metrics_sorted:
        data_points = []
        for timestamp in sorted_timestamps:
            avg_val = timestamp_averages.get(timestamp, {}).get(m)
            data_points.append(round(avg_val, 2) if avg_val is not None else None)
        
        datasets.append({
            'label': display_label(m),
            'metric': m,
            'color': color_for_metric(m),
            'data': data_points,
        })
    
    # Add safety datasets
    safe_data = [1 if status == 1 else None for status in safety_status]
    unsafe_data = [0 if status == 0 else None for status in safety_status]
    
    datasets.append({
        'label': 'Safe ✓',
        'metric': 'safety_safe',
        'color': '#22c55e',
        'data': safe_data,
        'yAxisID': 'y1',
        'borderWidth': 3,
        'pointRadius': 5,
        'pointHoverRadius': 7,
    })
    
    datasets.append({
        'label': 'Unsafe ✗',
        'metric': 'safety_unsafe',
        'color': '#ef4444',
        'data': unsafe_data,
        'yAxisID': 'y1',
        'borderWidth': 3,
        'pointRadius': 5,
        'pointHoverRadius': 7,
    })
    
    # Debug logging
    print(f"DEBUG: api_dashboard_location - Generated {len(datasets)} datasets, {len(labels)} labels, {len(time_buckets)} time buckets", file=sys.stderr)
    if not datasets:
        print(f"WARNING: api_dashboard_location - No datasets generated for location '{location}'", file=sys.stderr)
        print(f"DEBUG: api_dashboard_location - metrics_present: {metrics_present}, sorted_timestamps: {len(sorted_timestamps) if 'sorted_timestamps' in locals() else 0}", file=sys.stderr)
        print(f"DEBUG: api_dashboard_location - Input rows: {len(rows) if rows else 0}, time_buckets: {len(time_buckets)}", file=sys.stderr)
    sys.stderr.flush()
    
    response = jsonify({
        'location': location,
        'labels': labels,
        'datasets': datasets,
        'safety_status': safety_status,
        'is_live': is_live,
        'user_id': user_id,
        'username': username,
        'row_count': len(rows) if rows else 0,
        'point_count': len(sorted_timestamps) if 'sorted_timestamps' in locals() else 0,
        'time_buckets': len(time_buckets),
        'metrics_present': list(metrics_present) if 'metrics_present' in locals() else []
    })
    
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Authentication routes are now in routes/auth.py
from routes.auth import register_login_routes
register_login_routes(app)

# readings route is now in routes/dashboard.py

# Simple API routes are now in routes/api.py
from routes.api import register_api_routes
register_api_routes(app, get_user_key, add_user_key, user_pending_keys, pending_keys)

# api_public_active_sensors is now in routes/api.py

@app.route('/api/active_sensors')
@login_required
def api_active_sensors():
    """API endpoint to get active sensors with latest readings for current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        import sys
        # Get user's active sensors
        all_sensors = list_sensors()
        user_sensors = [s for s in all_sensors if s.get('user_id') == user_id and s.get('status') == 'active']
        
        print(f"DEBUG: api_active_sensors - Found {len(user_sensors)} active sensors for user {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        # Get latest readings for each sensor from user-specific cache first
        active_sensors = []
        sensors_with_cache_data = set()
        
        if user_id in user_latest_by_sensor and user_sensors:
            for sensor in user_sensors:
                device_id = sensor.get('device_id')
                if device_id in user_latest_by_sensor[user_id]:
                    sensor_data = user_latest_by_sensor[user_id][device_id]
                    # Only use cache if value is not None (has actual data)
                    if sensor_data.get('value') is not None:
                        active_sensors.append({
                            'device_id': device_id,
                            'device_type': sensor_data.get('device_type') or sensor.get('device_type'),
                            'location': sensor_data.get('location') or sensor.get('location') or 'Unassigned',
                            'value': sensor_data.get('value')
                        })
                        sensors_with_cache_data.add(device_id)
        
        # Always query database to get the latest readings (real-time data)
        # Use the same function that history page uses (list_recent_sensor_data)
        # This ensures consistency and reliability
        print(f"DEBUG: api_active_sensors - Querying database for latest readings...", file=sys.stderr)
        sys.stderr.flush()
        
        try:
            # Get recent sensor data from database (same as history page uses)
            db_readings = list_recent_sensor_data(limit=100, user_id=user_id)
            
            print(f"DEBUG: api_active_sensors - Retrieved {len(db_readings)} readings from database", file=sys.stderr)
            sys.stderr.flush()
            app_logger.error(f"DEBUG: api_active_sensors - Retrieved {len(db_readings)} readings from database for user_id={user_id}")
                
            # Build a map of latest reading per device_id
            latest_by_device = {}
            for reading in db_readings:
                device_id = reading.get('device_id')
                if not device_id:
                    continue
                
                # Get the most recent reading for each device
                recorded_at = reading.get('recorded_at')
                if device_id not in latest_by_device:
                    latest_by_device[device_id] = reading
                else:
                    # Compare timestamps to get the latest
                    existing_time = latest_by_device[device_id].get('recorded_at')
                    if recorded_at and existing_time and recorded_at > existing_time:
                        latest_by_device[device_id] = reading
            
            # Convert to active_sensors format - database data takes priority
            # Clear cache-based sensors and rebuild from database
            active_sensors = []
            for device_id, reading in latest_by_device.items():
                value = reading.get('value')  # Already decrypted by list_recent_sensor_data
                device_type = reading.get('device_type')
                location = reading.get('location') or 'Unassigned'
                
                # Find matching sensor info if available
                sensor_info = next((s for s in user_sensors if s.get('device_id') == device_id), None)
                if sensor_info:
                    device_type = device_type or sensor_info.get('device_type')
                    location = location or sensor_info.get('location') or 'Unassigned'
                
                recorded_at = reading.get('recorded_at')
                # Convert datetime to ISO string if it's a datetime object
                if recorded_at:
                    if hasattr(recorded_at, 'isoformat'):
                        recorded_at = recorded_at.isoformat()
                    elif isinstance(recorded_at, str):
                        # Already a string, keep as is
                        pass
                
                active_sensors.append({
                    'device_id': device_id,
                    'device_type': device_type,
                    'location': location,
                    'value': float(value) if value is not None else None,
                    'recorded_at': recorded_at
                })
                print(f"DEBUG: api_active_sensors - Added sensor {device_id}: value={value}, location={location}", file=sys.stderr)
                app_logger.error(f"DEBUG: api_active_sensors - Added sensor {device_id}: value={value}, location={location}, device_type={device_type}")
            
            # If we still have active sensors from list_sensors but no database readings,
            # include them with null values
            for sensor in user_sensors:
                device_id = sensor.get('device_id')
                if device_id not in latest_by_device:
                    # Check if already in active_sensors
                    if not any(s.get('device_id') == device_id for s in active_sensors):
                        active_sensors.append({
                            'device_id': device_id,
                            'device_type': sensor.get('device_type'),
                            'location': sensor.get('location') or 'Unassigned',
                            'value': None,
                            'recorded_at': None
                        })
                
        except Exception as db_err:
            import traceback
            print(f"ERROR: api_active_sensors - Database error: {db_err}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            sys.stderr.flush()
            # Fallback: if database query fails, use cache data we already have
            pass
        
        
        print(f"DEBUG: api_active_sensors - Returning {len(active_sensors)} sensors", file=sys.stderr)
        sys.stderr.flush()
        app_logger.error(f"DEBUG: api_active_sensors - Returning {len(active_sensors)} sensors for user_id={user_id}")
        if active_sensors:
            for s in active_sensors:
                msg = f"DEBUG: api_active_sensors - Sensor: {s.get('device_id')}, value: {s.get('value')}, location: {s.get('location')}"
                print(msg, file=sys.stderr)
                app_logger.error(msg)
        else:
            msg = f"DEBUG: api_active_sensors - WARNING: No sensors to return for user {user_id}, user_sensors count: {len(user_sensors)}, sensors_with_cache_data: {len(sensors_with_cache_data)}"
            print(msg, file=sys.stderr)
            app_logger.error(msg)
        sys.stderr.flush()
        
        result = {
            'active_sensors': active_sensors
        }
        app_logger.error(f"DEBUG: api_active_sensors - Returning JSON response with {len(active_sensors)} sensors")
        if active_sensors:
            for s in active_sensors[:5]:  # Log first 5 sensors
                app_logger.error(f"DEBUG: api_active_sensors - Sensor in response: device_id={s.get('device_id')}, value={s.get('value')}, location={s.get('location')}, device_type={s.get('device_type')}")
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"ERROR: api_active_sensors - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/latest')
@login_required
def api_latest():
    """API endpoint to get latest safety status for current user, optionally filtered by location."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    # Get optional location parameter
    location_filter = request.args.get('location', '').strip()
    
    try:
        import sys
        # Get user's latest data from cache first
        if user_id in user_latest_data:
            latest = user_latest_data[user_id]
        else:
            latest = latest_data  # Fallback to global
        
        # Get user's latest by metric for threshold checking
        if user_id in user_latest_by_metric:
            user_metric_data = user_latest_by_metric[user_id]
        else:
            user_metric_data = latest_by_metric  # Fallback to global
        
        # If cache is empty, query database for latest readings
        if not user_metric_data or not any(v.get("value") is not None for v in user_metric_data.values() if v):
            print(f"DEBUG: api_latest - Cache empty, querying database for user {user_id}...", file=sys.stderr)
            sys.stderr.flush()
            
            # Get latest readings from database (filter by location if specified)
            if location_filter:
                from db import list_recent_sensor_data_by_location
                db_readings = list_recent_sensor_data_by_location(location_filter, limit=100, user_id=user_id)
            else:
                db_readings = list_recent_sensor_data(limit=100, user_id=user_id)
            
            # Build metric data from database readings
            user_metric_data = {}
            latest_dict = {}
            
            for reading in db_readings:
                device_type = (reading.get('device_type') or '').lower()
                device_id = reading.get('device_id')
                value = reading.get('value')
                
                if device_type and value is not None:
                    try:
                        float_value = float(value)
                        # Store latest value per metric (keep most recent if multiple sensors for same metric)
                        if device_type not in user_metric_data:
                            user_metric_data[device_type] = {
                                'value': float_value,
                                'sensor_id': device_id
                            }
                        latest_dict[device_type] = float_value
                    except (ValueError, TypeError):
                        pass
            
            # Update latest dict with all metrics
            latest = latest_dict if latest_dict else latest
        
        # Build aggregate values (filtered by location if specified)
        agg_values = {}
        for metric, entry in user_metric_data.items():
            if entry and entry.get("value") is not None:
                # If location filter is specified, we need to check sensor location
                # For now, we'll use the cached data which may include all locations
                # The location filtering happens at the database query level above
                agg_values[metric] = entry.get("value")
        
        # Build thresholds
        agg_thresholds = {}
        for metric, entry in user_metric_data.items():
            sid = (entry or {}).get("sensor_id")
            tmap = build_effective_thresholds_for_sensor(sid)
            if tmap and metric in tmap:
                agg_thresholds[metric] = tmap[metric]
        
        # Fallback to defaults
        defaults = _build_type_defaults_map()
        for metric in agg_values.keys():
            if metric not in agg_thresholds and metric in defaults:
                agg_thresholds[metric] = defaults[metric]
        
        # Compute safety
        safe, reasons = compute_safety(agg_values, agg_thresholds)
        
        location_info = f" (location: {location_filter})" if location_filter else " (all locations)"
        print(f"DEBUG: api_latest - Returning data for user {user_id}{location_info}, metrics: {list(agg_values.keys())}, safe: {safe}", file=sys.stderr)
        sys.stderr.flush()
        
        return jsonify({
            'safe_to_drink': safe,
            'reasons': reasons if not safe else [],
            'latest': latest,
            'location': location_filter if location_filter else None
        })
    except Exception as e:
        import traceback
        print(f"ERROR: api_latest - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/reading_request', methods=['POST'])
@login_required
def api_reading_request():
    """API endpoint to request a reading from sensors at a specific location."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        data = request.get_json(force=True, silent=True) or {}
        location = sanitize_input(data.get('location') or '')
        
        if not location:
            return jsonify({"error": "Location is required"}), 400
        
        # Get user's sensors at this location
        all_sensors = list_sensors()
        location_filter = None if location == 'Unassigned' else location
        user_sensors = [
            s for s in all_sensors 
            if s.get('user_id') == user_id 
            and s.get('status') == 'active'
            and ((location_filter and s.get('location') == location_filter) or (not location_filter and (not s.get('location') or s.get('location') == '')))
        ]
        
        if not user_sensors:
            return jsonify({"error": f"No active sensors found for location '{location}'"}), 404
        
        # Check if MQTT is configured
        mqtt_host = os.environ.get('MQTT_HOST')
        if not mqtt_host:
            return jsonify({"error": "MQTT_HOST not configured on server"}), 500
        
        # Send MQTT reading request for each sensor at this location
        topic_base = os.environ.get('MQTT_READING_REQUEST_TOPIC_BASE', 'reading_request')
        successful_requests = 0
        failed_requests = []
        
        try:
            import paho.mqtt.publish as publish
            publish_kwargs = _get_mqtt_publish_kwargs()
            
            for sensor in user_sensors:
                device_id = sensor.get('device_id')
                if not device_id:
                    continue
                
                try:
                    # Create topic: reading_request/{device_id}/request
                    topic = f"{topic_base}/{device_id}/request"
                    
                    # Create payload with location and device info
                    payload = json.dumps({
                        "device_id": device_id,
                        "location": location,
                        "action": "request",
                        "user_id": str(user_id),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Publish MQTT message
                    publish.single(topic, payload, qos=1, **publish_kwargs)
                    successful_requests += 1
                    
                    print(f"[Reading Request] ✅ Sent MQTT message to {topic} for device {device_id} at location {location}")
                    
                except Exception as e:
                    error_msg = f"Failed to send request for {device_id}: {str(e)}"
                    failed_requests.append({"device_id": device_id, "error": str(e)})
                    print(f"[Reading Request] ❌ {error_msg}")
            
            if successful_requests == 0:
                return jsonify({
                    "error": "Failed to send reading requests to any sensors",
                    "failed_requests": failed_requests
                }), 500
            
            response = {
                "status": "sent",
                "location": location,
                "sensor_count": len(user_sensors),
                "successful_requests": successful_requests,
                "failed_requests": failed_requests if failed_requests else None
            }
            
            return jsonify(response)
            
        except ImportError:
            return jsonify({"error": "paho-mqtt library not available"}), 500
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Reading Request] ❌ MQTT publish failed: {e}")
            print(f"[Reading Request] Error details:\n{error_details}")
            return jsonify({"error": f"MQTT publish failed: {str(e)}"}), 500
    except Exception as e:
        import traceback
        print(f"ERROR: api_reading_request - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/history')
@login_required
def history():
    """Display historical sensor readings."""
    user_id = session.get('user_id')
    if not user_id:
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Get filter parameters
    location_filter = request.args.get('location', '').strip()
    type_filter = request.args.get('type', '').strip()
    status_filter = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    q = request.args.get('q', '').strip()
    
    # Get user's sensor data
    try:
        import sys
        # Get all locations for this user
        locations_data = get_locations_with_status(user_id=user_id)
        locations = [loc.get('location') for loc in locations_data] if locations_data else []
        
        # Get all device types from user's sensors
        all_sensors = list_sensors()
        user_sensors = [s for s in all_sensors if s.get('user_id') == user_id]
        device_types = sorted(list(set([s.get('device_type', '').lower() for s in user_sensors if s.get('device_type')])))
        statuses = ['normal', 'warning', 'critical']
        
        # Get historical data - always load data, not just when filters are provided
        # Use a larger limit to get more historical data
        limit = 5000 if not (date_from or date_to) else 10000  # More data when no date filter
        date_from_dt = None
        date_to_dt = None
        
        try:
            if date_from:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']:
                    try:
                        date_from_dt = datetime.strptime(date_from, fmt)
                        break
                    except ValueError:
                        continue
                if not date_from_dt:
                    date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    if date_from_dt.tzinfo:
                        date_from_dt = date_from_dt.replace(tzinfo=None)
            
            if date_to:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']:
                    try:
                        date_to_dt = datetime.strptime(date_to, fmt)
                        break
                    except ValueError:
                        continue
                if not date_to_dt:
                    date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    if date_to_dt.tzinfo:
                        date_to_dt = date_to_dt.replace(tzinfo=None)
                # Add one day to include the entire end date if it's just a date (no time)
                if date_to and len(date_to) <= 10:  # Just date, no time
                    date_to_dt = date_to_dt + timedelta(days=1)
        except Exception as e:
            print(f"WARNING: history - Invalid date format: {e}, date_from: {date_from}, date_to: {date_to}", file=sys.stderr)
            sys.stderr.flush()
        
        # Get readings based on filters
        if location_filter:
            readings = list_recent_sensor_data_by_location(
                location=location_filter,
                limit=limit,
                user_id=user_id,
                date_from=date_from_dt,
                date_to=date_to_dt
            )
        else:
            readings = list_recent_sensor_data(limit=limit, user_id=user_id)
        
        # Apply additional filters
        sensor_rows = []
        for row in readings:
            # Filter by type
            if type_filter and (row.get('device_type') or '').lower() != type_filter.lower():
                continue
            
            # Filter by status
            if status_filter and (row.get('status') or 'normal').lower() != status_filter.lower():
                continue
            
            # Filter by search query
            if q:
                q_lower = q.lower()
                device_id = (row.get('device_id') or '').lower()
                device_type = (row.get('device_type') or '').lower()
                location = (row.get('location') or '').lower()
                if q_lower not in device_id and q_lower not in device_type and q_lower not in location:
                    continue
            
            sensor_rows.append(row)
        
        # Pagination logic
        per_page = int(request.args.get('per', 20))
        page = int(request.args.get('page', 1))
        
        # Calculate total and pagination
        total = len(sensor_rows)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1  # Ceiling division
        
        # Validate page number
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        # Slice the data for the current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_rows = sensor_rows[start_idx:end_idx]
        
        print(f"DEBUG: history - Returning {len(paginated_rows)} rows (page {page}/{total_pages}) for user {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        return render_template('history.html', 
                             locations=locations,
                             device_types=device_types,
                             statuses=statuses,
                             location_filter=location_filter,
                             type_filter=type_filter,
                             status_filter=status_filter,
                             date_from=date_from,
                             date_to=date_to,
                             q=q,
                             sensor_rows=paginated_rows,
                             total=total,
                             page=page,
                             per=per_page,
                             total_pages=total_pages)
    except Exception as e:
        import traceback
        print(f"ERROR: history route - {e}")
        traceback.print_exc()
        flash('Error loading history data.', 'error')
        return render_template('history.html', 
                             locations=[], 
                             device_types=[],
                             statuses=[],
                             sensor_rows=[])

def compute_public_key_fingerprint(public_key_pem: str | None) -> str | None:
    """Compute a short fingerprint from a public key PEM string."""
    if not public_key_pem:
        return None
    try:
        # Compute SHA-256 hash of the key
        key_bytes = public_key_pem.encode('utf-8') if isinstance(public_key_pem, str) else public_key_pem
        key_hash = hashlib.sha256(key_bytes).hexdigest()
        # Return first 16 characters as fingerprint
        return key_hash[:16].upper()
    except Exception:
        return None

# Sensor routes are now in routes/sensors.py
from routes.sensors import register_sensor_routes
register_sensor_routes(
    app,
    get_user_key,
    get_user_key_file,
    notify_raspbian_key_cleanup,
    _build_type_defaults_map,
    build_effective_thresholds_for_sensor,
    compute_public_key_fingerprint
)

# Sensor routes (sensors, sensors/register, sensors/delete, sensors/update) are now in routes/sensors.py

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    user_id = session.get('user_id')
    username = session.get('user')
    
    if not user_id or not username:
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    try:
        user = get_user_by_username(username)
        if not user or user.get('sr_no') != user_id:
            flash('User not found', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            error = None
            email = sanitize_input(request.form.get('email') or '')
            name = sanitize_input(request.form.get('name') or '')
            username_new = sanitize_input(request.form.get('username') or '')
            current_password = request.form.get('current_password') or ''
            new_password = request.form.get('new_password') or ''
            confirm_password = request.form.get('confirm_password') or ''
            
            # Validate email
            if email != user.get('email'):
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    error = email_error or 'Invalid email address'
                else:
                    # Check if email is already taken
                    existing_email = get_user_by_email(email)
                    if existing_email and existing_email.get('sr_no') != user_id:
                        error = 'Email already registered'
            
            # Validate name
            if name != user.get('name'):
                name_valid, name_error = validate_name(name)
                if not name_valid and not error:
                    error = name_error or 'Invalid name'
            
            # Validate username
            if username_new != username:
                username_valid, username_error = validate_username(username_new)
                if not username_valid and not error:
                    error = username_error or 'Invalid username'
                else:
                    # Check if username is already taken
                    existing_user = get_user_by_username(username_new)
                    if existing_user and existing_user.get('sr_no') != user_id:
                        error = 'Username already taken'
            
            # Handle password change
            if new_password:
                if not current_password:
                    error = 'Current password is required to change password'
                elif not check_password_hash(user.get('password', ''), current_password):
                    error = 'Current password is incorrect'
                elif new_password != confirm_password:
                    error = 'New passwords do not match'
                else:
                    password_valid, password_error = validate_password(new_password)
                    if not password_valid and not error:
                        error = password_error or 'Invalid password'
            
            if not error:
                # Update profile - use current username to find the record
                if update_user_profile(username, email=email, name=name, username=username_new):
                    # Update password if provided
                    if new_password:
                        # Hash the new password before updating
                        password_hash = generate_password_hash(new_password)
                        # Use new username (after profile update, this is the username in DB)
                        if not update_user_password(username_new, password_hash):
                            error = 'Failed to update password'
                    
                    if not error:
                        # Update session with new username if it changed
                        if username_new != username:
                        session['user'] = username_new
                        flash('Profile updated successfully!', 'success')
                        return redirect(url_for('profile'))
                    else:
                        # Profile updated but password update failed - re-fetch user with new username
                        if username_new != username:
                            session['user'] = username_new
                        # Re-fetch user data to show updated profile info
                        user = get_user_by_username(username_new)
                        if not user:
                            # Fallback to original user if fetch fails
                            user = get_user_by_username(username)
                else:
                    error = 'Failed to update profile'
            
            if error:
                flash(error, 'error')
        
        return render_template('profile.html', user=user)
    except Exception as e:
        import traceback
        print(f"ERROR: profile route - {e}")
        traceback.print_exc()
        flash('Error loading profile.', 'error')
        user = get_user_by_username(username) if username else None
        return render_template('profile.html', user=user or {})

# api_sensor_type, api_key_upload_status, api_key_upload_fetch, api_sensor_key_timestamp, test_env_vars, test_mqtt_config are now in routes/api.py

@app.route('/test-db', methods=['GET'])
def test_db_connection():
    """Test database connection endpoint - useful for debugging"""
    try:
        import connect
        from db import get_pool, _get_connection, _return_connection, _get_cursor
        
        result = {
            "status": "testing",
            "config": {
                "host": connect.DB_HOST,
                "port": connect.DB_PORT,
                "user": connect.DB_USER,
                "database": connect.DB_NAME,
                "password_set": bool(connect.DB_PASSWORD)
            },
            "tests": {}
        }
        
        # Test 1: Connection pool
        try:
            pool = get_pool()
            if pool:
                result["tests"]["connection_pool"] = "✅ Created successfully"
            else:
                result["tests"]["connection_pool"] = "⚠️ Pool is None (using connect.py)"
        except Exception as e:
            result["tests"]["connection_pool"] = f"❌ Failed: {str(e)}"
        
        # Test 2: Direct connection
        try:
            conn = _get_connection(pool) if pool else connect.get_connection()
            cursor = _get_cursor(conn, dictionary=True) if pool else conn.cursor(dictionary=True)
            cursor.execute("SELECT DATABASE() as db, VERSION() as version, NOW() as current_time")
            db_info = cursor.fetchone()
            cursor.close()
            _return_connection(pool, conn) if pool else connect.close_connection(conn)
            
            result["tests"]["direct_connection"] = "✅ Connected successfully"
            result["database_info"] = {
                "database": db_info.get('db') if isinstance(db_info, dict) else db_info[0],
                "version": db_info.get('version') if isinstance(db_info, dict) else db_info[1],
                "server_time": str(db_info.get('current_time') if isinstance(db_info, dict) else db_info[2])
            }
        except Exception as e:
            result["tests"]["direct_connection"] = f"❌ Failed: {str(e)}"
        
        # Test 3: Query execution
        try:
            conn = _get_connection(pool) if pool else connect.get_connection()
            cursor = _get_cursor(conn, dictionary=True) if pool else conn.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            cursor.close()
            _return_connection(pool, conn) if pool else connect.close_connection(conn)
            
            table_names = [list(t.values())[0] if isinstance(t, dict) else t[0] for t in tables]
            result["tests"]["query_execution"] = f"✅ Success - Found {len(table_names)} tables"
            result["tables"] = table_names[:10]  # Show first 10 tables
        except Exception as e:
            result["tests"]["query_execution"] = f"❌ Failed: {str(e)}"
        
        # Test 4: Using connect.py test function
        try:
            if connect.test_connection():
                result["tests"]["connect_test"] = "✅ connect.test_connection() passed"
            else:
                result["tests"]["connect_test"] = "❌ connect.test_connection() failed"
        except Exception as e:
            result["tests"]["connect_test"] = f"❌ Error: {str(e)}"
        
        # Determine overall status
        all_passed = all("✅" in str(v) for v in result["tests"].values())
        result["status"] = "✅ All tests passed!" if all_passed else "⚠️ Some tests failed"
        
        return jsonify(result), 200 if all_passed else 500
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "❌ Error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == '__main__':
    # Start MQTT key subscriber if configured
    # Use wrapper function that calls extracted utility with app dependencies
    start_mqtt_key_subscriber()
    # Start MQTT sensor subscriber if configured
    # Use wrapper function that calls extracted utility with app dependencies
    start_mqtt_sensor_subscriber()
    
    # Default to 0.0.0.0 to accept connections from network (not just localhost)
    # Set FLASK_HOST=127.0.0.1 in environment if you want localhost-only
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', os.environ.get('PORT', '5000')))
    debug_env = str(os.environ.get('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug_env, use_reloader=debug_env)
