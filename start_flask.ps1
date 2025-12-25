# Flask Startup Script with MQTT Environment Variables
# Run this instead of "python app.py" directly

Write-Host "Setting MQTT environment variables..." -ForegroundColor Cyan

# Set MQTT configuration
$env:MQTT_HOST = "192.168.43.214"
$env:MQTT_USER = "water_monitor"  # <-- Updated to match ACL file
$env:MQTT_PASSWORD = "e2eeWater2025"  # <-- CHANGE THIS to your actual password!
$env:MQTT_PORT = "8883"  # TLS port
$env:MQTT_USE_TLS = "true"
$env:MQTT_TLS_INSECURE = "true"  # Set to "false" if using proper certificates

Write-Host "✅ MQTT_HOST: $env:MQTT_HOST" -ForegroundColor Green
Write-Host "✅ MQTT_USER: $env:MQTT_USER" -ForegroundColor Green
Write-Host "✅ MQTT_PORT: $env:MQTT_PORT" -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    .\venv\Scripts\Activate.ps1
}

Write-Host "Starting Flask server..." -ForegroundColor Cyan
Write-Host ""

# Start Flask with environment variables explicitly passed
# Use $env: to ensure variables are passed to the Python process
$env:PYTHONUNBUFFERED = "1"  # Ensure Python output is not buffered
python -u app.py
