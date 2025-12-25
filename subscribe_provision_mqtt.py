"""
MQTT Subscriber Script for Provision Messages

This script subscribes to provision messages and displays their structure.
Useful for:
- TC-025: Provision Message Integrity Verification (E2EE Tag Authentication)
- TC-026: Message Tampering Detection

Usage:
    python subscribe_provision_mqtt.py [--detailed] [--timeout SECONDS]

Options:
    --detailed    Show detailed E2EE field analysis (for TC-025)
    --timeout     Timeout in seconds (default: 60)
"""

import json
import ssl
import paho.mqtt.client as mqtt
import time
import sys
import argparse

# Configuration
MQTT_HOST = '192.168.43.214'
MQTT_PORT = 8883
MQTT_USER = 'water_monitor'
MQTT_PASS = 'e2eeWater2025'
TOPIC = 'provision/+/+'

message_received = False
captured_payload = None

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback when MQTT client connects."""
    if reason_code == 0:
        print('[✓] Connected to MQTT broker')
        print(f'[✓] Subscribed to {TOPIC}')
        print('[⏳] Waiting for provision messages...')
        print('[💡] TIP: In another terminal, run: python test_provision_mqtt.py sal01 update 1')
    else:
        print(f'[✗] Connection failed: {reason_code}')
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback when MQTT message is received."""
    global message_received, captured_payload
    message_received = True
    
    print(f'\n[📨] Message received on topic: {msg.topic}')
    
    try:
        payload = json.loads(msg.payload.decode())
        captured_payload = payload.copy()
        
        print('\n[📋] Payload structure:')
        print(f'  Keys: {list(payload.keys())}')
        
        # Detailed E2EE analysis (for TC-025)
        if args.detailed:
            # Check for E2EE fields (provision messages use tag, not hash)
            if all(k in payload for k in ['session_key', 'ciphertext', 'nonce', 'tag']):
                print('\n[✅] E2EE encrypted message found!')
                session_key_len = len(payload['session_key'])
                ciphertext_len = len(payload['ciphertext'])
                nonce_len = len(payload['nonce'])
                tag_len = len(payload['tag'])
                print(f'  session_key: {session_key_len} chars (RSA-encrypted session key)')
                print(f'  ciphertext: {ciphertext_len} chars (AES-encrypted data)')
                print(f'  nonce: {nonce_len} chars (encryption nonce)')
                print(f'  tag: {tag_len} chars (AES-EAX authentication tag)')
                print('\n[✅] Tag field provides integrity verification (equivalent to hash)')
                print('  The tag automatically detects tampering with ciphertext')
            elif 'hash' in payload:
                print('\n[⚠️] Hash field found, but provision messages should use E2EE tag')
                print('  This might be a sensor data message - use TC-027 instead')
            else:
                print('\n[⚠️] E2EE fields not found in payload')
                print('  Available fields:', list(payload.keys()))
                print('  [💡] Provision messages should have: session_key, ciphertext, nonce, tag')
        else:
            # Simple capture (for TC-026)
            if all(k in payload for k in ['session_key', 'ciphertext', 'nonce', 'tag']):
                print('\n[✅] E2EE encrypted message captured!')
                print(f'  session_key length: {len(payload["session_key"])} chars')
                print(f'  ciphertext length: {len(payload["ciphertext"])} chars')
                print(f'  nonce length: {len(payload["nonce"])} chars')
                print(f'  tag length: {len(payload["tag"])} chars')
        
        print(f'\n[📄] Full payload: {json.dumps(payload, indent=2)}')
        
    except Exception as e:
        print(f'  [✗] Error parsing payload: {type(e).__name__}: {e}')
        print(f'  Raw payload: {msg.payload.decode()[:200]}...')
    
    client.disconnect()

def main():
    """Main function to run the subscriber."""
    global args
    
    parser = argparse.ArgumentParser(
        description='Subscribe to MQTT provision messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple capture (for TC-026)
  python subscribe_provision_mqtt.py
  
  # Detailed analysis (for TC-025)
  python subscribe_provision_mqtt.py --detailed
  
  # Custom timeout
  python subscribe_provision_mqtt.py --timeout 30
        """
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed E2EE field analysis (for TC-025)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Create MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect and subscribe
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.subscribe(TOPIC)
        client.loop_start()
        
        # Wait for message
        timeout = args.timeout
        start = time.time()
        while not message_received and (time.time() - start) < timeout:
            time.sleep(0.1)
            elapsed = int(time.time() - start)
            if elapsed > 0 and elapsed % 10 == 0 and not message_received:
                print(f'[⏳] Still waiting... ({elapsed}s elapsed)')
        
        client.loop_stop()
        
        if message_received:
            print('\n[✅] Payload captured successfully!')
            if not args.detailed:
                print('[💾] Save this payload structure for tampering test (TC-026)')
            else:
                print('[💾] Use this for E2EE tag verification (TC-025)')
        else:
            print(f'\n[⚠️] No messages received after {timeout} seconds')
            print('[💡] Make sure to trigger a provision message in another terminal:')
            print('     python test_provision_mqtt.py sal01 update 1')
            print('\n[💡] Then run this subscriber script again.')
            sys.exit(1)
            
    except KeyboardInterrupt:
        print('\n[⚠️] Interrupted by user')
        client.loop_stop()
        sys.exit(0)
    except Exception as e:
        print(f'\n[✗] Error: {type(e).__name__}: {e}')
        client.loop_stop()
        sys.exit(1)

if __name__ == '__main__':
    main()
