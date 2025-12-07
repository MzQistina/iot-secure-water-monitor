# How to Restart Apache as Administrator (Windows)

## Step 1: Open PowerShell as Administrator

**Method 1: Right-click Menu**
1. Press `Win + X` (or right-click Start button)
2. Click **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
3. Click "Yes" when prompted by UAC

**Method 2: Search Menu**
1. Press `Win` key
2. Type "PowerShell"
3. Right-click "Windows PowerShell"
4. Select **"Run as administrator"**
5. Click "Yes" when prompted

**Method 3: Run Dialog**
1. Press `Win + R`
2. Type: `powershell`
3. Press `Ctrl + Shift + Enter` (opens as admin)
4. Click "Yes" when prompted

## Step 2: Navigate to Your Project (Optional)

```powershell
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
```

## Step 3: Restart Apache

```powershell
# Stop Apache
net stop Apache2.4

# Start Apache
net start Apache2.4
```

Or restart in one command:
```powershell
Restart-Service Apache2.4
```

## Alternative: Using Services GUI

1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Find **"Apache2.4"** or **"Apache HTTP Server"**
4. Right-click → **Restart**

## Verify Apache Restarted

```powershell
# Check Apache status
Get-Service Apache2.4
```

Should show "Running" status.

## Quick One-Liner

Open PowerShell as Admin, then run:
```powershell
Restart-Service Apache2.4
```

