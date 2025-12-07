# Fix Git Initialization Issue

## ⚠️ Problem

You initialized Git in the **wrong directory** (`C:\Users\NURMIZAN QISTINA\`) instead of your project directory.

## ✅ Solution

### Step 1: Remove Git from Home Directory

**Option A: Remove the .git folder (Recommended)**
```powershell
cd C:\Users\NURMIZAN QISTINA
Remove-Item -Recurse -Force .git
```

**Option B: Just ignore it and work in project directory**
- The git repo in home directory won't affect your project
- Just initialize git in the project directory

### Step 2: Navigate to Project Directory

```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
```

### Step 3: Initialize Git in Project Directory

```powershell
git init
```

### Step 4: Add Project Files

```powershell
git add .
```

### Step 5: Commit

```powershell
git commit -m "Initial commit for Render deployment"
```

### Step 6: Create GitHub Repository and Push

1. Create repository on GitHub
2. Add remote:
   ```powershell
   git remote add origin https://github.com/yourusername/iot-secure-water-monitor.git
   ```
3. Push:
   ```powershell
   git branch -M main
   git push -u origin main
   ```

## Quick Fix Commands

Run these commands in order:

```powershell
# 1. Remove git from home directory (optional but recommended)
cd C:\Users\NURMIZAN QISTINA
Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue

# 2. Navigate to project directory
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"

# 3. Initialize git in project directory
git init

# 4. Add all files
git add .

# 5. Commit
git commit -m "Initial commit for Render deployment"

# 6. Check status (verify sensitive files are excluded)
git status
```

## Verify

After running the commands, check:
- `git status` should show only project files
- Should NOT show: `keys/`, `sensor_keys/`, `user_keys/`, `.env`, `venv/`
- Should show: `app.py`, `Dockerfile`, `requirements.txt`, `templates/`, etc.

