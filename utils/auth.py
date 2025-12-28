"""Authentication utilities including login_required decorator."""
import sys
import traceback
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from db import get_user_by_username


def login_required(view_func):
    """
    Decorator to require user login for a route.
    Handles session validation, user_id verification, and redirects.
    """
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        import sys
        import traceback
        try:
            # Check session
            username = session.get('user')
            user_id = session.get('user_id')
            
            # Only log for provision endpoints to reduce noise
            if '/provision/' in request.path:
                print(f"[login_required] Checking auth for {request.path} - username: {username}, user_id: {user_id}", file=sys.stderr)
                sys.stderr.flush()
            
            if not username:
                # For API endpoints, return JSON instead of redirect
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication required", "message": "Please log in to access this resource"}), 401
                next_url = request.path
                return redirect(url_for('login', next=next_url))
            
            # Ensure user_id is set in session (critical for user isolation)
            if not user_id:
                user = get_user_by_username(username)
                if user:
                    session['user_id'] = user['sr_no']
                    session.permanent = True  # Make session persistent
                    if '/provision/' in request.path:
                        print(f"[login_required] Set user_id {user['sr_no']} for username {username}", file=sys.stderr)
                        sys.stderr.flush()
                else:
                    if '/provision/' in request.path:
                        print(f"[login_required] ERROR: User '{username}' not found in database!", file=sys.stderr)
                        sys.stderr.flush()
                    session.clear()  # Clear invalid session
                    # For API endpoints, return JSON instead of redirect
                    if request.path.startswith('/api/'):
                        return jsonify({"error": "Invalid session", "message": "User not found in database"}), 401
                    return redirect(url_for('login'))
            
            # Double-check: verify user_id matches username (security check)
            if user_id:
                user = get_user_by_username(username)
                if user and user['sr_no'] != user_id:
                    if '/provision/' in request.path:
                        print(f"[login_required] ERROR: Session mismatch! username={username}, session_user_id={user_id}, db_user_id={user['sr_no']}", file=sys.stderr)
                        sys.stderr.flush()
                    session.clear()  # Clear corrupted session
                    # For API endpoints, return JSON instead of redirect
                    if request.path.startswith('/api/'):
                        return jsonify({"error": "Session mismatch", "message": "Session validation failed"}), 401
                    return redirect(url_for('login'))
            
            # Call the actual view function
            if '/provision/' in request.path:
                print(f"[login_required] ✅ Auth passed, calling view function for {request.path}", file=sys.stderr)
                sys.stderr.flush()
            try:
                result = view_func(*args, **kwargs)
                if '/provision/' in request.path:
                    print(f"[login_required] ✅ View function returned successfully", file=sys.stderr)
                    sys.stderr.flush()
                return result
            except Exception as view_exc:
                if '/provision/' in request.path:
                    print(f"[login_required] ❌ Exception in view function: {view_exc}", file=sys.stderr)
                    print(f"[login_required] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
                    sys.stderr.flush()
                raise  # Re-raise to be handled by global error handler
        except Exception as e:
            # Catch any exception in the decorator itself
            error_msg = f"Exception in login_required decorator: {str(e)}"
            print("=" * 80, file=sys.stderr)
            print(f"[login_required] ❌ {error_msg}", file=sys.stderr)
            print(f"[login_required] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            sys.stderr.flush()
            # Re-raise to be caught by global error handler
            raise
    # Preserve original function name for Flask routing/debug
    wrapped_view.__name__ = getattr(view_func, '__name__', 'wrapped_view')
    return wrapped_view

