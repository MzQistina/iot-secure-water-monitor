# Raspbian vs Windows - What Runs Where

Clear guide showing which components run on Raspbian (VM) and which run on Windows (Host).

---

## 🖥️ **RASPBERRY PI (VirtualBox VM) - IP: 192.168.56.102**

### What Runs Here:
- ✅ **MQTT Broker (Mosquitto)** - Listens on port 8883 (TLS)
- ✅ **MQTT Certificates** - Stored in `/etc/mosquitto/certs/`
- ✅ **Sensor Simulator** (optional) - Can publish sensor data
- ✅ **Provision Agent** (optional) - Publishes keys via MQTT

### Commands to Run on Raspbian:

#### 1. Check Certificate CN:
```bash
sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject
```

#### 2. Regenerate Certificate (if needed):
```bash
cd /etc/mosquitto/certs
sudo openssl req -new -x509 -days 365 -key server-key.pem -out server-cert.pem -subj "/CN=192.168.56.102"
sudo chown mosquitto:mosquitto server-cert.pem
sudo chmod 644 server-cert.pem
sudo systemctl restart mosquitto
```

#### 3. Test MQTT (Subscribe):
```bash
mosquitto_sub -h 192.168.56.102 -p 8883 -t test/topic \
  --cafile /etc/mosquitto/certs/ca-cert.pem
```

#### 4. Test MQTT (Publish):
```bash
mosquitto_pub -h 192.168.56.102 -p 8883 -t test/topic -m "Hello from Raspbian" \
  --cafile /etc/mosquitto/certs/ca-cert.pem
```

#### 5. Check Mosquitto Status:
```bash
sudo systemctl status mosquitto
sudo netstat -tlnp | grep 8883
```

#### 6. Check IP Address:
```bash
ip addr show eth1 | grep "inet 192.168.56.102"
```

---

## 💻 **WINDOWS (Host Machine)**

### What Runs Here:
- ✅ **Flask Application** (`app.py`) - Web server
- ✅ **MQTT Listener** (`mqtt_listener.py`) - Listens for MQTT messages
- ✅ **CA Certificate** - Copied from Raspbian to `certs\ca-cert.pem`

### Commands to Run on Windows:

#### 1. Set Environment Variables (PowerShell):
```powershell
$env:MQTT_HOST = "192.168.56.102"
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_CA_CERTS = "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
$env:MQTT_TLS_INSECURE = "true"  # For testing only
```

#### 2. Copy CA Certificate from Raspbian:
```powershell
# Create certs directory
mkdir -Force certs

# Copy certificate (if SSH is enabled)
scp raspberry@192.168.56.102:/etc/mosquitto/certs/ca-cert.pem certs\ca-cert.pem
```

#### 3. Run MQTT Listener:
```powershell
python mqtt_listener.py
```

#### 4. Run Flask Application:
```powershell
python app.py
```

#### 5. Test Network Connectivity:
```powershell
Test-NetConnection -ComputerName 192.168.56.102 -Port 8883
```

#### 6. Test MQTT (if mosquitto tools installed):
```powershell
mosquitto_sub -h 192.168.56.102 -p 8883 -t test/topic `
  --cafile "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
```

---

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDOWS (Host)                            │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Flask App       │         │  mqtt_listener   │         │
│  │  (app.py)        │         │  (mqtt_listener  │         │
│  │                  │         │   .py)           │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                    │
│           │  MQTT (TLS)                │  MQTT (TLS)        │
│           │  Port 8883                 │  Port 8883         │
└───────────┼────────────────────────────┼────────────────────┘
            │                            │
            │   192.168.56.102:8883      │
            │                            │
┌───────────┼────────────────────────────┼────────────────────┐
│           │                            │                    │
│  ┌────────▼─────────┐                 │                    │
│  │  Mosquitto       │                 │                    │
│  │  MQTT Broker     │                 │                    │
│  │  Port 8883 (TLS) │                 │                    │
│  └──────────────────┘                 │                    │
│                                        │                    │
│  ┌──────────────────┐                 │                    │
│  │  Certificates    │                 │                    │
│  │  /etc/mosquitto/ │                 │                    │
│  │  certs/          │                 │                    │
│  └──────────────────┘                 │                    │
│                                        │                    │
│         RASPBERRY PI (VM)              │                    │
│         IP: 192.168.56.102             │                    │
└────────────────────────────────────────┘                    │
```

---

## 🔄 **Typical Workflow**

### Setup Phase:
1. **Raspbian:** Install and configure Mosquitto broker
2. **Raspbian:** Generate certificates with CN = 192.168.56.102
3. **Windows:** Copy CA certificate from Raspbian
4. **Windows:** Set environment variables

### Testing Phase:
1. **Windows:** Run `python mqtt_listener.py` (listens for messages)
2. **Raspbian:** Run `mosquitto_pub` (publishes test message)
3. **Windows:** Verify message received in listener

### Production Phase:
1. **Raspbian:** Run sensor simulator or provision agent (publishes data)
2. **Windows:** Flask app and mqtt_listener receive messages
3. **Windows:** Flask app displays data in web interface

---

## 📝 **Quick Reference**

| Component | Location | Purpose |
|-----------|----------|---------|
| **Mosquitto Broker** | Raspbian | MQTT message broker |
| **MQTT Certificates** | Raspbian | TLS certificates for secure MQTT |
| **CA Certificate** | Windows | Copied from Raspbian for client verification |
| **Flask App** | Windows | Web server and MQTT subscriber |
| **mqtt_listener.py** | Windows | Standalone MQTT message listener |
| **Sensor Simulator** | Raspbian (optional) | Publishes test sensor data |
| **Provision Agent** | Raspbian (optional) | Publishes encryption keys |

---

## ✅ **Summary**

- **Raspbian = Server** (MQTT broker, certificates, can publish messages)
- **Windows = Client** (Flask app, mqtt_listener, connects to broker)

**Connection Flow:**
- Windows → Connects to → Raspbian (192.168.56.102:8883)
- Raspbian → Publishes messages → Windows receives them


