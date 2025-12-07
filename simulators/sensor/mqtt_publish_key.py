import os
import sys
import json
import time
import paho.mqtt.publish as publish


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    device_id = os.environ.get('DEVICE_ID') or (len(sys.argv) > 1 and sys.argv[1])
    mqtt_host = os.environ.get('MQTT_HOST', 'localhost')
    mqtt_port = int(os.environ.get('MQTT_PORT', '1883'))
    mqtt_user = os.environ.get('MQTT_USER')
    mqtt_password = os.environ.get('MQTT_PASSWORD')
    mqtt_topic_base = os.environ.get('MQTT_KEYS_TOPIC_BASE', 'keys')
    
    # TLS/SSL configuration
    mqtt_use_tls = os.environ.get('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    mqtt_ca_certs = os.environ.get('MQTT_CA_CERTS')
    mqtt_certfile = os.environ.get('MQTT_CERTFILE')
    mqtt_keyfile = os.environ.get('MQTT_KEYFILE')
    mqtt_tls_insecure = os.environ.get('MQTT_TLS_INSECURE', 'false').lower() in ('true', '1', 'yes')

    if not device_id:
        print('Usage: DEVICE_ID=<id> MQTT_HOST=<host> python simulators/sensor/mqtt_publish_key.py')
        print('   or: python simulators/sensor/mqtt_publish_key.py <device_id>')
        sys.exit(1)

    pem_path = os.path.join(project_root, 'sensor_keys', device_id, 'sensor_public.pem')
    if not os.path.exists(pem_path):
        print(f"Public key not found at {pem_path}. Generate it first.")
        sys.exit(1)

    with open(pem_path, 'r', encoding='utf-8', errors='replace') as f:
        pem = f.read().strip()

    topic = f"{mqtt_topic_base}/{device_id}/public"
    payload = json.dumps({
        'device_id': device_id,
        'public_key': pem,
    })
    
    # Build publish kwargs
    publish_kwargs = {
        'hostname': mqtt_host,
        'port': mqtt_port
    }
    
    # Authentication
    if mqtt_user and mqtt_password:
        publish_kwargs['auth'] = {'username': mqtt_user, 'password': mqtt_password}
    
    # TLS/SSL configuration
    if mqtt_use_tls:
        import ssl
        tls_config = {}
        if mqtt_ca_certs and os.path.exists(mqtt_ca_certs):
            tls_config['ca_certs'] = mqtt_ca_certs
        if mqtt_certfile and os.path.exists(mqtt_certfile):
            tls_config['certfile'] = mqtt_certfile
        if mqtt_keyfile and os.path.exists(mqtt_keyfile):
            tls_config['keyfile'] = mqtt_keyfile
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        tls_config['insecure'] = mqtt_tls_insecure
        publish_kwargs['tls'] = tls_config
    
    publish.single(topic, payload, **publish_kwargs)
    print(f"Published key for '{device_id}' to topic '{topic}' on {mqtt_host}:{mqtt_port} ({'TLS' if mqtt_use_tls else 'plain'})")


if __name__ == '__main__':
    main()


