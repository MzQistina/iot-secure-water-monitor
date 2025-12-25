# Secure MQTT with TLS/SSL Setup Guide

This guide explains how to configure secure MQTT connections using TLS/SSL encryption for the IoT Secure Water Monitor project.

## Overview

The project now supports **secure MQTT** with TLS/SSL encryption. This provides:
- ✅ **Encrypted transport** - All MQTT messages are encrypted in transit
- ✅ **Certificate validation** - Prevents man-in-the-middle attacks
- ✅ **Authentication** - Username/password + optional client certificates
- ✅ **Backward compatible** - Can still use plain MQTT (not recommended for production)

## Security Levels

### Level 1: Plain MQTT (Default - Not Secure)
- Port: `1883`
- No encryption
- Username/password authentication only
- **Not recommended for production**

### Level 2: TLS with Certificate Validation (Recommended)
- Port: `8883` (standard MQTT over TLS port)
- Full encryption
- Certificate validation enabled
- Username/password authentication
- **Recommended for production**

### Level 3: TLS with Client Certificates (Most Secure)
- Port: `8883`
- Full encryption
- Certificate validation + client certificate authentication
- **Maximum security for production**

## Configuration

### Environment Variables

Add these environment variables to enable TLS:

#### Basic TLS Configuration
```bash
# Enable TLS
MQTT_USE_TLS=true

# MQTT broker settings
MQTT_HOST=your-mqtt-broker.com
MQTT_PORT=8883  # Standard TLS port (use 1883 for plain MQTT)

# Authentication (optional but recommended)
MQTT_USER=your_username
MQTT_PASSWORD=your_password
```

#### TLS Certificate Configuration

**Option 1: Use CA Certificate File (Recommended)**
```bash
MQTT_CA_CERTS=/path/to/ca-certificate.pem
```

**Option 2: Use System CA Certificates**
```bash
# Leave MQTT_CA_CERTS unset - will use system default CA certificates
```

**Option 3: Self-Signed Certificates (Development Only)**
```bash
MQTT_CA_CERTS=/path/to/ca-certificate.pem
MQTT_TLS_INSECURE=true  # Disables certificate validation
```

#### Client Certificate Authentication (Optional - Most Secure)
```bash
MQTT_CERTFILE=/path/to/client-certificate.pem
MQTT_KEYFILE=/path/to/client-private-key.pem
```

## Complete Configuration Examples

### Example 1: TLS with CA Certificate (Production)

```bash
MQTT_HOST=mqtt.example.com
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_CA_CERTS=/etc/ssl/certs/mqtt-ca.pem
MQTT_USER=water_monitor
MQTT_PASSWORD=secure_password_123
```

### Example 2: TLS with System CA Certificates

```bash
MQTT_HOST=mqtt.example.com
MQTT_PORT=8883
MQTT_USE_TLS=true
# MQTT_CA_CERTS not set - uses system CA certificates
MQTT_USER=water_monitor
MQTT_PASSWORD=secure_password_123
```

### Example 3: TLS with Client Certificates (Maximum Security)

```bash
MQTT_HOST=mqtt.example.com
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_CA_CERTS=/etc/ssl/certs/mqtt-ca.pem
MQTT_CERTFILE=/etc/ssl/certs/client-cert.pem
MQTT_KEYFILE=/etc/ssl/private/client-key.pem
MQTT_USER=water_monitor
MQTT_PASSWORD=secure_password_123
```

### Example 4: Self-Signed Certificate (Development/Testing)

```bash
MQTT_HOST=192.168.1.100
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_CA_CERTS=/path/to/self-signed-ca.pem
MQTT_TLS_INSECURE=true  # Only for development!
MQTT_USER=test_user
MQTT_PASSWORD=test_password
```

### Example 5: Plain MQTT (Legacy - Not Secure)

```bash
MQTT_HOST=192.168.1.100
MQTT_PORT=1883
# MQTT_USE_TLS not set or false
MQTT_USER=test_user
MQTT_PASSWORD=test_password
```

## MQTT Broker Setup

### Using Mosquitto (Open Source)

#### 1. Install Mosquitto

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
```

**macOS:**
```bash
brew install mosquitto
```

#### 2. Generate Certificates

```bash
# Create directory for certificates
mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs

# Generate CA private key
openssl genrsa -out ca-key.pem 2048

# Generate CA certificate
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem

# Generate server private key
openssl genrsa -out server-key.pem 2048

# Generate server certificate signing request
openssl req -new -key server-key.pem -out server.csr

# Sign server certificate with CA
openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -days 365
```

#### 3. Configure Mosquitto (`/etc/mosquitto/mosquitto.conf`)

```conf
# Basic settings
listener 1883
listener 8883

# TLS configuration
cafile /etc/mosquitto/certs/ca-cert.pem
certfile /etc/mosquitto/certs/server-cert.pem
keyfile /etc/mosquitto/certs/server-key.pem

# Require client certificates (optional - for maximum security)
# require_certificate true

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
```

#### 4. Create Password File

```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd water_monitor
# Enter password when prompted

# Restart Mosquitto
sudo systemctl restart mosquitto
```

### Using Cloud MQTT Brokers

#### HiveMQ Cloud
- Port: `8883` (TLS)
- Use provided CA certificate or system CA certificates
- Username/password provided by HiveMQ

#### AWS IoT Core
- Port: `8883` (TLS)
- Download AWS IoT CA certificate
- Use AWS IoT device certificates for client authentication

#### Azure IoT Hub
- Port: `8883` (TLS)
- Use Azure-provided CA certificates
- SAS tokens for authentication

#### Google Cloud IoT Core
- Port: `8883` (TLS)
- Use Google CA certificates
- JWT tokens for authentication

## Testing TLS Connection

### Test with Mosquitto Client

```bash
# Test TLS connection
mosquitto_sub -h mqtt.example.com -p 8883 \
  --cafile /path/to/ca-cert.pem \
  -u username -P password \
  -t test/topic

# Test with client certificate
mosquitto_sub -h mqtt.example.com -p 8883 \
  --cafile /path/to/ca-cert.pem \
  --cert /path/to/client-cert.pem \
  --key /path/to/client-key.pem \
  -t test/topic
```

### Test with Python Script

```python
import paho.mqtt.client as mqtt
import ssl

client = mqtt.Client()
client.username_pw_set("username", "password")
client.tls_set(
    ca_certs="/path/to/ca-cert.pem",
    certfile="/path/to/client-cert.pem",  # Optional
    keyfile="/path/to/client-key.pem",    # Optional
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS
)
client.connect("mqtt.example.com", 8883, 60)
client.loop_forever()
```

## Application Configuration

### Flask Application (app.py)

The application automatically detects TLS configuration from environment variables. No code changes needed!

### Provision Agent

The provision agent (`simulators/sensor/provision_agent.py`) also supports TLS automatically via environment variables.

### Simulators

All MQTT simulators support TLS via environment variables.

## Troubleshooting

### Connection Refused

**Problem:** Cannot connect to MQTT broker

**Solutions:**
- Check `MQTT_HOST` and `MQTT_PORT` are correct
- Verify broker is running and accessible
- Check firewall rules allow port 8883 (TLS) or 1883 (plain)

### Certificate Verification Failed

**Problem:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions:**
- Verify `MQTT_CA_CERTS` path is correct
- Ensure CA certificate matches broker's certificate
- For self-signed certificates, set `MQTT_TLS_INSECURE=true` (development only)
- Check certificate expiration date

### Authentication Failed

**Problem:** `Connection Refused: Bad User Name or Password`

**Solutions:**
- Verify `MQTT_USER` and `MQTT_PASSWORD` are correct
- Check broker password file is configured correctly
- Ensure user has proper permissions

### Client Certificate Error

**Problem:** Client certificate authentication fails

**Solutions:**
- Verify `MQTT_CERTFILE` and `MQTT_KEYFILE` paths are correct
- Ensure certificate is signed by the CA
- Check certificate hasn't expired
- Verify broker is configured to accept client certificates

## Security Best Practices

1. **Always use TLS in production** - Never use plain MQTT (port 1883) for production systems

2. **Use strong passwords** - Generate secure passwords for MQTT authentication

3. **Protect private keys** - Store client private keys securely with proper file permissions (600)

4. **Rotate certificates** - Regularly update certificates before expiration

5. **Use certificate validation** - Never disable certificate validation (`MQTT_TLS_INSECURE=false`) in production

6. **Network security** - Use firewall rules to restrict access to MQTT broker

7. **Monitor connections** - Log and monitor MQTT connections for suspicious activity

## Migration from Plain MQTT to TLS

### Step 1: Update Environment Variables

Change from:
```bash
MQTT_PORT=1883
```

To:
```bash
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_CA_CERTS=/path/to/ca-cert.pem
```

### Step 2: Test Connection

Test the TLS connection before deploying:
```bash
mosquitto_sub -h your-broker.com -p 8883 \
  --cafile /path/to/ca-cert.pem \
  -u username -P password \
  -t test/topic
```

### Step 3: Deploy

Update environment variables in your deployment platform (Render, LiteSpeed, etc.) and restart the application.

## Summary

✅ **TLS/SSL support is now fully implemented** in:
- Flask application (`app.py`)
- Provision agent (`provision_agent.py`)
- MQTT simulators (`mqtt_publish_key.py`)

✅ **Configuration via environment variables** - No code changes needed

✅ **Backward compatible** - Still works with plain MQTT if TLS is disabled

✅ **Production ready** - Supports all TLS security levels

---

**Next Steps:**
1. Set up your MQTT broker with TLS
2. Configure environment variables
3. Test the connection
4. Deploy to production

For server configuration instructions, see:
- `APACHE_SETUP.md`

