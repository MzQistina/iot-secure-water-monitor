# Test MQTT Publish (for Provision)
# This tests if Flask can publish MQTT messages

Write-Host "Testing MQTT Publish Configuration" -ForegroundColor Cyan
Write-Host ""

# Check if MQTT_HOST is set
$mqtt_host = $env:MQTT_HOST
if (-not $mqtt_host) {
    Write-Host "❌ MQTT_HOST is NOT set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Set it with:" -ForegroundColor Yellow
    Write-Host "  `$env:MQTT_HOST = '192.168.43.214'" -ForegroundColor Gray
    Write-Host "  `$env:MQTT_PORT = '8883'  # or 1883" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or create a .env file with:" -ForegroundColor Yellow
    Write-Host "  MQTT_HOST=192.168.43.214" -ForegroundColor Gray
    Write-Host "  MQTT_PORT=8883" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✅ MQTT_HOST: $mqtt_host" -ForegroundColor Green
$mqttPort = if ($env:MQTT_PORT) { $env:MQTT_PORT } else { '1883' }
Write-Host "✅ MQTT_PORT: $mqttPort" -ForegroundColor Green
Write-Host ""

# Test Python MQTT publish
Write-Host "Testing Python MQTT publish..." -ForegroundColor Yellow
$testScript = @"
import os
import sys
import json
try:
    import paho.mqtt.publish as publish
    
    mqtt_host = os.environ.get('MQTT_HOST')
    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    
    kwargs = {'hostname': mqtt_host, 'port': mqtt_port}
    if mqtt_user and mqtt_password:
        kwargs['auth'] = {'username': mqtt_user, 'password': mqtt_password}
    
    # TLS configuration
    if mqtt_use_tls or mqtt_port == 8883:
        import ssl
        mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
        mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')
        
        tls_config = {}
        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
            tls_config['ca_certs'] = mqtt_ca_certs
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        if mqtt_tls_insecure:
            tls_config['cert_reqs'] = ssl.CERT_NONE
        tls_config['insecure'] = mqtt_tls_insecure
        
        kwargs['tls'] = tls_config
        print(f'Using TLS (insecure={mqtt_tls_insecure})')
    
    # Test topic
    topic = 'provision/test_device/request'
    payload = json.dumps({'device_id': 'test_device', 'action': 'request', 'user_id': '6'})
    
    print(f'Publishing to {mqtt_host}:{mqtt_port}...')
    print(f'Topic: {topic}')
    print(f'Payload: {payload}')
    
    publish.single(topic, payload, qos=1, **kwargs)
    print('✅ MQTT publish successful!')
    sys.exit(0)
except ImportError as e:
    print(f'❌ paho-mqtt not installed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ MQTT publish failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@

$testScript | python
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ MQTT publish test PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If provision still fails, check:" -ForegroundColor Yellow
    Write-Host "  1. Flask console for detailed error messages" -ForegroundColor Gray
    Write-Host "  2. MQTT broker logs for connection attempts" -ForegroundColor Gray
    Write-Host "  3. Provision agent is running on Raspberry Pi" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ MQTT publish test FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - MQTT broker not running" -ForegroundColor Gray
    Write-Host "  - Wrong MQTT_HOST or MQTT_PORT" -ForegroundColor Gray
    Write-Host "  - Firewall blocking connection" -ForegroundColor Gray
    Write-Host "  - Wrong MQTT_USER/MQTT_PASSWORD" -ForegroundColor Gray
    Write-Host "  - TLS configuration mismatch" -ForegroundColor Gray
}
