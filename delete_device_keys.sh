#!/bin/bash
# Delete device keys from Raspbian VirtualBox
# Usage: ./delete_device_keys.sh <user_id> <device_id>
# Example: ./delete_device_keys.sh 1 pH01

if [ $# -ne 2 ]; then
    echo "Usage: $0 <user_id> <device_id>"
    echo "Example: $0 1 pH01"
    exit 1
fi

USER_ID=$1
DEVICE_ID=$2
KEY_PATH="sensor_keys/${USER_ID}/${DEVICE_ID}"

echo "🗑️  Deleting keys for device: $DEVICE_ID (user: $USER_ID)"

# Check user-specific location first
if [ -d "$KEY_PATH" ]; then
    echo "   Found keys at: $KEY_PATH"
    rm -rf "$KEY_PATH"
    echo "✅ Deleted: $KEY_PATH"
elif [ -d "sensor_keys/${DEVICE_ID}" ]; then
    # Check legacy location
    echo "   Found keys in legacy location: sensor_keys/${DEVICE_ID}"
    read -p "   Delete from legacy location? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "sensor_keys/${DEVICE_ID}"
        echo "✅ Deleted: sensor_keys/${DEVICE_ID}"
    else
        echo "❌ Deletion cancelled"
        exit 1
    fi
else
    echo "⚠️  Key directory not found: $KEY_PATH"
    echo "   Also checked: sensor_keys/${DEVICE_ID}"
    echo "   Keys may have already been deleted or device_id is incorrect"
    exit 1
fi

# Verify deletion
if [ ! -d "$KEY_PATH" ] && [ ! -d "sensor_keys/${DEVICE_ID}" ]; then
    echo "✅ Verification: Keys successfully deleted"
else
    echo "⚠️  Warning: Keys may still exist"
fi

