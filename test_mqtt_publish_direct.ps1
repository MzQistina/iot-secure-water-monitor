# Direct MQTT publish test to verify authentication and ACL
Write-Host "Testing MQTT publish directly..." -ForegroundColor Cyan
Write-Host ""

# Set MQTT credentials
$env:MQTT_HOST = "192.168.43.214"
$env:MQTT_PORT = "8883"
$env:MQTT_USER = "water_monitor"
$env:MQTT_PASSWORD = "e2eeWater2025"
$env:MQTT_USE_TLS = "true"
$env:MQTT_TLS_INSECURE = "true"
$env:MQTT_CA_CERTS = "certs\ca-cert.pem"

Write-Host "MQTT Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $env:MQTT_HOST" -ForegroundColor Gray
Write-Host "  Port: $env:MQTT_PORT" -ForegroundColor Gray
Write-Host "  User: $env:MQTT_USER" -ForegroundColor Gray
Write-Host "  Password: $($env:MQTT_PASSWORD.Substring(0,3))...$($env:MQTT_PASSWORD.Substring($env:MQTT_PASSWORD.Length-3))" -ForegroundColor Gray
Write-Host "  TLS: $env:MQTT_USE_TLS" -ForegroundColor Gray
Write-Host "  TLS Insecure: $env:MQTT_TLS_INSECURE" -ForegroundColor Gray
Write-Host ""

# Test topic
$testTopic = "provision/test_device/update"
$testPayload = '{"device_id":"test_device","action":"update","user_id":"6"}'

Write-Host "Testing publish to: $testTopic" -ForegroundColor Yellow
Write-Host "Payload: $testPayload" -ForegroundColor Gray
Write-Host ""

# Python script to test publish
$pythonScript = @"
import sys
import os
import json
import ssl
import paho.mqtt.publish as publish

mqtt_host = os.environ.get('MQTT_HOST')
mqtt_port = int(os.environ.get('MQTT_PORT', '8883'))
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'true').lower() in ('true', '1', 'yes')
mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'true').lower() in ('true', '1', 'yes')
mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')

print(f"Connecting to {mqtt_host}:{mqtt_port}")
print(f"User: {mqtt_user}")
print(f"Password set: {bool(mqtt_password)}")
print(f"TLS: {mqtt_use_tls}")
print(f"TLS Insecure: {mqtt_tls_insecure}")
print(f"CA Certs: {mqtt_ca_certs}")

publish_kwargs = {
    'hostname': mqtt_host,
    'port': mqtt_port,
    'auth': {'username': mqtt_user, 'password': mqtt_password}
}

if mqtt_use_tls:
    tls_config = {}
    if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
        tls_config['ca_certs'] = mqtt_ca_certs
    tls_config['tls_version'] = ssl.PROTOCOL_TLS
    if mqtt_tls_insecure:
        tls_config['cert_reqs'] = ssl.CERT_NONE
    tls_config['insecure'] = mqtt_tls_insecure
    publish_kwargs['tls'] = tls_config

topic = "$testTopic"
payload = "$testPayload"

print(f"\nPublishing to topic: {topic}")
print(f"Payload: {payload}")
print(f"Auth username: {publish_kwargs['auth']['username']}")
print(f"Auth password set: {bool(publish_kwargs['auth']['password'])}")

try:
    publish.single(topic, payload, qos=1, **publish_kwargs)
    print("\n✅ SUCCESS: Message published successfully!")
    sys.exit(0)
except Exception as e:
    error_str = str(e)
    print(f"\n❌ ERROR: {error_str}")
    if "not authorized" in error_str.lower():
        print("\n💡 This means:")
        print("   1. Authentication succeeded (username/password correct)")
        print("   2. But ACL doesn't allow publishing to this topic")
        print("   3. Check ACL file on Raspberry Pi:")
        print("      sudo cat /etc/mosquitto/acl.conf")
        print("   4. Should have: topic write provision/+/update")
    elif "connection refused" in error_str.lower():
        print("\n💡 Connection refused - broker might not be running")
    elif "timeout" in error_str.lower():
        print("\n💡 Timeout - network issue or broker unreachable")
    else:
        import traceback
        print(f"\nFull traceback:")
        traceback.print_exc()
    sys.exit(1)
"@

$pythonScript | python
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ MQTT publish test PASSED!" -ForegroundColor Green
    Write-Host "   This means authentication and ACL are working correctly." -ForegroundColor Gray
} else {
    Write-Host "❌ MQTT publish test FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Check ACL file on Raspberry Pi:" -ForegroundColor Gray
    Write-Host "     ssh pi@192.168.43.214 'sudo cat /etc/mosquitto/acl.conf'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Verify user exists in password file:" -ForegroundColor Gray
    Write-Host "     ssh pi@192.168.43.214 'sudo grep water_monitor /etc/mosquitto/passwd'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Restart Mosquitto after ACL changes:" -ForegroundColor Gray
    Write-Host "     ssh pi@192.168.43.214 'sudo systemctl restart mosquitto'" -ForegroundColor Cyan
}
