import paho.mqtt.client as mqtt
import ssl
import time

# --- CONFIGURATION ---
BROKER = "192.168.43.214"
PORT = 8883
USER = "water_monitor"
PASS = "e2eeWater2025"
TOPIC_TO_ATTACK = "provision/#"  # Admin-only topic

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[INFO] Connected to Broker. Starting Attack...")
        # Attack: Try to subscribe to the forbidden admin topic
        client.subscribe(TOPIC_TO_ATTACK)
    else:
        print(f"[ERROR] Could not connect. Return Code: {rc}")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    # Check the QoS code returned by the Broker
    # Code 128 (0x80) = Failure / Denied
    # Code 0, 1, 2    = Success / Allowed
    
    status = granted_qos[0]
    
    print("\n" + "="*50)
    if status == 128:
        print("✅ PASS: SECURITY IS WORKING")
        print("   The Broker REJECTED the subscription (Code 128).")
        print("   User 'water_monitor' IS BLOCKED from Admin data.")
    else:
        print("❌ FAIL: SECURITY IS BROKEN")
        print(f"   The Broker ACCEPTED the subscription (Code {status}).")
        print("   User 'water_monitor' HAS FULL ACCESS.")
    print("="*50 + "\n")
    
    client.disconnect()

# Setup Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.on_connect = on_connect
client.on_subscribe = on_subscribe

# Run
print(f"Connecting to {BROKER}...")
try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except Exception as e:
    print(f"Connection Error: {e}")