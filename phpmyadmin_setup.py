#!/usr/bin/env python3
"""
Comprehensive phpMyAdmin Setup and Diagnostic Tool
Combines functionality from find_apache_phpmyadmin.py, check_phpmyadmin.py, and configure_apache_phpmyadmin.py

Usage:
    python phpmyadmin_setup.py [--configure] [--check-only]
    
Options:
    --configure    : Automatically configure Apache for phpMyAdmin
    --check-only   : Only run diagnostics without configuring
"""

import subprocess
import socket
import os
import sys
import shutil
import urllib.request
import urllib.error
from datetime import datetime

APACHE_ROOT = r"C:\Apache24"
HTTPD_CONF = os.path.join(APACHE_ROOT, "conf", "httpd.conf")
PHPMYADMIN_PATH = os.path.join(APACHE_ROOT, "htdocs", "phpmyadmin")

def get_apache_path():
    """Get Apache installation path from Windows service."""
    try:
        result = subprocess.run(
            ['sc', 'qc', 'Apache2.4'],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'BINARY_PATH_NAME' in line:
                path = line.split(':', 1)[1].strip().strip('"')
                if '\\bin\\' in path:
                    apache_root = os.path.dirname(os.path.dirname(path))
                    return apache_root
        return None
    except Exception:
        return None

def check_service(service_name):
    """Check if a Windows service is running."""
    try:
        result = subprocess.run(
            ['sc', 'query', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'RUNNING' in result.stdout.upper()
    except Exception:
        return None

def check_port(host, port):
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def find_phpmyadmin(apache_root):
    """Find phpMyAdmin in common locations."""
    if not apache_root:
        return None
    
    common_paths = [
        os.path.join(apache_root, 'htdocs', 'phpmyadmin'),
        os.path.join(apache_root, 'htdocs', 'phpMyAdmin'),
        os.path.join(apache_root, 'www', 'phpmyadmin'),
        os.path.join(apache_root, 'www', 'phpMyAdmin'),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def check_alias_exists():
    """Check if phpMyAdmin alias already exists in httpd.conf."""
    if not os.path.exists(HTTPD_CONF):
        return False, None
    
    try:
        with open(HTTPD_CONF, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if 'Alias /phpmyadmin' in content or 'Alias /phpMyAdmin' in content:
                return True, None
            return False, None
    except Exception:
        return False, None

def backup_httpd_conf():
    """Create a backup of httpd.conf"""
    backup_path = HTTPD_CONF + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(HTTPD_CONF, backup_path)
        print(f"✓ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return False

def configure_apache():
    """Configure Apache for phpMyAdmin."""
    if not os.path.exists(HTTPD_CONF):
        print(f"✗ httpd.conf not found: {HTTPD_CONF}")
        return False
    
    if not backup_httpd_conf():
        response = input("Continue without backup? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        with open(HTTPD_CONF, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if 'Alias /phpmyadmin' in content:
            print("⚠ phpMyAdmin alias already exists. Skipping.")
            return True
        
        config_block = f"""
# phpMyAdmin Configuration - Added automatically
Alias /phpmyadmin "C:/Apache24/htdocs/phpmyadmin"

<Directory "C:/Apache24/htdocs/phpmyadmin">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
"""
        
        with open(HTTPD_CONF, 'a', encoding='utf-8') as f:
            f.write(config_block)
        print("✓ phpMyAdmin configuration added to httpd.conf")
        return True
    except Exception as e:
        print(f"✗ Error configuring Apache: {e}")
        return False

def run_diagnostics():
    """Run comprehensive diagnostics."""
    print("=" * 70)
    print("phpMyAdmin Setup and Diagnostic Tool")
    print("=" * 70)
    
    # Get Apache path
    print("\n[1] Finding Apache Installation...")
    apache_root = get_apache_path()
    if apache_root:
        print(f"  ✓ Apache found at: {apache_root}")
        global APACHE_ROOT, HTTPD_CONF, PHPMYADMIN_PATH
        APACHE_ROOT = apache_root
        HTTPD_CONF = os.path.join(APACHE_ROOT, "conf", "httpd.conf")
        PHPMYADMIN_PATH = os.path.join(APACHE_ROOT, "htdocs", "phpmyadmin")
    else:
        print("  ✗ Could not determine Apache path automatically")
        print(f"  → Using default: {APACHE_ROOT}")
    
    # Check services
    print("\n[2] Checking Services...")
    apache_running = check_service('Apache2.4') or check_service('Apache')
    mysql_running = check_service('MySQL') or check_service('MariaDB')
    
    if apache_running:
        print("  ✓ Apache service is RUNNING")
    else:
        print("  ✗ Apache service is NOT running")
        print("  → Start Apache: net start Apache2.4 (as Administrator)")
    
    if mysql_running:
        print("  ✓ MySQL/MariaDB service is RUNNING")
    else:
        print("  ✗ MySQL/MariaDB service is NOT running")
        print("  → Start MySQL service first")
    
    # Check ports
    print("\n[3] Checking Ports...")
    port_80_open = check_port('localhost', 80)
    port_3306_open = check_port('localhost', 3306)
    
    if port_80_open:
        print("  ✓ Port 80 is OPEN (Apache is listening)")
    else:
        print("  ✗ Port 80 is CLOSED")
    
    if port_3306_open:
        print("  ✓ Port 3306 is OPEN (MySQL is accessible)")
    else:
        print("  ✗ Port 3306 is CLOSED (MySQL not accessible)")
    
    # Check phpMyAdmin installation
    print("\n[4] Checking phpMyAdmin Installation...")
    phpmyadmin_path = find_phpmyadmin(APACHE_ROOT)
    if phpmyadmin_path:
        print(f"  ✓ phpMyAdmin found at: {phpmyadmin_path}")
        config_file = os.path.join(phpmyadmin_path, 'config.inc.php')
        if os.path.exists(config_file):
            print(f"  ✓ config.inc.php exists")
        else:
            print(f"  ⚠ config.inc.php missing")
    else:
        print("  ✗ phpMyAdmin not found")
        print(f"  → Expected location: {PHPMYADMIN_PATH}")
        print("  → Download from: https://www.phpmyadmin.net/downloads/")
    
    # Check Apache configuration
    print("\n[5] Checking Apache Configuration...")
    has_alias, _ = check_alias_exists()
    if has_alias:
        print("  ✓ phpMyAdmin alias found in httpd.conf")
    else:
        print("  ✗ phpMyAdmin alias NOT found in httpd.conf")
    
    # Test URLs
    print("\n[6] Testing phpMyAdmin URLs...")
    if port_80_open:
        for url in ['http://localhost/phpmyadmin', 'http://127.0.0.1/phpmyadmin']:
            try:
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'Mozilla/5.0')
                with urllib.request.urlopen(req, timeout=3) as response:
                    status = response.getcode()
                    if status in (200, 302, 401):
                        print(f"  ✓ {url} - Accessible (HTTP {status})")
                    else:
                        print(f"  ? {url} - Responds but status {status}")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print(f"  ✗ {url} - Not Found (404)")
                else:
                    print(f"  ? {url} - HTTP Error {e.code}")
            except Exception:
                print(f"  ✗ {url} - Connection refused")
    
    print("\n" + "=" * 70)
    return apache_running, mysql_running, phpmyadmin_path, has_alias

def main():
    import argparse
    parser = argparse.ArgumentParser(description='phpMyAdmin Setup and Diagnostic Tool')
    parser.add_argument('--configure', action='store_true', help='Automatically configure Apache')
    parser.add_argument('--check-only', action='store_true', help='Only run diagnostics')
    args = parser.parse_args()
    
    apache_running, mysql_running, phpmyadmin_path, has_alias = run_diagnostics()
    
    if args.check_only:
        print("\n✓ Diagnostics complete (check-only mode)")
        return
    
    if not phpmyadmin_path:
        print("\n⚠ Please install phpMyAdmin first, then run this script again.")
        return
    
    if has_alias:
        print("\n✓ Apache is already configured for phpMyAdmin!")
        print("  → Access at: http://localhost/phpmyadmin")
        if not apache_running:
            print("\n⚠ Apache service is not running. Start it to use phpMyAdmin.")
        return
    
    if args.configure:
        print("\n[7] Configuring Apache...")
        if configure_apache():
            print("\n✓ Configuration added successfully!")
            print("\nNext Steps:")
            print("  1. Restart Apache: Restart-Service Apache2.4 (as Administrator)")
            print("  2. Access phpMyAdmin: http://localhost/phpmyadmin")
        else:
            print("\n✗ Failed to configure Apache")
            print("  → You may need to run as Administrator")
    else:
        print("\n⚠ phpMyAdmin is not configured in Apache.")
        print("  → Run with --configure flag to automatically configure:")
        print("     python phpmyadmin_setup.py --configure")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()

