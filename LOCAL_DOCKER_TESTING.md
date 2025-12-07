# Local Docker Testing Guide

## Step 1: Install Docker Desktop

### Download and Install

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"
   - File: `Docker Desktop Installer.exe`

2. **Install Docker Desktop:**
   - Run the installer
   - Follow the installation wizard
   - **Important:** Enable "Use WSL 2 instead of Hyper-V" if prompted
   - Restart your computer if required

3. **Start Docker Desktop:**
   - Open Docker Desktop from Start menu
   - Wait for it to start (whale icon in system tray)
   - You'll see "Docker Desktop is running" when ready

4. **Verify Installation:**
   ```bash
   docker --version
   # Should show: Docker version 24.x.x or similar
   
   docker ps
   # Should show empty list (no containers running yet)
   ```

## Step 2: Prepare Your Project

### Check Required Files

Make sure you have:
- ✅ `Dockerfile` (already created)
- ✅ `.dockerignore` (already created)
- ✅ `requirements.txt` (already created)
- ✅ All Python files (`app.py`, `db.py`, etc.)

### Prepare Environment Variables

Create a `.env` file for local testing (optional, or use command line):

```bash
# .env file (for reference, don't commit this!)
DB_HOST=your-mysql-host.com
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=ilmuwanutara_e2eewater
MQTT_HOST=your-mqtt-host
MQTT_PORT=1883
MQTT_USER=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password
SECRET_KEY=your-secret-key-here-min-32-chars
PORT=10000
FLASK_ENV=production
```

**Note:** Don't commit `.env` to Git (it's in `.gitignore`)

## Step 3: Build Docker Image

### Navigate to Project Directory

```bash
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
```

### Build the Docker Image

```bash
docker build -t iot-water-monitor .
```

**What this does:**
- `-t iot-water-monitor` = Tag/name the image
- `.` = Build from current directory

**Expected output:**
```
Sending build context to Docker daemon...
Step 1/10 : FROM python:3.11-slim
...
Successfully built abc123def456
Successfully tagged iot-water-monitor:latest
```

**If build fails:**
- Check Dockerfile syntax
- Check requirements.txt exists
- Check all files are present

## Step 4: Run Docker Container

### Basic Run (Without Environment Variables)

```bash
docker run -p 10000:10000 iot-water-monitor
```

**What this does:**
- `-p 10000:10000` = Map port 10000 (host) to 10000 (container)
- `iot-water-monitor` = Image name

**Expected output:**
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 7
```

### Run with Environment Variables

**Option A: Command Line (Recommended for Testing)**

```bash
docker run -p 10000:10000 \
  -e DB_HOST=your-mysql-host.com \
  -e DB_PORT=3306 \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  -e DB_NAME=ilmuwanutara_e2eewater \
  -e MQTT_HOST=your-mqtt-host \
  -e MQTT_PORT=1883 \
  -e SECRET_KEY=your-secret-key-here \
  -e PORT=10000 \
  iot-water-monitor
```

**Option B: Using .env File**

```bash
# Create .env file first (see Step 2)
docker run -p 10000:10000 --env-file .env iot-water-monitor
```

**Option C: Interactive Mode (For Debugging)**

```bash
docker run -it -p 10000:10000 \
  -e DB_HOST=your-mysql-host.com \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  -e DB_NAME=ilmuwanutara_e2eewater \
  iot-water-monitor
```

## Step 5: Test Your Application

### Test in Browser

1. **Open browser:**
   ```
   http://localhost:10000
   ```

2. **Should see:**
   - Your Flask app home page
   - No errors

### Test API Endpoints

```bash
# Test home page
curl http://localhost:10000

# Test health (if you have a health endpoint)
curl http://localhost:10000/health
```

### Test with VirtualBox Client

**Important:** VirtualBox can't easily connect to `localhost:10000` on Windows host.

**Solutions:**

**Option 1: Use Host IP Address**
```bash
# Find your Windows IP address
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)

# In VirtualBox Raspbian, use:
python3 raspberry_pi_client.py pH01 http://192.168.1.100:10000
```

**Option 2: Port Forwarding (Advanced)**
- Configure VirtualBox network settings
- Forward port 10000 from host to guest

**Option 3: Test Locally First, Deploy to Render for VirtualBox**
- Test Docker locally for basic functionality
- Deploy to Render for VirtualBox testing (easier)

## Step 6: View Logs

### View Container Logs

**In another terminal:**
```bash
# List running containers
docker ps

# View logs (replace CONTAINER_ID)
docker logs CONTAINER_ID

# Follow logs (live updates)
docker logs -f CONTAINER_ID
```

**Or if you know container name:**
```bash
docker logs iot-water-monitor
```

## Step 7: Stop Container

### Stop Running Container

```bash
# List running containers
docker ps

# Stop container
docker stop CONTAINER_ID

# Or stop by name (if you named it)
docker stop iot-water-monitor
```

### Remove Container

```bash
# Remove stopped container
docker rm CONTAINER_ID

# Or remove by name
docker rm iot-water-monitor
```

## Common Commands Cheat Sheet

### Build and Run

```bash
# Build image
docker build -t iot-water-monitor .

# Run container (foreground)
docker run -p 10000:10000 iot-water-monitor

# Run container (background/detached)
docker run -d -p 10000:10000 --name my-app iot-water-monitor

# Run with environment variables
docker run -p 10000:10000 \
  -e DB_HOST=host \
  -e DB_USER=user \
  -e DB_PASSWORD=pass \
  iot-water-monitor
```

### Management

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View logs
docker logs CONTAINER_ID

# Stop container
docker stop CONTAINER_ID

# Start stopped container
docker start CONTAINER_ID

# Remove container
docker rm CONTAINER_ID

# Remove image
docker rmi iot-water-monitor
```

### Debugging

```bash
# Run container interactively (bash shell)
docker run -it --entrypoint /bin/bash iot-water-monitor

# Execute command in running container
docker exec -it CONTAINER_ID /bin/bash

# View container details
docker inspect CONTAINER_ID
```

## Troubleshooting

### "Docker command not found"

**Fix:**
- Install Docker Desktop
- Restart terminal/computer
- Verify: `docker --version`

### "Cannot connect to Docker daemon"

**Fix:**
- Start Docker Desktop
- Wait for it to fully start
- Check system tray for Docker icon

### "Port already in use"

**Fix:**
```bash
# Find process using port 10000
netstat -ano | findstr :10000

# Stop the process or use different port
docker run -p 10001:10000 iot-water-monitor
```

### "Database connection failed"

**Fix:**
- Check environment variables are set correctly
- Verify MySQL host is accessible from Docker
- Test MySQL connection from host first

### "Module not found"

**Fix:**
- Check `requirements.txt` includes the package
- Rebuild image: `docker build -t iot-water-monitor .`
- Check `.dockerignore` isn't excluding needed files

### "Permission denied"

**Fix:**
- On Windows, Docker Desktop handles permissions
- If issues persist, run Docker Desktop as administrator

## Testing Workflow

### Recommended Testing Flow

1. **Build Image:**
   ```bash
   docker build -t iot-water-monitor .
   ```

2. **Run Container:**
   ```bash
   docker run -p 10000:10000 \
     -e DB_HOST=... \
     -e DB_USER=... \
     -e DB_PASSWORD=... \
     iot-water-monitor
   ```

3. **Test in Browser:**
   - Open `http://localhost:10000`
   - Test registration/login
   - Test data submission

4. **Check Logs:**
   ```bash
   docker logs CONTAINER_ID
   ```

5. **Fix Issues:**
   - Update code
   - Rebuild image
   - Test again

6. **When Working:**
   - Push to GitHub
   - Deploy to Render

## Quick Start Script

### Create `test-docker.bat` (Windows)

```batch
@echo off
echo Building Docker image...
docker build -t iot-water-monitor .

echo.
echo Starting container...
docker run -p 10000:10000 ^
  -e DB_HOST=your-mysql-host.com ^
  -e DB_PORT=3306 ^
  -e DB_USER=your_user ^
  -e DB_PASSWORD=your_password ^
  -e DB_NAME=ilmuwanutara_e2eewater ^
  -e MQTT_HOST=your-mqtt-host ^
  -e MQTT_PORT=1883 ^
  -e SECRET_KEY=your-secret-key ^
  -e PORT=10000 ^
  iot-water-monitor
```

**Usage:**
```bash
# Edit the .bat file with your credentials
test-docker.bat
```

## Next Steps

### After Local Testing Works:

1. ✅ **Push to GitHub:**
   ```bash
   git add Dockerfile .dockerignore requirements.txt
   git commit -m "Add Docker support"
   git push
   ```

2. ✅ **Deploy to Render:**
   - Connect GitHub repo
   - Render detects Dockerfile
   - Set environment variables
   - Deploy!

3. ✅ **Test with VirtualBox:**
   - Use Render URL (e.g., `https://your-app.onrender.com`)
   - VirtualBox can connect easily

## Summary

**Local Docker Testing Steps:**

1. ✅ Install Docker Desktop
2. ✅ Build image: `docker build -t iot-water-monitor .`
3. ✅ Run container: `docker run -p 10000:10000 -e DB_HOST=... iot-water-monitor`
4. ✅ Test: `http://localhost:10000`
5. ✅ Check logs: `docker logs CONTAINER_ID`
6. ✅ Fix and rebuild as needed
7. ✅ Deploy to Render when working

---

**Ready to test! Install Docker Desktop first, then we'll build and run your container.** 🐳


