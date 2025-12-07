# IoT Secure Water Monitor

## 📚 Documentation Index

### Quick Start Guides
- **[RASPBIAN_QUICK_START.md](RASPBIAN_QUICK_START.md)** - Quick 5-minute setup for Raspbian simulation
- **[RASPBIAN_COMMANDS.txt](RASPBIAN_COMMANDS.txt)** - Complete Raspbian commands reference (detailed, 414 lines)

### Setup & Installation
- **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Raspberry Pi hardware setup
- **[RASPBERRY_PI_5_SD_CARD_SETUP.md](RASPBERRY_PI_5_SD_CARD_SETUP.md)** - Raspberry Pi 5 specific SD card setup
- **[FILES_TO_UPDATE_RASPBIAN.md](FILES_TO_UPDATE_RASPBIAN.md)** - Which files to update on Raspbian
- **File transfer methods** - See [RASPBIAN_SIMULATION_GUIDE.md](RASPBIAN_SIMULATION_GUIDE.md) Step 2 (SCP, Shared Folder, USB)

### Simulation Guides
- **[RASPBIAN_SIMULATION_GUIDE.md](RASPBIAN_SIMULATION_GUIDE.md)** - Complete simulation guide
- **[VIRTUALBOX_SIMULATION_SETUP.md](VIRTUALBOX_SIMULATION_SETUP.md)** - VirtualBox simulation setup
- **[HOW_TO_SIMULATE_READINGS.md](HOW_TO_SIMULATE_READINGS.md)** - How to simulate sensor readings

### Deployment Guides
- **[DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)** - Docker deployment
- **[LOCAL_DOCKER_TESTING.md](LOCAL_DOCKER_TESTING.md)** - Local Docker testing
- **[RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)** - Render.com deployment
- **[PYTHONANYWHERE_DEPLOYMENT_GUIDE.md](PYTHONANYWHERE_DEPLOYMENT_GUIDE.md)** - PythonAnywhere deployment
- **[FILEZILLA_DEPLOYMENT_GUIDE.md](FILEZILLA_DEPLOYMENT_GUIDE.md)** - FileZilla deployment
- **[LITESPEED_DEPLOYMENT_GUIDE.md](LITESPEED_DEPLOYMENT_GUIDE.md)** - LiteSpeed deployment
- **[VIRTUALBOX_SERVER_DEPLOYMENT.md](VIRTUALBOX_SERVER_DEPLOYMENT.md)** - VirtualBox server deployment

### Configuration & Setup
- **[APACHE_SETUP.md](APACHE_SETUP.md)** - Apache web server setup
- **[HIVEMQ_CLOUD_SETUP.md](HIVEMQ_CLOUD_SETUP.md)** - HiveMQ Cloud setup guide (recommended)
- **[MQTT_BROKER_SETUP.md](MQTT_BROKER_SETUP.md)** - MQTT broker host configuration guide
- **[MQTT_TLS_SETUP.md](MQTT_TLS_SETUP.md)** - MQTT TLS configuration
- **[PROVISION_AGENT_GUIDE.md](PROVISION_AGENT_GUIDE.md)** - Key provisioning agent setup
- **[PROVISION_AGENT_AUTOMATION.md](PROVISION_AGENT_AUTOMATION.md)** - Automate provision agent (auto-start on boot)

### Troubleshooting
- **[RASPBIAN_TROUBLESHOOTING.md](RASPBIAN_TROUBLESHOOTING.md)** - Raspbian-specific troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting guide

### Architecture & Analysis
- **[RASPBERRY_PI_ARCHITECTURE.md](RASPBERRY_PI_ARCHITECTURE.md)** - System architecture
- **[CPU_USAGE_ANALYSIS.md](CPU_USAGE_ANALYSIS.md)** - CPU usage analysis
- **[SAME_DEVICE_ID_DIFFERENT_USERS.md](SAME_DEVICE_ID_DIFFERENT_USERS.md)** - Multi-user device ID handling

### Pre-Deployment
- **[PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[RENDER_DATABASE_SETUP.md](RENDER_DATABASE_SETUP.md)** - Render database setup

## 🚀 Quick Start

1. **Windows Setup**: See `WINDOWS_STARTUP_SEQUENCE.txt` in root directory for startup sequence
2. **Raspbian Setup**: See [RASPBIAN_QUICK_START.md](RASPBIAN_QUICK_START.md) for quick setup
3. **Run Simulation**: `python3 multi_sensor_client.py --all http://10.0.2.2`

## 🛠️ Utilities

- **phpmyadmin_setup.py** - Comprehensive phpMyAdmin setup and diagnostic tool (replaces find_apache_phpmyadmin.py, check_phpmyadmin.py, configure_apache_phpmyadmin.py)
- **test_mysql_connection.py** - MySQL connection diagnostic
- **test_device_session.py** - Device session testing

## 📝 Notes

- Most comprehensive Raspbian command reference: `RASPBIAN_COMMANDS.txt` (414 lines)
- Windows startup sequence: `WINDOWS_STARTUP_SEQUENCE.txt` (root directory)
- For quick commands: `RASPBIAN_QUICK_START.md`
- Use `sensor_simulator.py --mode safe` or `--mode unsafe` instead of separate wrapper scripts

