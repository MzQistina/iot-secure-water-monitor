# IoT Secure Water Monitor

## 📚 Documentation Index

### Quick Start Guides
- **[RASPBERRY_PI_DEPLOYMENT.md](RASPBERRY_PI_DEPLOYMENT.md)** - Raspberry Pi deployment guide

### Setup & Installation
- **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Raspberry Pi hardware setup
- **[RASPBERRY_PI_5_SD_CARD_SETUP.md](RASPBERRY_PI_5_SD_CARD_SETUP.md)** - Raspberry Pi 5 specific SD card setup
- **[FILES_TO_UPDATE_RASPBIAN.md](FILES_TO_UPDATE_RASPBIAN.md)** - Which files to update on Raspbian

### Configuration & Setup
- **[APACHE_SETUP.md](APACHE_SETUP.md)** - Apache web server setup
- **[HIVEMQ_CLOUD_SETUP.md](HIVEMQ_CLOUD_SETUP.md)** - HiveMQ Cloud setup guide (recommended)
- **[MQTT_BROKER_SETUP.md](MQTT_BROKER_SETUP.md)** - MQTT broker host configuration guide
- **[MQTT_TLS_SETUP.md](MQTT_TLS_SETUP.md)** - MQTT TLS configuration
- **[PROVISION_AGENT_GUIDE.md](PROVISION_AGENT_GUIDE.md)** - Key provisioning agent setup
- **[PROVISION_AGENT_AUTOMATION.md](PROVISION_AGENT_AUTOMATION.md)** - Automate provision agent (auto-start on boot)

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting guide

### Architecture & Analysis
- **[RASPBERRY_PI_ARCHITECTURE.md](RASPBERRY_PI_ARCHITECTURE.md)** - System architecture
- **[CPU_USAGE_ANALYSIS.md](CPU_USAGE_ANALYSIS.md)** - CPU usage analysis
- **[SAME_DEVICE_ID_DIFFERENT_USERS.md](SAME_DEVICE_ID_DIFFERENT_USERS.md)** - Multi-user device ID handling

## 🚀 Quick Start

1. **Windows Setup**: See `WINDOWS_STARTUP_SEQUENCE.txt` in root directory for startup sequence
2. **Raspberry Pi Setup**: See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for hardware setup
3. **Docker Setup**: See Docker section below

## 🐳 Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Environment variables configured (see `.env.example` or docker-compose.yml)

### Quick Start with Docker

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f web
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

### Environment Variables

Create a `.env` file or set environment variables:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database connection
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASSWORD` - MQTT broker
- `MQTT_USE_TLS`, `MQTT_TLS_INSECURE` - MQTT TLS settings
- `SECRET_KEY` - Flask secret key (change in production!)

### Volumes

The following directories are mounted as volumes:
- `./keys` - Server keys (RSA key pairs)
- `./user_keys` - User-specific keys
- `./sensor_keys` - Sensor keys
- `./certs` - TLS certificates (read-only)

**Important:** Never commit keys or certificates to Git. They are excluded via `.gitignore`.

## 🛠️ Utilities

- **phpmyadmin_setup.py** - Comprehensive phpMyAdmin setup and diagnostic tool (replaces find_apache_phpmyadmin.py, check_phpmyadmin.py, configure_apache_phpmyadmin.py)
- **test_mysql_connection.py** - MySQL connection diagnostic
- **test_device_session.py** - Device session testing

## 📝 Notes

- Raspberry Pi deployment: See [RASPBERRY_PI_DEPLOYMENT.md](RASPBERRY_PI_DEPLOYMENT.md)

