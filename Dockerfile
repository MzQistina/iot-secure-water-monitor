# Dockerfile for Flask Web Server with MQTT Support
# NOTE: This is ONLY for the web server. The provision agent runs separately on Raspbian.
# See PROVISION_AGENT_GUIDE.md for setting up the provision agent on Raspberry Pi.

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (respects .dockerignore)
COPY . .

# Create necessary directories
RUN mkdir -p keys user_keys sensor_keys templates static certs

# Expose port (default 5000 for docker-compose, 10000 for Render)
EXPOSE 5000

# Set default environment variables
ENV PORT=5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check (simple socket check - no external dependencies)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost', ${PORT:-5000})); s.close()" || exit 1

# Run application with Gunicorn
# Use PORT environment variable (defaults to 5000)
# For docker-compose: PORT=5000
# For Render: PORT=10000 (or use $PORT from Render)
CMD exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app


