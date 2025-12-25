#!/usr/bin/env python3
"""
Security Testing Analyzer for MQTT Traffic
Analyzes Wireshark capture files (.pcap) for security vulnerabilities
"""

import sys
import json
from collections import defaultdict
from datetime import datetime

try:
    import pyshark
except ImportError:
    print("ERROR: pyshark not installed. Install with: pip install pyshark")
    sys.exit(1)

class MQTTSecurityAnalyzer:
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.findings = []
        self.stats = {
            'total_packets': 0,
            'mqtt_packets': 0,
            'encrypted_connections': 0,
            'unencrypted_connections': 0,
            'topics': set(),
            'message_types': defaultdict(int),
            'failed_auth': 0,
            'unique_clients': set(),
        }
    
    def analyze(self):
        """Main analysis function"""
        print("=" * 80)
        print("MQTT Security Analysis")
        print("=" * 80)
        print(f"Analyzing: {self.pcap_file}\n")
        
        try:
            cap = pyshark.FileCapture(
                self.pcap_file,
                display_filter='mqtt or tcp.port == 8883 or tcp.port == 1883'
            )
            
            for packet in cap:
                self.stats['total_packets'] += 1
                self._analyze_packet(packet)
            
            cap.close()
            
        except Exception as e:
            print(f"ERROR: Failed to analyze capture file: {e}")
            return False
        
        self._generate_report()
        return True
    
    def _analyze_packet(self, packet):
        """Analyze individual packet"""
        # Check for MQTT protocol
        if hasattr(packet, 'mqtt'):
            self.stats['mqtt_packets'] += 1
            self._analyze_mqtt_packet(packet)
        
        # Check for TLS
        if hasattr(packet, 'tls'):
            self._analyze_tls_packet(packet)
        
        # Check ports
        if hasattr(packet, 'tcp'):
            self._analyze_tcp_packet(packet)
    
    def _analyze_mqtt_packet(self, packet):
        """Analyze MQTT-specific packet"""
        mqtt = packet.mqtt
        
        # Message type
        if hasattr(mqtt, 'msgtype'):
            msgtype = int(mqtt.msgtype)
            self.stats['message_types'][msgtype] += 1
            
            # CONNECT (1)
            if msgtype == 1:
                self._analyze_connect(packet)
            
            # PUBLISH (3)
            elif msgtype == 3:
                self._analyze_publish(packet)
            
            # SUBSCRIBE (8)
            elif msgtype == 8:
                self._analyze_subscribe(packet)
            
            # CONNACK (2) - check for auth failures
            elif msgtype == 2:
                self._analyze_connack(packet)
    
    def _analyze_connect(self, packet):
        """Analyze MQTT CONNECT packet"""
        mqtt = packet.mqtt
        
        # Extract client ID
        if hasattr(mqtt, 'clientid'):
            self.stats['unique_clients'].add(mqtt.clientid)
        
        # Check for username/password
        if hasattr(mqtt, 'username'):
            username = mqtt.username
            # Check if password is visible (shouldn't be with TLS)
            if hasattr(mqtt, 'password'):
                self.findings.append({
                    'severity': 'HIGH',
                    'type': 'Credential Exposure',
                    'description': f'Password visible in CONNECT packet for user: {username}',
                    'packet': packet.number
                })
    
    def _analyze_publish(self, packet):
        """Analyze MQTT PUBLISH packet"""
        mqtt = packet.mqtt
        
        # Extract topic
        if hasattr(mqtt, 'topic'):
            topic = mqtt.topic
            self.stats['topics'].add(topic)
            
            # Check for sensitive topics
            sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
            if any(keyword in topic.lower() for keyword in sensitive_keywords):
                self.findings.append({
                    'severity': 'MEDIUM',
                    'type': 'Sensitive Topic',
                    'description': f'Sensitive topic name detected: {topic}',
                    'packet': packet.number
                })
        
        # Check if payload is readable (shouldn't be with TLS)
        if hasattr(mqtt, 'msg'):
            try:
                payload = mqtt.msg
                if payload and len(payload) > 0:
                    # If we can read it, it might be unencrypted
                    if packet.transport_layer == 'TCP':
                        if hasattr(packet.tcp, 'dstport') and packet.tcp.dstport == '1883':
                            self.findings.append({
                                'severity': 'CRITICAL',
                                'type': 'Unencrypted Payload',
                                'description': f'MQTT payload visible in unencrypted connection',
                                'packet': packet.number
                            })
            except:
                pass
    
    def _analyze_subscribe(self, packet):
        """Analyze MQTT SUBSCRIBE packet"""
        mqtt = packet.mqtt
        
        # Extract topics being subscribed to
        if hasattr(mqtt, 'topic'):
            topic = mqtt.topic
            self.stats['topics'].add(topic)
    
    def _analyze_connack(self, packet):
        """Analyze MQTT CONNACK packet for auth failures"""
        mqtt = packet.mqtt
        
        # Check return code (5 = not authorized)
        if hasattr(mqtt, 'connack_flags'):
            # Return code 5 indicates authentication failure
            if hasattr(mqtt, 'connack_flags') and '5' in str(mqtt.connack_flags):
                self.stats['failed_auth'] += 1
                self.findings.append({
                    'severity': 'INFO',
                    'type': 'Authentication Failure',
                    'description': 'Failed authentication attempt detected',
                    'packet': packet.number
                })
    
    def _analyze_tls_packet(self, packet):
        """Analyze TLS packet"""
        tls = packet.tls
        
        # Check TLS version
        if hasattr(tls, 'record_version'):
            version = tls.record_version
            if version and '1.0' in str(version) or '1.1' in str(version):
                self.findings.append({
                    'severity': 'MEDIUM',
                    'type': 'Weak TLS Version',
                    'description': f'Old TLS version detected: {version}',
                    'packet': packet.number
                })
        
        # Check handshake
        if hasattr(tls, 'handshake_type'):
            if tls.handshake_type == '1':  # Client Hello
                self.stats['encrypted_connections'] += 1
    
    def _analyze_tcp_packet(self, packet):
        """Analyze TCP packet for port information"""
        tcp = packet.tcp
        
        # Check for unencrypted MQTT (port 1883)
        if hasattr(tcp, 'dstport') and tcp.dstport == '1883':
            self.stats['unencrypted_connections'] += 1
            self.findings.append({
                'severity': 'CRITICAL',
                'type': 'Unencrypted Connection',
                'description': 'MQTT traffic on unencrypted port 1883',
                'packet': packet.number
            })
        
        # Check for encrypted MQTT (port 8883)
        if hasattr(tcp, 'dstport') and tcp.dstport == '8883':
            self.stats['encrypted_connections'] += 1
    
    def _generate_report(self):
        """Generate security analysis report"""
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Statistics
        print("\n[STATISTICS]")
        print(f"  Total Packets Analyzed: {self.stats['total_packets']}")
        print(f"  MQTT Packets: {self.stats['mqtt_packets']}")
        print(f"  Encrypted Connections (8883): {self.stats['encrypted_connections']}")
        print(f"  Unencrypted Connections (1883): {self.stats['unencrypted_connections']}")
        print(f"  Unique Clients: {len(self.stats['unique_clients'])}")
        print(f"  Unique Topics: {len(self.stats['topics'])}")
        print(f"  Failed Auth Attempts: {self.stats['failed_auth']}")
        
        # Message Types
        print("\n[MQTT MESSAGE TYPES]")
        msgtype_names = {
            1: 'CONNECT',
            2: 'CONNACK',
            3: 'PUBLISH',
            4: 'PUBACK',
            5: 'PUBREC',
            6: 'PUBREL',
            7: 'PUBCOMP',
            8: 'SUBSCRIBE',
            9: 'SUBACK',
            10: 'UNSUBSCRIBE',
            11: 'UNSUBACK',
            12: 'PINGREQ',
            13: 'PINGRESP',
            14: 'DISCONNECT'
        }
        for msgtype, count in sorted(self.stats['message_types'].items()):
            name = msgtype_names.get(msgtype, f'UNKNOWN({msgtype})')
            print(f"  {name}: {count}")
        
        # Topics
        if self.stats['topics']:
            print("\n[DISCOVERED TOPICS]")
            for topic in sorted(self.stats['topics']):
                print(f"  - {topic}")
        
        # Security Findings
        print("\n" + "=" * 80)
        print("SECURITY FINDINGS")
        print("=" * 80)
        
        if not self.findings:
            print("\n✓ No security issues detected!")
        else:
            # Group by severity
            by_severity = defaultdict(list)
            for finding in self.findings:
                by_severity[finding['severity']].append(finding)
            
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
            for severity in severity_order:
                if severity in by_severity:
                    print(f"\n[{severity}] Issues: {len(by_severity[severity])}")
                    for finding in by_severity[severity]:
                        print(f"  • {finding['type']}: {finding['description']}")
                        print(f"    Packet: {finding['packet']}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = []
        
        if self.stats['unencrypted_connections'] > 0:
            recommendations.append("CRITICAL: Disable port 1883 or restrict access")
        
        if self.stats['encrypted_connections'] == 0 and self.stats['mqtt_packets'] > 0:
            recommendations.append("CRITICAL: Enable TLS encryption for all MQTT traffic")
        
        if any(f['severity'] == 'CRITICAL' for f in self.findings):
            recommendations.append("CRITICAL: Address critical security findings immediately")
        
        if len(self.stats['topics']) > 50:
            recommendations.append("INFO: Consider topic naming conventions and access control")
        
        if self.stats['failed_auth'] > 10:
            recommendations.append("MEDIUM: Implement rate limiting on authentication failures")
        
        if not recommendations:
            recommendations.append("✓ Security posture looks good. Continue monitoring.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        # Export findings
        self._export_findings()
    
    def _export_findings(self):
        """Export findings to JSON file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'pcap_file': self.pcap_file,
            'statistics': {
                'total_packets': self.stats['total_packets'],
                'mqtt_packets': self.stats['mqtt_packets'],
                'encrypted_connections': self.stats['encrypted_connections'],
                'unencrypted_connections': self.stats['unencrypted_connections'],
                'unique_clients': len(self.stats['unique_clients']),
                'unique_topics': len(self.stats['topics']),
                'failed_auth': self.stats['failed_auth'],
            },
            'topics': sorted(list(self.stats['topics'])),
            'clients': sorted(list(self.stats['unique_clients'])),
            'findings': self.findings
        }
        
        output_file = self.pcap_file.replace('.pcap', '_security_report.json')
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[INFO] Full report exported to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python security_test_analyzer.py <pcap_file>")
        print("\nExample:")
        print("  python security_test_analyzer.py mqtt_capture.pcap")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    analyzer = MQTTSecurityAnalyzer(pcap_file)
    analyzer.analyze()


if __name__ == '__main__':
    main()



