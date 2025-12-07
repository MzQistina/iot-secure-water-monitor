# Installation Instructions

## Step 1: Navigate to Project Directory

Open your terminal/command prompt and go to your project folder:

```bash
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
```

## Step 2: Activate Virtual Environment

Since you have a `venv` folder, activate it first:

### Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows CMD:
```cmd
venv\Scripts\activate.bat
```

**Note:** If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Alternative: If you're using Git Bash or WSL:
```bash
source venv/Scripts/activate
```

## Step 3: Install Cryptography Package

Once the virtual environment is activated (you'll see `(venv)` in your prompt), install:

```bash
pip install cryptography>=41.0.0
```

Or install all requirements (including cryptography):

```bash
pip install -r requirements.txt
```

## Step 4: Verify Installation

Check that cryptography is installed:

```bash
pip show cryptography
```

You should see package information if it's installed correctly.

## Step 5: Generate Encryption Key

Now you can generate your encryption key:

```bash
python generate_db_key.py
```

## Quick Reference

**Full sequence (Windows PowerShell):**
```powershell
# Navigate to project
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"

# Activate venv
.\venv\Scripts\Activate.ps1

# Install cryptography
pip install cryptography>=41.0.0

# Generate key
python generate_db_key.py
```

**Full sequence (Windows CMD):**
```cmd
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
venv\Scripts\activate.bat
pip install cryptography>=41.0.0
python generate_db_key.py
```

## Troubleshooting

### "pip is not recognized"
- Make sure virtual environment is activated
- Try: `python -m pip install cryptography>=41.0.0`

### "Cannot activate venv"
- Make sure you're in the project directory
- Check that `venv\Scripts\activate.bat` exists

### "Package installed but import fails"
- Make sure Flask app is running with the same virtual environment
- Verify: `python -c "import cryptography; print(cryptography.__version__)"`

