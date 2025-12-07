# Database Encryption Setup Guide

This guide explains how to set up encryption for sensor data stored in the database.

## Overview

Sensor readings (tds, ph, turbidity, and sensor_data.value) are now encrypted before being stored in the database using **Fernet symmetric encryption** (AES-128 in CBC mode). This ensures that even if the database is compromised, the actual sensor values remain protected.

## Features

- ✅ **Production-safe encryption**: Uses cryptography library's Fernet (AES-128)
- ✅ **Automatic encryption/decryption**: Transparent to application code
- ✅ **Backward compatibility**: Handles legacy unencrypted data gracefully
- ✅ **Secure key management**: Supports environment variables and key files

## Quick Setup

### Step 1: Generate Encryption Key

Run the key generator script:

```bash
python generate_db_key.py
```

This will:
1. Generate a secure Fernet encryption key
2. Optionally save it to a file (`db_encryption.key`)
3. Display setup instructions

### Step 2: Configure Key

**Option A: Environment Variable (Recommended for Production)**

Set the `DB_ENCRYPTION_KEY` environment variable:

```bash
# Linux/Mac
export DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows PowerShell
$env:DB_ENCRYPTION_KEY='your-generated-key-here'

# Windows CMD
set DB_ENCRYPTION_KEY=your-generated-key-here
```

**Option B: Key File (Development)**

1. Save the generated key to a file (e.g., `db_encryption.key`)
2. Set the `DB_ENCRYPTION_KEY_FILE` environment variable:

```bash
export DB_ENCRYPTION_KEY_FILE='db_encryption.key'
```

**Option C: Default File Location**

If neither environment variable is set, the system will look for `db_encryption.key` in the project root.

### Step 3: Secure the Key File

If using a key file:

```bash
# Restrict file permissions (Linux/Mac)
chmod 600 db_encryption.key

# Add to .gitignore
echo "db_encryption.key" >> .gitignore
```

### Step 4: Restart Application

Restart your Flask application for the changes to take effect.

## Database Schema Changes

The following columns have been migrated from `DOUBLE` to `TEXT` to support encrypted storage:

- `water_readings.tds`
- `water_readings.ph`
- `water_readings.turbidity`
- `sensor_data.value`

The migration happens automatically on first run. Existing unencrypted data will be handled gracefully (decryption will attempt to parse as float if decryption fails).

## How It Works

### Encryption Flow

1. **On Insert**: Sensor values are encrypted before being stored:
   ```python
   # In db.py
   encrypted_value = encryption.encrypt_value(value)  # Encrypts float to base64 string
   # Store encrypted_value in database
   ```

2. **On Retrieve**: Encrypted values are decrypted when reading:
   ```python
   # In db.py
   decrypted_value = encryption.decrypt_value(encrypted_str)  # Decrypts base64 string to float
   # Return decrypted_value to application
   ```

### Application Code

No changes needed in your Flask routes! The encryption/decryption happens transparently in the database layer:

```python
# Your code remains the same
rows = list_recent_sensor_data(limit=200, user_id=user_id)
# rows[0]['value'] is automatically decrypted - no changes needed!
```

## Security Best Practices

1. **Never commit keys to version control**
   - Add `db_encryption.key` to `.gitignore`
   - Use environment variables in production

2. **Rotate keys periodically**
   - Generate a new key
   - Re-encrypt existing data (requires migration script)
   - Update environment variable

3. **Backup keys securely**
   - Store keys in a secure password manager
   - Use separate keys for development/staging/production
   - **Warning**: Lost keys mean lost data (cannot decrypt without key)

4. **Use environment variables in production**
   - More secure than files
   - Easier to manage in cloud platforms
   - Can be set in deployment configuration

## Troubleshooting

### Error: "DB_ENCRYPTION_KEY or DB_ENCRYPTION_KEY_FILE environment variable must be set"

**Solution**: Set the encryption key as described in Step 2.

### Error: "Invalid encryption key format"

**Solution**: Ensure the key is a valid Fernet key (base64-encoded, 32 bytes). Regenerate using `generate_db_key.py`.

### Warning: "Failed to decrypt value (may be legacy data)"

**Cause**: The database contains unencrypted data from before encryption was enabled.

**Solution**: This is handled automatically - the system will attempt to parse the value as a float. For a clean migration, you may want to re-encrypt existing data.

### Data appears as None after decryption

**Possible causes**:
1. Wrong encryption key
2. Corrupted encrypted data
3. Legacy unencrypted data that cannot be parsed

**Solution**: Verify the encryption key matches the one used to encrypt the data.

## Migration from Unencrypted Data

If you have existing unencrypted data, the system handles it gracefully. However, for a clean migration:

1. Ensure encryption is set up and working
2. New data will be encrypted automatically
3. Old data will be decrypted as floats (backward compatible)
4. Optionally, create a migration script to re-encrypt all existing data

## Testing

Test encryption/decryption:

```python
from db_encryption import encrypt_sensor_value, decrypt_sensor_value

# Encrypt
encrypted = encrypt_sensor_value(7.5)
print(f"Encrypted: {encrypted}")

# Decrypt
decrypted = decrypt_sensor_value(encrypted)
print(f"Decrypted: {decrypted}")  # Should print 7.5
```

## Production Deployment

### Render.com / Heroku / Cloud Platforms

Set the environment variable in your platform's dashboard:

```
DB_ENCRYPTION_KEY=your-generated-key-here
```

### Docker

Add to your `docker-compose.yml` or Dockerfile:

```yaml
environment:
  - DB_ENCRYPTION_KEY=${DB_ENCRYPTION_KEY}
```

Or use a secrets file (never commit to git):

```bash
docker run -e DB_ENCRYPTION_KEY="$(cat db_encryption.key)" your-app
```

## Support

For issues or questions:
1. Check that the encryption key is set correctly
2. Verify the `cryptography` package is installed: `pip install cryptography`
3. Check application logs for encryption/decryption errors


