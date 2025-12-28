"""MQTT utilities for key and sensor data subscribers."""
import os
import sys
import json
import re
import threading
import time
import ssl
from datetime import datetime, timezone


def _get_mqtt_publish_kwargs():
    """Get MQTT publish configuration including TLS settings."""
    kwargs = {}
    
    # MANUAL CONFIGURATION: Set MQTT credentials directly here
    # These values are used as fallback if environment variables are not set
    MQTT_CONFIG = {
        'host': '192.168.43.214',
        'port': 8883,
        'user': 'admin_flask',
        'password': 'flaske2ee25',
        'use_tls': True,
        'tls_insecure': True
    }
    
    # Try to get from environment variables first, fallback to manual config
    mqtt_host = os.environ.get('MQTT_HOST') or MQTT_CONFIG['host']
    mqtt_port = int(os.environ.get('MQTT_PORT') or str(MQTT_CONFIG['port']))
    mqtt_user = os.environ.get('MQTT_USER') or MQTT_CONFIG['user']
    mqtt_password = os.environ.get('MQTT_PASSWORD') or MQTT_CONFIG['password']
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'true').lower() in ('true', '1', 'yes') if os.environ.get('MQTT_USE_TLS') else MQTT_CONFIG['use_tls']
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'true').lower() in ('true', '1', 'yes') if os.environ.get('MQTT_TLS_INSECURE') else MQTT_CONFIG['tls_insecure']
    
    kwargs['hostname'] = mqtt_host
    kwargs['port'] = mqtt_port
    
    # Authentication - ALWAYS set if we have credentials
    if mqtt_user and mqtt_password:
        kwargs['auth'] = {'username': mqtt_user, 'password': mqtt_password}
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'true').lower() in ('true', '1', 'yes') if os.environ.get('MQTT_USE_TLS') else MQTT_CONFIG['use_tls']
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'true').lower() in ('true', '1', 'yes') if os.environ.get('MQTT_TLS_INSECURE') else MQTT_CONFIG['tls_insecure']
    
    if mqtt_use_tls:
        mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
        mqtt_certfile = os.environ.get('MQTT_CERTFILE')
        mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
        
        tls_config = {}
        # Always provide ca_certs if available (even in insecure mode, it's still used)
        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
            tls_config['ca_certs'] = mqtt_ca_certs
        if mqtt_certfile and os.path.exists(mqtt_certfile):
            tls_config['certfile'] = mqtt_certfile
        if mqtt_keyfile and os.path.exists(mqtt_keyfile):
            tls_config['keyfile'] = mqtt_keyfile
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        # Set cert_reqs to CERT_NONE when insecure mode is enabled
        if mqtt_tls_insecure:
            tls_config['cert_reqs'] = ssl.CERT_NONE
        tls_config['insecure'] = mqtt_tls_insecure
        
        kwargs['tls'] = tls_config
    
    return kwargs


def start_mqtt_key_subscriber(
    pending_keys,
    recent_nonces,
    recent_timestamps,
    add_user_key,
    get_sensor_by_device_id,
    update_sensor_by_device_id,
    mqtt_thread_started_ref,
    NONCE_CACHE_SIZE=50,
    REPLAY_MAX_SKEW_SECONDS=120
):
    """Start MQTT subscriber for key provisioning.
    
    Args:
        pending_keys: Dict to store pending keys
        recent_nonces: Dict to track recent nonces for replay protection
        recent_timestamps: Dict to track recent timestamps for replay protection
        add_user_key: Function to add user key to filesystem
        get_sensor_by_device_id: Function to get sensor from database
        update_sensor_by_device_id: Function to update sensor in database
        mqtt_thread_started_ref: List with single boolean to track if thread started
        NONCE_CACHE_SIZE: Maximum nonces to cache per device
        REPLAY_MAX_SKEW_SECONDS: Maximum timestamp skew allowed
    """
    if mqtt_thread_started_ref[0]:
        return
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        return
    try:
        import paho.mqtt.client as mqtt
    except Exception:
        print("MQTT: paho-mqtt not installed; skipping key subscriber.")
        return

    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_topic = os.environ.get('MQTT_KEYS_TOPIC', 'keys/+/public')
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
    mqtt_certfile = os.environ.get('MQTT_CERTFILE')
    mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')

    # Connection state tracking (nonlocal variable for nested functions)
    mqtt_connected = False
    
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        nonlocal mqtt_connected
        try:
            if reason_code == 0:
                result = client.subscribe(mqtt_topic)
                mqtt_connected = True
                print(f"MQTT: connected rc={reason_code}; subscribed to '{mqtt_topic}' (result: {result})", file=sys.stderr)
                sys.stderr.flush()
            else:
                mqtt_connected = False
                error_msg = f"MQTT: connection failed with rc={reason_code}"
                if reason_code == 5:
                    error_msg += " (Not authorized - check MQTT_USER and MQTT_PASSWORD, or ACL permissions)"
                print(f"MQTT: {error_msg}", file=sys.stderr)
                sys.stderr.flush()
        except Exception as e:
            mqtt_connected = False
            error_msg = f"MQTT subscribe error: {e}"
            print(f"MQTT: {error_msg}", file=sys.stderr)
            import traceback
            print(f"MQTT: Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()

    def _on_message(client, userdata, msg):
        try:
            payload_bytes = msg.payload or b''
            text = payload_bytes.decode('utf-8', errors='replace').strip()
            device_id = None
            # Attempt to parse device_id from topic
            try:
                m = re.match(r'^keys/([^/]+)/public$', msg.topic or '')
                if m:
                    device_id = m.group(1)
            except Exception:
                pass
            pem = None
            user_id_from_msg = None
            # Accept JSON {"device_id":"...","public_key":"PEM","user_id":"...", "nonce":..., "timestamp":...}
            if text.startswith('{'):
                try:
                    data = json.loads(text)
                    pem = (data.get('public_key') or '').strip()
                    device_id = (data.get('device_id') or device_id or '').strip()
                    # Extract user_id if provided
                    user_id_raw = data.get('user_id')
                    if user_id_raw is not None:
                        try:
                            user_id_from_msg = int(user_id_raw)
                        except (ValueError, TypeError):
                            user_id_from_msg = None
                    # --- REPLAY PROTECTION ---
                    nonce = data.get('nonce')
                    timestamp = data.get('timestamp')
                    if device_id and (nonce or timestamp):
                        # Check nonce replay
                        if nonce:
                            nonces = recent_nonces.setdefault(device_id, set())
                            if nonce in nonces:
                                print(f"[REPLAY BLOCKED] Duplicate nonce for device {device_id}: {nonce}")
                                return
                        # Check timestamp replay
                        if timestamp:
                            try:
                                ts = datetime.fromisoformat(timestamp)
                                now = datetime.now(timezone.utc)
                                skew = abs((now - ts).total_seconds())
                                if skew > REPLAY_MAX_SKEW_SECONDS:
                                    print(f"[REPLAY BLOCKED] Timestamp too old or far in future for device {device_id}: {timestamp}")
                                    return
                                # Optionally, block if timestamp not newer than last
                                last_ts = recent_timestamps.get(device_id)
                                if last_ts:
                                    last_dt = datetime.fromisoformat(last_ts)
                                    if ts <= last_dt:
                                        print(f"[REPLAY BLOCKED] Timestamp not newer than previous for device {device_id}: {timestamp}")
                                        return
                                recent_timestamps[device_id] = timestamp
                            except Exception as ts_err:
                                print(f"[REPLAY WARNING] Could not parse timestamp for device {device_id}: {timestamp} ({ts_err})")
                        # Store nonce (limit cache size)
                        if nonce:
                            nonces.add(nonce)
                            if len(nonces) > NONCE_CACHE_SIZE:
                                # Remove oldest (not strictly ordered, but set pop is fine for small cache)
                                while len(nonces) > NONCE_CACHE_SIZE:
                                    nonces.pop()
                except Exception:
                    pem = None
            else:
                pem = text
            if not device_id or not pem:
                print("MQTT: missing device_id or public_key; ignoring message")
                return
            # Store as pending and update DB if sensor already exists
            pending_keys[device_id] = pem
            try:
                # Use user_id if provided to get the correct sensor (important when multiple users have same device_id)
                srow = get_sensor_by_device_id(device_id, user_id_from_msg)
            except Exception:
                srow = None
            
            # Determine user_id for key storage
            user_id_for_key = None
            if srow:
                sensor_user_id = srow.get('user_id')
                user_id_for_key = user_id_from_msg if user_id_from_msg is not None else sensor_user_id
            elif user_id_from_msg is not None:
                user_id_for_key = user_id_from_msg
            
            # Save key to filesystem (user_keys directory) for E2EE encryption
            if user_id_for_key:
                try:
                    if add_user_key(user_id_for_key, device_id, pem):
                        print(f"MQTT: saved public key to user_keys/{user_id_for_key}/{device_id}_public.pem for E2EE")
                    else:
                        print(f"MQTT: warning - failed to save key to user_keys/{user_id_for_key}/{device_id}_public.pem")
                except Exception as key_save_err:
                    print(f"MQTT: error saving key to filesystem: {key_save_err}")
                    import traceback
                    traceback.print_exc()
            
            if srow:
                try:
                    # Update sensor - use user_id if available to ensure we update the correct sensor
                    sensor_db_id = srow.get('id')
                    sensor_user_id = srow.get('user_id')
                    
                    # Use user_id_from_msg if available, otherwise use sensor_user_id from database
                    user_id_for_update = user_id_from_msg if user_id_from_msg is not None else sensor_user_id
                    
                    update_sensor_by_device_id(
                        device_id=device_id,
                        location=srow.get('location'),
                        status=srow.get('status'),
                        public_key=pem,
                        min_threshold=srow.get('min_threshold'),
                        max_threshold=srow.get('max_threshold'),
                        user_id=user_id_for_update,
                    )
                    user_info = f" (user_id={user_id_for_update}, db_id={sensor_db_id})" if user_id_for_update else f" (db_id={sensor_db_id})"
                    print(f"MQTT: updated public key in DB for sensor '{device_id}'{user_info}")
                except Exception as e:
                    print(f"MQTT DB update error for {device_id}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                user_info = f" (user_id={user_id_from_msg})" if user_id_from_msg else ""
                print(f"MQTT: received key for unregistered device '{device_id}'{user_info} (stored pending)")
        except Exception as e:
            print(f"MQTT message error: {e}")

    def _run():
        retry_count = 0
        max_retries = 10  # Maximum retry attempts before giving up
        base_delay = 5  # Base delay in seconds
        
        while retry_count < max_retries:
            try:
                # Create MQTT client with API v2 (fixes deprecation warning)
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                
                # Configure authentication
                if mqtt_user and mqtt_password:
                    client.username_pw_set(mqtt_user, mqtt_password)
                
                # Configure TLS/SSL if enabled
                if mqtt_use_tls:
                    try:
                        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
                            # Use CA certificate for validation
                            client.tls_set(
                                ca_certs=mqtt_ca_certs,
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                            print(f"MQTT: TLS enabled with CA cert: {mqtt_ca_certs}")
                        else:
                            # Use system CA certificates (default)
                            client.tls_set(
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                            print(f"MQTT: TLS enabled (using system CA certs)")
                        
                        if mqtt_tls_insecure:
                            client.tls_insecure_set(True)
                            print("MQTT: TLS insecure mode enabled (certificate validation disabled)")
                    except Exception as tls_err:
                        print(f"MQTT: TLS configuration error: {tls_err}")
                        print("MQTT: Continuing without TLS (insecure)")
                
                # Set callbacks
                client.on_connect = _on_connect
                client.on_message = _on_message
                
                # Add disconnect callback to handle reconnection
                def _on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
                    """Callback when MQTT client disconnects (API v2)."""
                    nonlocal mqtt_connected
                    mqtt_connected = False
                    if reason_code != 0:
                        print(f"MQTT: Unexpected disconnection (rc={reason_code})", file=sys.stderr)
                        sys.stderr.flush()
                
                client.on_disconnect = _on_disconnect
                
                # Enable automatic reconnection
                client.reconnect_delay_set(min_delay=1, max_delay=120)
                
                print(f"MQTT: Attempting to connect to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'}) (attempt {retry_count + 1}/{max_retries})")
                
                # Use async connection
                try:
                    client.connect_async(mqtt_host, mqtt_port, keepalive=60)
                    client.loop_start()
                    
                    # Wait up to 5 seconds to see if connection succeeds
                    for _ in range(10):  # Check 10 times over 5 seconds
                        time.sleep(0.5)
                        if mqtt_connected:
                            print(f"MQTT: Successfully connected to {mqtt_host}:{mqtt_port}")
                            # Keep the loop running - it will handle reconnections automatically
                            while True:
                                time.sleep(10)
                                # If we lose connection and it doesn't reconnect, break to retry
                                if not mqtt_connected:
                                    # Give it some time to reconnect automatically
                                    time.sleep(5)
                                    if not mqtt_connected:
                                        print("MQTT: Connection lost and auto-reconnect failed, will retry...")
                                        break
                            break
                    else:
                        # Connection failed within timeout
                        client.loop_stop()
                        client.disconnect()
                        raise ConnectionError("Connection attempt timed out")
                        
                except Exception as conn_err:
                    print(f"MQTT: Connection error: {conn_err}")
                    try:
                        client.loop_stop()
                        client.disconnect()
                    except:
                        pass
                    raise
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff: delay increases with each retry
                    delay = min(base_delay * (2 ** (retry_count - 1)), 60)  # Cap at 60 seconds
                    print(f"MQTT: Connection failed (attempt {retry_count}/{max_retries}). Retrying in {delay} seconds...")
                    print(f"MQTT error: {e}")
                    time.sleep(delay)
                else:
                    print(f"MQTT: Max retries ({max_retries}) reached. MQTT subscriber stopped.")
                    print(f"MQTT: Last error: {e}")
                    import traceback
                    traceback.print_exc()
                    break

    t = threading.Thread(target=_run, name='mqtt-key-subscriber', daemon=True)
    t.start()
    mqtt_thread_started_ref[0] = True


def start_mqtt_sensor_subscriber(
    list_sensors,
    insert_sensor_data,
    _validate_device_session,
    build_effective_thresholds_for_sensor,
    _build_type_defaults_map,
    compute_safety,
    latest_by_metric,
    latest_by_sensor,
    user_latest_by_metric,
    user_latest_by_sensor,
    user_latest_data,
    mqtt_sensor_thread_started_ref,
    REQUIRE_DEVICE_SESSION=True
):
    """Start MQTT subscriber for secure/sensor topic to process sensor readings.
    
    Args:
        list_sensors: Function to list sensors
        insert_sensor_data: Function to insert sensor data
        _validate_device_session: Function to validate device session
        build_effective_thresholds_for_sensor: Function to build thresholds
        _build_type_defaults_map: Function to get default thresholds
        compute_safety: Function to compute safety status
        latest_by_metric: Dict for latest metric values
        latest_by_sensor: Dict for latest sensor values
        user_latest_by_metric: Dict for user-specific latest metric values
        user_latest_by_sensor: Dict for user-specific latest sensor values
        user_latest_data: Dict for user-specific latest data
        mqtt_sensor_thread_started_ref: List with single boolean to track if thread started
        REQUIRE_DEVICE_SESSION: Whether device sessions are required
    """
    if mqtt_sensor_thread_started_ref[0]:
        return
    mqtt_host = os.environ.get('MQTT_HOST')
    if not mqtt_host:
        return
    try:
        import paho.mqtt.client as mqtt
        from encryption_utils import aes_decrypt, hash_data
        import hashlib
    except Exception:
        print("MQTT: paho-mqtt not installed; skipping sensor subscriber.", file=sys.stderr)
        return

    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_topic = 'secure/sensor'
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
    mqtt_certfile = os.environ.get('MQTT_CERTFILE')
    mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')
    
    # AES key for MQTT decryption (must match simulator)
    AES_KEY = b'my16bytepassword'
    
    mqtt_sensor_connected = False
    
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when MQTT client connects (API v2)."""
        nonlocal mqtt_sensor_connected
        try:
            if reason_code == 0:
                result = client.subscribe(mqtt_topic, qos=1)
                mqtt_sensor_connected = True
                print(f"MQTT Sensor: connected rc={reason_code}; subscribed to '{mqtt_topic}' (result: {result})", file=sys.stderr)
                sys.stderr.flush()
            else:
                mqtt_sensor_connected = False
                error_msg = f"MQTT Sensor: connection failed with rc={reason_code}"
                if reason_code == 5:
                    error_msg += " (Not authorized - check MQTT_USER and MQTT_PASSWORD, or ACL permissions)"
                print(f"MQTT Sensor: {error_msg}", file=sys.stderr)
                sys.stderr.flush()
        except Exception as e:
            mqtt_sensor_connected = False
            print(f"MQTT Sensor: subscribe error: {e}", file=sys.stderr)
            import traceback
            print(f"MQTT Sensor: Traceback:\n{traceback.format_exc()}", file=sys.stderr)
            sys.stderr.flush()

    def _on_message(client, userdata, msg):
        """Process sensor reading from MQTT."""
        try:
            # Parse JSON payload
            payload_str = msg.payload.decode('utf-8', errors='replace')
            payload = json.loads(payload_str)
            
            # Extract encrypted data and hash
            encrypted_data = payload.get('data')
            received_hash = payload.get('hash')
            sha256_hash = payload.get('sha256')
            
            if not encrypted_data:
                print("MQTT Sensor: Missing 'data' field in payload", file=sys.stderr)
                return
            
            # Decrypt using AES
            # encrypted_data from payload should be a JSON string (from aes_encrypt)
            # But json.loads might have already parsed it, so check
            if isinstance(encrypted_data, dict):
                # If it's already a dict, convert back to JSON string for aes_decrypt
                encrypted_data_str = json.dumps(encrypted_data)
            elif isinstance(encrypted_data, str):
                encrypted_data_str = encrypted_data
            else:
                print(f"MQTT Sensor: Invalid encrypted_data type: {type(encrypted_data)}", file=sys.stderr)
                return
            
            try:
                # aes_decrypt expects a JSON string and returns a dict (it does json.loads internally)
                decrypted_data = aes_decrypt(encrypted_data_str, AES_KEY)
            except Exception as decrypt_err:
                print(f"MQTT Sensor: Decryption error: {decrypt_err}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                return
            
            # Verify hash
            if received_hash:
                # hash_data expects a dict, not a JSON string
                calculated_hash = hash_data(decrypted_data)
                if calculated_hash != received_hash:
                    print(f"MQTT Sensor: Hash mismatch - possible tampering", file=sys.stderr)
                    return
            
            # Verify SHA256 if provided
            if sha256_hash:
                data_json = json.dumps(decrypted_data, sort_keys=True).encode()
                computed_sha256 = hashlib.sha256(data_json).hexdigest()
                if computed_sha256 != sha256_hash:
                    print(f"MQTT Sensor: SHA256 hash mismatch", file=sys.stderr)
                    return
            
            # Extract sensor info
            device_id = decrypted_data.get('device_id')
            if not device_id:
                print("MQTT Sensor: Missing device_id in decrypted data", file=sys.stderr)
                return
            
            # Process the sensor reading (reuse logic from submit_data)
            # Note: MQTT format doesn't use RSA signatures, so we skip signature verification
            # but still validate the sensor exists and is active
            all_sensors = list_sensors()
            matching_sensors = [s for s in all_sensors if s.get('device_id', '').lower() == device_id.lower() and s.get('status') == 'active']
            
            if not matching_sensors:
                print(f"MQTT Sensor: Unregistered or inactive sensor '{device_id}'", file=sys.stderr)
                return
            
            # Use first matching active sensor (in production, you might want more sophisticated matching)
            sensor_row = matching_sensors[0]
            sensor_user_id = sensor_row.get('user_id')
            
            # Device session validation - validate and update session every time before storing
            session_token = decrypted_data.get('session_token')
            session_counter = decrypted_data.get('counter')
            
            # Debug: Log session token presence
            if session_token:
                print(f"MQTT Sensor: Session token found for {device_id}, counter={session_counter}", file=sys.stderr)
            else:
                print(f"MQTT Sensor: No session token in payload for {device_id}", file=sys.stderr)
            
            if REQUIRE_DEVICE_SESSION:
                # Sessions are required - reject if invalid
                ok, reason = _validate_device_session(session_token, device_id, session_counter)
                if not ok:
                    print(f"MQTT Sensor: Device session error for {device_id}: {reason}", file=sys.stderr)
                    return
                else:
                    print(f"MQTT Sensor: Session validated and updated for {device_id}, counter={session_counter}", file=sys.stderr)
            elif session_token:
                # Sessions are optional but provided - validate and update it
                ok, reason = _validate_device_session(session_token, device_id, session_counter)
                if not ok:
                    # Log warning but don't reject (sessions optional)
                    print(f"MQTT Sensor: Device session warning for {device_id}: {reason} (continuing anyway)", file=sys.stderr)
                else:
                    print(f"MQTT Sensor: Session validated and updated for {device_id}, counter={session_counter}", file=sys.stderr)
            
            # Initialize user-specific dictionaries if needed
            if sensor_user_id:
                if sensor_user_id not in user_latest_by_metric:
                    user_latest_by_metric[sensor_user_id] = {}
                if sensor_user_id not in user_latest_by_sensor:
                    user_latest_by_sensor[sensor_user_id] = {}
                if sensor_user_id not in user_latest_data:
                    user_latest_data[sensor_user_id] = {}
            
            # Extract metric values
            updated_values = {}
            supported_metrics = [
                "tds", "ph", "turbidity", "temperature", "dissolved_oxygen", "conductivity",
                "ammonia", "pressure", "nitrate", "nitrite", "orp", "chlorine", "salinity", "flow"
            ]
            for k in supported_metrics:
                if k in decrypted_data and decrypted_data[k] not in (None, ""):
                    try:
                        val = float(decrypted_data[k])
                        updated_values[k] = val
                        if sensor_user_id:
                            user_latest_by_metric[sensor_user_id][k] = {
                                "value": val,
                                "sensor_id": device_id,
                            }
                        latest_by_metric[k] = {
                            "value": val,
                            "sensor_id": device_id,
                        }
                    except Exception:
                        pass
            
            # Build aggregate values and thresholds
            if sensor_user_id and sensor_user_id in user_latest_by_metric:
                _lbm_snapshot = list(user_latest_by_metric[sensor_user_id].items())
            else:
                _lbm_snapshot = list(latest_by_metric.items())
            agg_values = {k: v.get("value") for k, v in _lbm_snapshot if v and v.get("value") is not None}
            
            agg_thresholds = {}
            for metric, entry in _lbm_snapshot:
                sid = (entry or {}).get("sensor_id")
                tmap = build_effective_thresholds_for_sensor(sid)
                if tmap and metric in tmap:
                    agg_thresholds[metric] = tmap[metric]
            for metric in agg_values.keys():
                if metric not in agg_thresholds:
                    defaults = _build_type_defaults_map()
                    if metric in defaults:
                        agg_thresholds[metric] = defaults[metric]
            
            # Evaluate safety
            safe, reasons = compute_safety(agg_values, agg_thresholds)
            
            # Store in database
            device_type = sensor_row.get('device_type')
            value_for_type = None
            
            if device_type:
                device_type_lower = str(device_type).lower().strip()
                for key, val in updated_values.items():
                    if key and str(key).lower().strip() == device_type_lower:
                        value_for_type = val
                        break
                if value_for_type is None and device_type in updated_values:
                    value_for_type = updated_values.get(device_type)
            
            if value_for_type is None and len(updated_values) > 0:
                value_for_type = next(iter(updated_values.values()))
            
            status_label = 'normal' if safe else 'warning'
            
            sensor_db_id = sensor_row.get('id')
            if sensor_db_id and value_for_type is not None:
                try:
                    result = insert_sensor_data(
                        sensor_db_id=sensor_db_id,
                        value=value_for_type,
                        status=status_label,
                        user_id=sensor_user_id,
                        device_id=device_id
                    )
                    if result:
                        print(f"MQTT Sensor: Stored reading for {device_id} ({device_type})", file=sys.stderr)
                        # Update sensor last_seen timestamp
                        try:
                            from db import _get_connection, _return_connection, _get_cursor, get_pool
                            pool = get_pool()
                            if pool:
                                conn = _get_connection(pool)
                                cur = _get_cursor(conn)
                                if sensor_user_id:
                                    cur.execute(
                                        "UPDATE sensors SET last_seen = NOW() WHERE device_id = %s AND user_id = %s",
                                        (device_id, sensor_user_id)
                                    )
                                else:
                                    cur.execute(
                                        "UPDATE sensors SET last_seen = NOW() WHERE device_id = %s",
                                        (device_id,)
                                    )
                                conn.commit()
                                cur.close()
                                _return_connection(pool, conn)
                        except Exception as update_err:
                            # Non-critical, just log
                            pass
                    else:
                        print(f"MQTT Sensor: Failed to store reading for {device_id}", file=sys.stderr)
                except Exception as db_err:
                    print(f"MQTT Sensor: Database error for {device_id}: {db_err}", file=sys.stderr)
            
            # Update caches
            if sensor_user_id:
                if sensor_user_id not in user_latest_by_sensor:
                    user_latest_by_sensor[sensor_user_id] = {}
                user_latest_by_sensor[sensor_user_id][device_id] = {
                    'device_id': device_id,
                    'device_type': device_type,
                    'location': sensor_row.get('location'),
                    'value': value_for_type,
                }
            latest_by_sensor[device_id] = {
                'device_id': device_id,
                'device_type': device_type,
                'location': sensor_row.get('location'),
                'value': value_for_type,
            }
            
        except Exception as e:
            print(f"MQTT Sensor: Error processing message: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    def _run():
        retry_count = 0
        max_retries = 10
        base_delay = 5
        
        while retry_count < max_retries:
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                
                if mqtt_user and mqtt_password:
                    client.username_pw_set(mqtt_user, mqtt_password)
                
                if mqtt_use_tls:
                    try:
                        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
                            client.tls_set(
                                ca_certs=mqtt_ca_certs,
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_REQUIRED if not mqtt_tls_insecure else ssl.CERT_NONE,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                        else:
                            client.tls_set(
                                certfile=mqtt_certfile if (mqtt_certfile and os.path.exists(mqtt_certfile)) else None,
                                keyfile=mqtt_keyfile if (mqtt_keyfile and os.path.exists(mqtt_keyfile)) else None,
                                cert_reqs=ssl.CERT_NONE if mqtt_tls_insecure else ssl.CERT_REQUIRED,
                                tls_version=ssl.PROTOCOL_TLS
                            )
                        if mqtt_tls_insecure:
                            client.tls_insecure_set(True)
                    except Exception as tls_err:
                        print(f"MQTT Sensor: TLS configuration error: {tls_err}", file=sys.stderr)
                
                client.on_connect = _on_connect
                client.on_message = _on_message
                
                def _on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
                    nonlocal mqtt_sensor_connected
                    mqtt_sensor_connected = False
                    if reason_code != 0:
                        print(f"MQTT Sensor: Unexpected disconnection (rc={reason_code})", file=sys.stderr)
                        sys.stderr.flush()
                
                client.on_disconnect = _on_disconnect
                client.reconnect_delay_set(min_delay=1, max_delay=120)
                
                print(f"MQTT Sensor: Attempting to connect to {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'}) (attempt {retry_count + 1}/{max_retries})", file=sys.stderr)
                
                try:
                    client.connect_async(mqtt_host, mqtt_port, keepalive=60)
                    client.loop_start()
                    
                    for _ in range(10):
                        time.sleep(0.5)
                        if mqtt_sensor_connected:
                            print(f"MQTT Sensor: Successfully connected to {mqtt_host}:{mqtt_port}", file=sys.stderr)
                            while True:
                                time.sleep(10)
                                if not mqtt_sensor_connected:
                                    time.sleep(5)
                                    if not mqtt_sensor_connected:
                                        print("MQTT Sensor: Connection lost and auto-reconnect failed, will retry...", file=sys.stderr)
                                        break
                            break
                    else:
                        client.loop_stop()
                        client.disconnect()
                        raise ConnectionError("Connection attempt timed out")
                        
                except Exception as conn_err:
                    print(f"MQTT Sensor: Connection error: {conn_err}", file=sys.stderr)
                    try:
                        client.loop_stop()
                        client.disconnect()
                    except:
                        pass
                    raise
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    delay = min(base_delay * (2 ** (retry_count - 1)), 60)
                    print(f"MQTT Sensor: Connection failed (attempt {retry_count}/{max_retries}). Retrying in {delay} seconds...", file=sys.stderr)
                    print(f"MQTT Sensor error: {e}", file=sys.stderr)
                    time.sleep(delay)
                else:
                    print(f"MQTT Sensor: Max retries ({max_retries}) reached. MQTT subscriber stopped.", file=sys.stderr)
                    print(f"MQTT Sensor: Last error: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()
                    break

    t = threading.Thread(target=_run, name='mqtt-sensor-subscriber', daemon=True)
    t.start()
    mqtt_sensor_thread_started_ref[0] = True

