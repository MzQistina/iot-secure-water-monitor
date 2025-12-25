# MQTT Environment Variables Setup Script
# Run this before starting Flask app to configure MQTT connection

# MQTT Broker Configuration
# Replace with your PHYSICAL Raspberry Pi's IP address
# Find your Pi's IP: On Pi, run: hostname -I
$env:MQTT_HOST = "192.168.1.100"  # TODO: Replace with your PHYSICAL Pi's IP
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"

# CA Certificate Path
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:MQTT_CA_CERTS = Join-Path $scriptPath "certs\ca-cert.pem"

# MQTT Authentication
# Replace with the username and password you set in Mosquitto
$env:MQTT_USER = "water_monitor"  # TODO: Replace with your MQTT username
$env:MQTT_PASSWORD = "your_password"  # TODO: Replace with your MQTT password

# TLS Configuration
$env:MQTT_TLS_INSECURE = "false"  # Set to "true" only for testing if CN doesn't match

# Topic Configuration
$env:MQTT_PROVISION_TOPIC_BASE = "provision"
$env:MQTT_KEYS_TOPIC_BASE = "keys"

# Display configuration
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MQTT Environment Variables Set" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MQTT Host: $env:MQTT_HOST" -ForegroundColor Yellow
Write-Host "MQTT Port: $env:MQTT_PORT" -ForegroundColor Yellow
Write-Host "TLS Enabled: $env:MQTT_USE_TLS" -ForegroundColor Yellow
Write-Host "CA Certificate: $env:MQTT_CA_CERTS" -ForegroundColor Yellow
Write-Host "MQTT User: $env:MQTT_USER" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if CA certificate exists
if (Test-Path $env:MQTT_CA_CERTS) {
    Write-Host "✅ CA certificate found" -ForegroundColor Green
} else {
    Write-Host "⚠️  CA certificate not found at: $env:MQTT_CA_CERTS" -ForegroundColor Yellow
    Write-Host "   Make sure to copy ca-cert.pem from Raspberry Pi" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "You can now start Flask app with: python app.py" -ForegroundColor Green


