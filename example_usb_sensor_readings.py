#!/usr/bin/env python3
"""
Example USB sensor reading functions for VirtualBox.

These functions read sensors connected via USB (USB-to-Serial, Arduino, etc.)
and can be used in VirtualBox with USB passthrough.

Copy the appropriate function into raspberry_pi_client.py
and replace the read_sensor_data() function.
"""

import serial
import json
import time
import re


# ============================================================================
# EXAMPLE 1: USB-to-Serial pH Sensor
# ============================================================================

def read_ph_usb_serial(device_id, port='/dev/ttyUSB0', baudrate=9600):
    """
    Read pH sensor via USB-to-Serial converter.
    
    Expected format: "pH:7.23" or "7.23" or "pH=7.23"
    
    Args:
        device_id: Device ID
        port: Serial port (e.g., '/dev/ttyUSB0', '/dev/ttyACM0')
        baudrate: Baud rate (default: 9600)
    
    Returns:
        dict with sensor data or None on error
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        
        # Read line
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()
        
        # Parse pH value (handles various formats)
        # Format: "pH:7.23" or "7.23" or "pH=7.23" or "PH 7.23"
        match = re.search(r'(\d+\.?\d*)', line)
        if match:
            ph_value = float(match.group(1))
            # Clamp to valid pH range
            ph_value = max(0, min(14, ph_value))
            
            return {
                "device_id": device_id,
                "device_type": "ph",
                "ph": round(ph_value, 2)
            }
        
        print(f"[Warning] Could not parse pH value from: {line}")
        return None
        
    except serial.SerialException as e:
        print(f"[Error] Serial port error: {e}")
        print(f"  Check: Port {port} exists and is accessible")
        return None
    except Exception as e:
        print(f"[Error] USB serial read failed: {e}")
        return None


# ============================================================================
# EXAMPLE 2: Arduino-based Multi-Sensor (JSON over Serial)
# ============================================================================

def read_arduino_sensors_json(device_id, port='/dev/ttyACM0', baudrate=9600):
    """
    Read Arduino-based sensors sending JSON over USB Serial.
    
    Expected format: {"ph":7.2,"tds":250,"temp":24.5}
    
    Args:
        device_id: Device ID
        port: Serial port (usually '/dev/ttyACM0' for Arduino)
        baudrate: Baud rate (default: 9600)
    
    Returns:
        dict with sensor data or None on error
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        
        # Read JSON line
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()
        
        # Parse JSON
        data = json.loads(line)
        
        return {
            "device_id": device_id,
            "device_type": "ph",  # Primary sensor type
            "ph": round(data.get('ph', 0), 2) if 'ph' in data else None,
            "tds": round(data.get('tds', 0), 0) if 'tds' in data else None,
            "turbidity": round(data.get('turbidity', 0), 2) if 'turbidity' in data else None,
            "temperature": round(data.get('temp', data.get('temperature', 0)), 2) if 'temp' in data or 'temperature' in data else None,
        }
        
    except json.JSONDecodeError as e:
        print(f"[Error] Invalid JSON: {e}")
        print(f"  Received: {line}")
        return None
    except serial.SerialException as e:
        print(f"[Error] Serial port error: {e}")
        return None
    except Exception as e:
        print(f"[Error] Arduino read failed: {e}")
        return None


# ============================================================================
# EXAMPLE 3: Arduino-based Sensors (CSV Format)
# ============================================================================

def read_arduino_sensors_csv(device_id, port='/dev/ttyACM0', baudrate=9600):
    """
    Read Arduino sensors sending CSV format over USB Serial.
    
    Expected format: "7.23,250,24.5" (pH,TDS,Temperature)
    
    Args:
        device_id: Device ID
        port: Serial port
        baudrate: Baud rate
    
    Returns:
        dict with sensor data or None on error
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        
        # Read CSV line
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()
        
        # Parse CSV
        values = [float(v.strip()) for v in line.split(',')]
        
        if len(values) >= 3:
            return {
                "device_id": device_id,
                "device_type": "ph",
                "ph": round(values[0], 2),
                "tds": round(values[1], 0),
                "temperature": round(values[2], 2),
            }
        else:
            print(f"[Warning] Expected 3 values, got {len(values)}")
            return None
            
    except ValueError as e:
        print(f"[Error] Could not parse CSV values: {e}")
        print(f"  Received: {line}")
        return None
    except Exception as e:
        print(f"[Error] CSV read failed: {e}")
        return None


# ============================================================================
# EXAMPLE 4: USB Temperature Probe
# ============================================================================

def read_usb_temperature(device_id, port='/dev/ttyUSB0', baudrate=9600):
    """
    Read USB temperature probe.
    
    Expected format: "TEMP:24.5" or "24.5" or "T=24.5"
    
    Args:
        device_id: Device ID
        port: Serial port
        baudrate: Baud rate
    
    Returns:
        dict with temperature data or None on error
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        
        # Some sensors need a command
        # Uncomment if your sensor requires a command:
        # ser.write(b'TEMP?\n')
        # time.sleep(0.1)
        
        # Read response
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()
        
        # Parse temperature
        match = re.search(r'(\d+\.?\d*)', line)
        if match:
            temp_value = float(match.group(1))
            
            return {
                "device_id": device_id,
                "device_type": "temperature",
                "temperature": round(temp_value, 2)
            }
        
        print(f"[Warning] Could not parse temperature from: {line}")
        return None
        
    except Exception as e:
        print(f"[Error] USB temperature read failed: {e}")
        return None


# ============================================================================
# EXAMPLE 5: Auto-detect USB Serial Port
# ============================================================================

def find_usb_serial_port():
    """
    Auto-detect USB serial port.
    
    Returns:
        str: Port path (e.g., '/dev/ttyUSB0') or None if not found
    """
    import glob
    
    # Common USB serial port patterns
    patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyS*']
    
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            # Return first available port
            return sorted(ports)[0]
    
    return None


def read_sensor_auto_detect(device_id, baudrate=9600):
    """
    Read sensor with auto-detection of USB port.
    
    Args:
        device_id: Device ID
        baudrate: Baud rate
    
    Returns:
        dict with sensor data or None on error
    """
    port = find_usb_serial_port()
    
    if not port:
        print("[Error] No USB serial port found")
        print("  Check: Device is connected and USB passthrough is enabled")
        return None
    
    print(f"[Info] Using port: {port}")
    
    # Try different reading methods
    # Method 1: Try JSON format (Arduino)
    result = read_arduino_sensors_json(device_id, port, baudrate)
    if result:
        return result
    
    # Method 2: Try CSV format
    result = read_arduino_sensors_csv(device_id, port, baudrate)
    if result:
        return result
    
    # Method 3: Try pH sensor format
    result = read_ph_usb_serial(device_id, port, baudrate)
    if result:
        return result
    
    print("[Error] Could not read sensor data from any format")
    return None


# ============================================================================
# EXAMPLE 6: USB Sensor with Retry Logic
# ============================================================================

def read_usb_sensor_with_retry(device_id, port='/dev/ttyUSB0', baudrate=9600, max_retries=3):
    """
    Read USB sensor with retry logic for unreliable connections.
    
    Args:
        device_id: Device ID
        port: Serial port
        baudrate: Baud rate
        max_retries: Maximum number of retry attempts
    
    Returns:
        dict with sensor data or None on error
    """
    for attempt in range(max_retries):
        try:
            result = read_ph_usb_serial(device_id, port, baudrate)
            if result:
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Warning] Read failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1)
            else:
                print(f"[Error] Read failed after {max_retries} attempts: {e}")
    
    return None


# ============================================================================
# EXAMPLE 7: Multiple USB Sensors (Multiple Ports)
# ============================================================================

def read_multiple_usb_sensors(device_id, ports=['/dev/ttyUSB0', '/dev/ttyUSB1'], baudrate=9600):
    """
    Read multiple sensors on different USB ports.
    
    Args:
        device_id: Device ID
        ports: List of serial ports
        baudrate: Baud rate
    
    Returns:
        dict with combined sensor data
    """
    data = {
        "device_id": device_id,
        "device_type": "ph",
    }
    
    # Read from each port
    for i, port in enumerate(ports):
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            # Parse based on port (customize for your setup)
            if i == 0:  # pH sensor
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    data["ph"] = round(float(match.group(1)), 2)
            elif i == 1:  # TDS sensor
                match = re.search(r'(\d+)', line)
                if match:
                    data["tds"] = round(float(match.group(1)), 0)
                    
        except Exception as e:
            print(f"[Warning] Failed to read from {port}: {e}")
    
    return data


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

if __name__ == "__main__":
    """Test USB sensor readings locally."""
    print("Testing USB sensor readings...")
    print("=" * 50)
    
    # Test auto-detection
    print("\n1. Auto-detecting USB port:")
    port = find_usb_serial_port()
    if port:
        print(f"   ✅ Found port: {port}")
    else:
        print("   ❌ No USB serial port found")
        print("   Check: Device connected and USB passthrough enabled")
    
    # Test reading (if port found)
    if port:
        print(f"\n2. Testing sensor read from {port}:")
        result = read_sensor_auto_detect("test_device", 9600)
        if result:
            print(f"   ✅ Success: {result}")
        else:
            print("   ❌ Failed to read sensor data")
            print("   Check: Sensor is sending data in expected format")
    
    print("\n" + "=" * 50)
    print("Testing complete!")
    print("\nNote: If no device found, ensure:")
    print("  1. USB device is connected to Windows host")
    print("  2. VirtualBox USB passthrough is enabled")
    print("  3. Device is attached to VM (Devices → USB)")
    print("  4. User is in dialout group: sudo usermod -aG dialout $USER")

