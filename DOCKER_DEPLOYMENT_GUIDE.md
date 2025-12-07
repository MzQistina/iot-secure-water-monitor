# Docker Deployment Guide for IoT Water Monitor

## Why Use Docker?

**Docker Benefits:**
- ✅ **Reproducible environment** - Same everywhere
- ✅ **Isolation** - App runs in container
- ✅ **Easy deployment** - Build once, run anywhere
- ✅ **Version control** - Dockerfile tracks environment
- ✅ **Scalability** - Easy to scale containers

**For Your App:**
- ✅ **Works with VirtualBox** - HTTP communication
- ✅ **Works with real Pi** - HTTP communication
- ✅ **Portable** - Run on any Docker platform
- ⚠️ **More complex** - Requires Docker knowledge

## Docker vs PythonAnywhere Comparison

| Feature | Docker | PythonAnywhere |
|--------|--------|----------------|
| **Setup Difficulty** | ⭐⭐⭐ Medium | ⭐⭐ Easy |
| **MySQL Included** | ❌ No (need external) | ✅ Yes |
| **File Upload** | ❌ Git only | ✅ Web interface |
| **VirtualBox Compatible** | ✅ Yes | ✅ Yes |
| **Free Tier** | ✅ Yes (Render/Railway) | ✅ Yes |
| **Custom Domain** | ✅ Free (Render) | ⚠️ Paid ($5+) |
| **Best For** | Docker users | Simple setup |

### Do You Need Docker?

**Docker** = A **technology/tool** for containerization  
**PythonAnywhere** = A **hosting platform** for Python apps

**They're not mutually exclusive!** You can:
- ✅ Use PythonAnywhere **without Docker** (recommended for simple setup)
- ✅ Use Render/Railway **with Docker** (if you need Docker)

**Your App Requirements:**
- ✅ Flask (Python package)
- ✅ MySQL database
- ✅ HTTP server
- ❌ **No Docker-specific features needed**

**Recommendation:** Use PythonAnywhere for simpler setup, or Render with Docker if you prefer Git-based deployment.

### Local vs Cloud Docker

**For Render deployment: NO, you don't need Docker installed locally!** ✅

Render builds and runs Docker containers **in the cloud** - you just need to push your code with a `Dockerfile`.

**You DON'T need:**
- ❌ Docker Desktop installed
- ❌ Docker extension in VS Code
- ❌ Docker CLI commands
- ❌ Local Docker testing

**You DO need:**
- ✅ `Dockerfile` in your project (already created!)
- ✅ Git repository (GitHub/GitLab)
- ✅ Render account (free)

### Can You Use Docker Only?

**Docker is a containerization technology** - it packages your app, but you still need somewhere to **run** the Docker container.

**Think of it like this:**
- **Docker** = Packaging system (like a shipping container)
- **Platform** = Where container runs (like a ship/port)

You can't use "Docker only" - you need a **host** to run Docker containers.

**Your Options:**
1. **Local Docker** (Your Windows PC) - For testing only
2. **Cloud Docker** (Render/Railway) - For production deployment
3. **PythonAnywhere** - No Docker needed, simpler alternative

## Step 1: Create Dockerfile

Create a `Dockerfile` in your project root:

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p keys user_keys sensor_keys templates static

# Expose port (Render uses $PORT, others use 10000)
EXPOSE 10000

# Set default environment variables
ENV PORT=10000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:$PORT/')" || exit 1

# Run application with Gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
```

## Step 2: Create .dockerignore

Create `.dockerignore` to exclude unnecessary files:

```
venv/
__pycache__/
*.pyc
*.pyo
*.log
.git/
.vscode/
.idea/
*.md
test_*.py
.DS_Store
Thumbs.db
.env
.env.local
```

## Step 3: Update requirements.txt

Ensure `requirements.txt` includes Gunicorn:

```txt
Flask>=3.0.0
Werkzeug>=3.0.0
mysql-connector-python>=8.0.0
paho-mqtt>=1.6.0
pycryptodome>=3.19.0
gunicorn>=21.2.0
```

## Step 4: Choose Docker Platform

### Option 1: Render (Recommended for Docker) ⭐

**Why Render:**
- ✅ **Dockerfile support** - Automatic detection
- ✅ **Free tier** - With Docker support
- ✅ **Free custom domain** - Professional URL
- ✅ **Easy deployment** - Git-based
- ✅ **Automatic SSL** - HTTPS included

**Setup:**
1. Push code to GitHub
2. Create Web Service on Render
3. Render detects Dockerfile automatically
4. Set environment variables
5. Deploy!

**VirtualBox Connection:**
```python
# In VirtualBox Raspbian
python3 raspberry_pi_client.py pH01 https://your-app.onrender.com
```

### Option 2: Railway

**Why Railway:**
- ✅ **Docker-native** - Built for containers
- ✅ **Free $5 credit** - Per month
- ✅ **Automatic detection** - Detects Dockerfile
- ✅ **Easy setup** - Git-based

**Setup:**
1. Push to GitHub
2. Connect Railway to GitHub
3. Railway detects Dockerfile
4. Set environment variables
5. Deploy!

### Option 3: Fly.io

**Why Fly.io:**
- ✅ **Docker support**
- ✅ **Free tier** - 3 shared VMs
- ✅ **Global deployment** - Edge computing
- ✅ **Good for IoT** - Low latency

**Setup:**
1. Install Fly CLI
2. `fly launch` (detects Dockerfile)
3. Set environment variables
4. Deploy!

### Option 4: DigitalOcean App Platform

**Why DigitalOcean:**
- ✅ **Docker support**
- ✅ **Reliable** - Enterprise-grade
- ⚠️ **Paid only** - $5/month minimum

## Step 5: Configure Database

### ✅ Option 1: Use External MySQL Database (Recommended)

**Use your supervisor's MySQL database or any external MySQL server.**

#### Step 5.1: Get Database Credentials

Get the following information from your supervisor:
- **DB_HOST**: MySQL server hostname or IP address
- **DB_PORT**: MySQL port (usually `3306`)
- **DB_USER**: MySQL username
- **DB_PASSWORD**: MySQL password
- **DB_NAME**: Database name (e.g., `ilmuwanutara_e2eewater`)

#### Step 5.2: Configure Database Access

**Important:** The MySQL server must allow connections from Render/Docker platform's IP addresses.

**Ask your supervisor to:**
1. **Whitelist platform IPs** - Allow connections from Render/cloud servers
   - Render uses dynamic IPs, so you may need to allow all IPs or use a specific range
   - Common solution: Allow connections from `%` (all IPs) for your database user
   
2. **Verify firewall rules** - Ensure MySQL port (3306) is accessible from internet
   - If MySQL is behind a firewall, it needs to allow inbound connections on port 3306

**SQL command for supervisor to run (if they have access):**
```sql
-- Allow your database user to connect from any IP (for Render/Docker)
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* TO 'your_db_user'@'%' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
```

#### Step 5.3: Set Environment Variables

In your Docker platform (Render/Railway/etc.) → **Environment** tab, add:

```
DB_HOST=your-supervisor-mysql-host.com
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=ilmuwanutara_e2eewater
```

**Example:**
```
DB_HOST=mysql.supervisor-university.edu.my
DB_PORT=3306
DB_USER=student_fyp
DB_PASSWORD=secure_password_123
DB_NAME=ilmuwanutara_e2eewater
```

### Option 2: Render PostgreSQL (Alternative)

If you prefer to use Render's managed database:

- Create PostgreSQL database on Render
- Update `db.py` to use PostgreSQL
- Install `psycopg2-binary` instead of `mysql-connector-python`

**Note:** This requires code changes. Using external MySQL (Option 1) is simpler if you already have MySQL credentials.

### Option 3: Managed MySQL Services

- AWS RDS, Google Cloud SQL, etc.
- More reliable but paid

## Step 6: Deploy on Render (Example)

### 6.1 Push to GitHub

```bash
git add Dockerfile .dockerignore requirements.txt
git commit -m "Add Docker support"
git push
```

### 6.2 Create Render Service

1. **Go to [render.com](https://render.com)**
2. **New + → Web Service**
3. **Connect GitHub repository**
4. **Configure:**
   - **Name:** `iot-water-monitor`
   - **Region:** Singapore (or closest)
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Runtime:** Docker (auto-detected)
   - **Build Command:** (auto - Docker builds)
   - **Start Command:** (auto - from Dockerfile CMD)

### 6.3 Set Environment Variables

In Render dashboard → Environment:

```
# Database Configuration (Supervisor's MySQL)
DB_HOST=your-supervisor-mysql-host.com
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=ilmuwanutara_e2eewater

# MQTT Configuration
MQTT_HOST=your-mqtt-host
MQTT_PORT=1883
MQTT_USER=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=10000
```

**Note:** Replace database credentials with your supervisor's MySQL database information. Ensure the database allows connections from Render's servers.

### 6.4 Deploy

1. Click **"Create Web Service"**
2. Render builds Docker image
3. Deploys container
4. Your app is live!

## Step 7: Update VirtualBox Client

**In VirtualBox Raspbian:**

```bash
# Update server URL
python3 raspberry_pi_client.py pH01 https://your-app.onrender.com
```

**Or set environment variable:**
```bash
export SERVER_URL=https://your-app.onrender.com
python3 raspberry_pi_client.py pH01 $SERVER_URL
```

## Docker-Specific Considerations

### 1. Keys Folder (Persistent Storage)

**Problem:** Docker containers are ephemeral - files lost on restart

**Solution Options:**

**Option A: Environment Variables (Recommended)**
```python
# Convert keys to base64
cat keys/private.pem | base64
cat keys/public.pem | base64

# Add to Render environment variables
PRIVATE_KEY_B64=<base64-encoded>
PUBLIC_KEY_B64=<base64-encoded>

# In app.py, read from env
if os.environ.get('PRIVATE_KEY_B64'):
    private_key = base64.b64decode(os.environ['PRIVATE_KEY_B64']).decode()
    # Write to file or use directly
```

**Option B: Render Disk (Paid)**
- Render offers persistent disk storage
- Mount to `/app/keys`

**Option C: External Storage**
- AWS S3, Google Cloud Storage
- Download keys on container start

### 2. Database Connection

**External MySQL:**
- Ensure MySQL allows connections from Render IPs
- Use connection string in environment variables
- Test connection in Docker container

### 3. MQTT Connection

**External MQTT Broker:**
- Use public MQTT broker (HiveMQ, Mosquitto Cloud)
- Or self-hosted MQTT server
- Set credentials in environment variables

## Testing Docker Locally

### Build and Run Locally:

```bash
# Build Docker image
docker build -t iot-water-monitor .

# Run container
docker run -p 10000:10000 \
  -e DB_HOST=your-db-host \
  -e DB_USER=your-user \
  -e DB_PASSWORD=your-pass \
  -e DB_NAME=ilmuwanutara_e2eewater \
  -e MQTT_HOST=your-mqtt-host \
  -e SECRET_KEY=your-secret \
  iot-water-monitor

# Test
curl http://localhost:10000
```

**VirtualBox Connection:**
```python
# In VirtualBox Raspbian
python3 raspberry_pi_client.py pH01 http://10.0.2.2:10000
```

## Docker Compose (Optional)

For local development with MySQL:

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "10000:10000"
    environment:
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWORD=password
      - DB_NAME=ilmuwanutara_e2eewater
      - MQTT_HOST=mqtt
      - MQTT_PORT=1883
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
      - mqtt

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ilmuwanutara_e2eewater
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  mqtt:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    volumes:
      - ./mqtt/config:/mosquitto/config

volumes:
  mysql_data:
```

**Run:**
```bash
docker-compose up
```

## Platform Comparison for Docker

| Platform | Docker Support | Free Tier | MySQL | Custom Domain | Best For |
|----------|---------------|-----------|-------|---------------|----------|
| **Render** | ✅ Yes | ✅ Yes | ❌ No | ✅ Free | General use |
| **Railway** | ✅ Yes | ✅ $5 credit | ❌ No | ✅ Free | Docker-first |
| **Fly.io** | ✅ Yes | ✅ Yes | ❌ No | ✅ Free | IoT/Edge |
| **DigitalOcean** | ✅ Yes | ❌ No | ❌ No | ✅ Yes | Production |
| **AWS ECS** | ✅ Yes | ❌ No | ❌ No | ✅ Yes | Enterprise |

## Recommendation

### Use Render with Docker:

**Why:**
1. ✅ **Docker support** - Full Dockerfile support
2. ✅ **Free tier** - Good for testing
3. ✅ **Free custom domain** - Professional URL
4. ✅ **Easy deployment** - Git-based
5. ✅ **Works with VirtualBox** - HTTP communication

**Setup Time:** ~20 minutes

## Migration Path

### From PythonAnywhere to Docker:

1. **Create Dockerfile** (see above)
2. **Push to GitHub**
3. **Deploy on Render**
4. **Set environment variables**
5. **Configure external MySQL**
6. **Update VirtualBox client URL**
7. **Done!**

## Troubleshooting

### "Docker build failed"

**Check:**
- Dockerfile syntax
- Requirements.txt exists
- All files copied correctly

### "Container won't start"

**Check:**
- Environment variables set
- Database connection works
- Port configuration correct

### "Keys not found"

**Fix:**
- Use environment variables for keys
- Or mount persistent volume
- Or download from external storage

### "Database connection failed"

**If using supervisor's MySQL database:**

1. **Verify credentials:**
   - Check `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` in environment variables
   - Test credentials locally first

2. **Check database access:**
   - Ask supervisor to verify database allows connections from external IPs
   - Check if MySQL user has `@'%'` (all IPs) or specific IP access
   - Verify firewall allows port 3306 from internet

3. **Test connection manually:**
   ```bash
   # From your local machine (if MySQL allows external connections)
   mysql -h your-supervisor-mysql-host.com -u your_db_user -p
   ```

4. **Check Docker logs:**
   - Look for specific MySQL error messages
   - Common errors:
     - `Access denied` → Wrong credentials or user doesn't have access from platform IPs
     - `Can't connect` → Firewall blocking or wrong host/port
     - `Unknown database` → Wrong database name

## Quick Start Checklist

- [ ] Create `Dockerfile`
- [ ] Create `.dockerignore`
- [ ] Update `requirements.txt` (add gunicorn)
- [ ] Push to GitHub
- [ ] Create Render/Railway account
- [ ] Deploy Docker service
- [ ] Set environment variables
- [ ] Configure external MySQL
- [ ] Test deployment
- [ ] Update VirtualBox client URL

## Important: Provision Agent Setup (Raspbian)

**⚠️ The provision agent does NOT run in Docker!**

The **provision agent** (`provision_agent.py`) is a **separate component** that runs on your **Raspberry Pi (Raspbian)**, not in the Docker container.

### Architecture Overview

```
┌─────────────────┐         MQTT          ┌──────────────────┐
│  Docker/Render  │ ◄──────────────────► │  Raspberry Pi    │
│  (Flask App)    │                       │  (Provision      │
│                 │                       │   Agent)         │
└─────────────────┘                       └──────────────────┘
        │                                          │
        │ HTTP/HTTPS                               │
        ▼                                          ▼
┌─────────────────┐                       ┌──────────────────┐
│  Web Browser    │                       │  Sensor Clients  │
│  (Users)        │                       │  (multi_sensor_  │
│                 │                       │   client.py)     │
└─────────────────┘                       └──────────────────┘
```

### What Runs Where?

**In Docker Container (Cloud Server):**
- ✅ Flask web application (`app.py`)
- ✅ Web interface for users
- ✅ MQTT client (publishes provision requests)
- ✅ Database connections
- ❌ **NOT** the provision agent

**On Raspberry Pi (Raspbian):**
- ✅ Provision agent (`provision_agent.py`) - **MUST run here!**
- ✅ Sensor simulation clients (`multi_sensor_client.py`)
- ✅ Sensor keys storage (`sensor_keys/`)

### Setting Up Provision Agent on Raspbian

After deploying Docker to Render/cloud, you **still need** to set up the provision agent on your Raspberry Pi:

1. **Copy provision agent to Raspbian:**
   ```bash
   # From Windows PowerShell
   $RASPBIAN_IP = "10.0.2.15"  # Your Raspbian IP
   $RASPBIAN_USER = "pi"
   scp simulators/sensor/provision_agent.py $RASPBIAN_USER@$RASPBIAN_IP:~/water-monitor/
   ```

2. **Install dependencies on Raspbian:**
   ```bash
   # On Raspbian
   pip3 install paho-mqtt pycryptodome
   ```

3. **Set MQTT environment variables on Raspbian:**
   ```bash
   # On Raspbian
   export MQTT_HOST="your-mqtt-broker-host"  # Same as Docker uses
   export MQTT_PORT="1883"  # Or 8883 for TLS
   export MQTT_USER="your_mqtt_username"
   export MQTT_PASSWORD="your_mqtt_password"
   ```

4. **Run provision agent on Raspbian:**
   ```bash
   # On Raspbian
   cd ~/water-monitor
   python3 simulators/sensor/provision_agent.py
   ```

**For complete setup instructions, see:**
- **[PROVISION_AGENT_GUIDE.md](PROVISION_AGENT_GUIDE.md)** - Detailed provision agent setup
- **[RASPBIAN_COMMANDS.txt](RASPBIAN_COMMANDS.txt)** - All Raspbian commands including provision agent

### Why Separate?

- **Provision agent** needs to generate keys **on the device** (Raspberry Pi)
- **Server** (Docker) only needs to **receive** public keys via MQTT
- **Security**: Private keys stay on the Raspberry Pi, never in the cloud

## Final Recommendation

**For Your FYP Project:**

**If you want Docker:**
- ✅ **Use Render** - Best Docker platform for free tier
- ✅ **Free custom domain** - Professional URL
- ⚠️ **Need external MySQL** - Use your existing or Render PostgreSQL
- ⚠️ **Need provision agent on Raspbian** - Separate setup required

**If you want simplicity:**
- ✅ **Use PythonAnywhere** - Easier, MySQL included
- ✅ **No Docker needed** - Simpler setup
- ⚠️ **Still need provision agent on Raspbian** - Separate setup required

**Both work with VirtualBox!** Choose based on your preference. 🐳

---

**Docker is great if you want containerization and portability. Render is the best platform for Docker deployment with free tier!** 🚀

**Remember:** The provision agent runs on Raspbian, not in Docker!


