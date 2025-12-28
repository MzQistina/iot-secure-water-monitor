"""Device session utilities."""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from db import (
    get_device_session,
    delete_device_session,
    update_device_session,
)

# Device session configuration (imported from app.py or set here)
DEVICE_SESSION_TTL_SECONDS = 900  # 15 minutes
DEVICE_CHALLENGE_TTL_SECONDS = 60  # 1 minute


def _issue_device_challenge(device_id: str, device_challenges_dict: dict):
    """Issue a challenge for device authentication.
    
    Args:
        device_id: The device identifier
        device_challenges_dict: Dictionary to store challenges (passed from app.py)
    
    Returns:
        tuple: (challenge_id, challenge)
    """
    challenge_id = secrets.token_urlsafe(16)
    challenge = secrets.token_urlsafe(32)
    device_challenges_dict[challenge_id] = {
        'device_id': device_id,
        'challenge': challenge,
        'expires_at': datetime.utcnow() + timedelta(seconds=DEVICE_CHALLENGE_TTL_SECONDS),
    }
    return challenge_id, challenge


def _validate_device_session(session_token: Optional[str], device_id: Optional[str], counter_value):
    """Validate device session from database. Returns (is_valid, reason)."""
    if not session_token:
        return False, "missing_session"
    
    # Get session from database
    sess = get_device_session(session_token)
    if not sess:
        return False, "invalid_session"
    
    # Check device match
    if not device_id or sess.get('device_id') != device_id:
        return False, "device_mismatch"
    
    # Check expiration (handle both datetime object and string)
    expires_at = sess.get('expires_at')
    if not isinstance(expires_at, datetime):
        if isinstance(expires_at, str):
            try:
                # Try multiple formats
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                    try:
                        expires_at = datetime.strptime(expires_at, fmt)
                        break
                    except ValueError:
                        continue
                if isinstance(expires_at, str):
                    expires_at = datetime.utcnow()
            except Exception:
                expires_at = datetime.utcnow()
        else:
            expires_at = datetime.utcnow()
    
    if datetime.utcnow() > expires_at:
        # Clean up expired session
        try:
            delete_device_session(session_token)
        except Exception:
            pass
        return False, "session_expired"
    
    # Validate counter if provided
    if counter_value is not None:
        try:
            cval = int(counter_value)
        except Exception:
            return False, "counter_invalid"
        last = int(sess.get('counter') or 0)
        if cval <= last:
            return False, "counter_reused"
        
        # Update session with new counter and sliding expiration
        # Pass TTL seconds instead of datetime to ensure timezone consistency with MySQL NOW()
        update_device_session(session_token, cval, DEVICE_SESSION_TTL_SECONDS)
    else:
        # Still update expiration on use (sliding expiration)
        # Pass TTL seconds instead of datetime to ensure timezone consistency with MySQL NOW()
        update_device_session(session_token, sess.get('counter', 0), DEVICE_SESSION_TTL_SECONDS)
    
    return True, "ok"

