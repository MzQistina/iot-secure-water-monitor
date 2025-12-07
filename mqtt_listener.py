import json
from encryption_utils import aes_decrypt, hash_data
import paho.mqtt.client as mqtt

AES_KEY = b'my16bytepassword'
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("water/data")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    encrypted_data = payload["data"]
    received_hash = payload["hash"]

    decrypted_data = aes_decrypt(encrypted_data, AES_KEY)
    calculated_hash = hash_data(decrypted_data)

    print("Received:", decrypted_data)

    if calculated_hash == received_hash:
        print("[✔] Hash verified — data is valid.")
    else:
        print("[✘] Hash mismatch — possible tampering.")

client = mqtt.Client()
client.connect("localhost")
client.subscribe("secure/sensor")
client.on_message = on_message

print("Listening for MQTT messages...")
client.loop_forever()
