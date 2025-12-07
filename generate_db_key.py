#!/usr/bin/env python3
"""
Generate a database encryption key for sensor data encryption.

This script generates a secure Fernet key that can be used to encrypt
sensor data before storing it in the database.

Usage:
    python generate_db_key.py

The generated key should be stored securely:
- Set as environment variable: DB_ENCRYPTION_KEY
- Or save to a file: DB_ENCRYPTION_KEY_FILE (default: db_encryption.key)

For production, prefer environment variables over files.
"""

import os
from db_encryption import generate_encryption_key


def main():
    """Generate and display encryption key."""
    print("=" * 70)
    print("Database Encryption Key Generator")
    print("=" * 70)
    print()
    
    # Generate key
    key = generate_encryption_key()
    
    print("Generated encryption key:")
    print("-" * 70)
    print(key)
    print("-" * 70)
    print()
    
    # Option to save to file
    save_to_file = input("Save key to file? (y/n): ").strip().lower()
    if save_to_file == 'y':
        key_file = os.environ.get('DB_ENCRYPTION_KEY_FILE', 'db_encryption.key')
        try:
            with open(key_file, 'w') as f:
                f.write(key)
            print(f"✓ Key saved to: {key_file}")
            print()
            print("IMPORTANT: Secure this file! Add it to .gitignore if not already.")
        except Exception as e:
            print(f"✗ Error saving key file: {e}")
    
    print()
    print("=" * 70)
    print("Setup Instructions (Environment Variable - Recommended):")
    print("=" * 70)
    print()
    print("Windows PowerShell (Current Session):")
    print(f"   $env:DB_ENCRYPTION_KEY='{key}'")
    print()
    print("Windows PowerShell (Permanent):")
    print(f"   [System.Environment]::SetEnvironmentVariable('DB_ENCRYPTION_KEY', '{key}', 'User')")
    print()
    print("Windows CMD (Current Session):")
    print(f"   set DB_ENCRYPTION_KEY={key}")
    print()
    print("Windows CMD (Permanent):")
    print(f'   setx DB_ENCRYPTION_KEY "{key}"')
    print()
    print("Windows GUI (Permanent - Recommended):")
    print("   1. Press Win+R, type 'sysdm.cpl', press Enter")
    print("   2. Click 'Environment Variables'")
    print("   3. Under 'User variables', click 'New'")
    print(f"   4. Name: DB_ENCRYPTION_KEY")
    print(f"   5. Value: {key}")
    print("   6. Click OK, then restart your terminal/IDE")
    print()
    print("Verify it's set:")
    print("   PowerShell: echo $env:DB_ENCRYPTION_KEY")
    print("   CMD: echo %DB_ENCRYPTION_KEY%")
    print()
    print("Security notes:")
    print("   - Never commit encryption keys to version control")
    print("   - Backup keys securely (you cannot decrypt data without the key!)")
    print("   - Use different keys for development/staging/production")
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()


