"""
Input validation utilities for the water monitoring application.
Provides functions to validate user inputs and sanitize data.
"""
import re
from typing import Optional, Tuple


# Email validation regex (RFC 5322 compliant, simplified)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Username validation: alphanumeric, underscore, hyphen, 3-150 chars
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,150}$')

# Device ID validation: alphanumeric, underscore, hyphen, dot, 3-100 chars
DEVICE_ID_REGEX = re.compile(r'^[a-zA-Z0-9_.-]{3,100}$')

# Location validation: alphanumeric, spaces, common punctuation, 1-255 chars
LOCATION_REGEX = re.compile(r'^[a-zA-Z0-9\s.,\-_()]{1,255}$')

# Public key PEM format validation (basic check)
PEM_PUBLIC_KEY_REGEX = re.compile(
    r'^-----BEGIN PUBLIC KEY-----\s*\n.*?\n-----END PUBLIC KEY-----\s*$',
    re.DOTALL | re.MULTILINE
)


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required."
    
    email = email.strip()
    
    if len(email) > 255:
        return False, "Email must be 255 characters or less."
    
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format. Please enter a valid email address."
    
    # Additional checks
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol."
    
    if email.startswith('.') or email.startswith('@') or email.endswith('.') or email.endswith('@'):
        return False, "Email cannot start or end with . or @"
    
    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required."
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    
    if len(username) > 150:
        return False, "Username must be 150 characters or less."
    
    if not USERNAME_REGEX.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens."
    
    # Username cannot start or end with underscore or hyphen
    if username.startswith('_') or username.startswith('-') or username.endswith('_') or username.endswith('-'):
        return False, "Username cannot start or end with underscore or hyphen."
    
    return True, None


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum password length (default: 8)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required."
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters."
    
    if len(password) > 128:
        return False, "Password must be 128 characters or less."
    
    # Check for at least one letter and one number (basic strength requirement)
    has_letter = re.search(r'[a-zA-Z]', password)
    has_number = re.search(r'[0-9]', password)
    
    if not has_letter:
        return False, "Password must contain at least one letter."
    
    if not has_number:
        return False, "Password must contain at least one number."
    
    # Check for common weak passwords
    weak_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
    if password.lower() in weak_passwords:
        return False, "Password is too common. Please choose a stronger password."
    
    return True, None


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate full name.
    
    Args:
        name: Name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Name is required."
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    
    if len(name) > 255:
        return False, "Name must be 255 characters or less."
    
    # Allow letters, spaces, hyphens, apostrophes, and periods
    if not re.match(r'^[a-zA-Z\s\'-.]{2,255}$', name):
        return False, "Name can only contain letters, spaces, hyphens, apostrophes, and periods."
    
    # Name cannot be all spaces
    if name.replace(' ', '').replace('-', '').replace("'", '').replace('.', '') == '':
        return False, "Name cannot be empty."
    
    return True, None


def validate_device_id(device_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate device ID format.
    
    Args:
        device_id: Device ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not device_id:
        return False, "Device ID is required."
    
    device_id = device_id.strip()
    
    if len(device_id) < 3:
        return False, "Device ID must be at least 3 characters."
    
    if len(device_id) > 100:
        return False, "Device ID must be 100 characters or less."
    
    if not DEVICE_ID_REGEX.match(device_id):
        return False, "Device ID can only contain letters, numbers, underscores, hyphens, and dots."
    
    # Device ID cannot start or end with special characters
    if device_id.startswith(('.', '_', '-')) or device_id.endswith(('.', '_', '-')):
        return False, "Device ID cannot start or end with a dot, underscore, or hyphen."
    
    return True, None


def validate_location(location: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate location string.
    
    Args:
        location: Location to validate (can be None/empty)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not location:
        return True, None  # Location is optional
    
    location = location.strip()
    
    if len(location) > 255:
        return False, "Location must be 255 characters or less."
    
    if not LOCATION_REGEX.match(location):
        return False, "Location contains invalid characters. Use only letters, numbers, spaces, and common punctuation."
    
    # Location cannot be all spaces or special characters
    if location.replace(' ', '').replace('.', '').replace(',', '').replace('-', '').replace('_', '').replace('(', '').replace(')', '') == '':
        return False, "Location cannot be empty."
    
    return True, None


def validate_public_key(public_key: Optional[str], required: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate public key PEM format.
    
    Args:
        public_key: Public key to validate (can be None/empty)
        required: Whether public key is required
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not public_key:
        if required:
            return False, "Public key is required."
        return True, None
    
    public_key = public_key.strip()
    
    if len(public_key) < 50:
        return False, "Public key appears to be too short."
    
    if len(public_key) > 10000:
        return False, "Public key appears to be too long."
    
    # Check for PEM format markers
    if '-----BEGIN PUBLIC KEY-----' not in public_key:
        return False, "Public key must be in PEM format (must contain '-----BEGIN PUBLIC KEY-----')."
    
    if '-----END PUBLIC KEY-----' not in public_key:
        return False, "Public key must be in PEM format (must contain '-----END PUBLIC KEY-----')."
    
    # Basic PEM structure check
    if not PEM_PUBLIC_KEY_REGEX.match(public_key):
        return False, "Public key format is invalid. Please ensure it's a valid PEM-formatted public key."
    
    return True, None


def validate_threshold(value: Optional[str], min_val: Optional[float] = None, max_val: Optional[float] = None) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate threshold value.
    
    Args:
        value: Threshold value as string (can be None/empty)
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        
    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    if not value or value.strip() == '':
        return True, None, None  # Thresholds are optional
    
    value = value.strip()
    
    try:
        float_val = float(value)
    except ValueError:
        return False, None, "Threshold must be a valid number."
    
    # Check reasonable bounds for sensor readings
    if float_val < -1000 or float_val > 10000:
        return False, None, "Threshold value is out of reasonable range (-1000 to 10000)."
    
    # Check against min/max constraints if provided
    if min_val is not None and float_val < min_val:
        return False, None, f"Threshold must be at least {min_val}."
    
    if max_val is not None and float_val > max_val:
        return False, None, f"Threshold must be at most {max_val}."
    
    return True, float_val, None


def validate_status(status: str) -> Tuple[bool, Optional[str]]:
    """
    Validate sensor status.
    
    Args:
        status: Status to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not status:
        return False, "Status is required."
    
    status = status.strip().lower()
    
    allowed_statuses = ['active', 'inactive']
    if status not in allowed_statuses:
        return False, f"Status must be one of: {', '.join(allowed_statuses)}."
    
    return True, None


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    Removes or escapes potentially dangerous characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (truncates if exceeded)
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Remove potential SQL injection patterns (basic protection)
    # Note: This is a secondary defense - parameterized queries are primary protection
    sql_patterns = [
        r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+',  # OR 1=1, AND 1=1
        r'(\bOR\b|\bAND\b)\s+[\'"]\s*=\s*[\'"]',  # OR ''=''
        r'UNION\s+SELECT',  # UNION SELECT
        r';\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)',  # ; DROP TABLE
        r'/\*.*?\*/',  # SQL comments
        r'--\s',  # SQL comments
        r'EXEC\s*\(',  # EXEC(
        r'EXECUTE\s*\(',  # EXECUTE(
    ]
    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove potential XSS patterns
    xss_patterns = [
        r'<script[^>]*>.*?</script>',  # <script> tags
        r'javascript:',  # javascript: protocol
        r'on\w+\s*=',  # onclick=, onerror=, etc.
        r'<iframe[^>]*>',  # <iframe> tags
        r'<object[^>]*>',  # <object> tags
        r'<embed[^>]*>',  # <embed> tags
        r'<link[^>]*>',  # <link> tags
        r'<meta[^>]*>',  # <meta> tags
        r'<style[^>]*>.*?</style>',  # <style> tags
        r'expression\s*\(',  # CSS expression()
        r'vbscript:',  # vbscript: protocol
        r'data:text/html',  # data: URLs with HTML
    ]
    for pattern in xss_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Trim whitespace
    text = text.strip()
    
    # Truncate if max_length specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS attacks.
    This should be used when rendering user input in HTML templates.
    
    Note: Flask templates auto-escape by default, but this can be used
    for programmatic HTML generation.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    
    # Escape HTML special characters
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    text = text.replace('/', '&#x2F;')
    
    return text


def validate_device_type(device_type: str, allowed_types: Optional[list] = None) -> Tuple[bool, Optional[str], str]:
    """
    Validate device type.
    
    Args:
        device_type: Device type to validate
        allowed_types: List of allowed device types (optional)
        
    Returns:
        Tuple of (is_valid, error_message, normalized_device_type)
        normalized_device_type has spaces converted to underscores
    """
    if not device_type:
        return False, "Device type is required.", ""
    
    device_type = device_type.strip()
    
    # Normalize: convert spaces to underscores
    normalized_device_type = device_type.replace(' ', '_')
    
    if len(normalized_device_type) > 100:
        return False, "Device type must be 100 characters or less.", normalized_device_type
    
    # Basic format check: alphanumeric, underscore, hyphen (after normalization)
    if not re.match(r'^[a-zA-Z0-9_-]+$', normalized_device_type):
        return False, "Device type can only contain letters, numbers, underscores, and hyphens.", normalized_device_type
    
    # Check against allowed types if provided
    if allowed_types:
        if normalized_device_type.lower() not in [t.lower() for t in allowed_types]:
            return False, f"Device type must be one of: {', '.join(allowed_types)}.", normalized_device_type
    
    return True, None, normalized_device_type

