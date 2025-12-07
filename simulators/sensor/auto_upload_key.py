import os
import sys
import time
import json
import requests


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    device_id = os.environ.get('DEVICE_ID') or (len(sys.argv) > 1 and sys.argv[1])
    server_url = (os.environ.get('SERVER_URL') or 'http://127.0.0.1:5000').rstrip('/')
    if not device_id:
        print('Usage: DEVICE_ID=<id> SERVER_URL=http://<server>:5000 python simulators/sensor/auto_upload_key.py')
        print('   or: python simulators/sensor/auto_upload_key.py <device_id> [server_url]')
        sys.exit(1)
    
    # Allow server_url as second argument
    if len(sys.argv) > 2:
        server_url = sys.argv[2].rstrip('/')

    # Try multiple possible paths
    possible_paths = [
        os.path.join(project_root, 'sensor_keys', device_id, 'sensor_public.pem'),
        os.path.join('sensor_keys', device_id, 'sensor_public.pem'),
        os.path.join(os.getcwd(), 'sensor_keys', device_id, 'sensor_public.pem'),
    ]
    
    pem_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pem_path = path
            break
    
    if not pem_path:
        print(f"❌ Public key not found!")
        print(f"   Searched in:")
        for path in possible_paths:
            print(f"     - {path}")
        print(f"\n   Make sure the file exists at: sensor_keys/{device_id}/sensor_public.pem")
        sys.exit(1)

    print(f"✅ Found public key at: {pem_path}")
    print(f"[Upload] Uploading public key for device '{device_id}' to {server_url}...")

    try:
        # Obtain token from open endpoint
        print("[Step 1] Getting upload token...")
        token_res = requests.post(f"{server_url}/api/key_upload_token_open", json={"device_id": device_id}, timeout=10)
        if not token_res.ok:
            print(f'❌ Failed to get token: {token_res.status_code} - {token_res.text}')
            print(f"   Check:")
            print(f"   - Server is running at {server_url}")
            print(f"   - Network connectivity")
            sys.exit(1)
        token_json = token_res.json()
        upload_url = token_json.get('upload_url')
        if not upload_url:
            print('❌ No upload_url in token response.')
            sys.exit(1)

        print(f"✅ Token obtained")
        print(f"[Step 2] Uploading key file...")
        
        # Upload the PEM file
        with open(pem_path, 'rb') as f:
            files = {
                'public_key_file': (os.path.basename(pem_path), f, 'application/octet-stream')
            }
            data = {
                'device_id': device_id
            }
            up_res = requests.post(upload_url, data=data, files=files, timeout=15)
        
        if up_res.ok:
            result = up_res.json()
            print(f"✅ SUCCESS! Public key uploaded successfully!")
            print(f"   Response: {result}")
            print(f"\n📝 Next steps:")
            print(f"   1. Go to the sensor registration page")
            print(f"   2. Enter device_id: {device_id}")
            print(f"   3. The key should auto-fill in the textarea")
        else:
            print(f"❌ Upload failed: {up_res.status_code} - {up_res.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: Cannot reach server at {server_url}")
        print(f"   Check:")
        print(f"   - Server is running")
        print(f"   - Network connectivity")
        print(f"   - Server URL is correct")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


