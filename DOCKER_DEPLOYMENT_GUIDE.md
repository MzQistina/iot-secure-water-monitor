# Docker Deployment on Same Server - Complete Guide

## ✅ Perfect Solution: Docker on Same Server as MySQL

**This solves your problem:**
- ✅ Docker runs Flask
- ✅ Connects to MySQL via `localhost`
- ✅ No remote MySQL access needed
- ✅ Your `connect.py` script works perfectly!

---

## 🎯 How It Works

```
Server: ilmuwanutara.my
├── MySQL (port 3306)
│   └── Database: ilmuwanutara_e2eewater
│
└── Docker Container
    └── Flask App
        └── Connects to localhost:3306 ✅
```

**Connection:**
- Flask (Docker) → `localhost:3306` → MySQL (same server) ✅
- No remote access needed! ✅

---

## 📋 What You Need

### Required:
1. **Docker installed on server** (`ilmuwanutara.my`)
2. **SSH access** to run Docker commands (or hosting help)
3. **Your Flask files** on the server

### Already Ready:
- ✅ `Dockerfile` - Flask container definition
- ✅ `docker-compose.production.yml` - Configured for localhost!
- ✅ `connect.py` - Already uses localhost
- ✅ All your Flask app files

---

## 🚀 Step-by-Step Deployment

### Step 1: Get Docker on Server

**Ask your supervisor/hosting:**

> "I want to deploy my Flask app using Docker on the server. Can you:
> 1. Install Docker on the server (ilmuwanutara.my)?
> 2. Give me SSH access to run Docker commands?
> 
> I'll upload the Docker files, then run docker-compose to start the app.
> The app will connect to MySQL via localhost (same server), so no remote access is needed."

---

### Step 2: Upload Docker Files

**Upload these files to the server:**

**Via FTP:**
- `Dockerfile`
- `docker-compose.production.yml`
- `requirements.txt`
- All Flask app files (app.py, connect.py, db.py, etc.)
- `templates/` folder
- `static/` folder
- `db_encryption.key`

**Or via SSH/SCP:**
```bash
scp -r iot-secure-water-monitor admin@ilmuwanutara.my:/home/admin/
```

---

### Step 3: SSH into Server

```bash
ssh admin@ilmuwanutara.my
```

**If SSH works, proceed to Step 4.**
**If SSH doesn't work, ask hosting to run the commands for you.**

---

### Step 4: Install Docker (If Not Installed)

**On the server, run:**

```bash
# Check if Docker is installed
docker --version

# If not installed, install it (Ubuntu/Debian):
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

---

### Step 5: Navigate to App Directory

```bash
cd /home/admin/iot-secure-water-monitor
# Or wherever you uploaded files
```

---

### Step 6: Run Docker Compose

```bash
# Build and start the Flask app
docker-compose -f docker-compose.production.yml up -d --build
```

**What this does:**
- Builds Flask Docker image
- Starts Flask container
- Connects to MySQL via `localhost` ✅
- No remote access needed! ✅

---

### Step 7: Verify It's Running

```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f web
```

**You should see:**
- Container running
- Flask app started
- Database connection successful

---

### Step 8: Access Your App

**Visit:**
```
https://e2eewater.ilmuwanutara.my:5000
```

**Or if port 5000 is mapped:**
```
https://e2eewater.ilmuwanutara.my
```

---

## ✅ Why This Works

**docker-compose.production.yml is configured:**
```yaml
DB_HOST: localhost  # ✅ Connects to MySQL on same server
network_mode: "host"  # ✅ Uses host network (can access localhost)
```

**Your `connect.py` script:**
```python
DB_HOST = os.getenv('DB_HOST', 'localhost')  # ✅ Uses localhost
```

**Result:**
- Docker container can access `localhost:3306`
- MySQL is on `localhost:3306`
- Connection works! ✅
- No remote access needed! ✅

---

## 🔧 Docker Commands Reference

### Start App:
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Stop App:
```bash
docker-compose -f docker-compose.production.yml down
```

### View Logs:
```bash
docker-compose -f docker-compose.production.yml logs -f web
```

### Restart App:
```bash
docker-compose -f docker-compose.production.yml restart
```

### Rebuild After Code Changes:
```bash
docker-compose -f docker-compose.production.yml up -d --build
```

---

## 📋 Files to Upload for Docker

### Must Upload:
- ✅ `Dockerfile`
- ✅ `docker-compose.production.yml`
- ✅ `requirements.txt`
- ✅ `app.py`
- ✅ `connect.py`
- ✅ `db.py`
- ✅ `encryption_utils.py`
- ✅ `validation.py`
- ✅ `db_encryption.py`
- ✅ `db_encryption.key`
- ✅ `templates/` folder
- ✅ `static/` folder
- ✅ `keys/`, `user_keys/`, `sensor_keys/` (empty folders)

### Don't Need:
- ❌ `passenger_wsgi.py` (Docker uses Dockerfile)
- ❌ `.htaccess` (Docker handles web server)

---

## 🎯 Summary

**Yes, Docker can work without remote MySQL access!**

**Requirements:**
- ✅ Docker on same server as MySQL
- ✅ SSH access (or hosting help)
- ✅ Upload Docker files
- ✅ Run `docker-compose -f docker-compose.production.yml up -d`

**Result:**
- ✅ Flask runs in Docker
- ✅ Connects to MySQL via localhost
- ✅ No remote access needed
- ✅ Your `connect.py` works perfectly!

**This is the perfect solution for your requirements!** 🎉

---

## 🆘 Next Steps

1. **Ask supervisor/hosting:**
   - Install Docker on server
   - Give SSH access (or run commands for you)

2. **Upload Docker files** (via FTP or SCP)

3. **Run docker-compose** on server

4. **Done!** ✅

I've created `DOCKER_SAME_SERVER.md` with detailed steps. This is the best solution for your situation!
