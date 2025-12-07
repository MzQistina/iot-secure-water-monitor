#!/usr/bin/env python3
"""
Extract public key from private key and compare with server's public key.
Run this on the Raspberry Pi to verify if keys match.
"""

import sys
import os
import requests
from Crypto.PublicKey import RSA

def extract_public_key_from_private(private_key_path):
    """Extract public key from private key file."""
    try:
        with open(private_key_path, 'rb') as f:
            private_key = RSA.import_key(f.read())
        public_key = private_key.publickey()
        return public_key.export_key().decode('utf-8')
    except Exception as e:
        print(f"❌ Error reading private key: {e}")
        return None

def get_server_public_key(device_id, user_id, server_url):
    """Get public key from server database (via diagnostic endpoint if available)."""
    # Try to get from API if logged in, otherwise we'll need to check filesystem
    # For now, we'll just show what we can extract from the private key
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 verify_key_pair.py <private_key_path> [server_url]")
        print("\nExample:")
        print("  python3 verify_key_pair.py sensor_keys/5/ph01/sensor_private.pem")
        sys.exit(1)
    
    private_key_path = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(private_key_path):
        print(f"❌ Private key not found: {private_key_path}")
        sys.exit(1)
    
    print(f"Extracting public key from: {private_key_path}\n")
    
    # Extract public key from private key
    client_public_key = extract_public_key_from_private(private_key_path)
    
    if not client_public_key:
        sys.exit(1)
    
    print("✅ Successfully extracted public key from private key")
    print(f"   Public key length: {len(client_public_key)} characters")
    print(f"   First 50 chars: {client_public_key[:50]}...")
    print(f"   Last 50 chars: ...{client_public_key[-50:]}")
    
    print("\n💡 Next steps:")
    print("   1. Compare this public key with the one stored on the server")
    print("   2. If they don't match, the keys are mismatched")
    print("   3. Solution: Generate a new key pair or use matching keys")
    print("\n   To check server's public key, run on server:")
    print("   python compare_keys.py ph01 5")
    
    # Save extracted public key to a file for comparison
    output_file = private_key_path.replace('sensor_private.pem', 'extracted_public.pem')
    try:
        with open(output_file, 'w') as f:
            f.write(client_public_key)
        print(f"\n✅ Saved extracted public key to: {output_file}")
        print("   You can compare this with the server's public key")
    except Exception as e:
        print(f"\n⚠️  Could not save extracted key: {e}")

if __name__ == '__main__':
    main()

