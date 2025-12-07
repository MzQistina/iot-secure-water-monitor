"""
Production-safe database encryption utilities for sensor data.

This module provides symmetric encryption (Fernet) for encrypting sensor values
before storing them in the database and decrypting them when retrieving.

Key Management:
- Encryption key is loaded from environment variable DB_ENCRYPTION_KEY
- If not set, a key file is used (DB_ENCRYPTION_KEY_FILE)
- Keys are 32-byte base64-encoded Fernet keys
- For production, generate a key using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class DatabaseEncryption:
    """Handles encryption/decryption of sensor data for database storage."""
    
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize Fernet cipher with key from environment or key file."""
        key = self._get_encryption_key()
        if key:
            try:
                self._fernet = Fernet(key)
            except Exception as e:
                raise ValueError(f"Invalid encryption key format: {e}")
        else:
            raise ValueError(
                "DB_ENCRYPTION_KEY or DB_ENCRYPTION_KEY_FILE environment variable must be set. "
                "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Get encryption key from environment variable or key file.
        
        Returns:
            bytes: Fernet key as bytes, or None if not found
        """
        # Try environment variable first (preferred for production)
        key_str = os.environ.get('DB_ENCRYPTION_KEY')
        if key_str:
            try:
                return key_str.encode('utf-8')
            except Exception as e:
                print(f"WARNING: Invalid DB_ENCRYPTION_KEY format: {e}")
        
        # Try key file (fallback)
        key_file = os.environ.get('DB_ENCRYPTION_KEY_FILE', 'db_encryption.key')
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"WARNING: Could not read key file {key_file}: {e}")
        
        return None
    
    def encrypt_value(self, value: Optional[float]) -> Optional[str]:
        """
        Encrypt a sensor value (float) for database storage.
        
        Args:
            value: The sensor reading value (float) or None
            
        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if value is None:
            return None
        
        try:
            # Convert float to string, then to bytes
            value_str = str(value)
            encrypted_bytes = self._fernet.encrypt(value_str.encode('utf-8'))
            # Return base64-encoded string for database storage
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Encryption failed for value {value}: {e}")
    
    def decrypt_value(self, encrypted_str: Optional[str]) -> Optional[float]:
        """
        Decrypt a sensor value from database storage.
        
        Args:
            encrypted_str: Base64-encoded encrypted string from database, or None
            
        Returns:
            Decrypted float value, or None if input is None or decryption fails
        """
        if encrypted_str is None or encrypted_str == '':
            return None
        
        try:
            # Decode base64, then decrypt
            encrypted_bytes = base64.b64decode(encrypted_str.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            # Convert back to float
            return float(decrypted_str)
        except Exception as e:
            # If decryption fails, try to handle legacy unencrypted data
            # This allows gradual migration
            try:
                return float(encrypted_str)
            except (ValueError, TypeError):
                print(f"WARNING: Failed to decrypt value (may be legacy data): {e}")
                return None
    
    def encrypt_dict_values(self, data_dict: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data_dict: Dictionary containing sensor data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            New dictionary with encrypted values
        """
        result = data_dict.copy()
        for field in fields_to_encrypt:
            if field in result:
                result[field] = self.encrypt_value(result[field])
        return result
    
    def decrypt_dict_values(self, data_dict: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data_dict: Dictionary containing encrypted sensor data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            New dictionary with decrypted values
        """
        result = data_dict.copy()
        for field in fields_to_decrypt:
            if field in result:
                result[field] = self.decrypt_value(result[field])
        return result


# Global instance for use across the application
_db_encryption: Optional[DatabaseEncryption] = None


def get_db_encryption() -> DatabaseEncryption:
    """
    Get or create the global database encryption instance.
    
    Returns:
        DatabaseEncryption: Singleton instance
    """
    global _db_encryption
    if _db_encryption is None:
        _db_encryption = DatabaseEncryption()
    return _db_encryption


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Returns:
        Base64-encoded key string (safe to store in environment variable)
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')


# Convenience functions for direct use
def encrypt_sensor_value(value: Optional[float]) -> Optional[str]:
    """Encrypt a sensor value."""
    return get_db_encryption().encrypt_value(value)


def decrypt_sensor_value(encrypted_str: Optional[str]) -> Optional[float]:
    """Decrypt a sensor value."""
    return get_db_encryption().decrypt_value(encrypted_str)


