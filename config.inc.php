<?php

/**
 * phpMyAdmin configuration file
 * Configured for standalone Apache + MySQL setup
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
 * First server
 */
$i++;
/* Authentication type - 'cookie' shows login page, 'config' auto-logs in */
$cfg['Servers'][$i]['auth_type'] = 'cookie';  // Use 'cookie' for login page, or 'config' for auto-login
/* Server parameters */
$cfg['Servers'][$i]['host'] = 'localhost';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['user'] = 'root';
$cfg['Servers'][$i]['password'] = '';  // Empty if no password set
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = true;  // Allow login without password

/**
 * End of servers configuration
 */

/**
 * Directories for saving/loading files from server
 */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

