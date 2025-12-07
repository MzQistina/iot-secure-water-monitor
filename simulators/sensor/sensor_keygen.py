import os
import sys
import stat
from typing import Tuple, Optional
from Crypto.PublicKey import RSA

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SENSOR_KEYS_DIR = os.path.join(PROJECT_ROOT, "sensor_keys")


def generate_sensor_keys(sensor_id: str, user_id: Optional[str] = None) -> Tuple[str, str]:
    """Generate sensor keys, optionally organized by user folder.
    
    Args:
        sensor_id: Device/sensor ID
        user_id: Optional user ID to organize keys in user-specific folder
    
    Returns:
        Tuple of (private_key_path, public_key_path)
    """
    os.makedirs(SENSOR_KEYS_DIR, exist_ok=True)
    key = RSA.generate(2048)

    # Create folder structure: sensor_keys/{user_id}/{sensor_id}/ or sensor_keys/{sensor_id}/
    if user_id:
        user_dir = os.path.join(SENSOR_KEYS_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        sensor_dir = os.path.join(user_dir, sensor_id)
    else:
        sensor_dir = os.path.join(SENSOR_KEYS_DIR, sensor_id)
    
    os.makedirs(sensor_dir, exist_ok=True)

    private_path = os.path.join(sensor_dir, "sensor_private.pem")
    public_path = os.path.join(sensor_dir, "sensor_public.pem")

    with open(private_path, "wb") as f:
        f.write(key.export_key())

    with open(public_path, "wb") as f:
        f.write(key.publickey().export_key())

    # Automatically set secure file permissions
    # Private key: 600 (read/write owner only)
    os.chmod(private_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    
    # Public key: 644 (read/write owner, read others)
    os.chmod(public_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0o644
    
    # Optional: Restrict directory access to owner only (700)
    os.chmod(sensor_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0o700

    if user_id:
        print(f"Generated sensor keys for '{sensor_id}' (user: {user_id}) at {sensor_dir}")
    else:
        print(f"Generated sensor keys for '{sensor_id}' at {sensor_dir}")
    return private_path, public_path


if __name__ == "__main__":
    # CLI: python simulators/sensor/sensor_keygen.py SENSOR_ID [USER_ID]
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python simulators/sensor/sensor_keygen.py <sensor_id> [user_id]")
        print("  sensor_id: Device/sensor ID (required)")
        print("  user_id: User ID for organizing keys in user folder (optional)")
        sys.exit(1)
    
    sensor_id = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) == 3 else None
    generate_sensor_keys(sensor_id, user_id)


