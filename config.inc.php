<?php

/**
 * phpMyAdmin configuration file
 * Configured for remote MySQL server (ilmuwanutara.my)
 */

declare(strict_types=1);

/**
 * This is needed for cookie based authentication to encrypt the cookie.
 * Needs to be a 32-bytes long string of random bytes.
 */
$cfg['blowfish_secret'] = 'a8b7c6d5e4f3g2h1i0j9k8l7m6n5o4p3'; /* 32-byte random string */

/**
 * Servers configuration
 */
$i = 0;

/**
 * First server - Remote MySQL Server
 */
$i++;
/* Authentication type - 'cookie' shows login page, 'config' auto-logs in */
$cfg['Servers'][$i]['auth_type'] = 'cookie';  // Use 'cookie' for login page, or 'config' for auto-login
/* Server parameters - Updated to match connect.py credentials */
$cfg['Servers'][$i]['host'] = 'ilmuwanutara.my';  // Remote MySQL host
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['user'] = 'ilmuwanutara_e2eewater';  // Database user
$cfg['Servers'][$i]['password'] = 'e2eeWater@2025';  // Database password
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = false;  // Password is required

/**
 * Local server (if you also have local MySQL)
 * Uncomment below if you want to add localhost as a second server option
 */
/*
$i++;
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['host'] = 'localhost';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['user'] = 'root';
$cfg['Servers'][$i]['password'] = '';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = true;
*/

/**
 * End of servers configuration
 */

/**
 * Directories for saving/loading files from server
 */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

/**
 * Import/Export settings - Important for large database imports
 */
$cfg['UploadDir'] = '';  // Directory for uploads (leave empty to use default)
$cfg['SaveDir'] = '';    // Directory for saves (leave empty to use default)

/**
 * Maximum upload size for SQL files (in bytes)
 * Note: This should also be set in php.ini (upload_max_filesize, post_max_size)
 */
$cfg['MaxSizeForInputField'] = 50 * 1024 * 1024;  // 50MB

/**
 * Timeout settings for long-running imports
 */
$cfg['ExecTimeLimit'] = 0;  // 0 = no limit (or set to higher value like 300 for 5 minutes)

/**
 * Memory limit (should match or be less than PHP memory_limit)
 */
ini_set('memory_limit', '256M');

/**
 * Display settings
 */
$cfg['DefaultLang'] = 'en';
$cfg['ServerDefault'] = 1;  // Use first server by default

