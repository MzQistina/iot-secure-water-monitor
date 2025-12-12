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


def ensure_keys(device_id: str, user_id: Optional[str] = None) -> str:
    """Generate or retrieve sensor keys, optionally organized by user folder.
    
    Args:
        device_id: Device/sensor ID
        user_id: Optional user ID to organize keys in user-specific folder
    
    Returns:
        Path to public key file
    """
    print(f"ensure_keys called: device_id='{device_id}', user_id={repr(user_id)}")
    
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

    # Subscribe to all provision requests: provision/<device_id>/request
    request_topic = f"{prov_base}/+/request"

    def on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        print(f'Provision agent connected: rc={reason_code}')
        if reason_code == 0:
            client.subscribe(request_topic)
            print(f'Provision agent subscribed to: {request_topic}')
        else:
            print(f'Provision agent connection failed: rc={reason_code}')

    def on_message(client, userdata, msg):
        try:
            device_id = None
            user_id = None
            
            # Extract device_id from topic
            m = re.match(r'^' + re.escape(prov_base) + r'/([^/]+)/request$', msg.topic or '')
            if m:
                device_id = (m.group(1) or '').strip()
            
            # Parse JSON body for device_id and user_id
            if (msg.payload or b'').strip():
                try:
                    payload_str = msg.payload.decode('utf-8', errors='replace')
                    data = json.loads(payload_str)
                    device_id = (data.get('device_id') or device_id or '').strip()
                    
                    # Extract user_id - handle both string and numeric values
                    user_id_raw = data.get('user_id')
                    if user_id_raw is not None:
                        # Convert to string and strip whitespace
                        user_id = str(user_id_raw).strip()
                        # Only use if not empty
                        if not user_id:
                            user_id = None
                    
                    # Debug logging
                    print(f"Provision agent received message:")
                    print(f"  Topic: {msg.topic}")
                    print(f"  Payload: {payload_str}")
                    print(f"  Device ID: {device_id}")
                    print(f"  User ID: {user_id}")
                except Exception as e:
                    print(f"Provision agent: Error parsing JSON: {e}")
                    print(f"  Raw payload: {msg.payload}")
            
            if not device_id:
                print('Provision agent: missing device_id; ignoring message')
                return
            
            # Generate keys in user folder if user_id provided
            print(f"Generating keys for device '{device_id}'" + (f" (user: {user_id})" if user_id else ""))
            pub_path = ensure_keys(device_id, user_id)
            with open(pub_path, 'r', encoding='utf-8', errors='replace') as f:
                pem = f.read().strip()
            
            payload = json.dumps({ 'device_id': device_id, 'public_key': pem })
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
    client.loop_forever()


if __name__ == '__main__':
    main()


