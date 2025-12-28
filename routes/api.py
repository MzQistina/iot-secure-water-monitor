"""API routes for sensor data, keys, and testing."""
from flask import jsonify, request, session
import os
from db import list_sensors, get_sensor_type_by_type, get_sensor_by_device_id, update_sensor_by_device_id
from validation import sanitize_input
from utils.auth import login_required


def register_api_routes(app, get_user_key, add_user_key, user_pending_keys, pending_keys):
    """Register API routes with the Flask app.
    
    Args:
        app: Flask application instance
        get_user_key: Function to get user's device key
        add_user_key: Function to add user's device key
        user_pending_keys: Dict of user-specific pending keys
        pending_keys: Dict of global pending keys
    """
    
    @app.route('/api/public/active_sensors')
    def api_public_active_sensors():
        """Public API endpoint for devices/simulators to get active sensor information."""
        # Return active sensors with device_id, device_type, user_id, and location
        # This allows simulators to get the correct device_type from the database
        try:
            all_sensors = list_sensors(user_id=None)  # Get all active sensors
            active_sensors = [s for s in all_sensors if s.get('status') == 'active']
            
            # Return minimal information needed by simulators
            sensor_list = []
            for sensor in active_sensors:
                sensor_list.append({
                    'device_id': sensor.get('device_id'),
                    'device_type': sensor.get('device_type'),  # Include device_type from database
                    'user_id': sensor.get('user_id'),
                    'location': sensor.get('location')
                })
            
            return jsonify({'active_sensors': sensor_list}), 200
        except Exception as e:
            # On error, return empty list (for backward compatibility)
            import sys
            print(f"ERROR: api_public_active_sensors - {e}", file=sys.stderr)
            sys.stderr.flush()
            return jsonify({'active_sensors': []}), 200

    @app.route('/api/sensor_type')
    @login_required
    def api_sensor_type():
        """API endpoint to get sensor type information."""
        try:
            sensor_type = request.args.get('type', '').strip().lower()
            if not sensor_type:
                return jsonify({"error": "Type parameter is required"}), 400
            
            sensor_type_info = get_sensor_type_by_type(sensor_type)
            if sensor_type_info:
                return jsonify({
                    'type_name': sensor_type_info.get('type_name'),
                    'default_min': sensor_type_info.get('default_min'),
                    'default_max': sensor_type_info.get('default_max')
                })
            else:
                return jsonify({"error": "Sensor type not found"}), 404
        except Exception as e:
            import traceback
            print(f"ERROR: api_sensor_type - {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/key_upload_status')
    @login_required
    def api_key_upload_status():
        """API endpoint to check if a key has been uploaded for a device."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found"}), 401
        
        try:
            device_id = sanitize_input(request.args.get('device_id') or '')
            if not device_id:
                return jsonify({"error": "device_id parameter is required"}), 400
            
            # Check if key exists in user's keys
            key = get_user_key(user_id, device_id)
            if key:
                # FIX: Added 'received': True
                return jsonify({"status": "uploaded", "received": True, "device_id": device_id})
            
            # Check pending keys
            if user_id in user_pending_keys and device_id in user_pending_keys[user_id]:
                # FIX: Added 'received': True
                return jsonify({"status": "pending", "received": True, "device_id": device_id})
            
            # Check global pending keys (legacy)
            if device_id in pending_keys:
                # FIX: Added 'received': True
                return jsonify({"status": "pending", "received": True, "device_id": device_id})
            
            return jsonify({"status": "not_found", "received": False, "device_id": device_id})
        except Exception as e:
            import traceback
            print(f"ERROR: api_key_upload_status - {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/key_upload_fetch')
    @login_required
    def api_key_upload_fetch():
        """API endpoint to fetch an uploaded key for a device."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found"}), 401
        
        try:
            device_id = sanitize_input(request.args.get('device_id') or '')
            if not device_id:
                return jsonify({"error": "device_id parameter is required"}), 400
            
            # Get key from user's keys
            key = get_user_key(user_id, device_id)
            if key:
                # Save to database if sensor exists (pass user_id to get correct sensor)
                sensor = get_sensor_by_device_id(device_id, user_id)
                if sensor:
                    try:
                        update_sensor_by_device_id(
                            device_id=device_id,
                            location=sensor.get('location'),
                            status=sensor.get('status'),
                            public_key=key,
                            min_threshold=sensor.get('min_threshold'),
                            max_threshold=sensor.get('max_threshold'),
                            user_id=user_id
                        )
                    except Exception:
                        pass
                
                return jsonify({"status": "success", "public_key": key, "device_id": device_id})
            
            # Check pending keys
            if user_id in user_pending_keys and device_id in user_pending_keys[user_id]:
                key = user_pending_keys[user_id][device_id]
                # Move to user's keys
                add_user_key(user_id, device_id, key)
                return jsonify({"status": "success", "public_key": key, "device_id": device_id})
            
            # Check global pending keys (legacy)
            if device_id in pending_keys:
                key = pending_keys[device_id]
                # Move to user's keys
                add_user_key(user_id, device_id, key)
                return jsonify({"status": "success", "public_key": key, "device_id": device_id})
            
            return jsonify({"error": "Key not found"}), 404
        except Exception as e:
            import traceback
            print(f"ERROR: api_key_upload_fetch - {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/sensor/key_timestamp')
    @login_required
    def api_sensor_key_timestamp():
        """API endpoint to get the key_updated_at timestamp for a sensor."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found"}), 401
        
        try:
            device_id = sanitize_input(request.args.get('device_id') or '')
            if not device_id:
                return jsonify({"error": "device_id parameter is required"}), 400
            
            # Get sensor (pass user_id to get correct sensor)
            sensor = get_sensor_by_device_id(device_id, user_id)
            if not sensor:
                return jsonify({"error": "Sensor not found"}), 404
            
            key_updated_at = sensor.get('key_updated_at')
            if key_updated_at:
                # Convert datetime to ISO string if it's a datetime object
                if hasattr(key_updated_at, 'isoformat'):
                    key_updated_at = key_updated_at.isoformat()
                elif isinstance(key_updated_at, str):
                    # Already a string, keep as is
                    pass
            
            return jsonify({
                "device_id": device_id,
                "key_updated_at": key_updated_at
            })
        except Exception as e:
            import traceback
            print(f"ERROR: api_sensor_key_timestamp - {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/test/env', methods=['GET'])
    @login_required
    def test_env_vars():
        """Test endpoint to check if environment variables are accessible."""
        import os
        return jsonify({
            "MQTT_HOST": os.environ.get('MQTT_HOST', 'NOT SET'),
            "MQTT_USER": os.environ.get('MQTT_USER', 'NOT SET'),
            "MQTT_PASSWORD": "SET" if os.environ.get('MQTT_PASSWORD') else "NOT SET",
            "MQTT_PORT": os.environ.get('MQTT_PORT', 'NOT SET'),
            "MQTT_USE_TLS": os.environ.get('MQTT_USE_TLS', 'NOT SET'),
            "MQTT_TLS_INSECURE": os.environ.get('MQTT_TLS_INSECURE', 'NOT SET'),
        })

    @app.route('/api/test/mqtt', methods=['GET'])
    @login_required
    def test_mqtt_config():
        """Test endpoint to check MQTT configuration."""
        mqtt_host = os.environ.get('MQTT_HOST')
        mqtt_port = os.environ.get('MQTT_PORT', '1883')
        mqtt_user = os.environ.get('MQTT_USER')
        mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
        
        config = {
            "mqtt_host": mqtt_host or "NOT SET",
            "mqtt_port": mqtt_port,
            "mqtt_user": mqtt_user or "NOT SET",
            "mqtt_use_tls": mqtt_use_tls,
            "configured": bool(mqtt_host)
        }
        
        return jsonify(config)

