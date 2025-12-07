# Next Steps: Complete Database Encryption Setup

## Step 1: Install Required Package

Make sure the `cryptography` package is installed:

```bash
pip install cryptography>=41.0.0
```

Or if you're using requirements.txt:

```bash
pip install -r requirements.txt
```

## Step 2: Generate Encryption Key

Run the key generator script:

```bash
python generate_db_key.py
```

This will:
- Generate a secure encryption key
- Optionally save it to `db_encryption.key`
- Display the key for you to copy

## Step 3: Configure the Key

**Choose ONE of these options:**

### Option A: Environment Variable (Recommended for Production)

```bash
# Linux/Mac
export DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows PowerShell
$env:DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows CMD
set DB_ENCRYPTION_KEY=your-generated-key-here
```

### Option B: Key File (Development)

If you saved the key to `db_encryption.key` during generation, it will be automatically used. Otherwise:

1. Create `db_encryption.key` file in your project root
2. Paste the generated key into it
3. Ensure it's in `.gitignore` (already added)

## Step 4: Test the Setup

Run the verification script to ensure encryption works:

```bash
python verify_encryption.py
```

This will show:
- How values are encrypted
- What encrypted data looks like
- That decryption works correctly

## Step 5: Restart Your Flask Application

```bash
# Stop your current Flask app (Ctrl+C)
# Then restart it
python app.py
# or
flask run
```

## Step 6: Test with Real Data

1. **Submit sensor data** via your `/submit-data` endpoint
2. **Check the database** - values should be encrypted (long base64 strings)
3. **View dashboard** - values should display correctly (automatically decrypted)

### Quick Database Check

You can verify encryption is working by checking the database directly:

```sql
-- In MySQL/phpMyAdmin
SELECT id, tds, ph, turbidity, created_at 
FROM water_readings 
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected Result:**
- `tds`, `ph`, `turbidity` columns should contain long encrypted strings like `gAAAAABl...`
- NOT plain numbers like `250.5` or `7.2`

### Verify Dashboard Shows Correct Values

1. Go to `/dashboard` in your browser
2. Sensor readings should display as normal numbers (7.5, 250.0, etc.)
3. This confirms decryption is working automatically

## Troubleshooting

### Error: "DB_ENCRYPTION_KEY must be set"

**Solution:** Make sure you've set the encryption key (Step 3)

### Error: "Invalid encryption key format"

**Solution:** Regenerate the key using `python generate_db_key.py` and ensure you copy it correctly

### Dashboard shows None or errors

**Solution:** 
1. Check that encryption key is set correctly
2. Verify `cryptography` package is installed
3. Check application logs for decryption errors

### Old data shows as None

**Cause:** Existing unencrypted data in database

**Solution:** The system handles this automatically - old data will be parsed as floats. New data will be encrypted.

## What Happens Now?

✅ **New sensor readings** → Automatically encrypted before storing  
✅ **Database storage** → Contains encrypted ciphertext  
✅ **Dashboard/API** → Automatically decrypts when displaying  
✅ **No code changes needed** → Encryption is transparent to your application

## Security Checklist

- [ ] Encryption key generated
- [ ] Key stored securely (environment variable or secure file)
- [ ] `db_encryption.key` added to `.gitignore` (already done)
- [ ] Key backed up securely (password manager, etc.)
- [ ] Application tested and working
- [ ] Database verified to contain encrypted data

## Need Help?

- See `DATABASE_ENCRYPTION_SETUP.md` for detailed documentation
- See `KEY_STORAGE_EXPLANATION.md` for key storage details
- Check application logs for any errors

