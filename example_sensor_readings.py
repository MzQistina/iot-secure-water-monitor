#!/usr/bin/env python3
"""
Example sensor reading functions for real hardware.

Copy the appropriate function into raspberry_pi_client.py
and replace the read_sensor_data() function.
"""

import time
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from w1thermsensor import W1ThermSensor
import adafruit_dht


# ============================================================================
# EXAMPLE 1: Single pH Sensor with ADS1115
# ============================================================================

def read_ph_sensor_ads1115(device_id):
    """Read pH sensor via ADS1115 ADC on channel 0."""
    try:
        # Initialize I2C and ADC
        i2c = board.I2C()
        ads = ADS.ADS1115(i2c)
        
        # Create analog input on channel 0
        ph_channel = AnalogIn(ads, ADS.P0)
        
        # Read voltage (0-3.3V)
        voltage = ph_channel.voltage
        
        # Convert voltage to pH
        # NOTE: This formula needs calibration with buffer solutions!
        # Typical DFRobot pH sensor: pH = 3.3 * voltage
        ph_value = 3.3 * voltage
        
        # Clamp to valid pH range
        ph_value = max(0, min(14, ph_value))
        
        return {
            "device_id": device_id,
            "device_type": "ph",
            "ph": round(ph_value, 2),
        }
    except Exception as e:
        print(f"[Error] Failed to read pH sensor: {e}")
        return None


# ============================================================================
# EXAMPLE 2: Multiple Analog Sensors (pH, TDS, Turbidity)
# ============================================================================

def read_multiple_analog_sensors(device_id):
    """Read pH, TDS, and Turbidity sensors via ADS1115."""
    try:
        # Initialize I2C and ADC
        i2c = board.I2C()
        ads = ADS.ADS1115(i2c)
        
        # Create analog inputs
        ph_channel = AnalogIn(ads, ADS.P0)      # pH on channel 0
        tds_channel = AnalogIn(ads, ADS.P1)     # TDS on channel 1
        turb_channel = AnalogIn(ads, ADS.P2)    # Turbidity on channel 2
        
        # Read pH
        ph_voltage = ph_channel.voltage
        ph_value = 3.3 * ph_voltage  # Calibrate as needed
        ph_value = max(0, min(14, ph_value))
        
        # Read TDS
        tds_voltage = tds_channel.voltage
        # TDS formula: ppm = (voltage * 1000) / 2
        tds_value = (tds_voltage * 1000) / 2
        tds_value = max(0, min(1000, tds_value))
        
        # Read Turbidity
        turb_voltage = turb_channel.voltage
        # Turbidity formula: NTU = voltage * 5
        turb_value = turb_voltage * 5
        turb_value = max(0, min(5, turb_value))
        
        return {
            "device_id": device_id,
            "device_type": "ph",
            "ph": round(ph_value, 2),
            "tds": round(tds_value, 0),
            "turbidity": round(turb_value, 2),
        }
    except Exception as e:
        print(f"[Error] Failed to read analog sensors: {e}")
        return None


# ============================================================================
# EXAMPLE 3: DS18B20 Temperature Sensor
# ============================================================================

def read_ds18b20_temperature(device_id):
    """Read DS18B20 temperature sensor."""
    try:
        # Initialize sensor
        sensor = W1ThermSensor()
        
        # Read temperature in Celsius
        temperature = sensor.get_temperature()
        
        return {
            "device_id": device_id,
            "device_type": "temperature",
            "temperature": round(temperature, 2),
        }
    except Exception as e:
        print(f"[Error] Failed to read DS18B20: {e}")
        return None


# ============================================================================
# EXAMPLE 4: DHT22 Temperature & Humidity
# ============================================================================

def read_dht22_temperature_humidity(device_id, gpio_pin=board.D4):
    """Read DHT22 temperature and humidity sensor.
    
    Args:
        device_id: Device ID
        gpio_pin: GPIO pin (default: D4, which is GPIO 4)
    """
    try:
        # Initialize DHT22
        dht = adafruit_dht.DHT22(gpio_pin)
        
        # Read temperature and humidity
        temperature = dht.temperature
        humidity = dht.humidity
        
        # Handle None values (sensor read errors)
        if temperature is None or humidity is None:
            print("[Warning] DHT22 read failed, retrying...")
            time.sleep(2)
            temperature = dht.temperature
            humidity = dht.humidity
        
        if temperature is None or humidity is None:
            raise RuntimeError("DHT22 read failed after retry")
        
        return {
            "device_id": device_id,
            "device_type": "temperature",
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
        }
    except RuntimeError as e:
        print(f"[Error] DHT22 read error: {e}")
        return None
    except Exception as e:
        print(f"[Error] DHT22 failed: {e}")
        return None


# ============================================================================
# EXAMPLE 5: Complete Multi-Sensor Setup
# ============================================================================

def read_all_sensors(device_id):
    """Read all connected sensors (pH, TDS, Turbidity, Temperature)."""
    data = {
        "device_id": device_id,
        "device_type": "ph",  # Primary sensor
    }
    
    # Read analog sensors via ADS1115
    try:
        i2c = board.I2C()
        ads = ADS.ADS1115(i2c)
        
        # pH sensor
        ph_channel = AnalogIn(ads, ADS.P0)
        ph_voltage = ph_channel.voltage
        ph_value = 3.3 * ph_voltage
        data["ph"] = round(max(0, min(14, ph_value)), 2)
        
        # TDS sensor
        tds_channel = AnalogIn(ads, ADS.P1)
        tds_voltage = tds_channel.voltage
        tds_value = (tds_voltage * 1000) / 2
        data["tds"] = round(max(0, min(1000, tds_value)), 0)
        
        # Turbidity sensor
        turb_channel = AnalogIn(ads, ADS.P2)
        turb_voltage = turb_channel.voltage
        turb_value = turb_voltage * 5
        data["turbidity"] = round(max(0, min(5, turb_value)), 2)
        
    except Exception as e:
        print(f"[Warning] Analog sensors read error: {e}")
    
    # Read temperature from DS18B20
    try:
        temp_sensor = W1ThermSensor()
        temperature = temp_sensor.get_temperature()
        data["temperature"] = round(temperature, 2)
    except Exception as e:
        print(f"[Warning] Temperature sensor read error: {e}")
    
    return data


# ============================================================================
# EXAMPLE 6: Sensor Reading with Averaging (Noise Reduction)
# ============================================================================

def read_ph_sensor_averaged(device_id, samples=10):
    """Read pH sensor with averaging to reduce noise."""
    try:
        i2c = board.I2C()
        ads = ADS.ADS1115(i2c)
        ph_channel = AnalogIn(ads, ADS.P0)
        
        # Take multiple samples and average
        voltages = []
        for _ in range(samples):
            voltages.append(ph_channel.voltage)
            time.sleep(0.1)  # Small delay between readings
        
        avg_voltage = sum(voltages) / len(voltages)
        ph_value = 3.3 * avg_voltage
        ph_value = max(0, min(14, ph_value))
        
        return {
            "device_id": device_id,
            "device_type": "ph",
            "ph": round(ph_value, 2),
        }
    except Exception as e:
        print(f"[Error] Failed to read pH sensor: {e}")
        return None


# ============================================================================
# EXAMPLE 7: Sensor Reading with Retry Logic
# ============================================================================

def read_sensor_with_retry(device_id, max_retries=3, retry_delay=1):
    """Read sensor with retry logic for unreliable connections."""
    for attempt in range(max_retries):
        try:
            i2c = board.I2C()
            ads = ADS.ADS1115(i2c)
            ph_channel = AnalogIn(ads, ADS.P0)
            
            voltage = ph_channel.voltage
            ph_value = 3.3 * voltage
            ph_value = max(0, min(14, ph_value))
            
            return {
                "device_id": device_id,
                "device_type": "ph",
                "ph": round(ph_value, 2),
            }
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Warning] Sensor read failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                print(f"[Error] Sensor read failed after {max_retries} attempts: {e}")
                return None
    
    return None


# ============================================================================
# EXAMPLE 8: Calibrated pH Sensor Reading
# ============================================================================

def read_ph_sensor_calibrated(device_id, calibration_a=3.3, calibration_b=0.0):
    """Read pH sensor with custom calibration.
    
    Args:
        device_id: Device ID
        calibration_a: Calibration coefficient (slope)
        calibration_b: Calibration offset (intercept)
    
    Calibration formula: pH = a * voltage + b
    
    To calibrate:
    1. Measure voltage at pH 4.0 buffer: v4
    2. Measure voltage at pH 7.0 buffer: v7
    3. Calculate: a = 3.0 / (v7 - v4)
    4. Calculate: b = 4.0 - a * v4
    """
    try:
        i2c = board.I2C()
        ads = ADS.ADS1115(i2c)
        ph_channel = AnalogIn(ads, ADS.P0)
        
        voltage = ph_channel.voltage
        ph_value = calibration_a * voltage + calibration_b
        ph_value = max(0, min(14, ph_value))
        
        return {
            "device_id": device_id,
            "device_type": "ph",
            "ph": round(ph_value, 2),
        }
    except Exception as e:
        print(f"[Error] Failed to read pH sensor: {e}")
        return None


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

if __name__ == "__main__":
    """Test sensor readings locally."""
    print("Testing sensor readings...")
    print("=" * 50)
    
    # Test pH sensor
    print("\n1. Testing pH sensor:")
    result = read_ph_sensor_ads1115("test_pH01")
    if result:
        print(f"   ✅ pH: {result.get('ph')}")
    else:
        print("   ❌ Failed to read pH sensor")
    
    # Test DS18B20
    print("\n2. Testing DS18B20 temperature:")
    try:
        result = read_ds18b20_temperature("test_temp01")
        if result:
            print(f"   ✅ Temperature: {result.get('temperature')}°C")
        else:
            print("   ❌ Failed to read DS18B20")
    except Exception as e:
        print(f"   ⚠️  DS18B20 not available: {e}")
    
    # Test DHT22
    print("\n3. Testing DHT22:")
    try:
        result = read_dht22_temperature_humidity("test_dht01")
        if result:
            print(f"   ✅ Temperature: {result.get('temperature')}°C")
            print(f"   ✅ Humidity: {result.get('humidity')}%")
        else:
            print("   ❌ Failed to read DHT22")
    except Exception as e:
        print(f"   ⚠️  DHT22 not available: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

