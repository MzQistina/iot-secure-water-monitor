#!/bin/bash
# Continuous resource monitoring script

LOG_FILE="${1:-/home/pi/resources_$(date +%Y%m%d_%H%M%S).log}"

echo "Starting resource monitoring..."
echo "Log file: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    echo "=== $(date) ===" >> "$LOG_FILE"
    echo "--- CPU & Memory ---" >> "$LOG_FILE"
    top -b -n 1 | head -20 >> "$LOG_FILE"
    echo "--- Network Connections (MQTT) ---" >> "$LOG_FILE"
    netstat -an | grep 8883 >> "$LOG_FILE"
    echo "--- Disk Usage ---" >> "$LOG_FILE"
    df -h >> "$LOG_FILE"
    echo "--- Active Processes (top 10 by CPU) ---" >> "$LOG_FILE"
    ps aux --sort=-%cpu | head -11 >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    sleep 10
done










