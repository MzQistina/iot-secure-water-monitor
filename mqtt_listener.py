import json
import os
import ssl
from encryption_utils import aes_decrypt, hash_data
import paho.mqtt.client as mqtt

AES_KEY = b'my16bytepassword'

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback when MQTT client connects (API v2)."""
    if reason_code == 0:
        print("Connected with result code "+str(reason_code))
        client.subscribe("water/data")
        client.subscribe("secure/sensor")
        print("Subscribed to topics: water/data, secure/sensor")
    else:
        print("Failed to connect with result code "+str(reason_code))

def on_message(client, userdata, msg):
    try:
        # Decode message payload
        message_text = msg.payload.decode()
        print(f"\n=== Received message on topic '{msg.topic}' ===")
        print(f"Raw message: {message_text[:200]}...")
        
        # Parse JSON
        payload = json.loads(message_text)
        
        # Extract data and hash
        encrypted_data = payload.get("data")
        received_hash = payload.get("hash")
        
        if not encrypted_data:
            print(f"[INFO] No 'data' field found. Showing full payload: {payload}")
            return
        
        if not received_hash:
            print(f"[WARNING] No 'hash' field found. Skipping hash verification.")
            print(f"Payload: {payload}")
            return
        
        # Try to decrypt (data should be encrypted JSON string)
        try:
            decrypted_data = aes_decrypt(encrypted_data, AES_KEY)
            print(f"Decrypted data: {decrypted_data}")
            
            # Verify hash
            calculated_hash = hash_data(decrypted_data)
            
            if calculated_hash == received_hash:
                print("[OK] Hash verified - data is valid.")
            else:
                print(f"[ERROR] Hash mismatch - possible tampering.")
                print(f"   Received hash: {received_hash}")
                print(f"   Calculated hash: {calculated_hash}")
        except Exception as decrypt_error:
            print(f"[ERROR] Failed to decrypt data: {decrypt_error}")
            print(f"   The 'data' field should be encrypted JSON. Received: {encrypted_data[:100]}...")
            print(f"   Hint: Use a proper encryption function to encrypt your data before sending.")
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error: {e}")
        print(f"   Raw message received: {msg.payload.decode()[:200]}")
    except Exception as e:
        print(f"[ERROR] Error processing message: {e}")
        import traceback
        traceback.print_exc()
        print(f"   Raw message received: {msg.payload.decode()[:200]}")

# Get MQTT configuration from environment variables
# Defaults updated for physical Raspberry Pi (update to your Pi's IP)
mqtt_host = os.environ.get('MQTT_HOST', '192.168.43.214')  # Update to your physical Pi's IP
mqtt_port = int(os.environ.get('MQTT_PORT', '8883'))
mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'true').lower() in ('true', '1', 'yes')
mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS', 'certs/ca-cert.pem')
mqtt_user = os.environ.get('MQTT_USER', '')
mqtt_password = os.environ.get('MQTT_PASSWORD', '')
mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')

# Create MQTT client with API v2 (fixes deprecation warning)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Configure TLS if enabled
if mqtt_use_tls:
    if os.path.exists(mqtt_ca_certs):
        client.tls_set(
            ca_certs=mqtt_ca_certs,
            cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        if mqtt_tls_insecure:
            client.tls_insecure_set(True)
            print(f"TLS enabled with CA cert: {mqtt_ca_certs} (INSECURE MODE - certificate validation disabled)")
        else:
            print(f"TLS enabled with CA cert: {mqtt_ca_certs}")
    else:
        print(f"Warning: CA cert not found at {mqtt_ca_certs}, TLS disabled")
        mqtt_use_tls = False

# Set username and password if provided
if mqtt_user:
    client.username_pw_set(mqtt_user, mqtt_password if mqtt_password else None)

# Set callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker
print(f"Connecting to MQTT broker: {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})")
try:
    client.connect(mqtt_host, mqtt_port, 60)
    print("Listening for MQTT messages...")
    client.loop_forever()
except ssl.SSLCertVerificationError as e:
    print(f"[ERROR] Certificate verification failed: {e}")
    print(f"   This usually means the certificate CN doesn't match the IP address '{mqtt_host}'")
    print(f"   Solutions:")
    print(f"   1. Check certificate CN on Raspbian: sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject")
    print(f"   2. Regenerate certificate with CN matching '{mqtt_host}' (see SELF_HOSTED_MQTT_TLS_SETUP.md)")
    print(f"   3. For testing only, set MQTT_TLS_INSECURE=true (NOT recommended for production)")
except Exception as e:
    print(f"[ERROR] Failed to connect to MQTT broker: {e}")
    print(f"   Check that MQTT broker is running at {mqtt_host}:{mqtt_port}")
    print(f"   Verify network connectivity: Test-NetConnection -ComputerName {mqtt_host} -Port {mqtt_port}")
    print(f"   Verify certificate path: {mqtt_ca_certs}")
