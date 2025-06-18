#!/bin/bash
set -e

echo "🚀 Deploying Teams Assistant Bot..."

# Load environment
source .env

# Build new image
echo "📦 Building Docker image..."
docker-compose build

# Health check function
health_check() {
    curl -f http://localhost:3978/health > /dev/null 2>&1
    return $?
}

# Blue-Green Deployment
echo "🔄 Starting Blue-Green deployment..."

# Start new container with different name
docker-compose -p teams-bot-new up -d

# Wait for new container to be healthy
echo "⏳ Waiting for new container to be healthy..."
for i in {1..30}; do
    if health_check; then
        echo "✅ New container is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ New container failed health check"
        docker-compose -p teams-bot-new down
        exit 1
    fi
    sleep 2
done

# Stop old container
echo "🛑 Stopping old container..."
docker-compose -p teams-bot down

# Rename new to current
echo "🔄 Switching to new container..."
docker-compose -p teams-bot-new down
docker-compose up -d

echo "✅ Deployment complete!"