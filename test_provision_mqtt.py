#!/usr/bin/env python3
"""
Test script to directly test MQTT provision message publishing.
This simulates what the Flask app does when sending provision requests.
"""

import os
import sys
import json
import paho.mqtt.publish as publish
import ssl

# Import encryption utilities for E2EE
from encryption_utils import encrypt_data

# MQTT Configuration - Update these to match your setup
MQTT_CONFIG = {
    'host': os.environ.get('MQTT_HOST', '192.168.43.214'),
    'port': int(os.environ.get('MQTT_PORT', '8883')),
    'user': os.environ.get('MQTT_USER', 'water_monitor'),
    'password': os.environ.get('MQTT_PASSWORD', 'e2eeWater2025'),
    'use_tls': os.environ.get('MQTT_USE_TLS', 'true').lower() in ('true', '1', 'yes'),
    'tls_insecure': os.environ.get('MQTT_TLS_INSECURE', 'true').lower() in ('true', '1', 'yes'),
    'ca_certs': os.environ.get('MQTT_CA_CERTS'),
}

def get_mqtt_kwargs():
    """Get MQTT publish configuration."""
    kwargs = {
        'hostname': MQTT_CONFIG['host'],
        'port': MQTT_CONFIG['port'],
    }
    
    # Authentication
    if MQTT_CONFIG['user'] and MQTT_CONFIG['password']:
        kwargs['auth'] = {
            'username': MQTT_CONFIG['user'],
            'password': MQTT_CONFIG['password']
        }
    
    # TLS/SSL configuration
    if MQTT_CONFIG['use_tls']:
        tls_config = {}
        if MQTT_CONFIG['ca_certs'] and os.path.exists(MQTT_CONFIG['ca_certs']):
            tls_config['ca_certs'] = MQTT_CONFIG['ca_certs']
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        if MQTT_CONFIG['tls_insecure']:
            tls_config['cert_reqs'] = ssl.CERT_NONE
        tls_config['insecure'] = MQTT_CONFIG['tls_insecure']
        kwargs['tls'] = tls_config
    
    return kwargs

def get_device_public_key_path(user_id, device_id):
    """Get path to device public key if it exists."""
    # Check user_keys directory (where Flask stores keys)
    user_keys_dir = os.path.join('user_keys', str(user_id))
    key_file = os.path.join(user_keys_dir, f'{device_id}_public.pem')
    if os.path.exists(key_file):
        return key_file
    
    # Also check sensor_keys directory (where provision agent stores keys)
    sensor_keys_dir = os.path.join('sensor_keys', str(user_id), device_id)
    key_file = os.path.join(sensor_keys_dir, 'sensor_public.pem')
    if os.path.exists(key_file):
        return key_file
    
    # Fallback to global sensor_keys
    sensor_keys_dir = os.path.join('sensor_keys', device_id)
    key_file = os.path.join(sensor_keys_dir, 'sensor_public.pem')
    if os.path.exists(key_file):
        return key_file
    
    return None

def test_provision_publish(device_id, action='update', user_id='1'):
    """Test publishing a provision message."""
    topic_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
    topic = f"{topic_base}/{device_id}/{action}"
    
    # Prepare payload dictionary
    payload_dict = {
        "device_id": device_id,
        "action": action,
        "user_id": str(user_id)
    }
    
    # Apply E2EE if device key exists (for "update" and "delete" actions)
    payload = None
    use_e2ee = False
    device_key_path = None
    
    if action in ('update', 'delete'):
        device_key_path = get_device_public_key_path(user_id, device_id)
        if device_key_path:
            try:
                encrypted_payload = encrypt_data(payload_dict, device_key_path)
                payload = json.dumps(encrypted_payload)
                use_e2ee = True
            except Exception as e2ee_err:
                print(f"[WARNING] E2EE encryption failed: {e2ee_err}, using plaintext")
                payload = json.dumps(payload_dict)
        else:
            payload = json.dumps(payload_dict)
    else:
        # "request" action - key may not exist yet, use plaintext
        payload = json.dumps(payload_dict)
    
    print("=" * 80)
    print("MQTT Provision Test")
    print("=" * 80)
    print(f"Host: {MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}")
    print(f"User: {MQTT_CONFIG['user']}")
    print(f"TLS: {MQTT_CONFIG['use_tls']}")
    print(f"Topic: {topic}")
    print(f"E2EE: {'✅ Enabled' if use_e2ee else '❌ Disabled (plaintext)'}")
    if device_key_path:
        print(f"Key Path: {device_key_path}")
    print(f"Payload length: {len(payload)} bytes")
    if not use_e2ee:
        print(f"Payload: {payload}")
    else:
        print(f"Payload: [Encrypted - contains session_key, ciphertext, nonce, tag]")
    print("=" * 80)
    
    try:
        publish_kwargs = get_mqtt_kwargs()
        publish_kwargs['keepalive'] = 60
        publish_kwargs['client_id'] = f"test_provision_{device_id}_{int(__import__('time').time())}"
        
        print(f"\n[PUBLISH] Publishing message...")
        publish.single(topic, payload, qos=1, **publish_kwargs)
        
        print(f"[SUCCESS] Message published to {topic}")
        print(f"\n[INFO] Next steps:")
        print(f"   1. Check provision agent console output")
        print(f"   2. Look for: 'Provision agent received message:'")
        print(f"   3. Verify topic matches: {topic_base}/+/{action}")
        return True
        
    except ConnectionRefusedError as e:
        print(f"[ERROR] Connection refused")
        print(f"   {e}")
        print(f"\n[INFO] Check:")
        print(f"   1. MQTT broker is running")
        print(f"   2. Host and port are correct: {MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}")
        return False
        
    except Exception as e:
        print(f"[ERROR] Failed to publish")
        print(f"   {type(e).__name__}: {e}")
        print(f"\n[INFO] Check:")
        print(f"   1. MQTT broker is accessible")
        print(f"   2. Authentication credentials are correct")
        print(f"   3. TLS certificates if using TLS")
        print(f"   4. Network connectivity")
        return False

def test_subscribe():
    """Test subscribing to provision topics to see if messages are being published."""
    import paho.mqtt.client as mqtt
    import time
    
    topic_base = os.environ.get('MQTT_PROVISION_TOPIC_BASE', 'provision')
    request_topic = f"{topic_base}/+/request"
    update_topic = f"{topic_base}/+/update"
    delete_topic = f"{topic_base}/+/delete"
    
    print("=" * 80)
    print("MQTT Subscribe Test")
    print("=" * 80)
    print(f"Subscribing to:")
    print(f"  - {request_topic}")
    print(f"  - {update_topic}")
    print(f"  - {delete_topic}")
    print(f"\nWaiting for messages (press Ctrl+C to stop)...")
    print("=" * 80)
    
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[SUCCESS] Connected to MQTT broker")
            client.subscribe(request_topic)
            client.subscribe(update_topic)
            client.subscribe(delete_topic)
            print(f"[SUCCESS] Subscribed to provision topics")
        else:
            print(f"[ERROR] Connection failed: rc={reason_code}")
    
    def on_message(client, userdata, msg):
        print(f"\n[RECEIVED] MESSAGE:")
        print(f"   Topic: {msg.topic}")
        try:
            payload_str = msg.payload.decode('utf-8')
            data = json.loads(payload_str)
            print(f"   Payload: {json.dumps(data, indent=2)}")
        except:
            print(f"   Payload (raw): {msg.payload}")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Authentication
    if MQTT_CONFIG['user'] and MQTT_CONFIG['password']:
        client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
    
    # TLS
    if MQTT_CONFIG['use_tls']:
        try:
            if MQTT_CONFIG['ca_certs'] and os.path.exists(MQTT_CONFIG['ca_certs']):
                client.tls_set(
                    ca_certs=MQTT_CONFIG['ca_certs'],
                    cert_reqs=ssl.CERT_REQUIRED if not MQTT_CONFIG['tls_insecure'] else ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLS
                )
            else:
                client.tls_set(
                    cert_reqs=ssl.CERT_NONE if MQTT_CONFIG['tls_insecure'] else ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
            if MQTT_CONFIG['tls_insecure']:
                client.tls_insecure_set(True)
        except Exception as e:
            print(f"[WARNING] TLS setup error: {e}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\nStopping...")
        client.disconnect()
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'subscribe':
        # Subscribe mode: listen for messages
        test_subscribe()
    else:
        # Publish mode: send a test message
        device_id = sys.argv[1] if len(sys.argv) > 1 else 'test_device'
        action = sys.argv[2] if len(sys.argv) > 2 else 'update'
        user_id = sys.argv[3] if len(sys.argv) > 3 else '1'
        
        print(f"\nUsage examples:")
        print(f"  # Test publish (default: test_device, update, user 1)")
        print(f"  python test_provision_mqtt.py")
        print(f"  python test_provision_mqtt.py sal01")
        print(f"  python test_provision_mqtt.py sal01 update 1")
        print(f"  python test_provision_mqtt.py sal01 request 1")
        print(f"\n  # Subscribe mode (listen for messages)")
        print(f"  python test_provision_mqtt.py subscribe")
        print()
        
        test_provision_publish(device_id, action, user_id)

