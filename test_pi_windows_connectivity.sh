#!/bin/bash
# Network Connectivity Test Script
# Run this on Raspberry Pi to diagnose connection issues with Windows server

WINDOWS_IP="${1:-192.168.43.196}"
PORT=5000

echo "=========================================="
echo "Network Connectivity Diagnostic Tool"
echo "=========================================="
echo ""
echo "Testing connection to Windows server: $WINDOWS_IP"
echo ""

# Get Pi's IP address
PI_IP=$(hostname -I | awk '{print $1}')
PI_SUBNET=$(echo $PI_IP | cut -d. -f1-3)
WIN_SUBNET=$(echo $WINDOWS_IP | cut -d. -f1-3)

echo "Pi IP Address: $PI_IP"
echo "Windows IP Address: $WINDOWS_IP"
echo ""

# Test 1: Subnet check
echo "Test 1: Network Subnet Check"
echo "----------------------------"
if [ "$PI_SUBNET" = "$WIN_SUBNET" ]; then
    echo "✅ Pi subnet: $PI_SUBNET"
    echo "✅ Windows subnet: $WIN_SUBNET"
    echo "✅ Both devices are on the same network"
else
    echo "❌ Pi subnet: $PI_SUBNET"
    echo "❌ Windows subnet: $WIN_SUBNET"
    echo "❌ WARNING: Devices appear to be on different networks!"
    echo "   They must be on the same network to communicate."
fi
echo ""

# Test 2: Ping test
echo "Test 2: Ping Connectivity"
echo "----------------------------"
if ping -c 3 -W 2 $WINDOWS_IP > /dev/null 2>&1; then
    echo "✅ Ping successful - basic network connectivity works"
    ping -c 2 $WINDOWS_IP | tail -2
else
    echo "❌ Ping failed - cannot reach Windows server"
    echo ""
    echo "Possible causes:"
    echo "  - Windows Firewall blocking ICMP (ping)"
    echo "  - Devices on different networks"
    echo "  - Windows server is offline"
    echo "  - Router blocking traffic"
fi
echo ""

# Test 3: Router connectivity
echo "Test 3: Router Connectivity"
echo "----------------------------"
ROUTER_IP=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -n "$ROUTER_IP" ]; then
    echo "Router IP: $ROUTER_IP"
    if ping -c 2 -W 2 $ROUTER_IP > /dev/null 2>&1; then
        echo "✅ Can reach router"
    else
        echo "❌ Cannot reach router - network issue"
    fi
else
    echo "⚠️  Could not determine router IP"
fi
echo ""

# Test 4: Internet connectivity
echo "Test 4: Internet Connectivity"
echo "----------------------------"
if ping -c 2 -W 2 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ Internet connectivity works (Pi has internet access)"
else
    echo "⚠️  No internet connectivity (may be normal if offline network)"
fi
echo ""

# Test 5: HTTP connection test
echo "Test 5: HTTP Connection to Flask Server"
echo "----------------------------"
if command -v curl > /dev/null 2>&1; then
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://$WINDOWS_IP:$PORT" 2>/dev/null)
    if [ "$HTTP_RESPONSE" = "200" ] || [ "$HTTP_RESPONSE" = "302" ] || [ "$HTTP_RESPONSE" = "404" ]; then
        echo "✅ HTTP connection successful (HTTP $HTTP_RESPONSE)"
        echo "   Flask server is reachable!"
    elif [ -n "$HTTP_RESPONSE" ]; then
        echo "⚠️  HTTP connection returned: $HTTP_RESPONSE"
        echo "   Server is reachable but may have issues"
    else
        echo "❌ HTTP connection failed"
        echo "   Testing connection..."
        curl -v --connect-timeout 5 "http://$WINDOWS_IP:$PORT" 2>&1 | head -10
    fi
else
    echo "⚠️  curl not installed - skipping HTTP test"
    echo "   Install with: sudo apt-get install curl"
fi
echo ""

# Test 6: Port connectivity (if nc is available)
echo "Test 6: Port Connectivity Check"
echo "----------------------------"
if command -v nc > /dev/null 2>&1; then
    if nc -zv -w 3 $WINDOWS_IP $PORT 2>&1 | grep -q "succeeded"; then
        echo "✅ Port $PORT is open and accessible"
    else
        echo "❌ Port $PORT is not accessible"
        echo "   This could mean:"
        echo "   - Flask server is not running"
        echo "   - Windows Firewall is blocking port $PORT"
        echo "   - Server is bound to localhost instead of 0.0.0.0"
    fi
else
    echo "⚠️  nc (netcat) not installed - skipping port test"
    echo "   Install with: sudo apt-get install netcat"
fi
echo ""

# Test 7: DNS resolution (if using hostname)
echo "Test 7: Network Interface Information"
echo "----------------------------"
echo "Active network interfaces:"
ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1" | head -6
echo ""

# Summary
echo "=========================================="
echo "Summary & Recommendations"
echo "=========================================="
echo ""

if [ "$PI_SUBNET" != "$WIN_SUBNET" ]; then
    echo "❌ CRITICAL: Devices are on different networks"
    echo "   Fix: Connect both devices to the same WiFi/router"
    echo ""
fi

if ! ping -c 1 -W 2 $WINDOWS_IP > /dev/null 2>&1; then
    echo "❌ Cannot ping Windows server"
    echo ""
    echo "Next steps:"
    echo "1. On Windows, check Windows Firewall:"
    echo "   - Allow ICMP (ping) through firewall"
    echo "   - Allow port $PORT (Flask server)"
    echo ""
    echo "2. Verify Flask server is running:"
    echo "   - Check if server is listening on 0.0.0.0:$PORT (not 127.0.0.1)"
    echo ""
    echo "3. Check network settings:"
    echo "   - Ensure both devices on same network"
    echo "   - Check router doesn't have AP Isolation enabled"
    echo ""
else
    echo "✅ Basic connectivity works (ping successful)"
    echo ""
    if command -v curl > /dev/null 2>&1; then
        HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://$WINDOWS_IP:$PORT" 2>/dev/null)
        if [ -z "$HTTP_TEST" ] || [ "$HTTP_TEST" = "000" ]; then
            echo "⚠️  Ping works but HTTP connection fails"
            echo "   This suggests:"
            echo "   - Flask server may not be running"
            echo "   - Port $PORT may be blocked by firewall"
            echo "   - Server may be bound to localhost (127.0.0.1) instead of 0.0.0.0"
        else
            echo "✅ HTTP connection also works!"
            echo "   You should be able to run the sensor client now."
        fi
    fi
fi

echo ""
echo "For detailed troubleshooting, see: FIX_PI_CANNOT_PING_WINDOWS.md"
echo ""

