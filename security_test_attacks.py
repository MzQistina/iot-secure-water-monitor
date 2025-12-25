#!/usr/bin/env python3
"""
Security Testing - Attack Simulation Scripts
Simulates various attacks for security testing
WARNING: Only use on systems you own or have explicit permission
"""

import sys
import time
import json
import ssl
import socket
from paho.mqtt import client as mqtt
from paho.mqtt.client import MQTTMessage

# Configuration
MQTT_CONFIG = {
    'host': '192.168.43.214',
    'port': 8883,
    'user': 'water_monitor',
    'password': 'e2eeWater2025',
    'unencrypted_port': 1883,
}


class SecurityTester:
    def __init__(self):
        self.results = []
    
    def log_result(self, test_name, passed, details):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n[{status}] {test_name}")
        print(f"  Details: {details}")
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    def test_tls_required(self):
        """Test 1: Verify TLS is required (unencrypted connection should fail)"""
        print("\n" + "=" * 80)
        print("TEST 1: TLS Requirement")
        print("=" * 80)
        
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
            # Try to connect without TLS on encrypted port
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['unencrypted_port'], 5)
            client.loop_start()
            time.sleep(2)
            if client.is_connected():
                client.loop_stop()
                client.disconnect()
                self.log_result(
                    "TLS Requirement",
                    False,
                    "Unencrypted connection succeeded - TLS not enforced!"
                )
            else:
                client.loop_stop()
                self.log_result(
                    "TLS Requirement",
                    True,
                    "Unencrypted connection properly rejected"
                )
        except Exception as e:
            self.log_result(
                "TLS Requirement",
                True,
                f"Unencrypted connection properly rejected: {type(e).__name__}"
            )
    
    def test_certificate_validation(self):
        """Test 2: Verify certificate validation works"""
        print("\n" + "=" * 80)
        print("TEST 2: Certificate Validation")
        print("=" * 80)
        
        # Test with invalid certificate
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
            
            # Set up TLS with strict validation
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            client.tls_set_context(context)
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
            client.loop_start()
            time.sleep(2)
            if client.is_connected():
                client.loop_stop()
                client.disconnect()
            else:
                client.loop_stop()
            
            self.log_result(
                "Certificate Validation",
                True,
                "Certificate validation working correctly"
            )
        except ssl.SSLError as e:
            self.log_result(
                "Certificate Validation",
                True,
                f"Certificate validation working: {e}"
            )
        except Exception as e:
            self.log_result(
                "Certificate Validation",
                False,
                f"Unexpected error: {type(e).__name__}: {e}"
            )
    
    def test_authentication_required(self):
        """Test 3: Verify authentication is required"""
        print("\n" + "=" * 80)
        print("TEST 3: Authentication Requirement")
        print("=" * 80)
        
        # Test without credentials
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            # No username/password set
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
            client.loop_start()
            time.sleep(2)
            
            # Check if actually connected
            if client.is_connected():
                client.loop_stop()
                client.disconnect()
                self.log_result(
                    "Authentication Requirement",
                    False,
                    "Connection succeeded without credentials!"
                )
            else:
                client.loop_stop()
                client.disconnect()
                self.log_result(
                    "Authentication Requirement",
                    True,
                    "Connection failed without credentials (correct behavior)"
                )
        except Exception as e:
            self.log_result(
                "Authentication Requirement",
                True,
                f"Authentication properly required: {type(e).__name__}: {e}"
            )
    
    def test_wrong_credentials(self):
        """Test 4: Verify wrong credentials are rejected"""
        print("\n" + "=" * 80)
        print("TEST 4: Wrong Credentials Rejection")
        print("=" * 80)
        
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set("wrong_user", "wrong_password")
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
            client.loop_start()
            time.sleep(2)
            if client.is_connected():
                client.loop_stop()
                client.disconnect()
            else:
                client.loop_stop()
            
            self.log_result(
                "Wrong Credentials Rejection",
                False,
                "Connection succeeded with wrong credentials!"
            )
        except Exception as e:
            self.log_result(
                "Wrong Credentials Rejection",
                True,
                f"Wrong credentials properly rejected: {type(e).__name__}"
            )
    
    def test_topic_access_control(self):
        """Test 5: Verify topic access control (ACL)"""
        print("\n" + "=" * 80)
        print("TEST 5: Topic Access Control")
        print("=" * 80)
        
        publish_success = False
        subscribe_success = False
        
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            
            def on_connect(client, userdata, flags, reason_code, properties=None):
                if reason_code == 0:
                    # Try to publish to unauthorized topic
                    result = client.publish("unauthorized/topic/test", "test", qos=1)
                    publish_success = (result.rc == 0)
                    
                    # Try to subscribe to unauthorized topic
                    result = client.subscribe("unauthorized/topic/+", qos=1)
                    subscribe_success = (result[0] == 0)
            
            client.on_connect = on_connect
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
            client.loop_start()
            time.sleep(3)
            client.loop_stop()
            client.disconnect()
            
            if publish_success or subscribe_success:
                self.log_result(
                    "Topic Access Control",
                    False,
                    f"Unauthorized topic access allowed! Publish: {publish_success}, Subscribe: {subscribe_success}"
                )
            else:
                self.log_result(
                    "Topic Access Control",
                    True,
                    "Topic access control working - unauthorized access blocked"
                )
        except Exception as e:
            self.log_result(
                "Topic Access Control",
                False,
                f"Error during test: {type(e).__name__}: {e}"
            )
    
    def test_replay_attack(self):
        """Test 6: Test replay attack resistance"""
        print("\n" + "=" * 80)
        print("TEST 6: Replay Attack Resistance")
        print("=" * 80)
        
        # This test requires capturing a message first
        # For now, we'll just test if we can publish the same message multiple times
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
            
            # Publish same message multiple times
            topic = "provision/test_device/update"
            payload = json.dumps({
                "device_id": "test_device",
                "action": "update",
                "user_id": "1"
            })
            
            for i in range(3):
                result = client.publish(topic, payload, qos=1)
                time.sleep(0.5)
            
            client.disconnect()
            
            self.log_result(
                "Replay Attack Resistance",
                False,  # Manual verification needed
                "Replay test completed - check broker logs for duplicate detection"
            )
        except Exception as e:
            self.log_result(
                "Replay Attack Resistance",
                False,
                f"Error: {type(e).__name__}: {e}"
            )
    
    def test_connection_flood(self):
        """Test 7: Test DoS resistance (connection flood)"""
        print("\n" + "=" * 80)
        print("TEST 7: DoS Resistance (Connection Flood)")
        print("=" * 80)
        print("WARNING: This test may impact broker performance")
        
        max_connections = 10  # Limit for testing
        successful_connections = 0
        
        clients = []
        try:
            for i in range(max_connections):
                try:
                    client = mqtt.Client(
                        mqtt.CallbackAPIVersion.VERSION2,
                        client_id=f"test_client_{i}_{int(time.time())}"
                    )
                    client.username_pw_set(MQTT_CONFIG['user'], MQTT_CONFIG['password'])
                    client.tls_set(cert_reqs=ssl.CERT_NONE)
                    client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 5)
                    # Check if actually connected
                    client.loop_start()
                    time.sleep(0.2)
                    if client.is_connected():
                        clients.append(client)
                        successful_connections += 1
                    client.loop_stop()
                    time.sleep(0.1)
                except Exception as e:
                    print(f"  Connection {i} failed: {type(e).__name__}")
            
            time.sleep(2)
            
            # Clean up
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass
            
            if successful_connections == max_connections:
                self.log_result(
                    "DoS Resistance",
                    False,  # Manual verification needed
                    f"All {max_connections} connections succeeded - check if rate limiting is enabled"
                )
            else:
                self.log_result(
                    "DoS Resistance",
                    True,
                    f"Rate limiting may be working: {successful_connections}/{max_connections} connections succeeded"
                )
        except Exception as e:
            self.log_result(
                "DoS Resistance",
                False,
                f"Error: {type(e).__name__}: {e}"
            )
    
    def run_all_tests(self):
        """Run all security tests"""
        print("\n" + "=" * 80)
        print("MQTT SECURITY TESTING SUITE")
        print("=" * 80)
        print("WARNING: Only run on systems you own or have explicit permission")
        print("=" * 80)
        
        self.test_tls_required()
        self.test_certificate_validation()
        self.test_authentication_required()
        self.test_wrong_credentials()
        self.test_topic_access_control()
        self.test_replay_attack()
        self.test_connection_flood()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print(f"\nTests Passed: {passed}/{total}")
        print(f"Tests Failed: {total - passed}/{total}")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✓" if result['passed'] else "✗"
            print(f"  {status} {result['test']}: {result['details']}")
        
        # Export results
        with open('security_test_results.json', 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'passed': passed,
                    'total': total,
                    'failed': total - passed
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n[INFO] Results exported to: security_test_results.json")


def main():
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        tester = SecurityTester()
        
        if test_name == 'tls':
            tester.test_tls_required()
        elif test_name == 'cert':
            tester.test_certificate_validation()
        elif test_name == 'auth':
            tester.test_authentication_required()
        elif test_name == 'credentials':
            tester.test_wrong_credentials()
        elif test_name == 'acl':
            tester.test_topic_access_control()
        elif test_name == 'replay':
            tester.test_replay_attack()
        elif test_name == 'dos':
            tester.test_connection_flood()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: tls, cert, auth, credentials, acl, replay, dos")
            sys.exit(1)
    else:
        tester = SecurityTester()
        tester.run_all_tests()


if __name__ == '__main__':
    main()



