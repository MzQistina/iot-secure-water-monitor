# Raspbian Simulation Quick Start

**Quick reference for simulating sensor data in Raspbian VirtualBox.**

---

## 🚀 5-Minute Setup

### 1. Copy Files to Raspbian

```powershell
# From Windows PowerShell
$IP = "10.0.2.15"  # Your Raspbian IP
scp multi_sensor_client.py encryption_utils.py pi@$IP:~/water-monitor/
scp -r keys/ sensor_keys/ pi@$IP:~/water-monitor/
```

### 2. Install Dependencies

```bash
# On Raspbian
cd ~/water-monitor
pip3 install requests pycryptodome
```

### 3. Run Simulation

```bash
# On Raspbian
cd ~/water-monitor
python3 multi_sensor_client.py --all http://10.0.2.2
```

---

## 📋 Common Commands

```bash
# Simulate all sensors
python3 multi_sensor_client.py --all http://10.0.2.2

# Simulate specific sensors
python3 multi_sensor_client.py --ids pH01,tds01 http://10.0.2.2

# Custom interval (30 seconds)
python3 multi_sensor_client.py --all --interval 30 http://10.0.2.2

# Filter by location
python3 multi_sensor_client.py --all --location "Tank A" http://10.0.2.2
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Use `10.0.2.2` (NAT) or Windows IP (Bridged) |
| No sensors found | Check sensors are active on server |
| Key not found | Verify `sensor_keys/<user_id>/<device_id>/sensor_private.pem` |
| Module not found | Run `pip3 install requests pycryptodome` |

---

## 📍 Server URLs

- **NAT Mode**: `http://10.0.2.2` (default VirtualBox)
- **Bridged Mode**: `http://192.168.1.100` (your Windows IP)
- **Custom Port**: `http://10.0.2.2:8080`

---

## ✅ Pre-Flight Checklist

- [ ] Server running on Windows
- [ ] Files copied to Raspbian
- [ ] Dependencies installed
- [ ] Keys in correct location
- [ ] Network connectivity tested

---

**Full guide**: See [RASPBIAN_SIMULATION_GUIDE.md](RASPBIAN_SIMULATION_GUIDE.md)

