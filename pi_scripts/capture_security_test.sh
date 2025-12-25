#!/bin/bash
# Complete security testing capture script for Raspberry Pi

TEST_NAME="${1:-security_test}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Use current user's home directory instead of hardcoded /home/pi
HOME_DIR="${HOME:-/home/$USER}"
BASE_DIR="${HOME_DIR}/security_captures/${TEST_NAME}_${TIMESTAMP}"

# Create directory and verify it was created
mkdir -p "$BASE_DIR" || {
    echo "ERROR: Failed to create directory: $BASE_DIR"
    echo "Current user: $USER"
    echo "Home directory: $HOME_DIR"
    exit 1
}

echo "Starting security test capture: $TEST_NAME"
echo "Output directory: $BASE_DIR"

# 1. Start packet capture
echo "Starting packet capture..."
# Check if tcpdump is available
if ! command -v tcpdump &> /dev/null; then
    echo "ERROR: tcpdump not found. Please install it first:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y tcpdump"
    exit 1
fi

sudo tcpdump -i any -w "$BASE_DIR/network.pcap" \
    port 8883 or port 1883 2>/dev/null &
TCPDUMP_PID=$!

# 2. Start Mosquitto log capture
echo "Starting Mosquitto log capture..."
sudo journalctl -u mosquitto -f > "$BASE_DIR/mosquitto.log" &
JOURNAL_PID=$!

# 3. Start resource monitoring
echo "Starting resource monitoring..."
(
    while true; do
        echo "=== $(date) ===" >> "$BASE_DIR/resources.log"
        echo "--- CPU & Memory ---" >> "$BASE_DIR/resources.log"
        top -b -n 1 | head -20 >> "$BASE_DIR/resources.log"
        echo "--- Network Connections ---" >> "$BASE_DIR/resources.log"
        netstat -an | grep 8883 >> "$BASE_DIR/resources.log"
        echo "--- Disk Usage ---" >> "$BASE_DIR/resources.log"
        df -h >> "$BASE_DIR/resources.log"
        echo "" >> "$BASE_DIR/resources.log"
        sleep 10
    done
) &
MONITOR_PID=$!

# 4. Start connection monitoring
echo "Starting connection monitoring..."
(
    while true; do
        echo "=== $(date) ===" >> "$BASE_DIR/connections.log"
        netstat -an | grep 8883 >> "$BASE_DIR/connections.log"
        sleep 5
    done
) &
CONNECTION_PID=$!

# Save PIDs for cleanup
echo $TCPDUMP_PID > "$BASE_DIR/pids.txt"
echo $JOURNAL_PID >> "$BASE_DIR/pids.txt"
echo $MONITOR_PID >> "$BASE_DIR/pids.txt"
echo $CONNECTION_PID >> "$BASE_DIR/pids.txt"

echo ""
echo "=== Capture Started ==="
echo "All captures running. Press Ctrl+C to stop."
echo "PIDs saved to: $BASE_DIR/pids.txt"
echo "Output directory: $BASE_DIR"
echo ""

# Wait for interrupt
trap "echo 'Stopping captures...'; kill $TCPDUMP_PID $JOURNAL_PID $MONITOR_PID $CONNECTION_PID 2>/dev/null; echo 'Captures stopped.'; exit" INT TERM
wait





