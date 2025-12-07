# Database Encryption Key Storage

## Where is the Key Stored?

The database encryption key can be stored in **two ways** (checked in this order):

### Option 1: Environment Variable (Recommended for Production)
**Location**: System environment variable `DB_ENCRYPTION_KEY`

**How to set:**
```bash
# Linux/Mac
export DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows PowerShell
$env:DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows CMD
set DB_ENCRYPTION_KEY=your-generated-key-here
```

**Advantages:**
- ✅ More secure (not stored in files)
- ✅ Easy to manage in cloud platforms (Render, Heroku, etc.)
- ✅ Can be set in deployment configuration
- ✅ No file permissions to manage

### Option 2: Key File (Development/Alternative)
**Location**: File on disk (default: `db_encryption.key` in project root)

**How to set:**
1. Generate key: `python generate_db_key.py`
2. Save to file (or use default `db_encryption.key`)
3. Optionally set custom path: `export DB_ENCRYPTION_KEY_FILE='/path/to/key'`

**Advantages:**
- ✅ Easy for local development
- ✅ Can be version controlled (NOT recommended - use .gitignore!)
- ✅ Simple file-based management

## Is It One-Time Only?

**Yes and No** - here's what you need to know:

### ✅ One-Time Generation
- You generate the key **once** using `python generate_db_key.py`
- The same key is used for all encryption/decryption operations

### ⚠️ Persistent Storage Required
- The key must be **kept available** for the lifetime of your application
- You need the **same key** to decrypt data that was encrypted with it
- If you lose the key, **you cannot decrypt existing encrypted data**

### 🔄 Key Rotation (Advanced)
If you need to change the key:
1. Generate a new key
2. Create a migration script to:
   - Read all encrypted data with old key
   - Decrypt with old key
   - Re-encrypt with new key
   - Update database
3. Update environment variable or key file
4. Restart application

## Key Storage Priority

The system checks in this order:

1. **Environment Variable** (`DB_ENCRYPTION_KEY`) - Used if set
2. **Key File** (`DB_ENCRYPTION_KEY_FILE` or default `db_encryption.key`) - Used if file exists
3. **Error** - If neither is found, the application will fail to start

## Security Best Practices

### For Production:
```bash
# Use environment variable (never commit to git)
export DB_ENCRYPTION_KEY='your-key-here'

# Or set in your cloud platform's dashboard:
# Render.com → Environment → Add Variable
# Heroku → Settings → Config Vars
```

### For Development:
```bash
# Generate key once
python generate_db_key.py

# Key saved to db_encryption.key (already in .gitignore)
# Application automatically finds and uses it
```

### Important Notes:

1. **Never commit keys to Git**
   - `db_encryption.key` is already in `.gitignore`
   - Environment variables are never committed

2. **Backup your key securely**
   - Store in password manager
   - Use separate keys for dev/staging/production
   - **Warning**: Lost key = lost ability to decrypt data

3. **File permissions** (if using key file):
   ```bash
   chmod 600 db_encryption.key  # Only owner can read/write
   ```

## Example Setup Flow

### First Time Setup:
```bash
# 1. Generate key
python generate_db_key.py
# Output: Key generated and optionally saved to db_encryption.key

# 2. For production, set environment variable:
export DB_ENCRYPTION_KEY='generated-key-string'

# 3. For development, key file is automatically used
# (if db_encryption.key exists in project root)

# 4. Restart application
# Encryption/decryption now works automatically!
```

### Application Startup:
```
1. Application starts
2. db_encryption.py loads key from:
   - Environment variable (if set) OR
   - Key file (if exists)
3. Key is cached in memory for performance
4. All database operations use this key automatically
```

## Troubleshooting

### "DB_ENCRYPTION_KEY must be set" Error
**Solution**: Generate and set the key:
```bash
python generate_db_key.py
export DB_ENCRYPTION_KEY='your-key-here'
```

### "Invalid encryption key format" Error
**Solution**: Regenerate key - ensure it's a valid Fernet key (base64, 32 bytes)

### Key File Not Found
**Solution**: Either:
- Set `DB_ENCRYPTION_KEY` environment variable, OR
- Ensure `db_encryption.key` exists in project root, OR
- Set `DB_ENCRYPTION_KEY_FILE` to point to your key file

## Summary

- **Storage**: Environment variable (preferred) or key file
- **Generation**: One-time (but keep it forever!)
- **Usage**: Same key for all operations (encrypt and decrypt)
- **Security**: Never commit to git, backup securely
- **Lifetime**: Keep available for as long as you need to decrypt data

