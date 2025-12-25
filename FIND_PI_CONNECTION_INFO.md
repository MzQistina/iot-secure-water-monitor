# How to Find Your Raspberry Pi Connection Info

## Quick Commands to Run on Raspberry Pi

### Find Hostname
```bash
hostname
# Example output: raspberrypi, mypi, watermonitor-pi, etc.
```

### Find IP Address
```bash
hostname -I
# Shows all IP addresses, first one is usually the main one
# Example: 192.168.1.100 192.168.56.102
```

### Find Username
```bash
whoami
# Example output: pi, admin, yourname, etc.
```

### Find Full Connection String
```bash
echo "$(whoami)@$(hostname)"
# Example output: pi@raspberrypi
```

---

## Common Scenarios

### Scenario 1: Default Raspberry Pi OS
- **Username**: `pi`
- **Hostname**: `raspberrypi` (default)
- **Connection**: `pi@raspberrypi.local` or `pi@192.168.1.100`

### Scenario 2: Custom Hostname
If you changed the hostname during setup:
- **Username**: `pi` (usually)
- **Hostname**: Your custom name (e.g., `watermonitor-pi`)
- **Connection**: `pi@watermonitor-pi.local` or `pi@192.168.1.100`

### Scenario 3: VirtualBox/VM
- **Username**: `pi`
- **Hostname**: `raspberrypi` or custom
- **IP**: Check VirtualBox network settings (e.g., `192.168.56.102`)
- **Connection**: `pi@192.168.56.102` (use IP directly)

### Scenario 4: Different Username
If you created a different user:
- **Username**: Your username (e.g., `admin`, `yourname`)
- **Hostname**: Your hostname
- **Connection**: `yourname@yourhostname.local`

---

## Examples

### Using Hostname (if .local works)
```powershell
# From Windows PowerShell
ssh pi@raspberrypi.local
scp file.py pi@raspberrypi.local:~/water-monitor/
```

### Using IP Address (more reliable)
```powershell
# From Windows PowerShell
ssh pi@192.168.1.100
scp file.py pi@192.168.1.100:~/water-monitor/
```

### Using Custom Hostname
```powershell
# If your Pi hostname is "watermonitor-pi"
ssh pi@watermonitor-pi.local
scp file.py pi@watermonitor-pi.local:~/water-monitor/
```

---

## Test Connection

### Test SSH Connection
```powershell
# From Windows PowerShell
ssh pi@YOUR_HOSTNAME_OR_IP
# Or
ssh YOUR_USERNAME@YOUR_HOSTNAME_OR_IP
```

### Test with Ping
```powershell
# Test if hostname resolves
ping raspberrypi.local

# Test if IP is reachable
ping 192.168.1.100
```

---

## Troubleshooting

### ".local" doesn't work
- Use IP address instead: `pi@192.168.1.100`
- Or add to Windows hosts file (advanced)

### "Connection refused" or "Host unreachable"
- Check Pi is powered on
- Check Pi is on same network
- Check firewall settings
- Try using IP instead of hostname

### "Permission denied"
- Check username is correct
- Check password is correct
- Check SSH is enabled on Pi: `sudo systemctl status ssh`

---

## Quick Reference

| What | Command | Example Output |
|------|---------|----------------|
| **Hostname** | `hostname` | `raspberrypi` |
| **IP Address** | `hostname -I` | `192.168.1.100` |
| **Username** | `whoami` | `pi` |
| **Full String** | `whoami@hostname` | `pi@raspberrypi` |

---

## For Your Project

Based on your setup, you likely need:

**If using VirtualBox (from pi_ip.txt):**
```powershell
# Use IP directly
$PI_IP = "192.168.56.102"
ssh pi@$PI_IP
scp file.py pi@$PI_IP:~/water-monitor/
```

**If using Physical Pi:**
```powershell
# Try hostname first
ssh pi@raspberrypi.local

# Or use IP if hostname doesn't work
ssh pi@192.168.1.100  # Replace with your Pi's actual IP
```





