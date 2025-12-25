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
                        print(f"  ✅ Deleted file: {filename}")
                except Exception as e:
                    print(f"  ⚠️  Error deleting file {filename}: {e}")
            
            # Remove the sensor directory itself
            try:
                os.rmdir(sensor_dir)
                print(f"  ✅ Deleted directory: {sensor_dir}")
            except OSError as e:
                # Directory might not be empty or other error
                if deleted_files:
                    print(f"  ⚠️  Could not remove directory (may not be empty): {e}")
                else:
                    print(f"  ⚠️  Error deleting directory: {e}")
            
            if deleted_files:
                user_info = f" (user: {user_id})" if user_id else ""
                print(f"✅ Deleted keys for device '{device_id}'{user_info}")
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
    print(f"ensure_keys called: device_id='{device_id}', user_id={repr(user_id)}, force_regenerate={force_regenerate}")
    
    # Create folder structure: sensor_keys/{user_id}/{device_id}/ or sensor_keys/{device_id}/
    if user_id:
        user_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', str(user_id))
        print(f"Creating user folder: {user_dir}")
        os.makedirs(user_dir, exist_ok=True)
        sensor_dir = os.path.join(user_dir, device_id)
        print(f"Creating sensor folder in user directory: {sensor_dir}")
    else:
        sensor_dir = os.path.join(PROJECT_ROOT, 'sensor_keys', device_id)
        print(f"Creating sensor folder (no user): {sensor_dir}")
    
    os.makedirs(sensor_dir, exist_ok=True)
    print(f"Final sensor directory: {sensor_dir} (exists: {os.path.exists(sensor_dir)})")
    
    priv = os.path.join(sensor_dir, 'sensor_private.pem')
    pub = os.path.join(sensor_dir, 'sensor_public.pem')
    
    # Delete existing keys if force_regenerate is True
    if force_regenerate:
        try:
            if os.path.exists(priv):
                os.remove(priv)
                print(f"  Force regenerate: Deleted existing private key")
            if os.path.exists(pub):
                os.remove(pub)
                print(f"  Force regenerate: Deleted existing public key")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not delete existing keys for force regenerate: {e}")
    
    if not (os.path.exists(priv) and os.path.exists(pub)):
        print(f"Keys don't exist, generating new keys...")
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
            print(f"✅ Generated keys for device '{device_id}' (user: {user_id}) at {sensor_dir}")
            print(f"✅ Set secure permissions: private key (600), public key (644), directory (700)")
        else:
            print(f"✅ Generated keys for device '{device_id}' at {sensor_dir}")
            print(f"✅ Set secure permissions: private key (600), public key (644), directory (700)")
    else:
        print(f"Keys already exist at {sensor_dir}")
    
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
        print(f'Provision agent connected: rc={reason_code}')
        if reason_code == 0:
            client.subscribe(request_topic)
            client.subscribe(update_topic)
            client.subscribe(delete_topic)
            print(f'Provision agent subscribed to: {request_topic}')
            print(f'Provision agent subscribed to: {update_topic}')
            print(f'Provision agent subscribed to: {delete_topic}')
        else:
            print(f'Provision agent connection failed: rc={reason_code}')

    def on_message(client, userdata, msg):
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
                print(f'Provision agent: Unknown topic format: {msg.topic}')
                return
            
            # Parse JSON body for device_id and user_id
            # Check if message is encrypted with E2EE
            decrypted_data = None
            if (msg.payload or b'').strip():
                try:
                    payload_str = msg.payload.decode('utf-8', errors='replace')
                    data = json.loads(payload_str)
                    
                    # Check if message is encrypted (has E2EE fields)
                    is_encrypted = all(k in data for k in ['session_key', 'ciphertext', 'nonce', 'tag'])
                    
                    if is_encrypted:
                        # Decrypt E2EE message
                        print(f"Provision agent: Detected E2EE encrypted message")
                        try:
                            # Get device_id from topic (already extracted above)
                            if not device_id:
                                print("Provision agent: Cannot decrypt - device_id not found in topic")
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
                                        print(f"✅ Provision agent: Successfully decrypted E2EE message using {key_path}")
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
                                                    print(f"✅ Provision agent: Successfully decrypted E2EE message using {key_path}")
                                                    break
                                                except Exception:
                                                    continue
                            
                            if decrypted_data is None:
                                print(f"⚠️  Provision agent: Private key not found for device '{device_id}', cannot decrypt E2EE message")
                                print(f"   Searched in: {', '.join(possible_paths[:3])}...")
                                print(f"   This may be a 'request' action or keys not yet generated")
                                # Fall through to try plaintext parsing
                        except Exception as decrypt_err:
                            print(f"⚠️  Provision agent: E2EE decryption failed: {decrypt_err}")
                            import traceback
                            print(f"   Traceback: {traceback.format_exc()}")
                            print(f"   Falling back to plaintext parsing")
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
                    
                    # Debug logging
                    print(f"Provision agent received message:")
                    print(f"  Topic: {msg.topic}")
                    print(f"  E2EE: {'✅ Encrypted (decrypted)' if is_encrypted and decrypted_data else '❌ Plaintext'}")
                    print(f"  Device ID: {device_id}")
                    print(f"  User ID: {user_id}")
                    print(f"  Action: {action_type.upper()}")
                except Exception as e:
                    print(f"Provision agent: Error parsing JSON: {e}")
                    print(f"  Raw payload: {msg.payload}")
            
            if not device_id:
                print('Provision agent: missing device_id; ignoring message')
                return
            
            # Handle delete request
            if action_type == 'delete':
                print(f"Processing delete request for device '{device_id}'" + (f" (user: {user_id})" if user_id else ""))
                
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
                
                if not deleted_any:
                    print(f"⚠️  No sensor directories found to delete for device '{device_id}'" + (f" (user: {user_id})" if user_id else ""))
                
                return
            
            # Handle update request (regenerate existing keys)
            if action_type == 'update':
                print(f"Updating/regenerating keys for device '{device_id}'" + (f" (user: {user_id})" if user_id else ""))
                # Force regenerate keys (delete old and create new)
                pub_path = ensure_keys(device_id, user_id, force_regenerate=True)
            
            # Handle request (initial key generation - only if keys don't exist)
            elif action_type == 'request':
                print(f"Requesting keys for device '{device_id}'" + (f" (user: {user_id})" if user_id else ""))
                # Generate keys only if they don't exist (don't force regenerate)
                pub_path = ensure_keys(device_id, user_id, force_regenerate=False)
            
            else:
                print(f"Unknown action type: {action_type}")
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
                
                if user_id:
                    print(f"Provision agent published key: {publish_topic} (user: {user_id})")
                else:
                    print(f"Provision agent published key: {publish_topic} (no user_id provided)")
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
                print(f"Provision agent: TLS enabled with CA cert: {mqtt_ca_certs}")
            else:
                client.tls_set(
                    certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                    keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                    cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
                print(f"Provision agent: TLS enabled (using system CA certs)")
            
            if mqtt_tls_insecure:
                client.tls_insecure_set(True)
                print("Provision agent: TLS insecure mode enabled")
        except Exception as tls_err:
            print(f"Provision agent: TLS configuration error: {tls_err}")
            print("Provision agent: Continuing without TLS (insecure)")
    
    client.on_connect = on_connect
    client.on_message = on_message
    print(f"Provision agent: Connecting to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})")
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    print("Provision agent: Starting message loop (press Ctrl+C to stop)...")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nProvision agent: Shutting down gracefully...")
        client.disconnect()
        print("Provision agent: Disconnected")
    except Exception as e:
        print(f"\nProvision agent: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        client.disconnect()


if __name__ == '__main__':
    main()


