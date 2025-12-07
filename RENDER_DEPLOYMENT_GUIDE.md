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

**Important:** In Render, you add environment variables **individually**, not as a group. Each variable is added separately.

**Steps in the Render dashboard:**

1. **Go to your Web Service** (the one you just created)
2. **Click on the "Environment" tab** (in the left sidebar or top menu)
3. **For each variable below:**
   - Click **"Add Environment Variable"** button (or **"Add"** button)
   - Enter the **Key** (variable name)
   - Enter the **Value** (variable value)
   - Click **"Save"**
   - Repeat for the next variable

**You will add these variables one by one:**

**Add these environment variables individually:**

**Database Configuration (External MySQL - Supervisor's Database):**
- Click "Add Environment Variable"
  - **Key:** `DB_HOST`
  - **Value:** `your-supervisor-mysql-host.com` (or IP address like `123.45.67.89`)
  - **⚠️ Important:** Use ONLY the hostname or IP address, NOT a URL!
    - ✅ Correct: `ilmuwanutara.my` or `mysql.example.com` or `123.45.67.89`
    - ❌ Wrong: `https://ilmuwanutara.my/phpmyadmin/` (this is phpMyAdmin URL, not MySQL host)
    - ❌ Wrong: `http://ilmuwanutara.my` (don't include http:// or https://)
  
  **📝 How to find MySQL hostname from phpMyAdmin URL:**
  - If phpMyAdmin URL is: `https://ilmuwanutara.my/phpmyadmin/`
  - Then MySQL hostname is usually: `ilmuwanutara.my` (same domain, no https:// or /phpmyadmin/)
  - If that doesn't work, ask supervisor for the actual MySQL server hostname/IP
  - Sometimes it's a subdomain like: `mysql.ilmuwanutara.my`
  
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `DB_PORT`
  - **Value:** `3306`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `DB_USER`
  - **Value:** `your_db_username`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `DB_PASSWORD`
  - **Value:** `your_db_password`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `DB_NAME`
  - **Value:** `ilmuwanutara_e2eewater`
  - Click "Save"

**Note:** Replace with your supervisor's MySQL database credentials. Ensure the database allows connections from Render's servers (see Step 4 for details).

**MQTT Configuration (HiveMQ Cloud - Recommended):**

**✅ Using HiveMQ Cloud?** See **[HIVEMQ_CLOUD_SETUP.md](HIVEMQ_CLOUD_SETUP.md)** for complete setup guide.

**Example for HiveMQ Cloud:**
- Click "Add Environment Variable"
  - **Key:** `MQTT_HOST`
  - **Value:** `your-cluster-id.s1.eu.hivemq.cloud` 
  c04db6249f624af8ac41e2bc1df846e3.s1.eu.hivemq.cloud
  
  **📍 Where to get this value:**
  1. Go to [HiveMQ Cloud Dashboard](https://console.hivemq.cloud/)
  2. Click on your cluster name (the one you just created)
  3. Look for **"Connection Details"** tab or **"Endpoint"** section
  4. You'll see a **"Broker URL"** like: `abc123def456.s1.eu.hivemq.cloud`
  5. Copy this entire URL (including the `.s1.eu.hivemq.cloud` part)
  6. Paste it as the value for `MQTT_HOST`
  
  **Example:** If you see `abc123def456.s1.eu.hivemq.cloud`, use that exact value.
  
  **📖 Detailed guide:** See **[HIVEMQ_FIND_HOST.md](HIVEMQ_FIND_HOST.md)** for step-by-step instructions with screenshots.
  
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_PORT`
  - **Value:** `8883` (TLS port for HiveMQ Cloud)
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_USE_TLS`
  - **Value:** `true`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_USER`
  - **Value:** `water-monitor-user` (or your HiveMQ username)
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_PASSWORD`
  - **Value:** `your_hivemq_password` (password you set in HiveMQ Cloud)
  - Click "Save"

**Note:** HiveMQ Cloud uses TLS by default (port 8883). No need for `MQTT_CA_CERTS` (uses system certificates).

**⚠️ Need help with other MQTT brokers?** See **[MQTT_BROKER_SETUP.md](MQTT_BROKER_SETUP.md)** for all options.

**MQTT Configuration (Secure TLS - Recommended):**
- Click "Add Environment Variable"
  - **Key:** `MQTT_HOST`
  - **Value:** `your-mqtt-broker-host`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_PORT`
  - **Value:** `8883`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_USE_TLS`
  - **Value:** `true`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_CA_CERTS`
  - **Value:** `/path/to/ca-certificate.pem`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_USER`
  - **Value:** `your_mqtt_username`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `MQTT_PASSWORD`
  - **Value:** `your_mqtt_password`
  - Click "Save"

**Note:** For TLS configuration, see `MQTT_TLS_SETUP.md` for detailed instructions.

**Flask Configuration:**
- Click "Add Environment Variable"
  - **Key:** `FLASK_ENV`
  - **Value:** `production`
  - Click "Save"
- Click "Add Environment Variable"
  - **Key:** `SECRET_KEY`
  - **Value:** Generate a random secret key (see instructions below)
  - Click "Save"

  **🔐 How to Generate SECRET_KEY:**
  
  **Option 1: Using Python (Recommended)**
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  This generates a secure 43-character random string.
  
  **Option 2: Using OpenSSL (if installed)**
  ```bash
  openssl rand -hex 32
  ```
  This generates a 64-character hexadecimal string.
  
  **Option 3: Online Generator**
  - Visit: https://randomkeygen.com/
  - Use "CodeIgniter Encryption Keys" or "Fort Knox Passwords"
  - Copy a random string (at least 32 characters)
  
  **Important:** 
  - Use a **different** secret key for production (don't use the example)
  - Keep it **secret** - never commit it to Git
  - At least **32 characters** long
  - Random and unpredictable
- Click "Add Environment Variable"
  - **Key:** `PORT`
  - **Value:** `10000`
  - Click "Save"

**Python Configuration (Optional - usually auto-detected):**
- Click "Add Environment Variable"
  - **Key:** `PYTHON_VERSION`
  - **Value:** `3.11.0`
  - Click "Save"

**Note:** You do NOT create an "environment group". You add each environment variable individually by clicking "Add Environment Variable" for each one.

**Summary:**
- ✅ Click "Add Environment Variable" for each variable
- ✅ Enter Key and Value
- ✅ Click "Save" (variables are saved immediately)
- ⚠️ **After saving all variables, you MUST redeploy** (see section 3.2.1 below)

### 3.2.1 After Adding Environment Variables

**⚠️ Important:** After saving environment variables, you need to **redeploy** your service for the changes to take effect.

**What happens when you click "Save":**
- ✅ Environment variable is **saved immediately** to Render's database
- ❌ But the **running service** does NOT automatically restart
- ⚠️ You must **manually redeploy** to apply the new variables

**Option 1: Automatic Redeploy (Recommended)**
- After saving environment variables, Render will show a notification: **"Environment variables updated. Redeploy to apply changes?"**
- Click **"Redeploy"** or **"Manual Deploy"** button
- Render will rebuild and redeploy with the new environment variables

**Option 2: Manual Redeploy**
- Go to your service dashboard
- Click **"Manual Deploy"** button (top right)
- Select **"Clear build cache & deploy"** (optional, but recommended for first deployment)
- Click **"Deploy latest commit"**
- Wait for deployment to complete (2-5 minutes)

**Workflow:**
1. Add all environment variables (click "Save" for each one)
2. After adding all variables, click **"Manual Deploy"** once
3. Wait for deployment to complete
4. Your service will now use the new environment variables

**Note:** 
- You can add all variables first, then redeploy once at the end (more efficient)
- Or redeploy after each variable (slower, but you can test each one)

### 3.3 Deploy (First Time)

**If you haven't created the service yet:**

1. **After adding all environment variables**, click **"Create Web Service"** button
2. Render will:
   - Clone your repository
   - Install dependencies
   - Build your Docker image
   - Start the service with your environment variables
3. Wait for deployment (usually 2-5 minutes)
4. Your app will be live at: `https://iot-water-monitor.onrender.com` (or your custom domain)

**If you already created the service:**

1. After adding/modifying environment variables, click **"Manual Deploy"** button
2. Select **"Clear build cache & deploy"** (optional)
3. Click **"Deploy latest commit"**
4. Wait for deployment to complete
5. Check logs to verify environment variables are loaded correctly

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
     - `Unknown MySQL server host 'https://...'` → **DB_HOST is set to a URL instead of hostname!**
       - Fix: Change `DB_HOST` from `https://example.com/phpmyadmin/` to just `example.com`
       - `DB_HOST` should be hostname/IP only, not a URL

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

4. **Set up provision agent automation (recommended):**
   
   **For automatic startup and auto-restart, see:**
   - **[PROVISION_AGENT_AUTOMATION.md](PROVISION_AGENT_AUTOMATION.md)** - Complete automation guide with systemd service
   
   **Quick manual run (for testing only):**
   ```bash
   # On Raspbian
   cd ~/water-monitor
   python3 simulators/sensor/provision_agent.py
   ```
   
   **For production, use systemd service (auto-starts on boot):**
   ```bash
   # Follow PROVISION_AGENT_AUTOMATION.md for full setup
   sudo systemctl enable provision-agent.service
   sudo systemctl start provision-agent.service
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


