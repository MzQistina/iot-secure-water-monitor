# PowerShell script to test MQTT provision messages
# Usage: .\test_provision_mqtt.ps1 [device_id] [action] [user_id]

param(
    [string]$DeviceId = "test_device",
    [string]$Action = "update",
    [string]$UserId = "1"
)

# MQTT Configuration
$MQTT_HOST = if ($env:MQTT_HOST) { $env:MQTT_HOST } else { "192.168.43.214" }
$MQTT_PORT = if ($env:MQTT_PORT) { [int]$env:MQTT_PORT } else { 8883 }
$MQTT_USER = if ($env:MQTT_USER) { $env:MQTT_USER } else { "water_monitor" }
$MQTT_PASSWORD = if ($env:MQTT_PASSWORD) { $env:MQTT_PASSWORD } else { "e2eeWater2025" }
$MQTT_USE_TLS = if ($env:MQTT_USE_TLS) { $env:MQTT_USE_TLS -eq "true" } else { $true }
$TOPIC_BASE = if ($env:MQTT_PROVISION_TOPIC_BASE) { $env:MQTT_PROVISION_TOPIC_BASE } else { "provision" }

$Topic = "$TOPIC_BASE/$DeviceId/$Action"
$Payload = @{
    device_id = $DeviceId
    action = $Action
    user_id = $UserId
} | ConvertTo-Json -Compress

$separator = "=" * 80
Write-Host $separator -ForegroundColor Cyan
Write-Host "MQTT Provision Test" -ForegroundColor Cyan
Write-Host $separator -ForegroundColor Cyan
Write-Host "Host: $MQTT_HOST`:$MQTT_PORT" -ForegroundColor Yellow
Write-Host "User: $MQTT_USER" -ForegroundColor Yellow
Write-Host "TLS: $MQTT_USE_TLS" -ForegroundColor Yellow
Write-Host "Topic: $Topic" -ForegroundColor Yellow
Write-Host "Payload: $Payload" -ForegroundColor Yellow
Write-Host $separator -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found. Please use the Python test script instead:" -ForegroundColor Red
    Write-Host "   python test_provision_mqtt.py $DeviceId $Action $UserId" -ForegroundColor Yellow
    exit 1
}

# Use Python script if available
if (Test-Path "test_provision_mqtt.py") {
    Write-Host "[PUBLISH] Running Python test script..." -ForegroundColor Green
    Write-Host ""
    python test_provision_mqtt.py $DeviceId $Action $UserId
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Python script failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
    exit $LASTEXITCODE
}

# Alternative: Try using mosquitto_pub if available
$mosquittoPub = Get-Command mosquitto_pub -ErrorAction SilentlyContinue
if ($mosquittoPub) {
    Write-Host "[PUBLISH] Using mosquitto_pub..." -ForegroundColor Green
    
    $mosquittoArgs = @(
        "-h", $MQTT_HOST
        "-p", $MQTT_PORT.ToString()
        "-u", $MQTT_USER
        "-P", $MQTT_PASSWORD
        "-t", $Topic
        "-m", $Payload
        "-q", "1"
    )
    
    if ($MQTT_USE_TLS) {
        $caCert = if ($env:MQTT_CA_CERTS) { $env:MQTT_CA_CERTS } else { "C:\path\to\ca-cert.pem" }
        if (Test-Path $caCert) {
            $mosquittoArgs += "--cafile", $caCert
        } else {
            Write-Host "[WARNING] CA certificate not found at $caCert" -ForegroundColor Yellow
            Write-Host "   Continuing without TLS certificate verification..." -ForegroundColor Yellow
        }
    }
    
    & mosquitto_pub @mosquittoArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Message published to $Topic" -ForegroundColor Green
        Write-Host ""
        Write-Host "[INFO] Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Check provision agent console output" -ForegroundColor White
        Write-Host "   2. Look for: 'Provision agent received message:'" -ForegroundColor White
        Write-Host "   3. Verify topic matches: $TOPIC_BASE/+/$Action" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "[ERROR] Failed to publish message" -ForegroundColor Red
        Write-Host "   Exit code: $LASTEXITCODE" -ForegroundColor Red
    }
    exit $LASTEXITCODE
}

# If neither Python script nor mosquitto_pub is available
Write-Host "[ERROR] No MQTT tools found. Please install one of:" -ForegroundColor Red
Write-Host "   1. Python with paho-mqtt: pip install paho-mqtt" -ForegroundColor Yellow
Write-Host "   2. Mosquitto client tools" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then use:" -ForegroundColor Cyan
Write-Host "   python test_provision_mqtt.py $DeviceId $Action $UserId" -ForegroundColor White
exit 1







