# Test MQTT Connection with Exact Credentials
# This tests the subscriber connection (same as Flask uses)

Write-Host "Testing MQTT Subscriber Connection" -ForegroundColor Cyan
Write-Host ""

# Use same credentials as start_flask.ps1
$env:MQTT_HOST = "192.168.43.214"
$env:MQTT_USER = "water_monitor"
$env:MQTT_PASSWORD = "e2eeWater2025"
$env:MQTT_PORT = "8883"
$env:MQTT_USE_TLS = "true"
$env:MQTT_TLS_INSECURE = "true"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $env:MQTT_HOST" -ForegroundColor Gray
Write-Host "  Port: $env:MQTT_PORT" -ForegroundColor Gray
Write-Host "  User: $env:MQTT_USER" -ForegroundColor Gray
Write-Host "  Password: $($env:MQTT_PASSWORD.Length) characters" -ForegroundColor Gray
Write-Host "  TLS: $env:MQTT_USE_TLS" -ForegroundColor Gray
Write-Host "  TLS Insecure: $env:MQTT_TLS_INSECURE" -ForegroundColor Gray
Write-Host ""

$testScript = @"
import os
import sys
import time
import ssl
try:
    import paho.mqtt.client as mqtt
    
    mqtt_host = os.environ.get('MQTT_HOST')
    mqtt_port = int(os.environ.get('MQTT_PORT', '8883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')
    
    print(f'Connecting to {mqtt_host}:{mqtt_port}...')
    print(f'Username: {mqtt_user}')
    print(f'Password length: {len(mqtt_password) if mqtt_password else 0}')
    
    # Create client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Set credentials
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
        print('Credentials set')
    
    # Configure TLS
    if mqtt_use_tls or mqtt_port == 8883:
        tls_config = {'tls_version': ssl.PROTOCOL_TLS}
        if mqtt_tls_insecure:
            tls_config['cert_reqs'] = ssl.CERT_NONE
        client.tls_set(**tls_config)
        if mqtt_tls_insecure:
            client.tls_insecure_set(True)
        print('TLS configured (insecure=True)')
    
    # Connection state
    connection_result = {'success': False, 'reason_code': None}
    
    # Connection callbacks
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print('✅ Connected successfully!')
            print(f'   Subscribing to keys/+/public...')
            result = client.subscribe('keys/+/public', qos=1)
            print(f'   Subscribe result: {result}')
            # Disconnect after successful test
            client.disconnect()
        else:
            print(f'❌ Connection failed: rc={reason_code}')
            if reason_code == 5:
                print('   Error: Not authorized')
                print('   Check: username, password, and ACL permissions')
            sys.exit(1)
    
    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        if reason_code == 0:
            print('✅ Disconnected successfully')
        else:
            print(f'⚠️  Unexpected disconnect: rc={reason_code}')
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    # Connect
    print('Attempting connection...')
    try:
        client.connect(mqtt_host, mqtt_port, 60)
        client.loop_start()
        
        # Wait for connection (max 10 seconds)
        timeout = 10
        start = time.time()
        while time.time() - start < timeout and connection_result['reason_code'] is None:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        if connection_result['success']:
            print('✅ Test completed successfully')
            sys.exit(0)
        else:
            print('❌ Test failed')
            sys.exit(1)
    except Exception as e:
        print(f'❌ Connection error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except ImportError as e:
    print(f'❌ paho-mqtt not installed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@

Write-Host "Running connection test..." -ForegroundColor Yellow
$testScript | python
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Connection test PASSED!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Connection test FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verify on Raspberry Pi:" -ForegroundColor Yellow
    Write-Host "  1. Password matches: sudo mosquitto_passwd /etc/mosquitto/passwd water_monitor" -ForegroundColor Gray
    Write-Host "  2. User exists: sudo grep water_monitor /etc/mosquitto/passwd" -ForegroundColor Gray
    Write-Host "  3. ACL configured: sudo cat /etc/mosquitto/acl.conf" -ForegroundColor Gray
    Write-Host "  4. Mosquitto running: sudo systemctl status mosquitto" -ForegroundColor Gray
}

