#!/usr/bin/env python3
"""
Key Cleanup Agent for Raspbian

This agent listens for device deletion events via MQTT and automatically
deletes the corresponding keypairs on Raspbian.

Usage:
    python3 key_cleanup_agent.py

Environment Variables:
    MQTT_HOST: MQTT broker host (default: localhost)
    MQTT_PORT: MQTT broker port (default: 1883)
    MQTT_USER: MQTT username (optional)
    MQTT_PASSWORD: MQTT password (optional)
    MQTT_DELETE_TOPIC: Topic to listen for deletion events (default: devices/delete)
    SENSOR_KEYS_DIR: Directory containing sensor keys (default: ./sensor_keys)
"""

import os
import sys
import json
import shutil
from typing import Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Install with: pip3 install paho-mqtt")
    sys.exit(1)


# Configuration
MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_DELETE_TOPIC = os.environ.get('MQTT_DELETE_TOPIC', 'devices/delete')

# SENSOR_KEYS_DIR: Default to current directory's sensor_keys, or use environment variable
# If running from ~/water-monitor/, it will use ~/water-monitor/sensor_keys
default_keys_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sensor_keys')
if os.path.exists(os.path.join(os.getcwd(), 'sensor_keys')):
    # If sensor_keys exists in current directory, use that
    default_keys_dir = os.path.join(os.getcwd(), 'sensor_keys')
SENSOR_KEYS_DIR = os.environ.get('SENSOR_KEYS_DIR', default_keys_dir)

# Resolve absolute path
SENSOR_KEYS_DIR = os.path.abspath(os.path.expanduser(SENSOR_KEYS_DIR))


def delete_device_keys(user_id: str, device_id: str) -> bool:
    """
    Delete device keys from Raspbian.
    
    Args:
        user_id: User ID
        device_id: Device ID
        
    Returns:
        True if keys were deleted, False otherwise
    """
    deleted = False
    
    # Try user-specific location first
    user_key_path = os.path.join(SENSOR_KEYS_DIR, str(user_id), device_id)
    if os.path.exists(user_key_path):
        try:
            shutil.rmtree(user_key_path)
            print(f"✅ Deleted: {user_key_path}")
            deleted = True
        except Exception as e:
            print(f"❌ Error deleting {user_key_path}: {e}")
            return False
    
    # Try legacy location
    legacy_key_path = os.path.join(SENSOR_KEYS_DIR, device_id)
    if os.path.exists(legacy_key_path):
        try:
            shutil.rmtree(legacy_key_path)
            print(f"✅ Deleted (legacy): {legacy_key_path}")
            deleted = True
        except Exception as e:
            print(f"❌ Error deleting {legacy_key_path}: {e}")
            return False
    
    if not deleted:
        print(f"⚠️  Keys not found for device '{device_id}' (user: {user_id})")
        print(f"   Checked: {user_key_path}")
        print(f"   Checked: {legacy_key_path}")
    
    return deleted


def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects."""
    if rc == 0:
        print(f"✅ Connected to MQTT broker: {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_DELETE_TOPIC)
        print(f"📡 Subscribed to topic: {MQTT_DELETE_TOPIC}")
    else:
        print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback when MQTT message is received."""
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        device_id = data.get('device_id')
        user_id = data.get('user_id')
        action = data.get('action', 'delete')
        
        if action != 'delete':
            print(f"⚠️  Ignoring non-delete action: {action}")
            return
        
        if not device_id:
            print("❌ Missing device_id in deletion message")
            return
        
        if not user_id:
            print(f"⚠️  Missing user_id, trying to delete from legacy location")
            user_id = 'unknown'
        
        print(f"\n🗑️  Received deletion request:")
        print(f"   Device ID: {device_id}")
        print(f"   User ID: {user_id}")
        print(f"   Topic: {msg.topic}")
        
        # Delete keys
        success = delete_device_keys(user_id, device_id)
        
        if success:
            print(f"✅ Successfully deleted keys for device '{device_id}'")
        else:
            print(f"⚠️  No keys found or deletion failed for device '{device_id}'")
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in message: {e}")
        print(f"   Payload: {payload[:100]}")
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()


def on_disconnect(client, userdata, rc):
    """Callback when MQTT client disconnects."""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection from MQTT broker (rc={rc})")
    else:
        print("✅ Disconnected from MQTT broker")


def main():
    """Main function to run the cleanup agent."""
    print("=" * 70)
    print("Key Cleanup Agent for Raspbian")
    print("=" * 70)
    print(f"MQTT Broker: {MQTT_HOST}:{MQTT_PORT}")
    print(f"Topic: {MQTT_DELETE_TOPIC}")
    print(f"Sensor Keys Directory: {SENSOR_KEYS_DIR}")
    print("=" * 70)
    
    # Verify sensor keys directory exists
    if not os.path.exists(SENSOR_KEYS_DIR):
        print(f"⚠️  Warning: Sensor keys directory not found: {SENSOR_KEYS_DIR}")
        print(f"   Creating directory...")
        try:
            os.makedirs(SENSOR_KEYS_DIR, mode=0o755, exist_ok=True)
            print(f"✅ Created directory: {SENSOR_KEYS_DIR}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            sys.exit(1)
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Set credentials if provided
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        print(f"🔐 Using MQTT authentication: {MQTT_USER}")
    
    # Connect to broker
    try:
        print(f"\n🔌 Connecting to MQTT broker...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Failed to connect to MQTT broker: {e}")
        print(f"   Check that MQTT broker is running at {MQTT_HOST}:{MQTT_PORT}")
        sys.exit(1)
    
    # Start listening
    print(f"\n👂 Listening for device deletion events...")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopping cleanup agent...")
        client.disconnect()
        print("✅ Cleanup agent stopped")


if __name__ == '__main__':
    main()

