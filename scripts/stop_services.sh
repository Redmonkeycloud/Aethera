#!/bin/bash
# Stop AETHERA Services

set -e

REDIS_PORT=6379

echo "Stopping AETHERA Services..."
echo ""

# Stop Redis
echo "Stopping Redis..."
if [ -f redis.pid ]; then
    kill $(cat redis.pid) 2>/dev/null || true
    rm redis.pid
    echo "✓ Redis stopped"
elif redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
    redis-cli -p "$REDIS_PORT" shutdown
    echo "✓ Redis stopped"
else
    echo "  Redis not running"
fi

echo ""

# Stop Celery
echo "Stopping Celery worker..."
if [ -f celery.pid ]; then
    kill $(cat celery.pid) 2>/dev/null || true
    rm celery.pid
    echo "✓ Celery stopped"
else
    pkill -f "celery.*celery_app" 2>/dev/null && echo "✓ Celery stopped" || echo "  Celery not running"
fi

echo ""

# Stop FastAPI
echo "Stopping FastAPI server..."
if [ -f api.pid ]; then
    kill $(cat api.pid) 2>/dev/null || true
    rm api.pid
    echo "✓ FastAPI stopped"
else
    pkill -f "uvicorn.*app:app" 2>/dev/null && echo "✓ FastAPI stopped" || echo "  FastAPI not running"
fi

echo ""
echo "All services stopped!"

