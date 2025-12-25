#!/bin/bash
# Script to verify MQTT ACL configuration
# Run this on your Raspberry Pi

echo "=========================================="
echo "MQTT ACL Verification"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Some checks require root. Run with sudo for full verification."
    echo ""
fi

MQTT_USER="${MQTT_USER:-monitor_water}"
echo "Checking ACL for user: $MQTT_USER"
echo ""

# Check ACL files
ACL_FILES=("/etc/mosquitto/acl.conf" "/etc/mosquitto/conf.d/acl.conf")

for ACL_FILE in "${ACL_FILES[@]}"; do
    if [ -f "$ACL_FILE" ]; then
        echo "✅ Found ACL file: $ACL_FILE"
        echo "   Contents:"
        echo "   ----------------------------------------"
        cat "$ACL_FILE" | sed 's/^/   /'
        echo "   ----------------------------------------"
        echo ""
        
        # Check if user exists
        if grep -q "^user $MQTT_USER$" "$ACL_FILE"; then
            echo "✅ User '$MQTT_USER' found in ACL file"
            
            # Check for provision permissions
            if grep -A 10 "^user $MQTT_USER$" "$ACL_FILE" | grep -q "topic write provision"; then
                echo "✅ Provision permissions found"
            else
                echo "❌ Provision permissions MISSING!"
            fi
        else
            echo "❌ User '$MQTT_USER' NOT found in ACL file"
        fi
        echo ""
    fi
done

# Check mosquitto.conf
MOSQUITTO_CONF="/etc/mosquitto/mosquitto.conf"
if [ -f "$MOSQUITTO_CONF" ]; then
    echo "Checking mosquitto.conf..."
    if grep -q "^acl_file" "$MOSQUITTO_CONF"; then
        ACL_FILE_IN_CONF=$(grep "^acl_file" "$MOSQUITTO_CONF" | awk '{print $2}')
        echo "✅ ACL file referenced: $ACL_FILE_IN_CONF"
        
        if [ -f "$ACL_FILE_IN_CONF" ]; then
            echo "✅ Referenced ACL file exists"
        else
            echo "❌ Referenced ACL file does NOT exist: $ACL_FILE_IN_CONF"
        fi
    else
        echo "❌ No acl_file directive in mosquitto.conf"
        echo "   Add: acl_file /etc/mosquitto/acl.conf"
    fi
    
    # Check allow_anonymous
    if grep -q "^allow_anonymous" "$MOSQUITTO_CONF"; then
        ALLOW_ANON=$(grep "^allow_anonymous" "$MOSQUITTO_CONF" | awk '{print $2}')
        echo "   allow_anonymous: $ALLOW_ANON"
        if [ "$ALLOW_ANON" = "true" ]; then
            echo "   ⚠️  Warning: allow_anonymous is true (ACL may be bypassed)"
        fi
    fi
    echo ""
fi

# Check Mosquitto status
echo "Checking Mosquitto service status..."
if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto is running"
else
    echo "❌ Mosquitto is NOT running"
    echo "   Start with: sudo systemctl start mosquitto"
fi
echo ""

# Check recent logs for authorization errors
echo "Recent Mosquitto logs (last 20 lines):"
echo "----------------------------------------"
if [ -f "/var/log/mosquitto/mosquitto.log" ]; then
    sudo tail -20 /var/log/mosquitto/mosquitto.log 2>/dev/null || echo "   (Cannot read log file - run with sudo)"
else
    echo "   Log file not found at /var/log/mosquitto/mosquitto.log"
    echo "   Check with: sudo journalctl -u mosquitto -n 50"
fi
echo "----------------------------------------"
echo ""

echo "=========================================="
echo "Verification complete!"
echo "=========================================="
