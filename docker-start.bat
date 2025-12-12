@echo off
REM Quick start script for Docker Compose (Windows)

echo 🚀 Starting Flask + MySQL with Docker Compose...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

echo 📦 Building and starting containers...
docker-compose up -d --build

if errorlevel 1 (
    echo ❌ Failed to start containers. Check the logs:
    echo    docker-compose logs
    exit /b 1
)

echo.
echo ✅ Containers started successfully!
echo.
echo 📊 Container status:
docker-compose ps
echo.
echo 🌐 Your Flask app is available at: http://localhost:5000
echo 🗄️  MySQL is available at: localhost:3306
echo.
echo 📝 Useful commands:
echo   View logs:        docker-compose logs -f
echo   Stop containers:  docker-compose down
echo   View status:      docker-compose ps
echo.

