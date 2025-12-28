# Raspberry Pi Security Testing Scripts

These scripts should be copied to your Raspberry Pi for security testing.

## Setup

1. **Copy scripts to Raspberry Pi:**
   ```bash
   # From Windows, copy scripts to Pi
   scp pi_scripts/*.sh pi@192.168.43.214:/home/pi/
   ```

2. **Make scripts executable:**
   ```bash
   # SSH into Pi
   ssh pi@192.168.43.214
   
   # Make executable
   chmod +x /home/pi/*.sh
   ```

3. **Create security_captures directory:**
   ```bash
   mkdir -p /home/pi/security_captures
   ```

## Scripts

### capture_security_test.sh
Comprehensive capture script that records:
- Network packets (tcpdump)
- Mosquitto broker logs
- System resources (CPU, memory, disk)
- Network connections

**Usage:**
```bash
./capture_security_test.sh test_name
# Press Ctrl+C to stop
```

### stop_captures.sh
Stops all running capture processes.

**Usage:**
```bash
./stop_captures.sh
```

### monitor_resources.sh
Continuous resource monitoring (can be run standalone).

**Usage:**
```bash
./monitor_resources.sh [log_file]
```

## Windows Scripts

### transfer_captures.ps1
PowerShell script to transfer capture files from Pi to Windows.

**Usage:**
```powershell
# Transfer all captures
.\transfer_captures.ps1

# Transfer specific test
.\transfer_captures.ps1 -TestName "replay_attack_test"
```

## Quick Workflow

1. **On Raspberry Pi:**
   ```bash
   ./capture_security_test.sh my_test
   ```

2. **On Windows:**
   - Run your attack/test
   - Wait for completion

3. **On Raspberry Pi:**
   - Press Ctrl+C to stop capture

4. **On Windows:**
   ```powershell
   .\transfer_captures.ps1 -TestName "my_test"
   ```

5. **Analyze:**
   ```bash
   python security_test_analyzer.py security_captures/my_test_*/network.pcap
   ```










