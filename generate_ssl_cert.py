#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for localhost HTTPS
"""
import subprocess
import sys
import os

def generate_certificate():
    """Generate self-signed SSL certificate for localhost"""
    
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    # Check if OpenSSL is available
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        print(f"✓ Found OpenSSL: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL not found!")
        print("\nPlease install OpenSSL:")
        print("1. Download from: https://slproweb.com/products/Win32OpenSSL.html")
        print("2. Or use Git Bash (includes OpenSSL)")
        print("3. Or use this alternative method:")
        print("\n   Using Python cryptography library...")
        return generate_certificate_python()
    
    # Generate certificate using OpenSSL
    print("\n🔐 Generating self-signed SSL certificate...")
    print(f"   Certificate: {cert_file}")
    print(f"   Private Key: {key_file}")
    
    try:
        # Generate private key and certificate in one command
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-nodes', '-out', cert_file, '-keyout', key_file,
            '-days', '365',
            '-subj', '/CN=localhost'
        ], check=True)
        
        print("✅ Certificate generated successfully!")
        print(f"\n📁 Files created:")
        print(f"   - {os.path.abspath(cert_file)}")
        print(f"   - {os.path.abspath(key_file)}")
        print("\n🚀 You can now use these files with Flask or Apache")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificate: {e}")
        return False

def generate_certificate_python():
    """Generate certificate using Python cryptography library"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        
        print("\n🔐 Generating self-signed SSL certificate using Python...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        cert_file = 'cert.pem'
        key_file = 'key.pem'
        
        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("✅ Certificate generated successfully!")
        print(f"\n📁 Files created:")
        print(f"   - {os.path.abspath(cert_file)}")
        print(f"   - {os.path.abspath(key_file)}")
        return True
        
    except ImportError:
        print("❌ cryptography library not installed!")
        print("\nInstall it with:")
        print("   pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("SSL Certificate Generator for Localhost HTTPS")
    print("=" * 60)
    
    if generate_certificate():
        print("\n" + "=" * 60)
        print("Next steps:")
        print("=" * 60)
        print("1. Flask: flask run --cert=cert.pem --key=key.pem")
        print("2. Or use: python run_https.py")
        print("3. Access: https://localhost:5000")
        print("\n⚠️  Note: Browser will show security warning (normal for self-signed cert)")
    else:
        sys.exit(1)

