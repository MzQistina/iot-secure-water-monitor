#!/bin/bash
# Comprehensive MQTT Authentication Fix Script
# Run this on Raspberry Pi with sudo

set -e

echo "=========================================="
echo "MQTT Authentication Fix"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

MQTT_USER="water_monitor"
PASSWORD_FILE="/etc/mosquitto/passwd"
ACL_FILE="/etc/mosquitto/acl.conf"
CONF_FILE="/etc/mosquitto/mosquitto.conf"

echo "Step 1: Checking password file..."
echo "----------------------------------------"
if [ -f "$PASSWORD_FILE" ]; then
    echo "✅ Password file exists: $PASSWORD_FILE"
    echo "   Users in password file:"
    sudo cut -d: -f1 "$PASSWORD_FILE" | sed 's/^/     - /'
    
    if grep -q "^$MQTT_USER:" "$PASSWORD_FILE"; then
        echo "✅ User '$MQTT_USER' exists in password file"
    else
        echo "❌ User '$MQTT_USER' NOT found in password file"
        echo ""
        echo "Adding user to password file..."
        echo "You will be prompted to enter a password for $MQTT_USER"
        sudo mosquitto_passwd "$PASSWORD_FILE" "$MQTT_USER"
        echo "✅ User added to password file"
    fi
else
    echo "❌ Password file does not exist: $PASSWORD_FILE"
    echo "Creating password file with user $MQTT_USER..."
    echo "You will be prompted to enter a password for $MQTT_USER"
    sudo mosquitto_passwd -c "$PASSWORD_FILE" "$MQTT_USER"
    echo "✅ Password file created"
fi
echo ""

echo "Step 2: Checking ACL file..."
echo "----------------------------------------"
if [ -f "$ACL_FILE" ]; then
    echo "✅ ACL file exists: $ACL_FILE"
    echo "   Contents:"
    cat "$ACL_FILE" | sed 's/^/     /'
    echo ""
    
    if grep -q "^user $MQTT_USER$" "$ACL_FILE"; then
        echo "✅ User '$MQTT_USER' found in ACL file"
        
        # Check for all required permissions
        HAS_WRITE_PROVISION=$(grep -A 10 "^user $MQTT_USER$" "$ACL_FILE" | grep -q "topic write provision" && echo "yes" || echo "no")
        HAS_READ_KEYS=$(grep -A 10 "^user $MQTT_USER$" "$ACL_FILE" | grep -q "topic read keys" && echo "yes" || echo "no")
        
        if [ "$HAS_WRITE_PROVISION" = "no" ]; then
            echo "❌ Missing provision write permissions"
            echo "   Adding provision permissions..."
            sudo sed -i "/^user $MQTT_USER$/a topic write provision/+/request\ntopic write provision/+/update\ntopic write provision/+/delete" "$ACL_FILE"
            echo "✅ Added provision permissions"
        else
            echo "✅ Provision write permissions found"
        fi
        
        if [ "$HAS_READ_KEYS" = "no" ]; then
            echo "❌ Missing keys read permissions"
            echo "   Adding keys read permission..."
            sudo sed -i "/^user $MQTT_USER$/a topic read keys/+/public" "$ACL_FILE"
            echo "✅ Added keys read permission"
        else
            echo "✅ Keys read permission found"
        fi
    else
        echo "❌ User '$MQTT_USER' NOT found in ACL file"
        echo "   Adding user with all required permissions..."
        cat >> "$ACL_FILE" << EOF

# Allow $MQTT_USER to publish to provision topics and subscribe to keys
user $MQTT_USER
topic write provision/+/request
topic write provision/+/update
topic write provision/+/delete
topic read keys/+/public
EOF
        echo "✅ User and permissions added to ACL file"
    fi
else
    echo "❌ ACL file does not exist: $ACL_FILE"
    echo "   Creating ACL file..."
    cat > "$ACL_FILE" << EOF
# Allow $MQTT_USER to publish to provision topics and subscribe to keys
user $MQTT_USER
topic write provision/+/request
topic write provision/+/update
topic write provision/+/delete
topic read keys/+/public
EOF
    chmod 644 "$ACL_FILE"
    echo "✅ ACL file created"
fi
echo ""

echo "Step 3: Checking mosquitto.conf..."
echo "----------------------------------------"
if [ -f "$CONF_FILE" ]; then
    # Check password_file
    if grep -q "^password_file" "$CONF_FILE"; then
        PASSWORD_FILE_IN_CONF=$(grep "^password_file" "$CONF_FILE" | awk '{print $2}')
        echo "✅ password_file configured: $PASSWORD_FILE_IN_CONF"
        if [ "$PASSWORD_FILE_IN_CONF" != "$PASSWORD_FILE" ]; then
            echo "⚠️  Warning: Config references different password file!"
            echo "   Config says: $PASSWORD_FILE_IN_CONF"
            echo "   We're using: $PASSWORD_FILE"
        fi
    else
        echo "❌ password_file not configured"
        echo "   Adding password_file directive..."
        echo "password_file $PASSWORD_FILE" >> "$CONF_FILE"
        echo "✅ Added password_file directive"
    fi
    
    # Check acl_file
    ACL_COUNT=$(grep -c "^acl_file" "$CONF_FILE" || echo "0")
    if [ "$ACL_COUNT" -eq 0 ]; then
        echo "❌ acl_file not configured"
        echo "   Adding acl_file directive..."
        echo "acl_file $ACL_FILE" >> "$CONF_FILE"
        echo "✅ Added acl_file directive"
    elif [ "$ACL_COUNT" -eq 1 ]; then
        ACL_FILE_IN_CONF=$(grep "^acl_file" "$CONF_FILE" | awk '{print $2}')
        echo "✅ acl_file configured: $ACL_FILE_IN_CONF"
        if [ "$ACL_FILE_IN_CONF" != "$ACL_FILE" ]; then
            echo "⚠️  Warning: Config references different ACL file!"
            echo "   Config says: $ACL_FILE_IN_CONF"
            echo "   We're using: $ACL_FILE"
        fi
    else
        echo "❌ Multiple acl_file entries found (duplicate)"
        echo "   Removing duplicates, keeping first one..."
        FIRST_ACL=$(grep "^acl_file" "$CONF_FILE" | head -1)
        sudo sed -i '/^acl_file/d' "$CONF_FILE"
        echo "$FIRST_ACL" >> "$CONF_FILE"
        echo "✅ Duplicates removed"
    fi
    
    # Check allow_anonymous
    if grep -q "^allow_anonymous" "$CONF_FILE"; then
        ALLOW_ANON=$(grep "^allow_anonymous" "$CONF_FILE" | awk '{print $2}')
        echo "   allow_anonymous: $ALLOW_ANON"
        if [ "$ALLOW_ANON" = "true" ]; then
            echo "   ⚠️  Warning: allow_anonymous is true (ACL may be bypassed)"
        fi
    fi
else
    echo "❌ mosquitto.conf not found: $CONF_FILE"
    exit 1
fi
echo ""

echo "Step 4: Verifying configuration..."
echo "----------------------------------------"
echo "Final ACL file contents:"
cat "$ACL_FILE" | sed 's/^/     /'
echo ""
echo "Users in password file:"
sudo cut -d: -f1 "$PASSWORD_FILE" | sed 's/^/     - /'
echo ""

echo "Step 5: Testing configuration..."
echo "----------------------------------------"
if sudo mosquitto -c "$CONF_FILE" -v 2>&1 | head -5; then
    echo "✅ Configuration syntax is valid"
else
    echo "❌ Configuration has errors"
    exit 1
fi
echo ""

echo "Step 6: Restarting Mosquitto..."
echo "----------------------------------------"
systemctl restart mosquitto
sleep 2

if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto restarted successfully"
    systemctl status mosquitto --no-pager -l | head -10
else
    echo "❌ Mosquitto failed to start"
    echo "Check logs: sudo journalctl -u mosquitto -n 50"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ Configuration complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Update the password in start_flask.ps1 on Windows"
echo "The password must match what you entered for $MQTT_USER"
echo ""
echo "Next steps:"
echo "1. Note the password you set for $MQTT_USER"
echo "2. Update start_flask.ps1: \$env:MQTT_PASSWORD = \"your_actual_password\""
echo "3. Restart Flask"
echo ""
