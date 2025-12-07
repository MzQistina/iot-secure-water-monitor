# Deploying to Render.com with Docker - Complete Guide

## 🎯 Your Specific Setup

**Configuration:**
- ✅ **Platform:** Render.com with Docker
- ✅ **Database:** Supervisor's MySQL database (external)
- ✅ **Domain:** Custom domain

**This guide is tailored for your exact setup!**

---

Render is a modern cloud platform that makes deploying Flask applications **much easier** than traditional shared hosting. It handles WSGI configuration, SSL certificates, and scaling automatically. With Docker support, you get a consistent, reproducible deployment environment.

## 📋 Quick Reference for Your Setup

**Deployment Flow:**
1. ✅ Push code with `Dockerfile` to GitHub
2. ✅ Create Render Web Service (select **Docker** runtime)
3. ✅ Configure supervisor's MySQL database access
4. ✅ Set environment variables (database, MQTT, Flask)
5. ✅ Add custom domain in Render
6. ✅ Update DNS records
7. ✅ Wait for SSL certificate
8. ✅ Set up provision agent on Raspbian (separate)

**Key Points:**
- Render automatically detects `Dockerfile` and uses it
- No need to set build/start commands (Dockerfile handles it)
- Supervisor must whitelist Render IPs for MySQL access
- Custom domain gets free SSL automatically

## Why Use Render?

✅ **Easier than LiteSpeed** - No manual WSGI configuration needed  
✅ **Free tier available** - Great for testing and small projects  
✅ **Automatic SSL** - HTTPS certificates included  
✅ **Git-based deployment** - Deploy with a simple git push  
✅ **Environment variables** - Easy configuration via dashboard  
✅ **Automatic scaling** - Handles traffic spikes  
✅ **Built-in logging** - View logs in dashboard  

## Prerequisites

1. **GitHub account** (or GitLab/Bitbucket)
2. **Render account** - Sign up at [render.com](https://render.com) (free)
3. **Your code** - Push your project to GitHub

## Step 1: Prepare Your Project for Docker Deployment

### 1.1 Verify Dockerfile Exists

Your project should already have a `Dockerfile` in the root directory. If not, create one (see `DOCKER_DEPLOYMENT_GUIDE.md` for details).

**Verify Dockerfile exists:**
```bash
ls Dockerfile
```

### 1.2 Verify `requirements.txt`

Ensure `requirements.txt` includes all dependencies:

```txt
Flask>=3.0.0
mysql-connector-python>=8.0.0
paho-mqtt>=1.6.0
pycryptodome>=3.19.0
Werkzeug>=3.0.0
gunicorn>=21.2.0
```

**Note:** Render will automatically detect your Dockerfile and use it for deployment.

### 1.3 Create `render.yaml` (Optional but Recommended)

Create a `render.yaml` file in your project root:

```yaml
services:
  - type: web
    name: iot-water-monitor
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DB_HOST
        sync: false
      - key: DB_PORT
        sync: false
      - key: DB_USER
        sync: false
      - key: DB_PASSWORD
        sync: false
      - key: DB_NAME
        sync: false
      - key: MQTT_HOST
        sync: false
      - key: MQTT_PORT
        value: 8883
      - key: MQTT_USE_TLS
        value: true
      - key: MQTT_USER
        sync: false
      - key: MQTT_PASSWORD
        sync: false
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
```

### 1.4 Verify Dockerfile CMD

Your `Dockerfile` should already have the correct CMD for Gunicorn:

```dockerfile
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
```

**Note:** Render will use the Dockerfile CMD, so no changes needed to `app.py` for Docker deployment.

### 1.5 Create `.renderignore` (Optional)

Create `.renderignore` to exclude unnecessary files:

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
simulators/
```

## Step 2: Push to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   ```

2. **Create GitHub repository:**
   - Go to GitHub.com
   - Click "New repository"
   - Name it (e.g., `iot-secure-water-monitor`)
   - Don't initialize with README
   - Click "Create repository"

3. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/yourusername/iot-secure-water-monitor.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Deploy on Render

### 3.1 Create New Web Service

1. **Log into Render Dashboard**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Sign up/login (free account)

2. **Click "New +" → "Web Service"**

3. **Connect Repository:**
   - Connect your GitHub account if not already connected
   - Select your repository: `iot-secure-water-monitor`

4. **Configure Service:**

   **Basic Settings:**
   - **Name:** `iot-water-monitor` (or your preferred name)
   - **Region:** Choose closest to your users (e.g., Singapore)
   - **Branch:** `main` (or your default branch)
   - **Root Directory:** Leave empty (or `iot-secure-water-monitor` if repo is in subfolder)
   - **Runtime:** `Docker` ⚠️ **Important: Select Docker, not Python 3!**
   - **Build Command:** (Leave empty - Dockerfile handles this)
   - **Start Command:** (Leave empty - Dockerfile CMD handles this)
   
   **Note:** When you select "Docker" as the runtime, Render will automatically:
   - Detect your `Dockerfile`
   - Build the Docker image
   - Run the container using the Dockerfile CMD

   **Advanced Settings:**
   - **Instance Type:** Free (or paid for better performance)
   - **Auto-Deploy:** Yes (deploys on every git push)

### 3.2 Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

**Database Configuration (External MySQL - Supervisor's Database):**
```
DB_HOST=your-supervisor-mysql-host.com
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=ilmuwanutara_e2eewater
```

**Note:** Replace with your supervisor's MySQL database credentials. Ensure the database allows connections from Render's servers (see Step 4 for details).

**MQTT Configuration (Plain - Not Secure):**
```
MQTT_HOST=your-mqtt-broker-host
MQTT_PORT=1883
MQTT_USER=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
```

**MQTT Configuration (Secure TLS - Recommended):**
```
MQTT_HOST=your-mqtt-broker-host
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_CA_CERTS=/path/to/ca-certificate.pem
MQTT_USER=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
```

**Note:** For TLS configuration, see `MQTT_TLS_SETUP.md` for detailed instructions.

**Flask Configuration:**
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-generate-random-string
PORT=10000
```

**Python Configuration:**
```
PYTHON_VERSION=3.11.0
```

### 3.3 Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Build your application
   - Start the service
3. Wait for deployment (usually 2-5 minutes)
4. Your app will be live at: `https://iot-water-monitor.onrender.com` (or your custom domain)

## Step 4: Configure Database

### ✅ Option 1: Use External MySQL Database (Recommended)

**Use your supervisor's MySQL database or any external MySQL server.**

#### Step 4.1: Get Database Credentials

Get the following information from your supervisor:
- **DB_HOST**: MySQL server hostname or IP address
- **DB_PORT**: MySQL port (usually `3306`)
- **DB_USER**: MySQL username
- **DB_PASSWORD**: MySQL password
- **DB_NAME**: Database name (e.g., `ilmuwanutara_e2eewater`)

#### Step 4.2: Configure Database Access

**Important:** The MySQL server must allow connections from Render's IP addresses.

**Ask your supervisor to:**
1. **Whitelist Render IPs** - Allow connections from Render's servers
   - Render uses dynamic IPs, so you may need to allow all IPs or use a specific range
   - Common solution: Allow connections from `%` (all IPs) for your database user
   
2. **Verify firewall rules** - Ensure MySQL port (3306) is accessible from internet
   - If MySQL is behind a firewall, it needs to allow inbound connections on port 3306

**SQL command for supervisor to run (if they have access):**
```sql
-- Allow your database user to connect from any IP (for Render)
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* TO 'your_db_user'@'%' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
```

#### Step 4.3: Set Environment Variables in Render

In Render dashboard → **Environment** tab, add these variables:

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

#### Step 4.4: Test Database Connection

After deployment, check Render logs to verify database connection:
- Go to Render dashboard → **Logs** tab
- Look for database connection messages
- If you see connection errors, check:
  - Credentials are correct
  - Database server allows connections from Render
  - Firewall allows port 3306

### Option 2: Use Render PostgreSQL (Alternative)

If you prefer to use Render's managed database:

1. **Create PostgreSQL Database:**
   - In Render dashboard: **New +** → **PostgreSQL**
   - Name: `iot-water-monitor-db`
   - Plan: Free (or paid)
   - Click **Create Database**

2. **Get Connection String:**
   - Copy the **Internal Database URL** from Render dashboard
   - Format: `postgresql://user:password@host:5432/dbname`

3. **Update `db.py` for PostgreSQL:**

   You'll need to modify `db.py` to use PostgreSQL instead of MySQL:
   - Install `psycopg2-binary` instead of `mysql-connector-python`
   - Update connection code to use PostgreSQL

**Note:** This requires code changes. Using external MySQL (Option 1) is simpler if you already have MySQL credentials.

## Step 5: Configure Custom Domain

**You're using a custom domain, so follow these steps:**

### Step 5.1: Add Custom Domain in Render

1. **In Render Dashboard:**
   - Go to your service → **Settings** → **Custom Domains**
   - Click **Add Custom Domain**
   - Enter your custom domain (e.g., `e2eewater.ilmuwanutara.my` or `yourdomain.com`)
   - Click **Save**

2. **Render will show you DNS instructions:**
   - You'll see a CNAME record to add
   - Example: `your-service.onrender.com`

### Step 5.2: Update DNS Records

**In your domain registrar's DNS settings, add:**

**For subdomain (e.g., `e2eewater.ilmuwanutara.my`):**
```
Type: CNAME
Name: e2eewater
Value: your-service.onrender.com
TTL: 3600 (or default)
```

**For root domain (e.g., `yourdomain.com`):**
```
Type: CNAME
Name: @
Value: your-service.onrender.com
TTL: 3600 (or default)
```

**Note:** Some registrars don't support CNAME on root domain. If that's the case:
- Use a subdomain instead (e.g., `www.yourdomain.com` or `app.yourdomain.com`)
- Or use A record with Render's IP (check Render docs for current IP)

### Step 5.3: Wait for SSL Certificate

1. **After DNS propagates** (can take 5 minutes to 48 hours):
   - Render automatically detects the domain
   - SSL certificate is automatically provisioned
   - Usually takes 5-10 minutes after DNS is correct

2. **Verify SSL:**
   - Visit `https://your-custom-domain.com`
   - Should show a valid SSL certificate
   - Browser should show padlock icon

### Step 5.4: Update Application URLs (If Needed)

If your application has hardcoded URLs, update them to use your custom domain:

**Environment Variable (Optional):**
```
APP_URL=https://your-custom-domain.com
```

**In your code, use:**
```python
app_url = os.environ.get('APP_URL', 'https://your-custom-domain.com')
```

### Step 5.5: Update Raspbian Client to Use Custom Domain

**Important:** After setting up your custom domain, update your Raspberry Pi clients to use it:

**On Raspbian:**
```bash
# Update server URL to use custom domain
python3 multi_sensor_client.py --all https://your-custom-domain.com

# Or set as environment variable
export SERVER_URL=https://your-custom-domain.com
python3 multi_sensor_client.py --all $SERVER_URL
```

**Replace:**
- `http://10.0.2.2` (local/VirtualBox) → `https://your-custom-domain.com`
- `https://your-app.onrender.com` (Render default) → `https://your-custom-domain.com`

**Note:** Use `https://` (not `http://`) since your custom domain has SSL enabled.

## Step 6: Upload Keys Folder

Since Render uses ephemeral file systems, you need to upload your `keys/` folder:

### Option 1: Commit to Git (Not Recommended for Private Keys)

**⚠️ Warning:** Only do this if your keys are not sensitive or if using test keys.

```bash
git add keys/
git commit -m "Add server keys"
git push
```

### Option 2: Use Render Environment Variables (Recommended)

1. **Convert keys to base64:**
   ```bash
   # On your local machine
   cat keys/private.pem | base64
   cat keys/public.pem | base64
   ```

2. **Add to Render Environment Variables:**
   ```
   PRIVATE_KEY_B64=<base64-encoded-private-key>
   PUBLIC_KEY_B64=<base64-encoded-public-key>
   ```

3. **Update `app.py` or `encryption_utils.py`** to read from environment variables:
   ```python
   import base64
   import os
   
   # In app.py or encryption_utils.py
   if os.environ.get('PRIVATE_KEY_B64'):
       private_key_content = base64.b64decode(os.environ.get('PRIVATE_KEY_B64')).decode()
       # Write to file or use directly
   ```

### Option 3: Use Render Disk (Paid Feature)

Render offers persistent disk storage for paid plans.

## Step 7: Verify Deployment

1. **Check Logs:**
   - In Render dashboard → **Logs** tab
   - Look for any errors

2. **Test Application:**
   - Visit your Render URL: `https://your-service.onrender.com`
   - Should see your Flask application (not directory listing!)

3. **Test Database Connection:**
   - Try registering a user
   - Check if data is saved

## Troubleshooting

### "Application failed to start"

**Check logs** in Render dashboard:
- Missing dependencies? Add to `requirements.txt`
- Import errors? Check Python version
- Database connection? Verify environment variables

### "Module not found"

- Ensure all dependencies are in `requirements.txt`
- Check build logs for installation errors

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

4. **Check Render logs:**
   - Look for specific MySQL error messages
   - Common errors:
     - `Access denied` → Wrong credentials or user doesn't have access from Render IPs
     - `Can't connect` → Firewall blocking or wrong host/port
     - `Unknown database` → Wrong database name

### "Keys not found"

- Ensure `keys/` folder is uploaded or use environment variables
- Check file paths in code

### Free Tier Limitations

Render's free tier has some limitations:
- **Spins down after 15 minutes** of inactivity (takes ~30 seconds to wake up)
- **512MB RAM** - May need paid plan for production
- **Limited CPU** - Fine for testing, may need upgrade for production

**Solution:** Use a paid plan ($7/month) for always-on service.

## Render vs LiteSpeed Comparison

| Feature | Render | LiteSpeed |
|--------|--------|-----------|
| **Setup Difficulty** | ⭐ Easy | ⭐⭐⭐ Hard |
| **WSGI Configuration** | Automatic | Manual |
| **SSL Certificates** | Automatic | Manual |
| **Git Deployment** | ✅ Yes | ❌ No |
| **Free Tier** | ✅ Yes (with limitations) | ❌ No |
| **Scaling** | Automatic | Manual |
| **Logs** | Built-in dashboard | SSH/File access |
| **Database** | Managed PostgreSQL | External MySQL |
| **Cost** | Free/$7+/month | Varies |

## Quick Start Checklist for Your Setup

**Your Configuration:**
- ✅ Render with Docker
- ✅ Supervisor's MySQL database
- ✅ Custom domain

**Deployment Steps:**

- [ ] Verify `Dockerfile` exists in project root
- [ ] Verify `requirements.txt` includes all dependencies (including `gunicorn`)
- [ ] Push code to GitHub
- [ ] Create Render account
- [ ] Create Web Service on Render (select **Docker** runtime)
- [ ] Get database credentials from supervisor
- [ ] Ask supervisor to whitelist Render IPs for MySQL access
- [ ] Set environment variables in Render:
  - [ ] Database credentials (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
  - [ ] MQTT configuration
  - [ ] Flask configuration (SECRET_KEY, FLASK_ENV, PORT)
- [ ] Deploy and test (check logs for database connection)
- [ ] Add custom domain in Render dashboard
- [ ] Update DNS records at domain registrar
- [ ] Wait for SSL certificate (5-10 minutes after DNS)
- [ ] Test custom domain access
- [ ] Set up provision agent on Raspbian (separate from Render)
- [ ] Monitor logs for errors

## Important: Provision Agent Setup (Raspbian)

**⚠️ The provision agent does NOT run on Render!**

The **provision agent** (`provision_agent.py`) is a **separate component** that runs on your **Raspberry Pi (Raspbian)**, not on the Render server.

### Architecture Overview

```
┌─────────────────┐         MQTT          ┌──────────────────┐
│  Render Server  │ ◄──────────────────► │  Raspberry Pi    │
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

**On Render (Cloud Server):**
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

After deploying to Render, you **still need** to set up the provision agent on your Raspberry Pi:

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
   export MQTT_HOST="your-mqtt-broker-host"  # Same as Render uses
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

5. **Update sensor clients to use custom domain:**
   ```bash
   # On Raspbian - Use your custom domain instead of Render URL
   python3 multi_sensor_client.py --all https://your-custom-domain.com
   ```

**For complete setup instructions, see:**
- **[PROVISION_AGENT_GUIDE.md](PROVISION_AGENT_GUIDE.md)** - Detailed provision agent setup
- **[RASPBIAN_COMMANDS.txt](RASPBIAN_COMMANDS.txt)** - All Raspbian commands including provision agent

### Why Separate?

- **Provision agent** needs to generate keys **on the device** (Raspberry Pi)
- **Server** (Render) only needs to **receive** public keys via MQTT
- **Security**: Private keys stay on the Raspberry Pi, never on the server

## Next Steps

1. **Get database credentials from supervisor** (MySQL host, user, password, database name)
2. **Ask supervisor to whitelist Render IPs** (allow external connections to MySQL)
3. **Set database environment variables** in Render dashboard
4. **Configure MQTT broker** (may need external service)
5. **Set up provision agent on Raspbian** (see above)
6. **Test full functionality** (user registration, sensor data, etc.)
7. **Set up monitoring** (Render provides basic monitoring)
8. **Consider paid plan** for production use

## Resources

- [Render Documentation](https://render.com/docs)
- [Render Python Guide](https://render.com/docs/deploy-flask)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Render Free Tier Info](https://render.com/docs/free)

---

**Render is much easier than LiteSpeed!** You'll have your app running in minutes instead of hours. 🚀


