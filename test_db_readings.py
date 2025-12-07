#!/usr/bin/env python3
"""Test database readings retrieval."""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from db import get_pool, list_recent_sensor_data, list_recent_sensor_data_by_location
from datetime import datetime, timedelta

def test_readings():
    print("=" * 60)
    print("TESTING DATABASE READINGS RETRIEVAL")
    print("=" * 60)
    
    # Test 1: Get all readings (no user filter)
    print("\n1. Testing list_recent_sensor_data (no user filter)...")
    all_readings = list_recent_sensor_data(limit=10)
    print(f"   Found {len(all_readings)} readings")
    if all_readings:
        for r in all_readings[:3]:
            print(f"   - ID: {r.get('id')}, Device: {r.get('device_id')}, Type: {r.get('device_type')}, Value: {r.get('value')}, Date: {r.get('recorded_at')}, User: {r.get('user_id')}")
    
    # Test 2: Get readings for a specific user (if we have user_id)
    print("\n2. Testing list_recent_sensor_data with user_id...")
    # Try to get a user_id from the readings
    if all_readings:
        test_user_id = all_readings[0].get('user_id')
        if test_user_id:
            print(f"   Testing with user_id: {test_user_id}")
            user_readings = list_recent_sensor_data(limit=10, user_id=test_user_id)
            print(f"   Found {len(user_readings)} readings for user {test_user_id}")
            if user_readings:
                for r in user_readings[:3]:
                    print(f"   - ID: {r.get('id')}, Device: {r.get('device_id')}, Type: {r.get('device_type')}, Value: {r.get('value')}, Date: {r.get('recorded_at')}")
    
    # Test 3: Get readings by location
    print("\n3. Testing list_recent_sensor_data_by_location...")
    if all_readings:
        test_location = all_readings[0].get('location')
        test_user_id = all_readings[0].get('user_id')
        if test_location and test_user_id:
            print(f"   Testing with location: '{test_location}', user_id: {test_user_id}")
            location_readings = list_recent_sensor_data_by_location(
                location=test_location,
                limit=10,
                user_id=test_user_id
            )
            print(f"   Found {len(location_readings)} readings for location '{test_location}'")
            if location_readings:
                for r in location_readings[:3]:
                    print(f"   - ID: {r.get('id')}, Device: {r.get('device_id')}, Type: {r.get('device_type')}, Value: {r.get('value')}, Date: {r.get('recorded_at')}")
    
    # Test 4: Check date range
    print("\n4. Testing date range filtering...")
    if all_readings:
        test_location = all_readings[0].get('location')
        test_user_id = all_readings[0].get('user_id')
        if test_location and test_user_id:
            # Get readings from last 7 days
            date_from = datetime.now() - timedelta(days=7)
            date_to = datetime.now()
            print(f"   Testing with date range: {date_from} to {date_to}")
            date_readings = list_recent_sensor_data_by_location(
                location=test_location,
                limit=100,
                user_id=test_user_id,
                date_from=date_from,
                date_to=date_to
            )
            print(f"   Found {len(date_readings)} readings in date range")
    
    # Test 5: Check database directly
    print("\n5. Direct database query test...")
    pool = get_pool()
    if pool:
        conn = pool.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) as count FROM sensor_data")
        total_count = cur.fetchone()['count']
        print(f"   Total sensor_data rows in database: {total_count}")
        
        cur.execute("SELECT MIN(recorded_at) as min_date, MAX(recorded_at) as max_date FROM sensor_data")
        date_range = cur.fetchone()
        print(f"   Date range: {date_range.get('min_date')} to {date_range.get('max_date')}")
        
        cur.execute("SELECT DISTINCT user_id FROM sensor_data LIMIT 5")
        user_ids = [r['user_id'] for r in cur.fetchall() if r.get('user_id')]
        print(f"   User IDs with data: {user_ids}")
        
        cur.close()
        conn.close()
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_readings()

