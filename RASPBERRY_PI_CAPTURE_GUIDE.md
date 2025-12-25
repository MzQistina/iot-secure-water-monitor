# Raspberry Pi Security Testing Capture Guide

## Overview

When performing security testing, capturing data on the Raspberry Pi (MQTT broker) provides crucial insights that complement Wireshark captures from the client side. This guide covers all the data you should capture during security testing.

---

## 1. Network Packet Capture (tcpdump)

### Basic Capture
```bash
# SSH into Raspberry Pi
ssh pi@192.168.43.214

# Capture all MQTT traffic
sudo tcpdump -i any -w /home/pi/mqtt_capture.pcap port 8883 or port 1883

# Or capture on specific interface (usually wlan0 or eth0)
sudo tcpdump -i wlan0 -w /home/pi/mqtt_capture.pcap port 8883 or port 1883
```

### Advanced Capture with More Details
```bash
# Capture with verbose output and larger packet size
sudo tcpdump -i any -s 65535 -w /home/pi/mqtt_capture_detailed.pcap \
    port 8883 or port 1883 -v

# Capture with timestamps
sudo tcpdump -i any -w /home/pi/mqtt_capture.pcap \
    port 8883 or port 1883 -tttt
```

### Capture During Specific Attack
```bash
# Start capture before running attack
sudo tcpdump -i any -w /home/pi/attack_replay.pcap \
    port 8883 or port 1883 &
    
# Run your attack from Windows machine
# Then stop capture
sudo pkill tcpdump
```

### Transfer Capture File to Windows
```bash
# From Windows PowerShell
scp pi@192.168.43.214:/home/pi/mqtt_capture.pcap ./
```

---

## 2. Mosquitto Broker Logs

### Enable Mosquitto Logging

First, check Mosquitto configuration:
```bash
# Check if logging is enabled
sudo cat /etc/mosquitto/mosquitto.conf | grep -i log

# Common log locations:
# - /var/log/mosquitto/mosquitto.log
# - /var/log/mosquitto/mosquitto.log (if configured)
# - syslog (journalctl)
```

### View Real-time Logs
```bash
# If Mosquitto logs to file
sudo tail -f /var/log/mosquitto/mosquitto.log

# Or via systemd journal
sudo journalctl -u mosquitto -f

# With timestamps
sudo journalctl -u mosquitto -f --since "1 hour ago"
```

### Capture Logs During Testing
```bash
# Method 1: Redirect to file
sudo journalctl -u mosquitto --since "now" > /home/pi/mosquitto_test.log

# Method 2: Use tee to see and save
sudo journalctl -u mosquitto -f | tee /home/pi/mosquitto_live.log

# Method 3: Capture specific time window
sudo journalctl -u mosquitto \
    --since "2025-01-15 10:00:00" \
    --until "2025-01-15 11:00:00" \
    > /home/pi/mosquitto_window.log
```

### What to Look For in Logs
- Authentication failures
- Connection attempts
- Topic access denials
- SSL/TLS handshake errors
- Client disconnections
- Error messages

---

## 3. System Logs (syslog/journalctl)

### Capture System Events
```bash
# All system logs during test period
sudo journalctl --since "1 hour ago" > /home/pi/system_logs.log

# Network-related logs
sudo journalctl -k --since "1 hour ago" > /home/pi/kernel_network.log

# Authentication-related logs
sudo journalctl -u ssh -u mosquitto --since "1 hour ago" \
    > /home/pi/auth_logs.log
```

### Monitor Failed Login Attempts
```bash
# Check for failed SSH attempts (brute force detection)
sudo journalctl -u ssh | grep "Failed password"

# Check for authentication failures
sudo journalctl -u mosquitto | grep -i "auth\|denied\|failed"
```

---

## 4. Network Connection Monitoring

### Monitor Active Connections
```bash
# Watch active MQTT connections in real-time
watch -n 1 'netstat -an | grep 8883'

# Or use ss command
watch -n 1 'ss -tunp | grep 8883'

# Save connection states during test
while true; do
    echo "=== $(date) ===" >> /home/pi/connections.log
    netstat -an | grep 8883 >> /home/pi/connections.log
    sleep 5
done
```

### Monitor Connection Attempts
```bash
# Track new connections
sudo tcpdump -i any -n 'tcp port 8883 and tcp[tcpflags] & tcp-syn != 0' \
    -w /home/pi/connection_attempts.pcap
```

---

## 5. Resource Monitoring (CPU, Memory, Network)

### Monitor System Resources
```bash
# Install iftop for network monitoring (if not installed)
sudo apt-get install iftop htop iotop

# Monitor CPU and memory
htop  # Interactive, or use:
top -b -n 1 > /home/pi/system_resources.log

# Monitor network traffic
sudo iftop -i wlan0 -t -s 60 > /home/pi/network_traffic.log

# Monitor disk I/O
sudo iotop -b -n 1 > /home/pi/disk_io.log
```

### Continuous Resource Monitoring Script
Create `/home/pi/monitor_resources.sh`:
```bash
#!/bin/bash
LOG_FILE="/home/pi/resources_$(date +%Y%m%d_%H%M%S).log"

while true; do
    echo "=== $(date) ===" >> "$LOG_FILE"
    echo "--- CPU & Memory ---" >> "$LOG_FILE"
    top -b -n 1 | head -20 >> "$LOG_FILE"
    echo "--- Network Connections ---" >> "$LOG_FILE"
    netstat -an | grep 8883 >> "$LOG_FILE"
    echo "--- Disk Usage ---" >> "$LOG_FILE"
    df -h >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    sleep 10
done
```

Make it executable and run:
```bash
chmod +x /home/pi/monitor_resources.sh
./monitor_resources.sh &
```

---

## 6. Authentication and Access Control Logs

### Monitor Mosquitto ACL Violations
```bash
# If ACL logging is enabled, check for denied access
sudo journalctl -u mosquitto | grep -i "denied\|acl\|unauthorized"

# Monitor password file access (if using password file)
sudo auditctl -w /etc/mosquitto/passwd -p rwxa -k mosquitto_auth
```

### Check Authentication Database
```bash
# If using password file, monitor changes (read-only check)
ls -la /etc/mosquitto/passwd
cat /etc/mosquitto/passwd | wc -l  # Count users
```

---

## 7. TLS/SSL Certificate Monitoring

### Check Certificate Usage
```bash
# Monitor certificate file access
sudo auditctl -w /etc/mosquitto/certs/ -p rwxa -k mosquitto_certs

# Check certificate expiration
openssl x509 -in /etc/mosquitto/certs/ca.crt -noout -dates
openssl x509 -in /etc/mosquitto/certs/server.crt -noout -dates
```

### Monitor TLS Handshake Failures
```bash
# In Mosquitto logs
sudo journalctl -u mosquitto | grep -i "tls\|ssl\|certificate\|handshake"
```

---

## 8. Complete Testing Capture Script

Create `/home/pi/capture_security_test.sh`:
```bash
#!/bin/bash
# Complete security testing capture script

TEST_NAME="${1:-security_test}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE_DIR="/home/pi/security_captures/${TEST_NAME}_${TIMESTAMP}"

mkdir -p "$BASE_DIR"

echo "Starting security test capture: $TEST_NAME"
echo "Output directory: $BASE_DIR"

# 1. Start packet capture
echo "Starting packet capture..."
sudo tcpdump -i any -w "$BASE_DIR/network.pcap" \
    port 8883 or port 1883 &
TCPDUMP_PID=$!

# 2. Start Mosquitto log capture
echo "Starting Mosquitto log capture..."
sudo journalctl -u mosquitto -f > "$BASE_DIR/mosquitto.log" &
JOURNAL_PID=$!

# 3. Start resource monitoring
echo "Starting resource monitoring..."
./monitor_resources.sh > "$BASE_DIR/resources.log" &
MONITOR_PID=$!

# 4. Start connection monitoring
echo "Starting connection monitoring..."
while true; do
    echo "=== $(date) ===" >> "$BASE_DIR/connections.log"
    netstat -an | grep 8883 >> "$BASE_DIR/connections.log"
    sleep 5
done &
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
echo ""

# Wait for interrupt
trap "kill $TCPDUMP_PID $JOURNAL_PID $MONITOR_PID $CONNECTION_PID 2>/dev/null; exit" INT TERM
wait
```

### Usage:
```bash
# Make executable
chmod +x /home/pi/capture_security_test.sh

# Start capture
./capture_security_test.sh replay_attack_test

# Run your attack from Windows machine
# Then stop with Ctrl+C

# Files will be in: /home/pi/security_captures/replay_attack_test_TIMESTAMP/
```

---

## 9. Stop All Captures Script

Create `/home/pi/stop_captures.sh`:
```bash
#!/bin/bash
# Stop all running captures

echo "Stopping all captures..."

# Kill tcpdump
sudo pkill tcpdump

# Kill journalctl followers
sudo pkill -f "journalctl -u mosquitto"

# Kill monitoring scripts
pkill -f monitor_resources.sh
pkill -f capture_security_test.sh

# Kill connection monitoring
pkill -f "netstat.*8883"

echo "All captures stopped."
```

---

## 10. Analysis After Capture

### Transfer All Files to Windows
```powershell
# From Windows PowerShell
scp -r pi@192.168.43.214:/home/pi/security_captures/* ./

# Or specific test
scp -r pi@192.168.43.214:/home/pi/security_captures/replay_attack_test_* ./
```

### Analyze on Windows
```bash
# Analyze pcap file
python security_test_analyzer.py network.pcap

# Review Mosquitto logs
notepad mosquitto.log

# Review resource usage
notepad resources.log
```

---

## 11. What to Capture for Each Attack Scenario

### Eavesdropping Attack
- [ ] Network packet capture (tcpdump)
- [ ] Mosquitto logs (check for unencrypted connections)
- [ ] System logs (check for warnings)

### MITM Attack
- [ ] Network packet capture (TLS handshake analysis)
- [ ] Mosquitto logs (TLS errors, certificate issues)
- [ ] Connection monitoring (failed connections)

### Credential Sniffing
- [ ] Network packet capture (CONNECT packets)
- [ ] Mosquitto logs (authentication attempts)
- [ ] System logs (failed logins)

### Replay Attack
- [ ] Network packet capture (duplicate messages)
- [ ] Mosquitto logs (message processing)
- [ ] Application logs (if provision agent logs)

### DoS Attack
- [ ] Network packet capture (traffic volume)
- [ ] Resource monitoring (CPU, memory, connections)
- [ ] Mosquitto logs (connection limits, errors)
- [ ] System logs (OOM killer, system stress)

### Unauthorized Access
- [ ] Network packet capture (failed connections)
- [ ] Mosquitto logs (ACL denials, auth failures)
- [ ] Connection monitoring (blocked attempts)

---

## 12. Quick Reference Commands

```bash
# Start all captures
./capture_security_test.sh test_name

# View live Mosquitto logs
sudo journalctl -u mosquitto -f

# Check active MQTT connections
netstat -an | grep 8883

# Monitor system resources
htop

# Stop all captures
./stop_captures.sh

# Transfer files to Windows
# (run from Windows PowerShell)
scp -r pi@192.168.43.214:/home/pi/security_captures/* ./
```

---

## 13. Important Notes

1. **Disk Space**: Captures can use significant disk space. Monitor with `df -h`
2. **Performance**: Running multiple captures may impact broker performance
3. **Permissions**: Some commands require `sudo`
4. **Timing**: Start captures BEFORE running attacks
5. **Synchronization**: Note the time when you start/stop captures for correlation

---

## 14. Recommended Capture Workflow

1. **Before Test**:
   ```bash
   # SSH into Pi
   ssh pi@192.168.43.214
   
   # Start comprehensive capture
   ./capture_security_test.sh my_security_test
   ```

2. **During Test**:
   - Run attack from Windows machine
   - Monitor live logs if needed: `sudo journalctl -u mosquitto -f`

3. **After Test**:
   ```bash
   # Stop captures (Ctrl+C or)
   ./stop_captures.sh
   
   # Verify files created
   ls -lh /home/pi/security_captures/my_security_test_*/
   ```

4. **Transfer to Windows**:
   ```powershell
   # From Windows
   scp -r pi@192.168.43.214:/home/pi/security_captures/my_security_test_* ./
   ```

5. **Analyze**:
   - Use Wireshark for `.pcap` files
   - Use `security_test_analyzer.py` for automated analysis
   - Review log files for broker-side events

---

This comprehensive capture approach gives you complete visibility into both network traffic and broker behavior during security testing.





