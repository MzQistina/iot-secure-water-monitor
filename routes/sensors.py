"""Sensor management routes: list, register, update, delete sensors."""
from flask import render_template, redirect, url_for, session, flash, request, jsonify
import os
import hashlib
from db import (
    list_sensors,
    list_sensor_types,
    get_sensor_by_device_id,
    create_sensor,
    update_sensor_by_device_id,
    delete_sensor_by_device_id,
)
from validation import (
    validate_device_id,
    validate_device_type,
    validate_location,
    validate_status,
    sanitize_input,
)
from utils.auth import login_required


def register_sensor_routes(app, get_user_key, get_user_key_file, notify_raspbian_key_cleanup,
                          _build_type_defaults_map, build_effective_thresholds_for_sensor,
                          compute_public_key_fingerprint):
    """Register sensor management routes with the Flask app.
    
    Args:
        app: Flask application instance
        get_user_key: Function to get user's device key
        get_user_key_file: Function to get user's key file path
        notify_raspbian_key_cleanup: Function to notify MQTT about key cleanup
        _build_type_defaults_map: Function to build type defaults map
        build_effective_thresholds_for_sensor: Function to get effective thresholds
        compute_public_key_fingerprint: Function to compute key fingerprint
    """
    
    @app.route('/sensors')
    @login_required
    def sensors():
        """Display and manage sensors."""
        user_id = session.get('user_id')
        if not user_id:
            flash('User session not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        try:
            import sys
            # Get filter parameters
            q = request.args.get('q', '').strip()
            status_filter = request.args.get('status', '').strip()
            
            # Get user's sensors
            all_sensors = list_sensors()
            user_sensors = [s for s in all_sensors if s.get('user_id') == user_id]
            
            # Get default thresholds map
            try:
                type_defaults = _build_type_defaults_map()
            except Exception as e:
                print(f"WARNING: Could not build type defaults map: {e}", file=sys.stderr)
                type_defaults = {}
            
            # Enhance each sensor with computed fields
            enhanced_sensors = []
            for sensor in user_sensors:
                try:
                    device_id = sensor.get('device_id')
                    if not device_id:
                        continue  # Skip sensors without device_id
                        
                    device_type = (sensor.get('device_type') or '').lower()
                    
                    # Get public key (from database or file)
                    public_key = sensor.get('public_key')
                    if not public_key:
                        # Try to get from user's key file
                        try:
                            public_key = get_user_key(user_id, device_id)
                        except Exception as e:
                            print(f"WARNING: Could not get user key for {device_id}: {e}", file=sys.stderr)
                            public_key = None
                    
                    # Compute public key fingerprint
                    try:
                        public_key_fingerprint = compute_public_key_fingerprint(public_key)
                    except Exception as e:
                        print(f"WARNING: Could not compute fingerprint for {device_id}: {e}", file=sys.stderr)
                        public_key_fingerprint = None
                    
                    # Get effective thresholds
                    try:
                        effective_thresholds = build_effective_thresholds_for_sensor(device_id)
                        threshold_for_type = effective_thresholds.get(device_type, {}) if effective_thresholds else {}
                    except Exception as e:
                        print(f"WARNING: Could not get effective thresholds for {device_id}: {e}", file=sys.stderr)
                        threshold_for_type = {}
                    
                    min_threshold_effective = threshold_for_type.get('min')
                    max_threshold_effective = threshold_for_type.get('max')
                    
                    # Get default thresholds for this device type
                    default_thresholds = type_defaults.get(device_type, {}) if type_defaults else {}
                    default_min = default_thresholds.get('min') if isinstance(default_thresholds, dict) else None
                    default_max = default_thresholds.get('max') if isinstance(default_thresholds, dict) else None
                    
                    # Determine threshold source
                    sensor_min = sensor.get('min_threshold')
                    sensor_max = sensor.get('max_threshold')
                    threshold_source = None
                    if sensor_min is not None or sensor_max is not None:
                        threshold_source = 'custom'
                    elif default_min is not None or default_max is not None:
                        threshold_source = 'default'
                    
                    # Create enhanced sensor dict
                    enhanced_sensor = dict(sensor)  # Copy original sensor data
                    enhanced_sensor['public_key_fingerprint'] = public_key_fingerprint
                    enhanced_sensor['has_key'] = bool(public_key)  # Track if key exists (for older sensors without key_updated_at)
                    enhanced_sensor['min_threshold_effective'] = min_threshold_effective
                    enhanced_sensor['max_threshold_effective'] = max_threshold_effective
                    enhanced_sensor['default_min'] = default_min
                    enhanced_sensor['default_max'] = default_max
                    enhanced_sensor['threshold_source'] = threshold_source
                    
                    enhanced_sensors.append(enhanced_sensor)
                except Exception as e:
                    print(f"ERROR: Failed to enhance sensor {sensor.get('device_id', 'unknown')}: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    # Continue processing other sensors even if one fails
                    continue
            
            # Apply filters
            if q:
                q_lower = q.lower()
                enhanced_sensors = [s for s in enhanced_sensors if 
                              q_lower in (s.get('device_id') or '').lower() or
                              q_lower in (s.get('device_type') or '').lower() or
                              q_lower in (s.get('location') or '').lower()]
            
            if status_filter:
                enhanced_sensors = [s for s in enhanced_sensors if s.get('status') == status_filter]
            
            print(f"DEBUG: sensors - Returning {len(enhanced_sensors)} sensors for user {user_id}", file=sys.stderr)
            sys.stderr.flush()
            
            return render_template('sensors.html', 
                                 sensors=enhanced_sensors,
                                 q=q,
                                 status_filter=status_filter)
        except Exception as e:
            import traceback
            print(f"ERROR: sensors route - {e}")
            traceback.print_exc()
            flash('Error loading sensors.', 'error')
            return render_template('sensors.html', sensors=[], q='', status_filter='')

    @app.route('/sensors/register', methods=['GET', 'POST'])
    @login_required
    def sensors_register():
        """Register a new sensor."""
        user_id = session.get('user_id')
        if not user_id:
            flash('User session not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            try:
                device_id = sanitize_input(request.form.get('device_id') or '')
                device_type = sanitize_input(request.form.get('device_type') or '')
                location = sanitize_input(request.form.get('location') or '')
                
                # Get status and public_key from the form
                status = sanitize_input(request.form.get('status') or 'active')
                public_key = request.form.get('public_key')
                if public_key:
                    public_key = public_key.strip()
                
                # Validation
                device_id_valid, device_id_error = validate_device_id(device_id)
                if not device_id_valid:
                    flash(device_id_error or 'Invalid device ID', 'error')
                    return render_template('sensors_register.html', 
                                         sensor_types=list_sensor_types() or [])
                
                device_type_valid, device_type_error, normalized_device_type = validate_device_type(device_type)
                if not device_type_valid:
                    flash(device_type_error or 'Invalid device type', 'error')
                    return render_template('sensors_register.html',
                                         sensor_types=list_sensor_types() or [])
                # Use normalized device type (spaces converted to underscores)
                device_type = normalized_device_type
                
                location_valid, location_error = validate_location(location)
                if not location_valid and location:  # Location can be empty
                    flash(location_error or 'Invalid location', 'error')
                    return render_template('sensors_register.html',
                                         sensor_types=list_sensor_types() or [])
                
                # Check if device_id already exists for this user
                existing = get_sensor_by_device_id(device_id, user_id)
                if existing:
                    flash(f'Sensor with device ID "{device_id}" already registered', 'error')
                    return render_template('sensors_register.html',
                                         sensor_types=list_sensor_types() or [])
                
                # Check if this will be their first sensor (before creating)
                user_sensors_before = list_sensors(user_id=user_id) or []
                is_first_sensor = len(user_sensors_before) == 0
                
                # Create sensor
                sensor_created = create_sensor(
                    device_id=device_id,
                    device_type=device_type,
                    location=location or None,
                    public_key=public_key or None,
                    user_id=user_id,
                    status=status
                )
                
                if sensor_created:
                    # Sensor created successfully - redirect immediately to avoid duplicate submissions
                    flash(f'Sensor "{device_id}" registered successfully!', 'success')
                    if is_first_sensor:
                        # Redirect with tour parameter for first-time users
                        return redirect(url_for('sensors') + '?tour=first_sensor')
                    return redirect(url_for('sensors'))
                else:
                    # create_sensor returned False - could be duplicate or other error
                    # Re-check if sensor exists now (might have been created by concurrent request)
                    verify_existing = get_sensor_by_device_id(device_id, user_id)
                    if verify_existing:
                        flash(f'Sensor with device ID "{device_id}" already registered', 'error')
                    else:
                        flash('Failed to register sensor. Please try again.', 'error')
            except Exception as e:
                import traceback
                print(f"ERROR: sensors_register POST - {e}")
                traceback.print_exc()
                flash(f'Error registering sensor: {str(e)}', 'error')
        
        # GET request - show form
        try:
            sensor_types = list_sensor_types() or []
            import sys
            print(f"DEBUG: sensors_register GET - Found {len(sensor_types)} sensor types", file=sys.stderr)
            if sensor_types:
                print(f"DEBUG: Sensor types: {[t.get('type_name', 'NO_NAME') if isinstance(t, dict) else getattr(t, 'type_name', 'NO_NAME') for t in sensor_types[:3]]}", file=sys.stderr)
            sys.stderr.flush()
            
            # Check if user is first-time (has no sensors yet)
            user_sensors = list_sensors(user_id=user_id) or []
            is_first_time = len(user_sensors) == 0
            
            return render_template('sensors_register.html', sensor_types=sensor_types, is_first_time=is_first_time)
        except Exception as e:
            import traceback
            print(f"ERROR: sensors_register GET - {e}")
            traceback.print_exc()
            return render_template('sensors_register.html', sensor_types=[])

    @app.route('/sensors/delete', methods=['POST'])
    @login_required
    def sensors_delete():
        """Delete a sensor."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found"}), 401
        
        try:
            device_id = sanitize_input(request.form.get('device_id') or '')
            if not device_id:
                flash('Device ID is required', 'error')
                return redirect(url_for('sensors'))
            
            # Verify sensor belongs to user (pass user_id to get correct sensor)
            sensor = get_sensor_by_device_id(device_id, user_id)
            if not sensor:
                flash('Sensor not found or access denied', 'error')
                return redirect(url_for('sensors'))
            
            # IMPORTANT: Send MQTT delete message BEFORE deleting database record
            # This ensures public_key is still available for E2EE encryption
            # Notify via MQTT if configured (before deleting from DB)
            notify_raspbian_key_cleanup(device_id, user_id)
            
            # Delete sensor (pass user_id if delete function supports it)
            if delete_sensor_by_device_id(device_id):
                # Also delete user's key file if exists
                key_file = get_user_key_file(user_id, device_id)
                if os.path.exists(key_file):
                    try:
                        os.remove(key_file)
                    except Exception:
                        pass
                
                flash(f'Sensor "{device_id}" deleted successfully', 'success')
            else:
                flash('Failed to delete sensor', 'error')
        except Exception as e:
            import traceback
            print(f"ERROR: sensors_delete - {e}")
            traceback.print_exc()
            flash(f'Error deleting sensor: {str(e)}', 'error')
        
        return redirect(url_for('sensors'))

    @app.route('/sensors/update', methods=['POST'])
    @login_required
    def sensors_update():
        """Update a sensor."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found"}), 401
        
        try:
            device_id = sanitize_input(request.form.get('device_id') or '')
            location = sanitize_input(request.form.get('location') or '')
            status = sanitize_input(request.form.get('status') or '')
            min_threshold = request.form.get('min_threshold')
            max_threshold = request.form.get('max_threshold')
            
            if not device_id:
                flash('Device ID is required', 'error')
                return redirect(url_for('sensors'))
            
            # Verify sensor belongs to user (pass user_id to get correct sensor)
            sensor = get_sensor_by_device_id(device_id, user_id)
            if not sensor:
                flash('Sensor not found or access denied', 'error')
                return redirect(url_for('sensors'))
            
            # Validate inputs
            if location:
                location_valid, location_error = validate_location(location)
                if not location_valid:
                    flash(location_error or 'Invalid location', 'error')
                    return redirect(url_for('sensors'))
            
            if status:
                status_valid, status_error = validate_status(status)
                if not status_valid:
                    flash(status_error or 'Invalid status', 'error')
                    return redirect(url_for('sensors'))
            
            # Parse thresholds (handle empty strings as None)
            min_thresh = None
            max_thresh = None
            if min_threshold and str(min_threshold).strip():
                try:
                    min_thresh = float(min_threshold)
                except (ValueError, TypeError):
                    flash('Invalid minimum threshold', 'error')
                    return redirect(url_for('sensors'))
            
            if max_threshold and str(max_threshold).strip():
                try:
                    max_thresh = float(max_threshold)
                except (ValueError, TypeError):
                    flash('Invalid maximum threshold', 'error')
                    return redirect(url_for('sensors'))
            
            # Update sensor
            update_sensor_by_device_id(
                device_id=device_id,
                location=location or sensor.get('location'),
                status=status or sensor.get('status'),
                public_key=sensor.get('public_key'),  # Preserve existing public_key
                min_threshold=min_thresh,
                max_threshold=max_thresh,
                user_id=user_id,
            )
            
            flash(f'Sensor "{device_id}" updated successfully', 'success')
        except Exception as e:
            import traceback
            print(f"ERROR: sensors_update - {e}")
            traceback.print_exc()
            flash(f'Error updating sensor: {str(e)}', 'error')
        
        return redirect(url_for('sensors'))

