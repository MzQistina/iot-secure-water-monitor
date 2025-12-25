"""
Test script to create tampered provision messages for TC-026 testing.

This script:
1. Takes a captured payload (from subscribe_provision_mqtt.py)
2. Creates tampered versions by modifying ciphertext, tag, or nonce
3. Shows how to test tampering detection

Usage:
    python test_tamper_message.py
    
    Or modify the script with your captured payload values.
"""

import json

# ============================================================================
# STEP 1: Replace these values with your captured payload from subscribe_provision_mqtt.py
# ============================================================================
# Run: python subscribe_provision_mqtt.py
# Copy the payload values and paste them below:

original = {
    "session_key": "tmhCXkBZAKsxl2lI3RHGF3c8S4I3f9VRSF68h1xEWNrlylzWxbw0d2Yxyw2kYv8EB91+LuwkhtBsrjIR/KBfAXTgAe07Q4Hyn0Tl9O8T5LabpEq6H23FHYfM6XYpdKy5+H5hYvpysTEjoW+Vh2nIdgetOmkXZ+gZ2MHb3biyawJc4IUTLGyRxBS5udGTWXbA8AJzs3uGxU9+s1bHX1f8F8XNOTnIMTLOhg9fxtO1QFNi3j5isiHpJdEoF+1V/3X2VCLs9+eNNxk8bOONCq6A8NraaKT1S0LIP/BX4tFhRMfLoLTQsdj+Qp+oeUor9mElHkwgwzM8bjH8JLM9JxtszQ==",
  "nonce": "8Ugpkz0qS1VzITxVn2kfNw==",
  "ciphertext": "AUQyvNxsZXQJxZYCIW3YladTGyhuwihGwIhGu2pHXLogMZAGAf/yW9ll4WAo8MHC67sEgX3fzdDPMg==",
  "tag": "PGHyxkilIB0aSnVv2+aB8Q=="
}

# ============================================================================
# STEP 2: Create tampered versions
# ============================================================================

# Option 1: Modify ciphertext (tamper)
tampered = original.copy()
tampered["ciphertext"] = "MODIFIED_CIPHERTEXT_12345"
# The tag will no longer match the modified ciphertext

# Option 2: Modify tag (tamper)
tampered2 = original.copy()
tampered2["tag"] = "MODIFIED_TAG_12345"
# The tag won't match the original ciphertext

# Option 3: Modify nonce (tamper)
tampered3 = original.copy()
tampered3["nonce"] = "MODIFIED_NONCE_12345"
# The nonce won't match the original encryption

# ============================================================================
# STEP 3: Display results
# ============================================================================

print("=" * 70)
print("TAMPERING TEST - Provision Message")
print("=" * 70)

print("\n✅ Tampered messages created")
print(f"Original tag: {original['tag'][:20]}...")
print(f"Tampered ciphertext: {tampered['ciphertext'][:50]}...")
print(f"Tampered tag: {tampered2['tag'][:20]}...")
print(f"Tampered nonce: {tampered3['nonce'][:20]}...")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("1. Use these tampered payloads in Step 4 of TC-026")
print("2. Publish them to test if the system detects tampering")
print("3. Check server logs for decryption/authentication failures")
print("\nExample payloads:")
print(f"\nTampered (ciphertext): {json.dumps(tampered, indent=2)}")
print(f"\nTampered (tag): {json.dumps(tampered2, indent=2)}")
print(f"\nTampered (nonce): {json.dumps(tampered3, indent=2)}")

print("\n" + "=" * 70)
print("NOTE:")
print("=" * 70)
print("For provision messages, the 'tag' field (AES-EAX authentication tag)")
print("will detect any tampering. Any modification to ciphertext, tag, or")
print("nonce will cause decryption to fail.")
