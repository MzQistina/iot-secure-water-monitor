#!/usr/bin/env python3
"""
Simple test to check if HTTPS server can start
"""
import os
import sys

print("Testing HTTPS server startup...")
print("=" * 60)

# Check certificate files
cert_file = 'cert.pem'
key_file = 'key.pem'

if not os.path.exists(cert_file):
    print(f"❌ Certificate file not found: {cert_file}")
    sys.exit(1)

if not os.path.exists(key_file):
    print(f"❌ Key file not found: {key_file}")
    sys.exit(1)

print(f"✓ Certificate files found")
print(f"  - {cert_file}")
print(f"  - {key_file}")

# Try importing app
print("\n[1] Testing app import...")
try:
    from app import app
    print("✓ App imported successfully")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test SSL context
print("\n[2] Testing SSL context...")
try:
    ssl_context = (cert_file, key_file)
    print("✓ SSL context created")
except Exception as e:
    print(f"❌ Failed to create SSL context: {e}")
    sys.exit(1)

# Try to start server
print("\n[3] Starting server...")
print("=" * 60)
print("Server should start now. Press Ctrl+C to stop.")
print("Access: https://localhost:5000")
print("=" * 60)

try:
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        ssl_context=ssl_context,
        use_reloader=False  # Disable reloader to avoid issues
    )
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
except Exception as e:
    print(f"\n❌ Server error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

