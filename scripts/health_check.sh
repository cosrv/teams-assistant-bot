#!/bin/bash
# Simple health check script

HEALTH_URL="http://localhost:3978/health"

if curl -f -s $HEALTH_URL > /dev/null; then
    echo "✅ Bot is healthy"
    exit 0
else
    echo "❌ Bot health check failed"
    exit 1
fi