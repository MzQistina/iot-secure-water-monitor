# Pre-Push Checklist for Render Deployment

**Your Setup:**
- ✅ Render with Docker
- ✅ Supervisor's MySQL database
- ✅ Custom domain

## ✅ Pre-Push Checklist

### 1. Required Files
- [x] `Dockerfile` exists and is correct
- [x] `requirements.txt` includes all dependencies (including `gunicorn`)
- [x] `.gitignore` excludes sensitive files
- [x] `.dockerignore` configured correctly

### 2. Sensitive Files (MUST be excluded)
- [x] `keys/` folder (contains server private keys) - **EXCLUDED in .gitignore**
- [x] `sensor_keys/` folder (contains sensor private keys) - **EXCLUDED in .gitignore**
- [x] `user_keys/` folder - **EXCLUDED in .gitignore**
- [x] `.env` files - **EXCLUDED in .gitignore**
- [x] `*.key` files - **EXCLUDED in .gitignore**
- [x] `venv/` folder - **EXCLUDED in .gitignore**
- [x] `*.log` files - **EXCLUDED in .gitignore**

### 3. Code Files (MUST be included)
- [x] `app.py` - Main Flask application
- [x] `db.py` - Database connection
- [x] `encryption_utils.py` - Encryption utilities
- [x] `validation.py` - Input validation
- [x] `templates/` - HTML templates
- [x] `static/` - Static files (CSS, images, etc.)
- [x] `mqtt_listener.py` - MQTT listener

### 4. Configuration Files
- [x] `requirements.txt` - Python dependencies
- [x] `Dockerfile` - Docker configuration
- [x] `.dockerignore` - Docker ignore rules
- [x] `.gitignore` - Git ignore rules
- [x] `default_thresholds.json` - Default sensor thresholds

### 5. Before Pushing

**Verify sensitive files are NOT tracked:**
```bash
git status
# Should NOT show: keys/, sensor_keys/, user_keys/, .env, *.log, venv/
```

**If sensitive files are tracked, remove them:**
```bash
git rm -r --cached keys/
git rm -r --cached sensor_keys/
git rm -r --cached user_keys/
git rm --cached *.log
git rm -r --cached venv/
```

### 6. Keys Handling for Render

**Server keys (`keys/` folder) will be handled via:**
- Option 1: Environment variables (recommended)
- Option 2: Render Disk (paid feature)
- Option 3: Generate new keys on first deployment

**See:** `RENDER_DEPLOYMENT_GUIDE.md` → Step 6 for details

### 7. Ready to Push?

**If all checks pass:**
```bash
git add .
git commit -m "Prepare for Render deployment with Docker"
git push origin main
```

**After pushing:**
1. Create Render Web Service
2. Select **Docker** runtime
3. Set environment variables (database, MQTT, Flask)
4. Deploy!

## ⚠️ Important Notes

1. **Never commit private keys** - They're excluded in `.gitignore`
2. **Keys will be created on Render** - Either via environment variables or generated on first run
3. **Database credentials** - Set in Render environment variables, NOT in code
4. **MQTT credentials** - Set in Render environment variables, NOT in code

## 🔒 Security Checklist

- [x] No hardcoded passwords in code
- [x] No database credentials in code
- [x] No API keys in code
- [x] All sensitive files in `.gitignore`
- [x] Environment variables used for secrets

---

**Your folder is ready to push!** ✅

Just make sure to:
1. Review `git status` to ensure no sensitive files are tracked
2. Set all credentials as environment variables in Render (not in code)
3. Handle keys via environment variables or generate on Render

