-- SQL script to create a MySQL user that can connect from remote IPs
-- Run this in phpMyAdmin SQL tab

-- Option 1: Allow connection from your specific IP (115.164.210.80)
CREATE USER IF NOT EXISTS 'ilmuwanutara_e2eewater'@'115.164.210.80' IDENTIFIED BY 'e2eeWater@2025';
GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* TO 'ilmuwanutara_e2eewater'@'115.164.210.80';
FLUSH PRIVILEGES;

-- Option 2: Allow connection from any IP (less secure, but easier)
-- Uncomment the lines below if you want to allow from any IP:
-- CREATE USER IF NOT EXISTS 'ilmuwanutara_e2eewater'@'%' IDENTIFIED BY 'e2eeWater@2025';
-- GRANT ALL PRIVILEGES ON ilmuwanutara_e2eewater.* TO 'ilmuwanutara_e2eewater'@'%';
-- FLUSH PRIVILEGES;

-- Verify the user was created:
SELECT User, Host FROM mysql.user WHERE User = 'ilmuwanutara_e2eewater';

