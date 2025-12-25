#!/bin/bash
# Stop all running security test captures

echo "Stopping all captures..."

# Kill tcpdump
sudo pkill tcpdump

# Kill journalctl followers
sudo pkill -f "journalctl -u mosquitto"

# Kill monitoring scripts
pkill -f "top -b"
pkill -f "netstat.*8883"

# Kill any remaining capture scripts
pkill -f capture_security_test.sh

echo "All captures stopped."
echo ""
echo "To verify, check for running processes:"
echo "  ps aux | grep -E 'tcpdump|journalctl|netstat' | grep -v grep"





