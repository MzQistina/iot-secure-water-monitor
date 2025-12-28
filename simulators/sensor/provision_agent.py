import os
import sys
import json
import time
import threading
import re
import stat
import paho.mqtt.client as mqtt
from typing import Optional
from Crypto.PublicKey import RSA


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Import encryption utilities for E2EE
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from encryption_utils import decrypt_data

# --- REPLAY ATTACK PROTECTION ---
# Store recent nonces and timestamps for each device_id (in-memory, resets on restart)
recent_nonces = {}  # device_id -> set of nonces
recent_timestamps = {}  # device_id -> last timestamp (ISO8601 string)
recent_payload_hashes = {}  # device_id -> list of (hash, timestamp) tuples (for messages without nonces/timestamps)
NONCE_CACHE_SIZE = 50  # How many nonces to remember per device
REPLAY_MAX_SKEW_SECONDS = 120  # Allow up to 2 minutes clock skew
PAYLOAD_HASH_CACHE_SIZE = 20  # How many payload hashes to remember per device
PAYLOAD_HASH_EXPIRY_SECONDS = 30  # Expire payload hashes after 30 seconds (allows legitimate retries)


def _delete_sensor_directory(sensor_dir: str, device_id: str, user_id: Optional[str]) -> bool:
    """Delete all files in a sensor directory and remove the directory itself.
    
    Returns True if any files were deleted, False otherwise.
    """
    deleted_files = []
    try:
        # Remove all files in the sensor directory
        if os.path.exists(sensor_dir):
            for filename in os.listdir(sensor_dir):
                file_path = os.path.join(sensor_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_files.append(filename)
                except Exception as e:
                    print(f"  ⚠️  Error deleting file {filename}: {e}")
            
            # Remove the sensor directory itself
            try:
                os.rmdir(sensor_dir)
            except OSError:
                pass  # Directory might not be empty
            
            if deleted_files:
                return True
    except Exception as e:
        print(f"  ⚠️  Error processing directory {sensor_dir}: {e}")
        import traceback
        traceback.print_exc()
    
    return False


def ensure_keys(device_id: str, user_id: Optional[str] = None, force_regenerate: bool = False) -> str:
    """Generate or retrieve sensor keys, optionally organized by user folder.
    
    Args:
        device_id: Device/sensor ID
        user_id: Optional user ID to organize keys in user-specific folder
        force_regenerate: If True, delete existing keys and generate new ones
    
    Returns:
        Path to public key file
    """
    # Create folder structure: sensor_keys/{user_id}/{device_id}/ or sensor_keys/{device_id}/
    if user_id:
        user_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        sensor_dir = os.path.join(user_dir, device_id)
    else:
        sensor_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', device_id)
    
    os.makedirs(sensor_dir, exist_ok=True)
    
    priv = os.path.join(sensor_dir, 'sensor_private.pem')
    pub = os.path.join(sensor_dir, 'sensor_public.pem')
    
    # Delete existing keys if force_regenerate is True
    if force_regenerate:
        try:
            if os.path.exists(priv):
                os.remove(priv)
            if os.path.exists(pub):
                os.remove(pub)
        except Exception as e:
            print(f"⚠️  Could not delete keys: {e}")
    
    if not (os.path.exists(priv) and os.path.exists(pub)):
        key = RSA.generate(2048)
        with open(priv, 'wb') as f:
            f.write(key.export_key())
        with open(pub, 'wb') as f:
            f.write(key.publickey().export_key())
        
        # Automatically set secure file permissions
        # Private key: 600 (read/write owner only)
        os.chmod(priv, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        
        # Public key: 644 (read/write owner, read others)
        os.chmod(pub, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0o644
        
        # Restrict directory access to owner only (700)
        os.chmod(sensor_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0o700
        
        if user_id:
            print(f"✅ Generated keys: {device_id} (user: {user_id})")
        else:
            print(f"✅ Generated keys: {device_id}")
    
    return pub


def main():
    mqtt_host = os.environ.get('MQTT_HOST', 'localhost')
    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    prov_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
    keys_base = os.environ.get('MQTT_KEYS_TOPIC_BASE', 'keys')
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
    mqtt_certfile = os.environ.get('MQTT_CERTFILE')
    mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')

    # Subscribe to three topics: request, update, and delete
    request_topic = f"{prov_base}/+/request"  # Initial key generation
    update_topic = f"{prov_base}/+/update"     # Regenerate/update existing keys
    delete_topic = f"{prov_base}/+/delete"    # Delete keys

    def on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        if reason_code == 0:
            client.subscribe(request_topic, qos=1)
            client.subscribe(update_topic, qos=1)
            client.subscribe(delete_topic, qos=1)
            print(f'✅ Connected & subscribed')
        else:
            print(f'❌ Connection failed: rc={reason_code}')
    
    def on_subscribe(client, userdata, mid, granted_qos, properties):
        """Callback when subscription is confirmed."""
        pass  # Silent - connection message is enough
    
    def on_message(client, userdata, msg):
        """Callback when message is received."""
        try:
            device_id = None
            user_id = None
            action_type = None  # 'request', 'update', or 'delete'
            
            # Check which topic this message is for
            delete_match = re.match(r'^' + re.escape(prov_base) + r'/([^/]+)/delete$', msg.topic or '')
            update_match = re.match(r'^' + re.escape(prov_base) + r'/([^/]+)/update$', msg.topic or '')
            request_match = re.match(r'^' + re.escape(prov_base) + r'/([^/]+)/request$', msg.topic or '')
            
            if delete_match:
                device_id = (delete_match.group(1) or '').strip()
                action_type = 'delete'
            elif update_match:
                device_id = (update_match.group(1) or '').strip()
                action_type = 'update'
            elif request_match:
                device_id = (request_match.group(1) or '').strip()
                action_type = 'request'
            else:
                print(f'⚠️  Unknown topic: {msg.topic}')
                return
            
            # Parse JSON body for device_id and user_id
            # Check if message is encrypted with E2EE
            # 
            # E2EE Expected Behavior:
            # - "request": NO E2EE (keys don't exist yet - chicken-and-egg problem)
            # - "update": YES E2EE (keys should exist from previous request)
            # - "delete": YES E2EE (keys should exist from previous request)
            # 
            # Note: We try to decrypt all messages, but fall back to plaintext if decryption fails
            # This handles the case where "request" messages are sent as plaintext
            decrypted_data = None
            if (msg.payload or b'').strip():
                try:
                    payload_str = msg.payload.decode('utf-8', errors='replace')
                    data = json.loads(payload_str)
                    
                    # Check if message is encrypted (has E2EE fields)
                    is_encrypted = all(k in data for k in ['session_key', 'ciphertext', 'nonce', 'tag'])
                    
                    if is_encrypted:
                        # Decrypt E2EE message
                        try:
                            # Get device_id from topic (already extracted above)
                            if not device_id:
                                print("⚠️  Cannot decrypt: device_id not found")
                                return
                            
                            # Try to find private key - we need to try multiple locations
                            # because user_id might be in the encrypted payload
                            private_key_path = None
                            possible_paths = []
                            
                            # First, try global location (most common)
                            global_sensor_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', device_id)
                            possible_paths.append(os.path.join(global_sensor_dir, 'sensor_private.pem'))
                            
                            # Also try common user IDs (1, 2, etc.) if we have a hint
                            # We'll try a few common user IDs, or scan user_keys directories
                            if user_id:
                                # If we have user_id (from plaintext message or previous attempt)
                                user_sensor_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', str(user_id), device_id)
                                possible_paths.insert(0, os.path.join(user_sensor_dir, 'sensor_private.pem'))
                            
                            # Try each possible path
                            for key_path in possible_paths:
                                if os.path.exists(key_path):
                                    try:
                                        decrypted_data = decrypt_data(data, key_path)
                                        private_key_path = key_path
                                        break
                                    except Exception as decrypt_err:
                                        # Try next path
                                        continue
                            
                            if decrypted_data is None:
                                # If still not decrypted, try scanning user_keys directories
                                sensor_keys_base = os.path.join(PROJECT_ROOT, 'sensor_keys')
                                if os.path.exists(sensor_keys_base):
                                    for user_dir in os.listdir(sensor_keys_base):
                                        user_path = os.path.join(sensor_keys_base, user_dir)
                                        if os.path.isdir(user_path):
                                            device_path = os.path.join(user_path, device_id)
                                            key_path = os.path.join(device_path, 'sensor_private.pem')
                                            if os.path.exists(key_path):
                                                try:
                                                    decrypted_data = decrypt_data(data, key_path)
                                                    private_key_path = key_path
                                                    break
                                                except Exception:
                                                    continue
                            
                            # For "request" messages: Try server private key if device key not found
                            # Check topic pattern to determine if it's a request (action_type might not be set yet)
                            is_request_topic = '/request' in msg.topic or action_type == 'request'
                            if decrypted_data is None and is_request_topic:
                                server_private_key_path = os.path.join(PROJECT_ROOT, 'keys', 'private.pem')
                                if os.path.exists(server_private_key_path):
                                    try:
                                        decrypted_data = decrypt_data(data, server_private_key_path)
                                        private_key_path = server_private_key_path
                                        print(f"✅ Decrypted REQUEST using server private key")
                                    except Exception as server_decrypt_err:
                                        # Fall through to try plaintext parsing
                                        pass
                            
                            if decrypted_data is None:
                                if action_type != 'request':
                                    print(f"⚠️  Cannot decrypt {device_id}: key not found")
                                # Fall through to try plaintext parsing
                        except Exception as decrypt_err:
                            print(f"⚠️  Decryption failed: {decrypt_err}")
                            # Fall through to try plaintext parsing
                    
                    # If not encrypted or decryption failed, use data as-is
                    if decrypted_data is None:
                        decrypted_data = data
                    
                    # Extract device_id and user_id from decrypted/plaintext data
                    device_id = (decrypted_data.get('device_id') or device_id or '').strip()
                    
                    # Extract user_id - handle both string and numeric values
                    user_id_raw = decrypted_data.get('user_id')
                    if user_id_raw is not None:
                        # Convert to string and strip whitespace
                        user_id = str(user_id_raw).strip()
                        # Only use if not empty
                        if not user_id:
                            user_id = None
                    
                    # --- REPLAY ATTACK PROTECTION ---
                    # Check for duplicate nonces and timestamps (only for update/delete actions)
                    if action_type in ('update', 'delete') and device_id:
                        nonce = decrypted_data.get('nonce')
                        timestamp = decrypted_data.get('timestamp')
                        
                        # If message has no nonce or timestamp, use payload-based duplicate detection
                        if not nonce and not timestamp:
                            import hashlib
                            from datetime import datetime, timezone
                            # Create a hash of the payload (excluding any nonce/timestamp that might be added later)
                            payload_str = json.dumps(decrypted_data, sort_keys=True)
                            payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
                            
                            # Get current timestamp
                            now = datetime.now(timezone.utc)
                            
                            # Get or create payload hash cache (list of (hash, timestamp) tuples)
                            payload_hashes = recent_payload_hashes.setdefault(device_id, [])
                            
                            # Clean up expired hashes first
                            expired_cutoff = now.timestamp() - PAYLOAD_HASH_EXPIRY_SECONDS
                            payload_hashes[:] = [(h, ts) for h, ts in payload_hashes if ts > expired_cutoff]
                            
                            # Check if we've seen this exact payload recently (within expiry window)
                            for stored_hash, stored_ts in payload_hashes:
                                if stored_hash == payload_hash:
                                    # Found duplicate within expiry window - block it
                                    age_seconds = now.timestamp() - stored_ts
                                    print(f"🚫 [REPLAY BLOCKED] {device_id}/{action_type.upper()}: duplicate payload (seen {age_seconds:.1f}s ago)")
                                    # Publish replay blocked status for test verification
                                    try:
                                        status_topic = f"provision/status/{device_id}/replay_blocked"
                                        status_payload = json.dumps({
                                            "device_id": device_id,
                                            "payload_hash": payload_hash,
                                            "reason": "duplicate_payload_no_nonce_timestamp",
                                            "age_seconds": age_seconds,
                                            "timestamp": now.isoformat()
                                        })
                                        client.publish(status_topic, status_payload, qos=1)
                                    except Exception:
                                        pass  # Don't fail if status publish fails
                                    return  # Block replay
                            
                            # Store payload hash with current timestamp (limit cache size)
                            payload_hashes.append((payload_hash, now.timestamp()))
                            if len(payload_hashes) > PAYLOAD_HASH_CACHE_SIZE:
                                # Remove oldest entries
                                payload_hashes.sort(key=lambda x: x[1])  # Sort by timestamp
                                while len(payload_hashes) > PAYLOAD_HASH_CACHE_SIZE:
                                    payload_hashes.pop(0)  # Remove oldest
                        
                        # Check nonce replay
                        if nonce:
                            nonces = recent_nonces.setdefault(device_id, set())
                            if nonce in nonces:
                                print(f"🚫 [REPLAY BLOCKED] {device_id}/{action_type.upper()}: duplicate nonce")
                                # Publish replay blocked status for test verification
                                try:
                                    from datetime import datetime, timezone
                                    status_topic = f"provision/status/{device_id}/replay_blocked"
                                    status_payload = json.dumps({
                                        "device_id": device_id,
                                        "nonce": nonce,
                                        "reason": "duplicate_nonce",
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    })
                                    client.publish(status_topic, status_payload, qos=1)
                                except Exception:
                                    pass  # Don't fail if status publish fails
                                return  # Block replay
                        
                        # Check timestamp replay
                        if timestamp:
                            try:
                                from datetime import datetime, timezone
                                # Parse timestamp and ensure it's timezone-aware
                                ts_str = timestamp.replace('Z', '+00:00')
                                ts = datetime.fromisoformat(ts_str)
                                # Ensure ts is timezone-aware (in case fromisoformat returns naive)
                                if ts.tzinfo is None:
                                    ts = ts.replace(tzinfo=timezone.utc)
                                now = datetime.now(timezone.utc)
                                skew = abs((now - ts).total_seconds())
                                
                                if skew > REPLAY_MAX_SKEW_SECONDS:
                                    print(f"🚫 [REPLAY BLOCKED] {device_id}/{action_type.upper()}: timestamp skew {skew:.0f}s (max {REPLAY_MAX_SKEW_SECONDS}s)")
                                    # Publish replay blocked status for test verification
                                    try:
                                        status_topic = f"provision/status/{device_id}/replay_blocked"
                                        status_payload = json.dumps({
                                            "device_id": device_id,
                                            "timestamp": timestamp,
                                            "reason": "timestamp_skew",
                                            "skew_seconds": skew,
                                            "blocked_at": datetime.now(timezone.utc).isoformat()
                                        })
                                        client.publish(status_topic, status_payload, qos=1)
                                    except Exception:
                                        pass  # Don't fail if status publish fails
                                    return  # Block replay
                                
                                # Block if timestamp not newer than last
                                last_ts = recent_timestamps.get(device_id)
                                if last_ts:
                                    last_dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
                                    # Ensure both datetimes are timezone-aware for comparison
                                    if last_dt.tzinfo is None:
                                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                                    if ts <= last_dt:
                                        print(f"🚫 [REPLAY BLOCKED] {device_id}/{action_type.upper()}: timestamp not newer")
                                        # Publish replay blocked status for test verification
                                        try:
                                            status_topic = f"provision/status/{device_id}/replay_blocked"
                                            status_payload = json.dumps({
                                                "device_id": device_id,
                                                "timestamp": timestamp,
                                                "previous_timestamp": last_ts,
                                                "reason": "timestamp_not_newer",
                                                "blocked_at": datetime.now(timezone.utc).isoformat()
                                            })
                                            client.publish(status_topic, status_payload, qos=1)
                                        except Exception:
                                            pass  # Don't fail if status publish fails
                                        return  # Block replay
                                
                                recent_timestamps[device_id] = timestamp
                            except Exception as ts_err:
                                print(f"⚠️  Invalid timestamp {device_id}: {ts_err}")
                        
                        # Store nonce (limit cache size)
                        if nonce:
                            nonces.add(nonce)
                            if len(nonces) > NONCE_CACHE_SIZE:
                                while len(nonces) > NONCE_CACHE_SIZE:
                                    nonces.pop()
                    
                    # Log message summary
                    e2ee_status = '🔒 E2EE' if (is_encrypted and decrypted_data) else '📝 Plaintext'
                    if action_type in ('update', 'delete') and not (is_encrypted and decrypted_data):
                        e2ee_status = '⚠️  Plaintext (E2EE expected)'
                    
                    user_str = f" (user:{user_id})" if user_id else ""
                    print(f"📨 {action_type.upper()} {device_id}{user_str} | {e2ee_status}")
                except Exception as e:
                    print(f"⚠️  JSON parse error: {e}")
                    return
            
            if not device_id:
                print('⚠️  Missing device_id, ignoring')
                return
            
            # Handle delete request
            if action_type == 'delete':
                deleted_any = False
                
                # Try user-specific location first if user_id provided
                if user_id:
                    sensor_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', str(user_id), device_id)
                    if os.path.exists(sensor_dir):
                        deleted_any = _delete_sensor_directory(sensor_dir, device_id, user_id) or deleted_any
                
                # Also try global location (in case keys were stored there)
                sensor_dir_global = os.path.join(PROJECT_ROOT, 'sensor_keys', device_id)
                if os.path.exists(sensor_dir_global):
                    deleted_any = _delete_sensor_directory(sensor_dir_global, device_id, None) or deleted_any
                
                if deleted_any:
                    print(f"✅ Deleted keys: {device_id}")
                else:
                    print(f"⚠️  No keys found: {device_id}")
                
                return
            
            # Handle update request (regenerate existing keys)
            if action_type == 'update':
                pub_path = ensure_keys(device_id, user_id, force_regenerate=True)
            
            # Handle request (initial key generation - only if keys don't exist)
            elif action_type == 'request':
                pub_path = ensure_keys(device_id, user_id, force_regenerate=False)
            
            else:
                print(f"⚠️  Unknown action: {action_type}")
                return
            
            # Publish the public key (for both request and update)
            if action_type in ('request', 'update'):
                with open(pub_path, 'r', encoding='utf-8', errors='replace') as f:
                    pem = f.read().strip()
                
                # Include user_id in payload so Flask can update the correct sensor
                payload_dict = { 'device_id': device_id, 'public_key': pem }
                if user_id:
                    payload_dict['user_id'] = str(user_id)
                payload = json.dumps(payload_dict)
                publish_topic = f"{keys_base}/{device_id}/public"
                client.publish(publish_topic, payload)
                print(f"📤 Published key: {publish_topic}")
        except Exception as e:
            print(f'Provision agent error: {e}')
            import traceback
            traceback.print_exc()

    # Create MQTT client with API v2 (fixes deprecation warning)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Configure authentication
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
    
    # Configure TLS/SSL if enabled
    if mqtt_use_tls:
        try:
            import ssl
            if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
                client.tls_set(
                    ca_certs=mqtt_ca_certs,
                    certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                    keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                    cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLS
                )
            else:
                client.tls_set(
                    certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                    keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                    cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
            
            if mqtt_tls_insecure:
                client.tls_insecure_set(True)
        except Exception as tls_err:
            print(f"⚠️  TLS error: {tls_err}")
    
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    print(f"🔌 Connecting to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})...")
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        client.disconnect()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        client.disconnect()


if __name__ == '__main__':
    main()


