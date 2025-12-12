#!/usr/bin/env python3
"""
WSGI entry point for Apache/mod_wsgi deployment
"""
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Activate virtual environment if it exists
# Note: Modern virtual environments may not have activate_this.py
# If using WSGIDaemonProcess with python-home, this may not be necessary
venv_path = os.path.join(project_dir, 'venv')
if os.path.exists(venv_path):
    # Try Windows path first
    activate_this = os.path.join(venv_path, 'Scripts', 'activate_this.py')
    if not os.path.exists(activate_this):
        # Try Linux/Mac path
        activate_this = os.path.join(venv_path, 'bin', 'activate_this.py')
    
    if os.path.exists(activate_this):
        try:
            with open(activate_this) as f:
                exec(f.read(), {'__file__': activate_this})
        except Exception as e:
            # If activate_this.py fails, try adding venv site-packages to path
            if sys.platform == 'win32':
                site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
            else:
                site_packages = os.path.join(venv_path, 'lib', 'python{}.{}'.format(
                    sys.version_info.major, sys.version_info.minor), 'site-packages')
            
            if os.path.exists(site_packages) and site_packages not in sys.path:
                sys.path.insert(0, site_packages)
    else:
        # Fallback: add venv site-packages to path directly
        if sys.platform == 'win32':
            site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
        else:
            site_packages = os.path.join(venv_path, 'lib', 'python{}.{}'.format(
                sys.version_info.major, sys.version_info.minor), 'site-packages')
        
        if os.path.exists(site_packages) and site_packages not in sys.path:
            sys.path.insert(0, site_packages)

# Set environment variables for the application
# These are set here because mod_wsgi doesn't automatically pick up SetEnv from Apache config
# Note: Use setdefault() so existing environment variables take precedence
os.environ.setdefault('MQTT_HOST', '192.168.56.102')
os.environ.setdefault('MQTT_PORT', '8883')
# Enable MQTT subscriber by default so provision_agent can receive responses.
# If you want to keep it disabled set START_MQTT_SUBSCRIBER=0 in the environment.
os.environ.setdefault('START_MQTT_SUBSCRIBER', '1')
# TLS settings: use TLS for port 8883 or when MQTT_TLS=1.
# For local/self-signed brokers set MQTT_TLS_INSECURE=1 to skip cert verification.
os.environ.setdefault('MQTT_TLS', '1')
os.environ.setdefault('MQTT_TLS_INSECURE', '1')

# Diagnostic: help debug missing key responses
# Configure with environment variables:
#   PROVISION_RESPONSE_TOPIC (default: 'provision/response')
#   START_MQTT_DIAGNOSTIC (0/1) - enable diagnostic listener (default 1)
#   DIAGNOSTIC_DURATION (seconds) - how long to listen (default 60)
#   DIAGNOSTIC_PUBLISH (0/1) - whether to publish a short test message to PROVISION_REQUEST_TOPIC (default 0)
os.environ.setdefault('PROVISION_RESPONSE_TOPIC', 'provision/response')
os.environ.setdefault('START_MQTT_DIAGNOSTIC', '1')
os.environ.setdefault('DIAGNOSTIC_DURATION', '60')
os.environ.setdefault('DIAGNOSTIC_PUBLISH', '0')

# Database configuration - using local MySQL by default
# To use remote MySQL, set these environment variables before running:
# DB_HOST=ilmuwanutara.my DB_USER=ilmuwanutara_e2eewater DB_PASSWORD=e2eeWater@2025
os.environ.setdefault('DB_HOST', '127.0.0.1')  # Local MySQL host
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'root')  # Local MySQL user
os.environ.setdefault('DB_PASSWORD', '')  # Local MySQL password (empty by default)
os.environ.setdefault('DB_NAME', 'ilmuwanutara_e2eewater')
os.environ.setdefault('FLASK_APP', 'app.py')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DB_ENCRYPTION_KEY', 'rxyJ__s_iQzXo49e-3Cju-Vh7nnNdlFW2KK-1c_0xKo=')

# Make paho-mqtt's on_disconnect invocation tolerant to callback signature differences.
# This is applied before importing the application so user callbacks defined inside start_mqtt_key_subscriber
# won't crash the paho background thread if the paho library passes an extra "properties" arg.
try:
    import paho.mqtt.client as mqtt
    if not hasattr(mqtt.Client, '_original_do_on_disconnect'):
        mqtt.Client._original_do_on_disconnect = mqtt.Client._do_on_disconnect

        def _patched_do_on_disconnect(self, packet_from_broker=False, v1_rc=0):
            try:
                return mqtt.Client._original_do_on_disconnect(self, packet_from_broker=packet_from_broker, v1_rc=v1_rc)
            except TypeError:
                # Best-effort fallback: try calling the user on_disconnect callback with fewer args
                try:
                    cb = getattr(self, 'on_disconnect', None)
                    if not cb:
                        return
                    userdata = getattr(self, 'userdata', None)
                    rc = v1_rc
                    # Try decreasing argument counts until one works (do not raise)
                    candidates = [
                        (self, userdata, rc, None),
                        (self, userdata, rc),
                        (self, userdata),
                        (self,)
                    ]
                    for args in candidates:
                        try:
                            cb(*args)
                            return
                        except TypeError:
                            continue
                except Exception:
                    # swallow to avoid crashing mod_wsgi worker thread
                    return

        mqtt.Client._do_on_disconnect = _patched_do_on_disconnect
except Exception:
    # paho not available or patch failed — continue normally
    pass

# Lightweight diagnostic listener to confirm provision responses are published
def _start_mqtt_diagnostic():
    try:
        start_diag_env = os.environ.get('START_MQTT_DIAGNOSTIC', '0').lower()
        if start_diag_env in ('0', 'false', 'no'):
            print("[WSGI][DIAG] MQTT diagnostic disabled (START_MQTT_DIAGNOSTIC=0)", file=sys.stderr)
            return

        import threading, time, ssl, socket
        import paho.mqtt.client as mqtt
        mqtt_proto = getattr(mqtt, 'MQTTv5', mqtt.MQTTv311)

        mqtt_host = os.environ.get('MQTT_HOST', '127.0.0.1')
        try:
            mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
        except Exception:
            mqtt_port = 1883

        topic = os.environ.get('PROVISION_RESPONSE_TOPIC', 'provision/response')
        duration = int(os.environ.get('DIAGNOSTIC_DURATION', '60'))
        do_publish = os.environ.get('DIAGNOSTIC_PUBLISH', '0').lower() not in ('0', 'false', 'no')
        request_topic = os.environ.get('PROVISION_REQUEST_TOPIC', 'provision/request')

        # Flexible callbacks that accept either v3 or v5 signatures
        def _safe_on_connect(client, *args, **kwargs):
            try:
                # log args/kwargs for debugging
                print(f"[WSGI][DIAG][on_connect] args={args} kwargs={kwargs}", file=sys.stderr)
                client.subscribe(topic, qos=1)
                print(f"[WSGI][DIAG] Subscribed to diagnostic topic: {topic}", file=sys.stderr)
            except Exception as e:
                print(f"[WSGI][DIAG] on_connect error: {e}", file=sys.stderr)

        def _safe_on_disconnect(client, *args, **kwargs):
            try:
                print(f"[WSGI][DIAG][on_disconnect] args={args} kwargs={kwargs}", file=sys.stderr)
            except Exception as e:
                print(f"[WSGI][DIAG] on_disconnect error: {e}", file=sys.stderr)

        def _safe_on_message(client, *args, **kwargs):
            try:
                # message object may be in args or kwargs depending on signature
                msg = None
                for a in args:
                    if getattr(a, 'topic', None):
                        msg = a
                        break
                if not msg and 'msg' in kwargs:
                    msg = kwargs['msg']
                if msg:
                    try:
                        payload = msg.payload.decode('utf-8', errors='replace')
                    except Exception:
                        payload = repr(msg.payload)
                    print(f"[WSGI][DIAG] Received message on '{msg.topic}': {payload}", file=sys.stderr)
                else:
                    print(f"[WSGI][DIAG] on_message called with args={args} kwargs={kwargs}", file=sys.stderr)
            except Exception as e:
                print(f"[WSGI][DIAG] on_message error: {e}", file=sys.stderr)

        def _safe_on_subscribe(client, *args, **kwargs):
            print(f"[WSGI][DIAG][on_subscribe] args={args} kwargs={kwargs}", file=sys.stderr)

        def _safe_on_log(client, *args, **kwargs):
            try:
                # paho log signature varies; just print what we get
                print(f"[WSGI][DIAG][on_log] args={args} kwargs={kwargs}", file=sys.stderr)
            except Exception:
                pass

        client = mqtt.Client(client_id=f"diag-{os.getpid()}-{int(time.time())}", protocol=mqtt_proto)
        client.enable_logger()  # helps paho emit logs to python logging; we also attach on_log
        # assign flexible callbacks
        client.on_connect = _safe_on_connect
        client.on_disconnect = _safe_on_disconnect
        client.on_message = _safe_on_message
        client.on_subscribe = _safe_on_subscribe
        client.on_log = _safe_on_log

        use_tls = os.environ.get('MQTT_TLS', '0').lower() not in ('0', 'false', 'no') or mqtt_port == 8883
        if use_tls:
            ctx = ssl.create_default_context()
            if os.environ.get('MQTT_TLS_INSECURE', '0').lower() in ('1', 'true', 'yes'):
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                print("[WSGI][DIAG] MQTT diagnostic using insecure TLS (skip cert verification)", file=sys.stderr)
            client.tls_set_context(ctx)
            # also set tls_insecure_set for older paho behaviour
            try:
                client.tls_insecure_set(os.environ.get('MQTT_TLS_INSECURE', '0').lower() in ('1', 'true', 'yes'))
            except Exception:
                pass

        def _diag_runner():
            try:
                print(f"[WSGI][DIAG] Diagnostic connecting to {mqtt_host}:{mqtt_port} (use_tls={use_tls})", file=sys.stderr)
                client.connect(mqtt_host, mqtt_port, keepalive=10)
                client.loop_start()
            except Exception as e:
                print(f"[WSGI][DIAG] MQTT diagnostic connect failed to {mqtt_host}:{mqtt_port}: {e}", file=sys.stderr)
                return

            # optionally publish a short request to provoke a response (disabled by default)
            if do_publish:
                try:
                    payload = '{"diag":"ping"}'
                    client.publish(request_topic, payload, qos=1)
                    print(f"[WSGI][DIAG] Published diagnostic message to {request_topic}", file=sys.stderr)
                except Exception as e:
                    print(f"[WSGI][DIAG] Diagnostic publish failed: {e}", file=sys.stderr)

            # Listen for 'duration' seconds then stop
            time.sleep(duration)
            try:
                client.loop_stop()
                client.disconnect()
                print(f"[WSGI][DIAG] Diagnostic listener stopped after {duration}s", file=sys.stderr)
            except Exception as e:
                print(f"[WSGI][DIAG] Diagnostic cleanup error: {e}", file=sys.stderr)

        t = threading.Thread(target=_diag_runner, daemon=True)
        t.start()
        print(f"[WSGI][DIAG] Diagnostic listener started (listening for {duration}s) on topic '{topic}'", file=sys.stderr)
    except Exception as e:
        print(f"[WSGI][DIAG] Failed to start diagnostic listener: {e}", file=sys.stderr)

# Start diagnostic early so it can capture responses to provision requests
_start_mqtt_diagnostic()

# Import the Flask application
try:
    # Log WSGI loading
    print(f"[WSGI] Loading app from {project_dir}", file=sys.stderr)
    print(f"[WSGI] MQTT_HOST env: {os.environ.get('MQTT_HOST', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] MQTT_PORT env: {os.environ.get('MQTT_PORT', 'NOT SET')}", file=sys.stderr)
    # Log database configuration
    print(f"[WSGI] DB_HOST: {os.environ.get('DB_HOST', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] DB_PORT: {os.environ.get('DB_PORT', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] DB_USER: {os.environ.get('DB_USER', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] DB_NAME: {os.environ.get('DB_NAME', 'NOT SET')}", file=sys.stderr)
    print(f"[WSGI] DB_PASSWORD: {'*' * len(os.environ.get('DB_PASSWORD', '')) if os.environ.get('DB_PASSWORD') else 'NOT SET'}", file=sys.stderr)
    
    from app import app as application, start_mqtt_key_subscriber

    # MQTT subscriber start is optional under mod_wsgi to avoid background thread errors/log spam.
    # Default to enabled so provision_agent can receive responses unless explicitly disabled.
    start_mqtt_env = os.environ.get('START_MQTT_SUBSCRIBER', '1').lower()
    start_mqtt = start_mqtt_env not in ('0', 'false', 'no')
    if not start_mqtt:
        print(f"[WSGI] START_MQTT_SUBSCRIBER is disabled (current value: {start_mqtt_env}). To enable set START_MQTT_SUBSCRIBER=1", file=sys.stderr)
    else:
        mqtt_host = os.environ.get('MQTT_HOST', '').strip()
        try:
            mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
        except Exception:
            mqtt_port = 1883

        if not mqtt_host:
            print("[WSGI] MQTT_HOST not configured; skipping MQTT subscriber start.", file=sys.stderr)
        else:
            print(f"[WSGI] Checking MQTT broker {mqtt_host}:{mqtt_port} before starting subscriber...", file=sys.stderr)
            try:
                import socket
                use_tls_env = os.environ.get('MQTT_TLS', '0').lower()
                use_tls = use_tls_env not in ('0', 'false', 'no') or mqtt_port == 8883
                if use_tls:
                    import ssl
                    ctx = ssl.create_default_context()
                    if os.environ.get('MQTT_TLS_INSECURE', '0').lower() in ('1', 'true', 'yes'):
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        print("[WSGI] MQTT TLS insecure mode enabled (MQTT_TLS_INSECURE=1)", file=sys.stderr)
                    with socket.create_connection((mqtt_host, mqtt_port), timeout=5) as sock:
                        with ctx.wrap_socket(sock, server_hostname=mqtt_host):
                            # successful TLS handshake
                            pass
                else:
                    # plain TCP check
                    with socket.create_connection((mqtt_host, mqtt_port), timeout=3):
                        pass
            except Exception as conn_err:
                print(f"[WSGI] MQTT broker appears unreachable or TLS handshake failed ({mqtt_host}:{mqtt_port}): {conn_err}", file=sys.stderr)
                print("[WSGI] Skipping MQTT subscriber start to avoid repeated connection attempts. "
                      "Set START_MQTT_SUBSCRIBER=0 to disable, or fix broker/network/certs and restart Apache.", file=sys.stderr)
            else:
                print("[WSGI] Broker reachable — attempting to start MQTT key subscriber...", file=sys.stderr)
                try:
                    start_mqtt_key_subscriber()
                    print("[WSGI] MQTT key subscriber started successfully", file=sys.stderr)
                except TypeError as te:
                    # Common cause: paho-mqtt callback signature mismatch (on_disconnect signature mismatch)
                    import traceback
                    print(f"[WSGI] MQTT subscriber raised TypeError (likely callback signature issue): {te}", file=sys.stderr)
                    print("[WSGI] Hint: verify start_mqtt_key_subscriber callback signatures and paho-mqtt version.", file=sys.stderr)
                    print(f"[WSGI] Traceback: {traceback.format_exc()}", file=sys.stderr)
                except Exception as mqtt_err:
                    import traceback
                    print(f"[WSGI] MQTT subscriber start error (non-fatal): {mqtt_err}", file=sys.stderr)
                    print(f"[WSGI] Traceback: {traceback.format_exc()}", file=sys.stderr)

except Exception as e:
    # Log error for debugging (check Apache error logs)
    import traceback
    error_msg = f"[WSGI] Failed to import app: {str(e)}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    raise

# Git / Push instructions (PowerShell)
# -----------------------------------
# cd "C:\Users\NURMIZAN QISTINA\Desktop\fyp\iot-secure-water-monitor"
# 
# If repo not initialized:
#   git init
#   git add .
#   git commit -m "chore: initial commit"
#   git remote add origin https://github.com/<your-username>/<your-repo>.git
#   git branch -M main
#   git push -u origin main
#
# If repo already exists remotely and you cloned earlier:
#   git status
#   git add .
#   git commit -m "chore: update"
#   git pull --rebase origin main      # resolve conflicts if any
#   git push
#
# Notes:
# - Use the interactive credential prompt or Git Credential Manager to authenticate.
# - For GitHub over HTTPS use a Personal Access Token (PAT) when prompted; DO NOT hardcode tokens into files.
# - To use SSH, add your public key to the remote account and use the SSH URL (git@github.com:...).
# - If you need to force-push (careful), use: git push --force-with-lease origin main

