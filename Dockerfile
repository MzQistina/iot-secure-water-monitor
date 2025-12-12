# Dockerfile for Flask Web Server (Render/Docker deployment)
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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p keys user_keys sensor_keys templates static

# Expose port (default 5000 for docker-compose, 10000 for Render)
EXPOSE 5000

# Set default environment variables
ENV PORT=5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run application with Gunicorn
# Use PORT environment variable (defaults to 5000)
# For docker-compose: PORT=5000
# For Render: PORT=10000 (or use $PORT from Render)
CMD exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app


