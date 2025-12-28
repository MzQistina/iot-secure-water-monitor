"""Dashboard routes: landing, dashboard, readings, history, profile."""
from flask import render_template, redirect, url_for, session, flash, request
from db import get_user_by_username, get_locations_with_status, list_recent_sensor_data, get_pool, _get_connection, _get_cursor, _return_connection
from utils.auth import login_required


def register_dashboard_routes(app, user_latest_by_metric):
    """Register dashboard routes with the Flask app.
    
    Args:
        app: Flask application instance
        user_latest_by_metric: Global dict for real-time metrics (user_id -> metric_name -> data)
    """
    
    @app.route('/')
    def landing():
        return render_template('landing.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        import sys
        # Get current user ID (should be set by login_required decorator)
        user_id = session.get('user_id')
        username = session.get('user')
        
        print(f"DEBUG: dashboard - username: {username}, user_id: {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        if not user_id:
            print("ERROR: dashboard - user_id not found in session!", file=sys.stderr)
            sys.stderr.flush()
            flash('User session not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # SECURITY: Verify user_id matches username (prevent session hijacking)
        if username:
            user = get_user_by_username(username)
            if user and user['sr_no'] != user_id:
                print(f"ERROR: dashboard - Session mismatch! username={username}, session_user_id={user_id}, db_user_id={user['sr_no']}", file=sys.stderr)
                sys.stderr.flush()
                session.clear()
                flash('Session error. Please log in again.', 'error')
                return redirect(url_for('login'))
        
        # Get locations that belong to this user ONLY
        print(f"DEBUG: dashboard - Calling get_locations_with_status for user_id {user_id}", file=sys.stderr)
        sys.stderr.flush()
        
        # Get real-time metrics if available (same as live readings uses)
        # Structure: user_latest_by_metric[user_id][metric_name] = {'value': val, 'sensor_id': device_id}
        # We need to pass this to get_locations_with_status so it can filter by location
        realtime_metrics_data = None
        if user_id and user_id in user_latest_by_metric:
            realtime_metrics_data = user_latest_by_metric[user_id]
        
        locations_data = get_locations_with_status(user_id=user_id, realtime_metrics_data=realtime_metrics_data)
        
        print(f"DEBUG: dashboard - Found {len(locations_data)} locations for user_id {user_id} (username: {username})", file=sys.stderr)
        for loc in locations_data:
            print(f"DEBUG: dashboard - Location: {loc.get('location')}, Safe: {loc.get('safe')}, Sensors: {loc.get('sensor_count')}", file=sys.stderr)
        sys.stderr.flush()
        
        # If no locations, check why
        if not locations_data:
            print(f"WARNING: dashboard - No locations found for user_id {user_id}!", file=sys.stderr)
            # Check if user has sensors
            pool = get_pool()
            if pool:
                conn = _get_connection(pool)
                cur = _get_cursor(conn, dictionary=True)
                cur.execute("SELECT COUNT(*) as count FROM sensors WHERE user_id = %s", (int(user_id),))
                sensor_count = cur.fetchone()['count']
                cur.close()
                _return_connection(pool, conn)
                print(f"WARNING: dashboard - User {user_id} has {sensor_count} sensors but no locations!", file=sys.stderr)
                
                # Check sensor details
                if sensor_count > 0:
                    conn = _get_connection(pool)
                    cur = _get_cursor(conn, dictionary=True)
                    cur.execute("SELECT device_id, location, status FROM sensors WHERE user_id = %s LIMIT 10", (int(user_id),))
                    sensors = cur.fetchall()
                    cur.close()
                    _return_connection(pool, conn)
                    print(f"DEBUG: dashboard - Sample sensors for user {user_id}:", file=sys.stderr)
                    for s in sensors:
                        print(f"DEBUG: dashboard -   Sensor: {s.get('device_id')}, Location: {s.get('location')}, Status: {s.get('status')}", file=sys.stderr)
            sys.stderr.flush()
        
        # Get first location as default, or None if no locations
        default_location = locations_data[0]['location'] if locations_data else None
        
        return render_template(
            "dashboard.html",
            locations=locations_data,
            default_location=default_location,
            current_user_id=user_id,  # Pass for debugging
            current_username=username,  # Pass for debugging
        )

    @app.route('/readings')
    @login_required
    def readings():
        """Display live sensor readings page."""
        user_id = session.get('user_id')
        if not user_id:
            flash('User session not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        return render_template('readings.html')

