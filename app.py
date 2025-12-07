from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from encryption_utils import decrypt_data
import base64
import hashlib
import json
import os
import secrets
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

from db import (
    # insert_reading,  # Removed - using sensor_data table only
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
    # list_recent_water_readings,  # Removed - using sensor_data table only
    create_device_session,
    get_device_session,
    update_device_session,
    delete_device_session,
    cleanup_expired_sessions,
)

app = Flask(__name__)

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
    
    error_msg = f"ERROR: Unhandled exception in route {request.path} [{request.method}]: {str(e)}"
    exception_type = type(e).__name__
    full_traceback = traceback.format_exc()
    
    # Log to file
    app_logger.error(f"{error_msg}\nException type: {exception_type}\n{full_traceback}")
    
    # Also print to stderr (for Apache error log)
    print(error_msg, file=sys.stderr)
    print(f"Exception type: {exception_type}", file=sys.stderr)
    print(full_traceback, file=sys.stderr)
    sys.stderr.flush()
    
    # In debug mode, show more details
    debug_mode = str(os.environ.get('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
    if debug_mode:
        return f"Internal Server Error: {str(e)}\n\n{full_traceback}", 500
    return f"Internal Server Error: {str(e)}\n\nCheck Apache error log or flask_error.log file for details.", 500

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
provision_last_sent = {}
device_challenges = {}

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


def _get_mqtt_publish_kwargs():
    """Get MQTT publish configuration including TLS settings."""
    kwargs = {}
    
    mqtt_host = os.environ.get('MQTT_HOST')
    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    
    kwargs['hostname'] = mqtt_host
    kwargs['port'] = mqtt_port
    
    # Authentication
    if mqtt_user and mqtt_password:
        kwargs['auth'] = {'username': mqtt_user, 'password': mqtt_password}
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    if mqtt_use_tls:
        import ssl
        mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
        mqtt_certfile = os.environ.get('MQTT_CERTFILE')
        mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
        mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')
        
        tls_config = {}
        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
            tls_config['ca_certs'] = mqtt_ca_certs
        if mqtt_certfile and os.path.exists(mqtt_certfile):
            tls_config['certfile'] = mqtt_certfile
        if mqtt_keyfile and os.path.exists(mqtt_keyfile):
            tls_config['keyfile'] = mqtt_keyfile
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        tls_config['insecure'] = mqtt_tls_insecure
        
        kwargs['tls'] = tls_config
    
    return kwargs


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
        return False
    
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        return False
    
    try:
        mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
        mqtt_user = os.environ.get('MQTT_USER')
        mqtt_password = os.environ.get('MQTT_PASSWORD')
        delete_topic = os.environ.get('MQTT_DELETE_TOPIC', 'devices/delete')
        
        client = mqtt.Client()
        if mqtt_user and mqtt_password:
            client.username_pw_set(mqtt_user, mqtt_password)
        
        client.connect(mqtt_host, mqtt_port, 60)
        
        payload = json.dumps({
            'action': 'delete',
            'device_id': device_id,
            'user_id': str(user_id),
            'timestamp': datetime.now().isoformat()
        })
        
        result = client.publish(delete_topic, payload, qos=1)
        client.disconnect()
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"MQTT: Sent key cleanup notification for device '{device_id}' (user: {user_id})")
            return True
        else:
            print(f"MQTT: Failed to send cleanup notification (rc={result.rc})")
            return False
    except Exception as e:
        print(f"MQTT: Error sending cleanup notification: {e}")
        return False


def start_mqtt_key_subscriber():
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

    def _on_connect(client, userdata, flags, rc):
        try:
            client.subscribe(mqtt_topic)
            print(f"MQTT: connected rc={rc}; subscribed to '{mqtt_topic}'")
        except Exception as e:
            print(f"MQTT subscribe error: {e}")

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
            # Accept JSON {"device_id":"...","public_key":"PEM"}
            if text.startswith('{'):
                try:
                    data = json.loads(text)
                    pem = (data.get('public_key') or '').strip()
                    device_id = (data.get('device_id') or device_id or '').strip()
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
                srow = get_sensor_by_device_id(device_id)
            except Exception:
                srow = None
            if srow:
                try:
                    update_sensor_by_device_id(
                        device_id=device_id,
                        location=srow.get('location'),
                        status=srow.get('status'),
                        public_key=pem,
                        min_threshold=srow.get('min_threshold'),
                        max_threshold=srow.get('max_threshold'),
                    )
                    print(f"MQTT: updated public key in DB for sensor '{device_id}'")
                except Exception as e:
                    print(f"MQTT DB update error for {device_id}: {e}")
            else:
                print(f"MQTT: received key for unregistered device '{device_id}' (stored pending)")
        except Exception as e:
            print(f"MQTT message error: {e}")

    def _run():
        try:
            client = mqtt.Client()
            
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
            
            client.on_connect = _on_connect
            client.on_message = _on_message
            client.connect(mqtt_host, mqtt_port, keepalive=60)
            print(f"MQTT: Connecting to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})")
            client.loop_forever()
        except Exception as e:
            print(f"MQTT thread exit: {e}")
            import traceback
            traceback.print_exc()

    t = threading.Thread(target=_run, name='mqtt-key-subscriber', daemon=True)
    t.start()
    mqtt_thread_started = True


 

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
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "  # Allow Chart.js CDN
        "style-src 'self' 'unsafe-inline'; "   # unsafe-inline needed for inline styles
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

def login_required(view_func):
    def wrapped_view(*args, **kwargs):
        import sys
        # Check session
        username = session.get('user')
        user_id = session.get('user_id')
        
        print(f"DEBUG: login_required - username: {username}, user_id: {user_id}, path: {request.path}", file=sys.stderr)
        sys.stderr.flush()
        
        if not username:
            next_url = request.path
            return redirect(url_for('login', next=next_url))
        
        # Ensure user_id is set in session (critical for user isolation)
        if not user_id:
            user = get_user_by_username(username)
            if user:
                session['user_id'] = user['sr_no']
                session.permanent = True  # Make session persistent
                print(f"DEBUG: login_required - Set user_id {user['sr_no']} for username {username}", file=sys.stderr)
                sys.stderr.flush()
            else:
                print(f"ERROR: login_required - User '{username}' not found in database!", file=sys.stderr)
                sys.stderr.flush()
                session.clear()  # Clear invalid session
                return redirect(url_for('login'))
        
        # Double-check: verify user_id matches username (security check)
        if user_id:
            user = get_user_by_username(username)
            if user and user['sr_no'] != user_id:
                print(f"ERROR: login_required - Session mismatch! username={username}, session_user_id={user_id}, db_user_id={user['sr_no']}", file=sys.stderr)
                sys.stderr.flush()
                session.clear()  # Clear corrupted session
                return redirect(url_for('login'))
        
        return view_func(*args, **kwargs)
    # Preserve original function name for Flask routing/debug
    wrapped_view.__name__ = getattr(view_func, '__name__', 'wrapped_view')
    return wrapped_view


def _issue_device_challenge(device_id: str):
    challenge_id = secrets.token_urlsafe(16)
    challenge = secrets.token_urlsafe(32)
    device_challenges[challenge_id] = {
        'device_id': device_id,
        'challenge': challenge,
        'expires_at': datetime.utcnow() + timedelta(seconds=DEVICE_CHALLENGE_TTL_SECONDS),
    }
    return challenge_id, challenge


def _validate_device_session(session_token: Optional[str], device_id: Optional[str], counter_value):
    """Validate device session from database. Returns (is_valid, reason)."""
    if not session_token:
        return False, "missing_session"
    
    # Get session from database
    sess = get_device_session(session_token)
    if not sess:
        return False, "invalid_session"
    
    # Check device match
    if not device_id or sess.get('device_id') != device_id:
        return False, "device_mismatch"
    
    # Check expiration (handle both datetime object and string)
    expires_at = sess.get('expires_at')
    if not isinstance(expires_at, datetime):
        if isinstance(expires_at, str):
            try:
                # Try multiple formats
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                    try:
                        expires_at = datetime.strptime(expires_at, fmt)
                        break
                    except ValueError:
                        continue
                if isinstance(expires_at, str):
                    expires_at = datetime.utcnow()
            except Exception:
                expires_at = datetime.utcnow()
        else:
            expires_at = datetime.utcnow()
    
    if datetime.utcnow() > expires_at:
        # Clean up expired session
        try:
            delete_device_session(session_token)
        except Exception:
            pass
        return False, "session_expired"
    
    # Validate counter if provided
    if counter_value is not None:
        try:
            cval = int(counter_value)
        except Exception:
            return False, "counter_invalid"
        last = int(sess.get('counter') or 0)
        if cval <= last:
            return False, "counter_reused"
        
        # Update session with new counter and sliding expiration
        new_expires_at = datetime.utcnow() + timedelta(seconds=DEVICE_SESSION_TTL_SECONDS)
        update_device_session(session_token, cval, new_expires_at)
    else:
        # Still update expiration on use (sliding expiration)
        new_expires_at = datetime.utcnow() + timedelta(seconds=DEVICE_SESSION_TTL_SECONDS)
        update_device_session(session_token, sess.get('counter', 0), new_expires_at)
    
    return True, "ok"


@app.route('/api/device/session/request', methods=['GET'])
def api_device_session_request():
    try:
        device_id = sanitize_input(request.args.get('device_id') or '')
        device_id_valid, device_id_error = validate_device_id(device_id)
        if not device_id_valid:
            return jsonify({"error": device_id_error or "Invalid device_id."}), 400
        
        # Multiple users can have the same device_id, so check all active sensors
        try:
            all_sensors = list_sensors()
        except Exception as db_err:
            print(f"ERROR: Database error in session request: {db_err}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Database error occurred"}), 500
        
        matching_sensors = [s for s in (all_sensors or []) if s.get('device_id', '').lower() == device_id.lower() and s.get('status') == 'active']
        if not matching_sensors:
            return jsonify({"error": "device not active or not found"}), 403
        
        # Issue challenge - signature verification in establish will identify which sensor
        try:
            challenge_id, challenge = _issue_device_challenge(device_id)
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
    all_sensors = list_sensors()
    matching_sensors = [s for s in all_sensors if s.get('device_id', '').lower() == device_id.lower() and s.get('status') == 'active']
    if not matching_sensors:
        return jsonify({"error": "device not active or not found"}), 403
    
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
    expires_at = datetime.utcnow() + timedelta(seconds=DEVICE_SESSION_TTL_SECONDS)
    
    for _ in range(max_attempts):
        candidate = secrets.token_urlsafe(48)
        # Check if token exists in database
        existing = get_device_session(candidate)
        if not existing:
            # Try to create session in database
            if create_device_session(candidate, device_id, expires_at):
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
    # Publish a provision request to MQTT so the Pi agent can generate and publish its key
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        return jsonify({"error": "MQTT_HOST not configured on server"}), 500
    
    # Get current user ID
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session invalid"}), 401
    
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    device_id = sanitize_input(data.get('device_id') or '')
    device_id_valid, device_id_error = validate_device_id(device_id)
    if not device_id_valid:
        return jsonify({"error": device_id_error or "Invalid device_id."}), 400
    
    # Prevent duplicate requests within 5 seconds for the same device_id
    last_sent_time = provision_last_sent.get(device_id)
    if last_sent_time:
        time_since_last = (datetime.utcnow() - last_sent_time).total_seconds()
        if time_since_last < 5:
            print(f"[Provision Request] ⏭️  Skipping duplicate request for '{device_id}' (last sent {time_since_last:.1f}s ago)")
            return jsonify({"status": "skipped", "reason": "duplicate_request", "device_id": device_id})
    
    topic_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
    topic = f"{topic_base}/{device_id}/request"
    # Include user_id in payload so Pi can create user folder
    payload = json.dumps({"device_id": device_id, "action": "generate_and_publish_key", "user_id": str(user_id)})
    print(f"[Provision Request] Sending MQTT message:")
    print(f"  Topic: {topic}")
    print(f"  Payload: {payload}")
    print(f"  User ID: {user_id}")
    print(f"  Device ID: {device_id}")
    try:
        import paho.mqtt.publish as publish
        publish_kwargs = _get_mqtt_publish_kwargs()
        publish.single(topic, payload, **publish_kwargs)
        print(f"[Provision Request] ✅ MQTT message sent successfully")
        try:
            provision_last_sent[device_id] = datetime.utcnow()
        except Exception:
            pass
        return jsonify({"status": "sent", "topic": topic, "user_id": str(user_id)})
    except Exception as e:
        print(f"[Provision Request] ❌ MQTT publish failed: {e}")
        return jsonify({"error": f"MQTT publish failed: {e}"}), 500

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
            
            # Cross-check device_type
            payload_device_type = decrypted_data.get("device_type")
            if payload_device_type and payload_device_type.lower() != sensor_row.get('device_type', '').lower():
                return jsonify({"status": "error", "message": "device_type mismatch for sensor."}), 400

            # Optional device session enforcement
            session_token = decrypted_data.get('session_token')
            session_counter = decrypted_data.get('counter')
            if REQUIRE_DEVICE_SESSION:
                ok, reason = _validate_device_session(session_token, sensor_id, session_counter)
                if not ok:
                    return jsonify({"status": "error", "message": f"Device session error: {reason}"}), 401
            elif session_token:
                _validate_device_session(session_token, sensor_id, session_counter)

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
                device_type_lower = device_type.lower()
                # Prefer exact match first
                if device_type in updated_values:
                    value_for_type = updated_values.get(device_type)
                else:
                    # Try case-insensitive match
                    for key, val in updated_values.items():
                        if key and key.lower() == device_type_lower:
                            value_for_type = val
                            break

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
                elif value_for_type is None:
                    msg = f"ERROR: value_for_type is None for device_id: {sensor_id}, device_type: {device_type}, updated_values: {updated_values}\n"
                    print(msg, file=sys.stderr)
                    sys.stderr.flush()
                else:
                    msg = f"DEBUG: Attempting insert_sensor_data - device_id: {sensor_id}, sensor_db_id: {sensor_db_id}, value: {value_for_type}, device_type: {device_type}\n"
                    print(msg, file=sys.stderr)
                    sys.stderr.flush()
                    
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
                    else:
                        msg = f"SUCCESS: insert_sensor_data completed for device_id: {sensor_id}, sensor_db_id: {sensor_db_id}, value: {value_for_type}\n"
                        print(msg, file=sys.stderr)
                        sys.stderr.flush()
            except Exception as e:
                import sys
                import traceback
                msg = f"ERROR: Failed to insert sensor_data for device_id: {sensor_id}, sensor_db_id: {sensor_row.get('id')}\n"
                msg += f"ERROR: Exception: {e}\n"
                msg += traceback.format_exc()
                print(msg, file=sys.stderr)
                sys.stderr.flush()
            
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
        return f"Decryption error: {str(e)}", 400
@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 500 errors."""
    return '', 204  # No Content

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    import sys
    # Get current user ID (should be set by login_required decorator)
    user_id = session.get('user_id')
    username = session.get('user')
    
    print(f"DEBUG: dashboard - username: {username}, user_id: {user_id}", file=sys.stderr)
    sys.stderr.flush()
    
    if not user_id:
        print("ERROR: dashboard - user_id not found in session!", file=sys.stderr)
        sys.stderr.flush()
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # SECURITY: Verify user_id matches username (prevent session hijacking)
    if username:
        user = get_user_by_username(username)
        if user and user['sr_no'] != user_id:
            print(f"ERROR: dashboard - Session mismatch! username={username}, session_user_id={user_id}, db_user_id={user['sr_no']}", file=sys.stderr)
            sys.stderr.flush()
            session.clear()
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
    
    # Get locations that belong to this user ONLY
    print(f"DEBUG: dashboard - Calling get_locations_with_status for user_id {user_id}", file=sys.stderr)
    sys.stderr.flush()
    
    # Get real-time metrics if available (same as live readings uses)
    # Structure: user_latest_by_metric[user_id][metric_name] = {'value': val, 'sensor_id': device_id}
    # We need to pass this to get_locations_with_status so it can filter by location
    realtime_metrics_data = None
    if user_id and user_id in user_latest_by_metric:
        realtime_metrics_data = user_latest_by_metric[user_id]
    
    locations_data = get_locations_with_status(user_id=user_id, realtime_metrics_data=realtime_metrics_data)
    
    print(f"DEBUG: dashboard - Found {len(locations_data)} locations for user_id {user_id} (username: {username})", file=sys.stderr)
    for loc in locations_data:
        print(f"DEBUG: dashboard - Location: {loc.get('location')}, Safe: {loc.get('safe')}, Sensors: {loc.get('sensor_count')}", file=sys.stderr)
    sys.stderr.flush()
    
    # If no locations, check why
    if not locations_data:
        print(f"WARNING: dashboard - No locations found for user_id {user_id}!", file=sys.stderr)
        # Check if user has sensors
        from db import get_pool
        pool = get_pool()
        if pool:
            conn = pool.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) as count FROM sensors WHERE user_id = %s", (int(user_id),))
            sensor_count = cur.fetchone()['count']
            cur.close()
            conn.close()
            print(f"WARNING: dashboard - User {user_id} has {sensor_count} sensors but no locations!", file=sys.stderr)
            
            # Check sensor details
            if sensor_count > 0:
                conn = pool.get_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT device_id, location, status FROM sensors WHERE user_id = %s LIMIT 10", (int(user_id),))
                sensors = cur.fetchall()
                cur.close()
                conn.close()
                print(f"DEBUG: dashboard - Sample sensors for user {user_id}:", file=sys.stderr)
                for s in sensors:
                    print(f"DEBUG: dashboard -   Sensor: {s.get('device_id')}, Location: {s.get('location')}, Status: {s.get('status')}", file=sys.stderr)
        sys.stderr.flush()
    
    # Get first location as default, or None if no locations
    default_location = locations_data[0]['location'] if locations_data else None
    
    return render_template(
        "dashboard.html",
        locations=locations_data,
        default_location=default_location,
        current_user_id=user_id,  # Pass for debugging
        current_username=username,  # Pass for debugging
    )

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
    from db import get_pool
    pool = get_pool()
    if pool:
        conn = pool.get_connection()
        cur = conn.cursor(dictionary=True)
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
        conn.close()
        
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        next_url = request.args.get('next') or request.form.get('next') or url_for('dashboard')
        if request.method == 'POST':
            username = sanitize_input(request.form.get('username') or '')
            password = request.form.get('password') or ''
            if not username or not password:
                flash('Please enter both username and password', 'error')
            else:
                user = get_user_by_username(username)
                if user and check_password_hash(user.get('password', ''), password):
                    session['user'] = user.get('username')
                    session['user_id'] = user.get('sr_no')
                    session.permanent = True
                    return redirect(next_url or url_for('dashboard'))
                else:
                    flash('Invalid username or password', 'error')
        # Render login template (for both GET and POST if login failed)
        return render_template('login.html', next=next_url)
    except Exception as e:
        import sys
        import traceback
        error_msg = f"ERROR: login route exception: {str(e)}\n"
        print(error_msg, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return f"Login error: {e}", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    try:
        next_url = request.args.get('next') or request.form.get('next') or url_for('dashboard')
        error = None
        
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email') or '')
            name = sanitize_input(request.form.get('name') or '')
            username = sanitize_input(request.form.get('username') or '')
            password = request.form.get('password') or ''
            confirm = request.form.get('confirm') or ''
            
            # Validation
            if not all([email, name, username, password, confirm]):
                error = 'All fields are required'
            elif password != confirm:
                error = 'Passwords do not match'
            else:
                # Validate inputs
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    error = email_error or 'Invalid email address'
                
                name_valid, name_error = validate_name(name)
                if not name_valid and not error:
                    error = name_error or 'Invalid name'
                
                username_valid, username_error = validate_username(username)
                if not username_valid and not error:
                    error = username_error or 'Invalid username'
                
                password_valid, password_error = validate_password(password)
                if not password_valid and not error:
                    error = password_error or 'Invalid password'
            
            if not error:
                # Check if username or email already exists
                existing_user = get_user_by_username(username)
                if existing_user:
                    error = 'Username already exists'
                else:
                    existing_email = get_user_by_email(email)
                    if existing_email:
                        error = 'Email already registered'
                    else:
                        # Create user
                        try:
                            user_id = create_user(
                                username=username,
                                email=email,
                                password=password,
                                name=name
                            )
                            if user_id:
                                flash('Registration successful! Please log in.', 'success')
                                return redirect(url_for('login', next=next_url))
                            else:
                                error = 'Registration failed. Please try again.'
                        except Exception as db_error:
                            import sys
                            print(f"ERROR: Registration database error: {db_error}", file=sys.stderr)
                            error = 'Registration failed. Please try again.'
        
        return render_template('register.html', error=error, next=next_url)
    except Exception as e:
        import sys
        import traceback
        error_msg = f"ERROR: register route exception: {str(e)}\n"
        print(error_msg, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return f"Registration error: {e}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/readings')
@login_required
def readings():
    """Display live sensor readings page."""
    user_id = session.get('user_id')
    if not user_id:
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    return render_template('readings.html')

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
        
        if user_id in user_latest_by_sensor:
            for sensor in user_sensors:
                device_id = sensor.get('device_id')
                if device_id in user_latest_by_sensor[user_id]:
                    sensor_data = user_latest_by_sensor[user_id][device_id]
                    active_sensors.append({
                        'device_id': device_id,
                        'device_type': sensor_data.get('device_type') or sensor.get('device_type'),
                        'location': sensor_data.get('location') or sensor.get('location') or 'Unassigned',
                        'value': sensor_data.get('value')
                    })
                    sensors_with_cache_data.add(device_id)
        
        # If cache is empty or incomplete, query database for latest readings
        if not active_sensors or len(sensors_with_cache_data) < len(user_sensors):
            print(f"DEBUG: api_active_sensors - Cache incomplete ({len(sensors_with_cache_data)}/{len(user_sensors)}), querying database...", file=sys.stderr)
            sys.stderr.flush()
            
            # Get latest readings from database for each sensor
            from db import get_pool
            pool = get_pool()
            if pool:
                conn = pool.get_connection()
                cur = conn.cursor(dictionary=True)
                
                # Get latest reading per device_id for this user
                for sensor in user_sensors:
                    device_id = sensor.get('device_id')
                    # Skip if we already have cache data for this sensor
                    if device_id in sensors_with_cache_data:
                        continue
                    
                    # Query database for latest reading for this device
                    cur.execute("""
                        SELECT sd.value, sd.recorded_at, s.device_type, s.location
                        FROM sensor_data sd
                        JOIN sensors s ON s.id = sd.sensor_id
                        WHERE sd.device_id = %s AND sd.user_id = %s
                        ORDER BY sd.recorded_at DESC, sd.id DESC
                        LIMIT 1
                    """, (device_id, int(user_id)))
                    
                    row = cur.fetchone()
                    if row:
                        # Decrypt the value
                        from db_encryption import get_db_encryption
                        encryption = get_db_encryption()
                        encrypted_value = row.get('value')
                        decrypted_value = encryption.decrypt_value(encrypted_value) if encrypted_value else None
                        
                        if decrypted_value is not None:
                            active_sensors.append({
                                'device_id': device_id,
                                'device_type': row.get('device_type') or sensor.get('device_type'),
                                'location': row.get('location') or sensor.get('location') or 'Unassigned',
                                'value': float(decrypted_value) if decrypted_value else None
                            })
                            print(f"DEBUG: api_active_sensors - Found database reading for {device_id}: {decrypted_value}", file=sys.stderr)
                        else:
                            # Add sensor even without reading value
                            active_sensors.append({
                                'device_id': device_id,
                                'device_type': sensor.get('device_type'),
                                'location': sensor.get('location') or 'Unassigned',
                                'value': None
                            })
                    else:
                        # No readings in database, but sensor is active - include it with null value
                        active_sensors.append({
                            'device_id': device_id,
                            'device_type': sensor.get('device_type'),
                            'location': sensor.get('location') or 'Unassigned',
                            'value': None
                        })
                
                cur.close()
                conn.close()
        
        print(f"DEBUG: api_active_sensors - Returning {len(active_sensors)} sensors", file=sys.stderr)
        sys.stderr.flush()
        
        return jsonify({
            'active_sensors': active_sensors
        })
    except Exception as e:
        import traceback
        print(f"ERROR: api_active_sensors - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/latest')
@login_required
def api_latest():
    """API endpoint to get latest safety status for current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
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
            
            # Get latest readings from database
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
                        # Store latest value per metric
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
        
        # Build aggregate values
        agg_values = {k: v.get("value") for k, v in user_metric_data.items() if v and v.get("value") is not None}
        
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
        
        print(f"DEBUG: api_latest - Returning data for user {user_id}, metrics: {list(agg_values.keys())}, safe: {safe}", file=sys.stderr)
        sys.stderr.flush()
        
        return jsonify({
            'safe_to_drink': safe,
            'reasons': reasons if not safe else [],
            'latest': latest
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
        
        # In a real implementation, this would send an MQTT message to request readings
        # For now, just return success
        return jsonify({
            "status": "sent",
            "location": location,
            "sensor_count": len(user_sensors)
        })
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

@app.route('/sensors')
@login_required
def sensors():
    """Display and manage sensors."""
    user_id = session.get('user_id')
    if not user_id:
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    try:
        import sys
        # Get filter parameters
        q = request.args.get('q', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Get user's sensors
        all_sensors = list_sensors()
        user_sensors = [s for s in all_sensors if s.get('user_id') == user_id]
        
        # Get default thresholds map
        try:
            type_defaults = _build_type_defaults_map()
        except Exception as e:
            print(f"WARNING: Could not build type defaults map: {e}", file=sys.stderr)
            type_defaults = {}
        
        # Enhance each sensor with computed fields
        enhanced_sensors = []
        for sensor in user_sensors:
            try:
                device_id = sensor.get('device_id')
                if not device_id:
                    continue  # Skip sensors without device_id
                    
                device_type = (sensor.get('device_type') or '').lower()
                
                # Get public key (from database or file)
                public_key = sensor.get('public_key')
                if not public_key:
                    # Try to get from user's key file
                    try:
                        public_key = get_user_key(user_id, device_id)
                    except Exception as e:
                        print(f"WARNING: Could not get user key for {device_id}: {e}", file=sys.stderr)
                        public_key = None
                
                # Compute public key fingerprint
                try:
                    public_key_fingerprint = compute_public_key_fingerprint(public_key)
                except Exception as e:
                    print(f"WARNING: Could not compute fingerprint for {device_id}: {e}", file=sys.stderr)
                    public_key_fingerprint = None
                
                # Get effective thresholds
                try:
                    effective_thresholds = build_effective_thresholds_for_sensor(device_id)
                    threshold_for_type = effective_thresholds.get(device_type, {}) if effective_thresholds else {}
                except Exception as e:
                    print(f"WARNING: Could not get effective thresholds for {device_id}: {e}", file=sys.stderr)
                    threshold_for_type = {}
                
                min_threshold_effective = threshold_for_type.get('min')
                max_threshold_effective = threshold_for_type.get('max')
                
                # Get default thresholds for this device type
                default_thresholds = type_defaults.get(device_type, {}) if type_defaults else {}
                default_min = default_thresholds.get('min') if isinstance(default_thresholds, dict) else None
                default_max = default_thresholds.get('max') if isinstance(default_thresholds, dict) else None
                
                # Determine threshold source
                sensor_min = sensor.get('min_threshold')
                sensor_max = sensor.get('max_threshold')
                threshold_source = None
                if sensor_min is not None or sensor_max is not None:
                    threshold_source = 'custom'
                elif default_min is not None or default_max is not None:
                    threshold_source = 'default'
                
                # Create enhanced sensor dict
                enhanced_sensor = dict(sensor)  # Copy original sensor data
                enhanced_sensor['public_key_fingerprint'] = public_key_fingerprint
                enhanced_sensor['min_threshold_effective'] = min_threshold_effective
                enhanced_sensor['max_threshold_effective'] = max_threshold_effective
                enhanced_sensor['default_min'] = default_min
                enhanced_sensor['default_max'] = default_max
                enhanced_sensor['threshold_source'] = threshold_source
                
                enhanced_sensors.append(enhanced_sensor)
            except Exception as e:
                print(f"ERROR: Failed to enhance sensor {sensor.get('device_id', 'unknown')}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                # Continue processing other sensors even if one fails
                continue
        
        # Apply filters
        if q:
            q_lower = q.lower()
            enhanced_sensors = [s for s in enhanced_sensors if 
                          q_lower in (s.get('device_id') or '').lower() or
                          q_lower in (s.get('device_type') or '').lower() or
                          q_lower in (s.get('location') or '').lower()]
        
        if status_filter:
            enhanced_sensors = [s for s in enhanced_sensors if s.get('status') == status_filter]
        
        print(f"DEBUG: sensors - Returning {len(enhanced_sensors)} sensors for user {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        return render_template('sensors.html', 
                             sensors=enhanced_sensors,
                             q=q,
                             status_filter=status_filter)
    except Exception as e:
        import traceback
        print(f"ERROR: sensors route - {e}")
        traceback.print_exc()
        flash('Error loading sensors.', 'error')
        return render_template('sensors.html', sensors=[], q='', status_filter='')

@app.route('/sensors/register', methods=['GET', 'POST'])
@login_required
def sensors_register():
    """Register a new sensor."""
    user_id = session.get('user_id')
    if not user_id:
        flash('User session not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            device_id = sanitize_input(request.form.get('device_id') or '')
            device_type = sanitize_input(request.form.get('device_type') or '')
            location = sanitize_input(request.form.get('location') or '')
            
            # Validation
            device_id_valid, device_id_error = validate_device_id(device_id)
            if not device_id_valid:
                flash(device_id_error or 'Invalid device ID', 'error')
                return render_template('sensors_register.html', 
                                     sensor_types=list_sensor_types() or [])
            
            device_type_valid, device_type_error = validate_device_type(device_type)
            if not device_type_valid:
                flash(device_type_error or 'Invalid device type', 'error')
                return render_template('sensors_register.html',
                                     sensor_types=list_sensor_types() or [])
            
            location_valid, location_error = validate_location(location)
            if not location_valid and location:  # Location can be empty
                flash(location_error or 'Invalid location', 'error')
                return render_template('sensors_register.html',
                                     sensor_types=list_sensor_types() or [])
            
            # Check if device_id already exists for this user
            existing = get_sensor_by_device_id(device_id)
            if existing and existing.get('user_id') == user_id:
                flash(f'Sensor with device ID "{device_id}" already registered', 'error')
                return render_template('sensors_register.html',
                                     sensor_types=list_sensor_types() or [])
            
            # Create sensor
            sensor_id = create_sensor(
                device_id=device_id,
                device_type=device_type,
                location=location or None,
                user_id=user_id,
                status='inactive'  # Start as inactive
            )
            
            if sensor_id:
                flash(f'Sensor "{device_id}" registered successfully!', 'success')
                return redirect(url_for('sensors'))
            else:
                flash('Failed to register sensor', 'error')
        except Exception as e:
            import traceback
            print(f"ERROR: sensors_register POST - {e}")
            traceback.print_exc()
            flash(f'Error registering sensor: {str(e)}', 'error')
    
    # GET request - show form
    try:
        sensor_types = list_sensor_types() or []
        return render_template('sensors_register.html', sensor_types=sensor_types)
    except Exception as e:
        import traceback
        print(f"ERROR: sensors_register GET - {e}")
        traceback.print_exc()
        return render_template('sensors_register.html', sensor_types=[])

@app.route('/sensors/delete', methods=['POST'])
@login_required
def sensors_delete():
    """Delete a sensor."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        device_id = sanitize_input(request.form.get('device_id') or '')
        if not device_id:
            flash('Device ID is required', 'error')
            return redirect(url_for('sensors'))
        
        # Verify sensor belongs to user
        sensor = get_sensor_by_device_id(device_id)
        if not sensor or sensor.get('user_id') != user_id:
            flash('Sensor not found or access denied', 'error')
            return redirect(url_for('sensors'))
        
        # Delete sensor
        if delete_sensor_by_device_id(device_id):
            # Also delete user's key file if exists
            key_file = get_user_key_file(user_id, device_id)
            if os.path.exists(key_file):
                try:
                    os.remove(key_file)
                except Exception:
                    pass
            
            # Notify via MQTT if configured
            notify_raspbian_key_cleanup(device_id, user_id)
            
            flash(f'Sensor "{device_id}" deleted successfully', 'success')
        else:
            flash('Failed to delete sensor', 'error')
    except Exception as e:
        import traceback
        print(f"ERROR: sensors_delete - {e}")
        traceback.print_exc()
        flash(f'Error deleting sensor: {str(e)}', 'error')
    
    return redirect(url_for('sensors'))

@app.route('/sensors/update', methods=['POST'])
@login_required
def sensors_update():
    """Update a sensor."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        device_id = sanitize_input(request.form.get('device_id') or '')
        location = sanitize_input(request.form.get('location') or '')
        status = sanitize_input(request.form.get('status') or '')
        min_threshold = request.form.get('min_threshold')
        max_threshold = request.form.get('max_threshold')
        
        if not device_id:
            flash('Device ID is required', 'error')
            return redirect(url_for('sensors'))
        
        # Verify sensor belongs to user
        sensor = get_sensor_by_device_id(device_id)
        if not sensor or sensor.get('user_id') != user_id:
            flash('Sensor not found or access denied', 'error')
            return redirect(url_for('sensors'))
        
        # Validate inputs
        if location:
            location_valid, location_error = validate_location(location)
            if not location_valid:
                flash(location_error or 'Invalid location', 'error')
                return redirect(url_for('sensors'))
        
        if status:
            status_valid, status_error = validate_status(status)
            if not status_valid:
                flash(status_error or 'Invalid status', 'error')
                return redirect(url_for('sensors'))
        
        # Parse thresholds
        min_thresh = None
        max_thresh = None
        if min_threshold:
            try:
                min_thresh = float(min_threshold)
            except ValueError:
                flash('Invalid minimum threshold', 'error')
                return redirect(url_for('sensors'))
        
        if max_threshold:
            try:
                max_thresh = float(max_threshold)
            except ValueError:
                flash('Invalid maximum threshold', 'error')
                return redirect(url_for('sensors'))
        
        # Update sensor
        if update_sensor_by_device_id(
            device_id=device_id,
            location=location or None,
            status=status or sensor.get('status'),
            min_threshold=min_thresh,
            max_threshold=max_thresh
        ):
            flash(f'Sensor "{device_id}" updated successfully', 'success')
        else:
            flash('Failed to update sensor', 'error')
    except Exception as e:
        import traceback
        print(f"ERROR: sensors_update - {e}")
        traceback.print_exc()
        flash(f'Error updating sensor: {str(e)}', 'error')
    
    return redirect(url_for('sensors'))

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
                # Update profile
                if update_user_profile(user_id, email=email, name=name, username=username_new):
                    # Update password if provided
                    if new_password:
                        if not update_user_password(user_id, new_password):
                            error = 'Failed to update password'
                    
                    if not error:
                        # Update session
                        session['user'] = username_new
                        flash('Profile updated successfully!', 'success')
                        return redirect(url_for('profile'))
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

@app.route('/api/sensor_type')
@login_required
def api_sensor_type():
    """API endpoint to get sensor type information."""
    try:
        sensor_type = request.args.get('type', '').strip().lower()
        if not sensor_type:
            return jsonify({"error": "Type parameter is required"}), 400
        
        sensor_type_info = get_sensor_type_by_type(sensor_type)
        if sensor_type_info:
            return jsonify({
                'type_name': sensor_type_info.get('type_name'),
                'default_min': sensor_type_info.get('default_min'),
                'default_max': sensor_type_info.get('default_max')
            })
        else:
            return jsonify({"error": "Sensor type not found"}), 404
    except Exception as e:
        import traceback
        print(f"ERROR: api_sensor_type - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/key_upload_status')
@login_required
def api_key_upload_status():
    """API endpoint to check if a key has been uploaded for a device."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        device_id = sanitize_input(request.args.get('device_id') or '')
        if not device_id:
            return jsonify({"error": "device_id parameter is required"}), 400
        
        # Check if key exists in user's keys
        key = get_user_key(user_id, device_id)
        if key:
            return jsonify({"status": "uploaded", "device_id": device_id})
        
        # Check pending keys
        if user_id in user_pending_keys and device_id in user_pending_keys[user_id]:
            return jsonify({"status": "pending", "device_id": device_id})
        
        # Check global pending keys (legacy)
        if device_id in pending_keys:
            return jsonify({"status": "pending", "device_id": device_id})
        
        return jsonify({"status": "not_found", "device_id": device_id})
    except Exception as e:
        import traceback
        print(f"ERROR: api_key_upload_status - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/key_upload_fetch')
@login_required
def api_key_upload_fetch():
    """API endpoint to fetch an uploaded key for a device."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User session not found"}), 401
    
    try:
        device_id = sanitize_input(request.args.get('device_id') or '')
        if not device_id:
            return jsonify({"error": "device_id parameter is required"}), 400
        
        # Get key from user's keys
        key = get_user_key(user_id, device_id)
        if key:
            # Save to database if sensor exists
            sensor = get_sensor_by_device_id(device_id)
            if sensor and sensor.get('user_id') == user_id:
                try:
                    update_sensor_by_device_id(
                        device_id=device_id,
                        location=sensor.get('location'),
                        status=sensor.get('status'),
                        public_key=key,
                        min_threshold=sensor.get('min_threshold'),
                        max_threshold=sensor.get('max_threshold')
                    )
                except Exception:
                    pass
            
            return jsonify({"status": "success", "public_key": key, "device_id": device_id})
        
        # Check pending keys
        if user_id in user_pending_keys and device_id in user_pending_keys[user_id]:
            key = user_pending_keys[user_id][device_id]
            # Move to user's keys
            add_user_key(user_id, device_id, key)
            return jsonify({"status": "success", "public_key": key, "device_id": device_id})
        
        # Check global pending keys (legacy)
        if device_id in pending_keys:
            key = pending_keys[device_id]
            # Move to user's keys
            add_user_key(user_id, device_id, key)
            return jsonify({"status": "success", "public_key": key, "device_id": device_id})
        
        return jsonify({"error": "Key not found"}), 404
    except Exception as e:
        import traceback
        print(f"ERROR: api_key_upload_fetch - {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start MQTT key subscriber if configured
    start_mqtt_key_subscriber()
    
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', os.environ.get('PORT', '5000')))
    debug_env = str(os.environ.get('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug_env, use_reloader=debug_env)
