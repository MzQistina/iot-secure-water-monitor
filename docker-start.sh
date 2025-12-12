#!/bin/bash
# Quick start script for Docker Compose

echo "🚀 Starting Flask + MySQL with Docker Compose..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: docker-compose is not installed."
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "📦 Building and starting containers..."
$COMPOSE_CMD up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Containers started successfully!"
    echo ""
    echo "📊 Container status:"
    $COMPOSE_CMD ps
    echo ""
    echo "🌐 Your Flask app is available at: http://localhost:5000"
    echo "🗄️  MySQL is available at: localhost:3306"
    echo ""
    echo "📝 Useful commands:"
    echo "  View logs:        $COMPOSE_CMD logs -f"
    echo "  Stop containers:  $COMPOSE_CMD down"
    echo "  View status:      $COMPOSE_CMD ps"
    echo ""
else
    echo "❌ Failed to start containers. Check the logs:"
    echo "   $COMPOSE_CMD logs"
    exit 1
fi

