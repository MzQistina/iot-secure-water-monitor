#!/usr/bin/env python3
"""
Run Flask app with HTTPS on localhost
"""
import os
import sys

def main():
    # Check if certificate files exist
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("❌ SSL certificate files not found!")
        print("\nGenerating certificate...")
        import generate_ssl_cert
        if not generate_ssl_cert.generate_certificate():
            print("\n❌ Failed to generate certificate. Exiting.")
            sys.exit(1)
        print()
    
    # Set environment variables
    os.environ.setdefault('FLASK_APP', 'app.py')
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # Import Flask app
    from app import app, start_mqtt_key_subscriber
    
    # Start MQTT subscriber
    try:
        start_mqtt_key_subscriber()
        print("✓ MQTT key subscriber started")
    except Exception as e:
        print(f"⚠ MQTT subscriber error (non-fatal): {e}")
    
    # Run with HTTPS
    print("\n" + "=" * 60)
    print("Starting Flask with HTTPS...")
    print("=" * 60)
    print(f"Certificate: {cert_file}")
    print(f"Private Key: {key_file}")
    print("\n🌐 Access your app at:")
    print("   https://localhost:5000")
    print("   https://127.0.0.1:5000")
    print("\n⚠️  Browser will show security warning (normal for self-signed cert)")
    print("   Click 'Advanced' → 'Proceed to localhost'")
    print("=" * 60 + "\n")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        ssl_context=(cert_file, key_file)
    )

if __name__ == '__main__':
    main()

