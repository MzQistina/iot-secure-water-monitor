#!/usr/bin/env python3
"""
Verify that a private key matches a public key by testing signature verification.
This helps diagnose if ph01's keys are mismatched.
"""

import sys
import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

def verify_key_match(private_key_path, public_key_path):
    """Test if private key matches public key by signing and verifying."""
    try:
        # Load private key
        if not os.path.exists(private_key_path):
            print(f"❌ Private key not found: {private_key_path}")
            return False
        
        with open(private_key_path, 'rb') as f:
            private_key = RSA.import_key(f.read())
        print(f"✅ Loaded private key from: {private_key_path}")
        
        # Load public key
        if not os.path.exists(public_key_path):
            print(f"❌ Public key not found: {public_key_path}")
            return False
        
        with open(public_key_path, 'rb') as f:
            public_key = RSA.import_key(f.read())
        print(f"✅ Loaded public key from: {public_key_path}")
        
        # Test signature
        test_message = b"test message for verification"
        h = SHA256.new(test_message)
        signature = pkcs1_15.new(private_key).sign(h)
        
        # Verify signature
        try:
            pkcs1_15.new(public_key).verify(h, signature)
            print("\n✅ SUCCESS: Private key matches public key!")
            print("   The keys are a valid pair.")
            return True
        except Exception as e:
            print(f"\n❌ FAILED: Private key does NOT match public key!")
            print(f"   Error: {e}")
            print("\n💡 This means the keys were generated separately.")
            print("   Solution: Generate a new key pair or use matching keys.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python verify_key_match.py <private_key_path> <public_key_path>")
        print("\nExample:")
        print("  python verify_key_match.py sensor_keys/5/ph01/sensor_private.pem user_keys/5/ph01_public.pem")
        sys.exit(1)
    
    private_path = sys.argv[1]
    public_path = sys.argv[2]
    
    print(f"Verifying key match...")
    print(f"  Private key: {private_path}")
    print(f"  Public key: {public_path}\n")
    
    verify_key_match(private_path, public_path)

