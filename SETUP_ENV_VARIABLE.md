# Setting Up DB_ENCRYPTION_KEY Environment Variable (Windows)

## Step 1: Generate Your Encryption Key

First, generate the key:

```bash
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Generate key
python generate_db_key.py
```

Copy the generated key (it will be a long string like `gAAAAABl...`)

## Step 2: Set Environment Variable

### Option A: PowerShell (Current Session Only)

```powershell
$env:DB_ENCRYPTION_KEY='your-generated-key-here'
```

**Note:** This only lasts for the current PowerShell session. When you close PowerShell, it's gone.

### Option B: PowerShell (Permanent - User Level)

```powershell
# Set permanently for your user account
[System.Environment]::SetEnvironmentVariable('DB_ENCRYPTION_KEY', 'your-generated-key-here', 'User')

# Refresh environment in current session
$env:DB_ENCRYPTION_KEY = [System.Environment]::GetEnvironmentVariable('DB_ENCRYPTION_KEY', 'User')
```

### Option C: Windows GUI (Permanent - Recommended)

1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click **"Environment Variables"** button
3. Under **"User variables"**, click **"New"**
4. Variable name: `DB_ENCRYPTION_KEY`
5. Variable value: Paste your generated key
6. Click **OK** on all dialogs
7. **Restart your terminal/IDE** for changes to take effect

### Option D: Command Prompt (Current Session Only)

```cmd
set DB_ENCRYPTION_KEY=your-generated-key-here
```

### Option E: Command Prompt (Permanent)

```cmd
setx DB_ENCRYPTION_KEY "your-generated-key-here"
```

**Note:** After using `setx`, close and reopen your terminal.

## Step 3: Verify It's Set

### PowerShell:
```powershell
echo $env:DB_ENCRYPTION_KEY
```

### Command Prompt:
```cmd
echo %DB_ENCRYPTION_KEY%
```

### Python Test:
```python
import os
print(os.environ.get('DB_ENCRYPTION_KEY'))
```

## Step 4: Test Your Flask App

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run your Flask app
python app.py
```

The app should start without encryption key errors.

## Important Notes

### For Development:
- **Temporary** (Option A or D) is fine if you always run from the same terminal
- **Permanent** (Option B, C, or E) is better so you don't have to set it every time

### For Production:
- Set in your cloud platform's dashboard:
  - **Render.com**: Environment → Add Variable
  - **Heroku**: Settings → Config Vars
  - **PythonAnywhere**: Web → Environment variables

### Security:
- ✅ Never commit the key to Git (already in `.gitignore`)
- ✅ Don't share the key publicly
- ✅ Use different keys for development/staging/production

## Troubleshooting

### "DB_ENCRYPTION_KEY must be set" Error

**Check:**
1. Is the variable set? Run: `echo $env:DB_ENCRYPTION_KEY` (PowerShell)
2. Did you restart your terminal/IDE after setting it permanently?
3. Is your Flask app running in the same environment?

**Solution:**
- Set it again in your current terminal session
- Or restart your terminal/IDE after setting permanently

### Variable Not Found After Restart

**Solution:**
- Use Option B (PowerShell permanent) or Option C (GUI) - these persist across sessions
- Or create a startup script that sets it automatically

## Quick Setup Script (Optional)

Create a file `setup_env.ps1`:

```powershell
# setup_env.ps1
$key = Read-Host "Enter your DB_ENCRYPTION_KEY"
[System.Environment]::SetEnvironmentVariable('DB_ENCRYPTION_KEY', $key, 'User')
Write-Host "✓ DB_ENCRYPTION_KEY set permanently!"
Write-Host "Please restart your terminal/IDE for changes to take effect."
```

Run it:
```powershell
.\setup_env.ps1
```

