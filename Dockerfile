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

# Expose port (Render uses $PORT, others use 10000)
EXPOSE 10000

# Set default environment variables
ENV PORT=10000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:$PORT/')" || exit 1

# Run application with Gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app


