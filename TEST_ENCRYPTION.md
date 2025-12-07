# How to Test Database Encryption

## Quick Test Checklist

### ✅ Test 1: Verify Encryption Key is Loaded

**Check Apache Error Log:**
```powershell
# View recent Apache errors
Get-Content C:\Apache24\logs\error.log -Tail 50 | Select-String "encryption\|DB_ENCRYPTION"
```

**Or test in Python:**
```powershell
# Activate venv
cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
.\venv\Scripts\Activate.ps1

# Test encryption
python -c "from db_encryption import get_db_encryption; e = get_db_encryption(); print('✓ Encryption loaded successfully!')"
```

### ✅ Test 2: Submit Sensor Data

1. **Submit data** via your `/submit-data` endpoint (or use your sensor simulator)
2. **Check database** - values should be encrypted

### ✅ Test 3: Check Database (Encrypted Storage)

**In MySQL/phpMyAdmin:**
```sql
SELECT id, tds, ph, turbidity, created_at 
FROM water_readings 
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected Result:**
- `tds`, `ph`, `turbidity` should be **long encrypted strings** like `gAAAAABl...`
- **NOT** plain numbers like `250.5` or `7.2`

### ✅ Test 4: View Dashboard (Decrypted Display)

1. Go to `/dashboard` in your browser
2. Sensor readings should display as **normal numbers** (7.5, 250.0, etc.)
3. This confirms decryption is working automatically

### ✅ Test 5: Test Encryption/Decryption Directly

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run verification script
python verify_encryption.py
```

This will show:
- Original values (plaintext)
- Encrypted values (what's stored)
- Decrypted values (what you see)

## Quick Test Script

Create `test_db_encryption.py`:

```python
from db_encryption import get_db_encryption
from db import insert_reading, list_recent_water_readings

# Test encryption
encryption = get_db_encryption()
print("✓ Encryption module loaded")

# Test encrypt/decrypt
test_value = 7.5
encrypted = encryption.encrypt_value(test_value)
decrypted = encryption.decrypt_value(encrypted)
print(f"✓ Encrypt/Decrypt test: {test_value} → encrypted → {decrypted}")

# Test database insert (if you want)
# insert_reading(tds=250.5, ph=7.2, turbidity=3.1, safe=True, reasons=None)
# print("✓ Test data inserted")

# Test database retrieval
readings = list_recent_water_readings(limit=1)
if readings:
    print(f"✓ Retrieved reading: tds={readings[0]['tds']}, ph={readings[0]['ph']}")
    print("  (Values should be decrypted - normal numbers)")
```

Run it:
```powershell
python test_db_encryption.py
```

## What to Look For

### ✅ Success Signs:
- Database contains encrypted strings (long base64 text)
- Dashboard shows normal numbers (automatically decrypted)
- No errors in Apache logs
- Encryption test script runs without errors

### ❌ Failure Signs:
- Database still has plain numbers (encryption not working)
- Dashboard shows `None` or errors (decryption failing)
- "DB_ENCRYPTION_KEY must be set" error in logs
- "Invalid encryption key format" error

## Troubleshooting

**If encryption not working:**
1. Check Apache restarted: `Get-Service Apache2.4`
2. Check app.wsgi has the key (line 60)
3. Check Apache error logs for errors

**If decryption failing:**
1. Verify key in app.wsgi matches the one you generated
2. Check database - old unencrypted data will show as None (that's OK)
3. New data should work fine

