# Test MQTT Provision Configuration
# This script helps diagnose why provision requests are failing

Write-Host "MQTT Provision Configuration Test" -ForegroundColor Cyan
Write-Host ""

# Check environment variables
Write-Host "1. Checking MQTT Environment Variables:" -ForegroundColor Yellow
$mqtt_host = $env:MQTT_HOST
$mqtt_port = $env:MQTT_PORT
$mqtt_user = $env:MQTT_USER
$mqtt_password = $env:MQTT_PASSWORD
$mqtt_use_tls = $env:MQTT_USE_TLS
$mqtt_ca_certs = $env:MQTT_CA_CERTS
$topic_base = $env:MQTT_PROVISION_TOPIC_BASE

if ($mqtt_host) {
    Write-Host "   ✅ MQTT_HOST: $mqtt_host" -ForegroundColor Green
} else {
    Write-Host "   ❌ MQTT_HOST: NOT SET" -ForegroundColor Red
}

if ($mqtt_port) {
    Write-Host "   ✅ MQTT_PORT: $mqtt_port" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  MQTT_PORT: Using default (1883)" -ForegroundColor Yellow
}

if ($mqtt_user) {
    Write-Host "   ✅ MQTT_USER: $mqtt_user" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  MQTT_USER: Not set (no authentication)" -ForegroundColor Yellow
}

if ($mqtt_use_tls -eq "true" -or $mqtt_use_tls -eq "1" -or $mqtt_use_tls -eq "yes") {
    Write-Host "   ✅ MQTT_USE_TLS: Enabled" -ForegroundColor Green
    if ($mqtt_ca_certs) {
        if (Test-Path $mqtt_ca_certs) {
            Write-Host "   ✅ MQTT_CA_CERTS: $mqtt_ca_certs (exists)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ MQTT_CA_CERTS: $mqtt_ca_certs (FILE NOT FOUND)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠️  MQTT_CA_CERTS: Not set" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  MQTT_USE_TLS: Disabled (plain connection)" -ForegroundColor Yellow
}

if ($topic_base) {
    Write-Host "   ✅ MQTT_PROVISION_TOPIC_BASE: $topic_base" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  MQTT_PROVISION_TOPIC_BASE: Using default ('provision')" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2. Expected MQTT Topics:" -ForegroundColor Yellow
Write-Host "   Request: $topic_base/{device_id}/request" -ForegroundColor Gray
Write-Host "   Update:  $topic_base/{device_id}/update" -ForegroundColor Gray
Write-Host "   Delete:  $topic_base/{device_id}/delete" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Testing Python MQTT Library:" -ForegroundColor Yellow
try {
    $pythonTest = python -c "import paho.mqtt.publish as publish; print('OK')" 2>&1
    if ($pythonTest -eq "OK") {
        Write-Host "   ✅ paho-mqtt library is installed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ paho-mqtt library error: $pythonTest" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Failed to test paho-mqtt: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Common Issues:" -ForegroundColor Cyan
Write-Host "   ❌ MQTT_HOST not set: Set MQTT_HOST environment variable" -ForegroundColor Red
Write-Host "   ❌ MQTT broker not running: Start Mosquitto or your MQTT broker" -ForegroundColor Red
Write-Host "   ❌ Network connectivity: Check if Flask can reach MQTT broker" -ForegroundColor Yellow
Write-Host "   ❌ TLS certificate issues: Verify MQTT_CA_CERTS path is correct" -ForegroundColor Yellow
Write-Host "   ❌ Authentication failed: Check MQTT_USER and MQTT_PASSWORD" -ForegroundColor Yellow
Write-Host ""

Write-Host "5. Check Flask Console Output:" -ForegroundColor Yellow
Write-Host "   When you click 'Update/Regenerate Key', look for:" -ForegroundColor Gray
Write-Host "   - [Provision Update] Sending MQTT message:" -ForegroundColor Gray
Write-Host "   - [Provision Update] MQTT publish kwargs: {...}" -ForegroundColor Gray
Write-Host "   - [Provision Update] ✅ MQTT message sent successfully" -ForegroundColor Green
Write-Host "   - [Provision Update] ❌ MQTT publish failed: ..." -ForegroundColor Red
Write-Host ""

Write-Host "6. Check Provision Agent (Raspberry Pi):" -ForegroundColor Yellow
Write-Host "   Make sure provision_agent.py is running on the Pi:" -ForegroundColor Gray
Write-Host "   python simulators/sensor/provision_agent.py" -ForegroundColor Gray
Write-Host "   You should see:" -ForegroundColor Gray
Write-Host "   - Provision agent subscribed to: provision/+/request" -ForegroundColor Gray
Write-Host "   - Provision agent subscribed to: provision/+/update" -ForegroundColor Gray
Write-Host "   - Provision agent subscribed to: provision/+/delete" -ForegroundColor Gray
Write-Host ""
