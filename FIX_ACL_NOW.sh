#!/bin/bash
# Quick fix for MQTT ACL - run this on Raspberry Pi

set -e

MQTT_USER="water_monitor"
ACL_FILE="/etc/mosquitto/acl.conf"
PASSWD_FILE="/etc/mosquitto/passwd"

echo "=========================================="
echo "Fixing MQTT ACL for $MQTT_USER"
echo "=========================================="
echo ""

# Check if ACL file exists
if [ ! -f "$ACL_FILE" ]; then
    echo "❌ ACL file not found: $ACL_FILE"
    echo "Creating new ACL file..."
    sudo touch "$ACL_FILE"
    sudo chown mosquitto:mosquitto "$ACL_FILE"
    sudo chmod 644 "$ACL_FILE"
fi

# Check if user exists in password file
if ! sudo grep -q "^$MQTT_USER:" "$PASSWD_FILE" 2>/dev/null; then
    echo "❌ User $MQTT_USER not found in password file!"
    echo "Creating user with password: e2eeWater2025"
    echo "e2eeWater2025" | sudo mosquitto_passwd -c "$PASSWD_FILE" "$MQTT_USER"
    echo "✅ User created"
else
    echo "✅ User $MQTT_USER exists in password file"
fi

# Check current ACL content
echo ""
echo "Current ACL file content:"
echo "----------------------------------------"
sudo cat "$ACL_FILE" 2>/dev/null || echo "(empty)"
echo "----------------------------------------"
echo ""

# Check if user entry exists in ACL
if ! sudo grep -q "^user $MQTT_USER$" "$ACL_FILE" 2>/dev/null; then
    echo "❌ User entry not found in ACL file"
    echo "Adding user entry..."
    echo "user $MQTT_USER" | sudo tee -a "$ACL_FILE" > /dev/null
    echo "✅ User entry added"
else
    echo "✅ User entry exists in ACL file"
fi

# Check if provision topics are allowed
NEEDS_UPDATE=0

if ! sudo grep -q "topic write provision/+/request" "$ACL_FILE" 2>/dev/null; then
    echo "❌ Missing: topic write provision/+/request"
    NEEDS_UPDATE=1
fi

if ! sudo grep -q "topic write provision/+/update" "$ACL_FILE" 2>/dev/null; then
    echo "❌ Missing: topic write provision/+/update"
    NEEDS_UPDATE=1
fi

if ! sudo grep -q "topic write provision/+/delete" "$ACL_FILE" 2>/dev/null; then
    echo "❌ Missing: topic write provision/+/delete"
    NEEDS_UPDATE=1
fi

if ! sudo grep -q "topic read keys/+/public" "$ACL_FILE" 2>/dev/null; then
    echo "❌ Missing: topic read keys/+/public"
    NEEDS_UPDATE=1
fi

if [ $NEEDS_UPDATE -eq 1 ]; then
    echo ""
    echo "Updating ACL file..."
    
    # Remove old topic entries for this user (if any)
    sudo sed -i "/^user $MQTT_USER$/,/^user /{ /^topic /d; }" "$ACL_FILE"
    sudo sed -i "/^user $MQTT_USER$/,${ /^topic /d; }" "$ACL_FILE"
    
    # Add new topic entries after user line
    sudo sed -i "/^user $MQTT_USER$/a topic write provision/+/request\ntopic write provision/+/update\ntopic write provision/+/delete\ntopic read keys/+/public" "$ACL_FILE"
    
    echo "✅ ACL file updated"
else
    echo "✅ All required topics are already in ACL file"
fi

# Show final ACL content
echo ""
echo "Final ACL file content:"
echo "----------------------------------------"
sudo cat "$ACL_FILE"
echo "----------------------------------------"
echo ""

# Restart mosquitto
echo "Restarting mosquitto service..."
sudo systemctl restart mosquitto
sleep 2

if sudo systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto restarted successfully"
else
    echo "❌ Mosquitto failed to start!"
    echo "Check logs: sudo journalctl -u mosquitto -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ ACL fix completed!"
echo "=========================================="
echo ""
echo "Test the connection from Windows:"
echo "  .\test_mqtt_publish_direct.ps1"
