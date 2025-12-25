#!/bin/bash
# Script to fix MQTT ACL permissions for provision topics
# Run this on your Raspberry Pi (where Mosquitto is running)

set -e

echo "=========================================="
echo "MQTT ACL Configuration Fix"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get MQTT username from environment or prompt
MQTT_USER="${MQTT_USER:-}"
if [ -z "$MQTT_USER" ]; then
    echo "Enter your MQTT username (the value of MQTT_USER environment variable):"
    read MQTT_USER
fi

if [ -z "$MQTT_USER" ]; then
    echo "❌ MQTT username is required!"
    exit 1
fi

echo "✅ Using MQTT username: $MQTT_USER"
echo ""

# Find Mosquitto config directory
MOSQUITTO_CONF="/etc/mosquitto/mosquitto.conf"
ACL_FILE="/etc/mosquitto/acl.conf"
ACL_FILE_ALT="/etc/mosquitto/conf.d/acl.conf"

# Check which ACL file exists or should be created
if [ -f "$ACL_FILE" ]; then
    ACL_FILE_TO_USE="$ACL_FILE"
elif [ -f "$ACL_FILE_ALT" ]; then
    ACL_FILE_TO_USE="$ACL_FILE_ALT"
else
    # Create new ACL file
    ACL_FILE_TO_USE="$ACL_FILE"
    echo "Creating new ACL file: $ACL_FILE_TO_USE"
    touch "$ACL_FILE_TO_USE"
    chmod 644 "$ACL_FILE_TO_USE"
fi

echo "✅ Using ACL file: $ACL_FILE_TO_USE"
echo ""

# Check if user already exists in ACL file
if grep -q "^user $MQTT_USER$" "$ACL_FILE_TO_USE"; then
    echo "⚠️  User '$MQTT_USER' already exists in ACL file"
    echo "Checking if provision permissions exist..."
    
    if grep -q "topic write provision" "$ACL_FILE_TO_USE"; then
        echo "✅ Provision permissions already exist"
        echo ""
        echo "Current ACL entries for $MQTT_USER:"
        sed -n "/^user $MQTT_USER$/,/^user /p" "$ACL_FILE_TO_USE" | head -n -1
        echo ""
        echo "If permissions are missing, you may need to add them manually."
    else
        echo "❌ Provision permissions missing. Adding them..."
        # Add permissions after the user line
        sed -i "/^user $MQTT_USER$/a topic write provision/+/request\ntopic write provision/+/update\ntopic write provision/+/delete\ntopic read keys/+/public" "$ACL_FILE_TO_USE"
        echo "✅ Added provision permissions"
    fi
else
    echo "Adding user '$MQTT_USER' with provision permissions..."
    cat >> "$ACL_FILE_TO_USE" << EOF

# Allow $MQTT_USER to publish to provision topics
user $MQTT_USER
topic write provision/+/request
topic write provision/+/update
topic write provision/+/delete
topic read keys/+/public
EOF
    echo "✅ Added user and permissions"
fi

echo ""
echo "Verifying ACL file configuration..."
echo "----------------------------------------"
grep -A 5 "^user $MQTT_USER$" "$ACL_FILE_TO_USE" || echo "⚠️  Could not find user entry (this might be okay if using pattern-based ACL)"
echo "----------------------------------------"
echo ""

# Check if mosquitto.conf references the ACL file
if [ -f "$MOSQUITTO_CONF" ]; then
    if grep -q "^acl_file" "$MOSQUITTO_CONF"; then
        ACL_FILE_IN_CONF=$(grep "^acl_file" "$MOSQUITTO_CONF" | awk '{print $2}')
        echo "✅ Mosquitto config references ACL file: $ACL_FILE_IN_CONF"
        if [ "$ACL_FILE_IN_CONF" != "$ACL_FILE_TO_USE" ]; then
            echo "⚠️  Warning: Config references different ACL file!"
            echo "   Config says: $ACL_FILE_IN_CONF"
            echo "   We modified: $ACL_FILE_TO_USE"
        fi
    else
        echo "⚠️  Mosquitto config does not reference acl_file"
        echo "Adding acl_file directive to mosquitto.conf..."
        echo "" >> "$MOSQUITTO_CONF"
        echo "# ACL file for access control" >> "$MOSQUITTO_CONF"
        echo "acl_file $ACL_FILE_TO_USE" >> "$MOSQUITTO_CONF"
        echo "✅ Added acl_file directive"
    fi
else
    echo "⚠️  Warning: Could not find mosquitto.conf at $MOSQUITTO_CONF"
fi

echo ""
echo "=========================================="
echo "Restarting Mosquitto..."
echo "=========================================="
systemctl restart mosquitto

if [ $? -eq 0 ]; then
    echo "✅ Mosquitto restarted successfully"
    echo ""
    echo "Checking Mosquitto status..."
    systemctl status mosquitto --no-pager -l | head -n 10
else
    echo "❌ Failed to restart Mosquitto!"
    echo "Check logs with: sudo journalctl -u mosquitto -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Configuration complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test MQTT publish from Windows: .\test_mqtt_publish.ps1"
echo "2. Try the provision request again from the web interface"
echo "3. Check Mosquitto logs if issues persist:"
echo "   sudo tail -f /var/log/mosquitto/mosquitto.log"
echo ""
