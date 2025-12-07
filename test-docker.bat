@echo off
REM Quick Docker Test Script for Windows
REM Edit the environment variables below with your actual values

echo ========================================
echo Building Docker Image...
echo ========================================
docker build -t iot-water-monitor .

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Docker build failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build successful!
echo ========================================
echo.
echo Starting container...
echo.
echo NOTE: Edit this file to set your environment variables!
echo Press Ctrl+C to stop the container.
echo.

REM ========================================
REM EDIT THESE VALUES WITH YOUR ACTUAL CREDENTIALS
REM ========================================
docker run -p 10000:10000 ^
  -e DB_HOST=your-mysql-host.com ^
  -e DB_PORT=3306 ^
  -e DB_USER=your_db_user ^
  -e DB_PASSWORD=your_db_password ^
  -e DB_NAME=ilmuwanutara_e2eewater ^
  -e MQTT_HOST=your-mqtt-host ^
  -e MQTT_PORT=1883 ^
  -e MQTT_USER=your_mqtt_user ^
  -e MQTT_PASSWORD=your_mqtt_password ^
  -e SECRET_KEY=your-secret-key-min-32-characters-long ^
  -e PORT=10000 ^
  -e FLASK_ENV=production ^
  iot-water-monitor

pause


