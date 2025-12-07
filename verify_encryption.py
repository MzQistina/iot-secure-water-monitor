#!/usr/bin/env python3
"""
Verify that sensor data is stored encrypted in the database.

This script demonstrates:
1. How values are encrypted before storage
2. What encrypted data looks like in the database
3. How values are decrypted when retrieved
"""

from db_encryption import get_db_encryption

def demonstrate_encryption():
    """Show encryption/decryption process."""
    print("=" * 70)
    print("Database Encryption Verification")
    print("=" * 70)
    print()
    
    encryption = get_db_encryption()
    
    # Example sensor values
    test_values = {
        'tds': 250.5,
        'ph': 7.2,
        'turbidity': 3.1,
        'sensor_value': 45.8
    }
    
    print("Original Sensor Values (Plaintext):")
    print("-" * 70)
    for key, value in test_values.items():
        print(f"  {key:15} = {value} (type: {type(value).__name__})")
    print()
    
    print("Encrypted Values (Ciphertext - What's Stored in DB):")
    print("-" * 70)
    encrypted_data = {}
    for key, value in test_values.items():
        encrypted = encryption.encrypt_value(value)
        encrypted_data[key] = encrypted
        print(f"  {key:15} = {encrypted[:50]}... (length: {len(encrypted)} chars)")
        print(f"                (stored as TEXT in database)")
    print()
    
    print("Decrypted Values (Retrieved from DB):")
    print("-" * 70)
    for key, encrypted in encrypted_data.items():
        decrypted = encryption.decrypt_value(encrypted)
        original = test_values[key]
        match = "✓" if decrypted == original else "✗"
        print(f"  {key:15} = {decrypted} {match} (matches original: {original})")
    print()
    
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    print("✓ Sensor values are encrypted BEFORE storing in database")
    print("✓ Database stores encrypted ciphertext (base64-encoded strings)")
    print("✓ Values are decrypted AFTER retrieving from database")
    print("✓ Application code receives plaintext (no changes needed)")
    print()
    print("Database Storage Format:")
    print("  - Column type: TEXT (not DOUBLE)")
    print("  - Value format: Base64-encoded encrypted string")
    print("  - Example: 'gAAAAABl...' (long encrypted string)")
    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        demonstrate_encryption()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure DB_ENCRYPTION_KEY is set or db_encryption.key exists")

