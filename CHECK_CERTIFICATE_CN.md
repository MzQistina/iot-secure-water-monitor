# Check MQTT Certificate Common Name (CN)

Quick guide to check and fix certificate CN mismatch.

---

## ✅ Step 1: Check Certificate CN on Raspbian

**On Raspbian, run:**

```bash
# Check the server certificate CN
sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject

# Also check the full certificate details
sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -text | grep -A 2 "Subject:"
```

**Expected output:**
- If CN is `192.168.56.102`: `subject=CN = 192.168.56.102`
- If CN is different: `subject=CN = <different-ip-or-name>`

---

## ✅ Step 2: If CN is Already 192.168.56.102

**If the certificate CN is already `192.168.56.102`, but you're still getting errors:**

### Check 1: Verify IP Address is Correct

**On Raspbian:**
```bash
# Check what IP eth1 actually has
ip addr show eth1 | grep "inet 192.168.56.102"
```

**On Windows:**
```powershell
# Verify you're connecting to the right IP
echo $env:MQTT_HOST
# Should show: 192.168.56.102
```

### Check 2: Verify Certificate File on Windows

**On Windows:**
```powershell
# Check if CA certificate exists
Test-Path "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"

# View certificate (should match the one on Raspbian)
Get-Content "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem"
```

### Check 3: Test Connection with mosquitto tools

**On Windows (if you have mosquitto installed):**
```powershell
# Test connection
mosquitto_sub -h 192.168.56.102 -p 8883 -t test/topic `
  --cafile "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem" `
  -W 2
```

**If this works but Python doesn't:** The issue might be with how Python's SSL library validates the certificate.

---

## ✅ Step 3: If CN is NOT 192.168.56.102

**If the certificate CN is different (e.g., `192.168.56.101` or `localhost`):**

### Option A: Regenerate Certificate with Correct CN

**On Raspbian:**
```bash
cd /etc/mosquitto/certs

# Generate new server certificate with CN = 192.168.56.102
sudo openssl req -new -x509 -days 365 -key server-key.pem -out server-cert.pem -subj "/CN=192.168.56.102"

# Set permissions
sudo chown mosquitto:mosquitto server-cert.pem
sudo chmod 644 server-cert.pem

# Verify CN
sudo openssl x509 -in server-cert.pem -noout -subject
# Should show: subject=CN = 192.168.56.102

# Restart Mosquitto
sudo systemctl restart mosquitto
```

**Then copy the CA certificate to Windows again:**
```powershell
# On Windows
scp raspberry@192.168.56.102:/etc/mosquitto/certs/ca-cert.pem certs\ca-cert.pem
```

### Option B: Use the IP that Matches the Certificate

**If certificate CN is `192.168.56.101`, use that IP instead:**

```powershell
# On Windows
$env:MQTT_HOST = "192.168.56.101"
python mqtt_listener.py
```

---

## ✅ Step 4: Test After Fix

**After fixing the certificate or IP, test:**

```powershell
# On Windows
python mqtt_listener.py
```

**Expected output:**
```
TLS enabled with CA cert: C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor\certs\ca-cert.pem
Connecting to MQTT broker: 192.168.56.102:8883 (TLS)
Connected with result code 0
Subscribed to topics: water/data, secure/sensor
Listening for MQTT messages...
```

---

## 🔍 Troubleshooting

### Problem: Still getting certificate verification error

**Try using insecure mode for testing:**
```powershell
$env:MQTT_TLS_INSECURE = "true"
python mqtt_listener.py
```

**If this works:** The certificate CN definitely doesn't match. Regenerate the certificate.

### Problem: Certificate CN is correct but still fails

**Check:**
1. Certificate file on Windows matches the one on Raspbian
2. IP address is actually `192.168.56.102` on Raspbian
3. Mosquitto is listening on port 8883: `sudo netstat -tlnp | grep 8883`

---

## 📝 Summary

1. **Check certificate CN:** `sudo openssl x509 -in /etc/mosquitto/certs/server-cert.pem -noout -subject`
2. **If CN = 192.168.56.102:** Verify IP and certificate file match
3. **If CN ≠ 192.168.56.102:** Regenerate certificate with correct CN
4. **Test connection:** `python mqtt_listener.py`


