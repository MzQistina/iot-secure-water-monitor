#!/usr/bin/env python3
"""
Compare the public key extracted from Raspberry Pi with server's stored keys.
"""

import sys
import os

def read_key_file(filepath):
    """Read and normalize a key file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return f.read().strip()

def compare_keys(key1, key2, name1, name2):
    """Compare two keys and report if they match."""
    if key1 is None:
        print(f"❌ {name1} not found")
        return False
    if key2 is None:
        print(f"❌ {name2} not found")
        return False
    
    key1_norm = key1.strip()
    key2_norm = key2.strip()
    
    if key1_norm == key2_norm:
        print(f"✅ MATCH: {name1} matches {name2}")
        return True
    else:
        print(f"❌ MISMATCH: {name1} does NOT match {name2}")
        print(f"   {name1} length: {len(key1_norm)} chars")
        print(f"   {name2} length: {len(key2_norm)} chars")
        print(f"   {name1} first 50: {key1_norm[:50]}...")
        print(f"   {name2} first 50: {key2_norm[:50]}...")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_with_pi_key.py <extracted_public_key_file>")
        print("\nExample:")
        print("  python compare_with_pi_key.py sensor_keys/5/ph01/extracted_public.pem")
        print("\nOr provide the key content directly:")
        print("  python compare_with_pi_key.py <path_to_pi_extracted_key>")
        sys.exit(1)
    
    pi_key_file = sys.argv[1]
    
    if not os.path.exists(pi_key_file):
        print(f"❌ File not found: {pi_key_file}")
        print("\n💡 On Raspberry Pi, run:")
        print("   python3 verify_key_pair.py sensor_keys/5/ph01/sensor_private.pem")
        print("   Then copy sensor_keys/5/ph01/extracted_public.pem to the server")
        sys.exit(1)
    
    print(f"Reading Pi's extracted public key from: {pi_key_file}\n")
    pi_key = read_key_file(pi_key_file)
    
    if not pi_key:
        print(f"❌ Could not read key from {pi_key_file}")
        sys.exit(1)
    
    print(f"✅ Pi's extracted key: {len(pi_key)} characters\n")
    
    # Compare with user_keys file
    user_keys_file = "user_keys/5/ph01_public.pem"
    user_keys_key = read_key_file(user_keys_file)
    
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    matches_user_keys = compare_keys(pi_key, user_keys_key, "Pi extracted key", f"user_keys/5/ph01_public.pem")
    
    # Compare with legacy sensor_keys file
    legacy_file = "sensor_keys/ph01/sensor_public.pem"
    legacy_key = read_key_file(legacy_file)
    
    if legacy_key:
        matches_legacy = compare_keys(pi_key, legacy_key, "Pi extracted key", f"sensor_keys/ph01/sensor_public.pem")
    else:
        print(f"ℹ️  Legacy file not found: {legacy_file}")
        matches_legacy = False
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if matches_user_keys:
        print("✅ Pi's private key MATCHES user_keys/5/ph01_public.pem")
        print("   The keys are correct!")
        print("\n⚠️  However, the database might have a different key.")
        print("   Solution: Update the database with the correct public key:")
        print("   1. Use the web interface to edit ph01 sensor")
        print("   2. Upload the public key from user_keys/5/ph01_public.pem")
    elif matches_legacy:
        print("✅ Pi's private key MATCHES legacy sensor_keys/ph01/sensor_public.pem")
        print("   But does NOT match user_keys file.")
        print("   Solution: Copy the legacy key to user_keys or update database")
    else:
        print("❌ Pi's private key does NOT match any server public keys!")
        print("   This confirms the key mismatch issue.")
        print("\n💡 Solution:")
        print("   1. Generate a new matching key pair")
        print("   2. Update the public key on the server")
        print("   3. Update the private key on the Raspberry Pi")

if __name__ == '__main__':
    main()

