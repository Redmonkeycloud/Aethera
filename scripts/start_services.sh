#!/bin/bash
# Start AETHERA Services
# This script starts Redis, Celery worker, and FastAPI server

set -e

BACKGROUND=false
REDIS_PORT=6379
API_PORT=8000
API_HOST=localhost

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --background|-b)
            BACKGROUND=true
            shift
            ;;
        --redis-port)
            REDIS_PORT="$2"
            shift 2
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --api-host)
            API_HOST="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting AETHERA Services..."
echo ""

# Check if Redis is running
echo "Checking Redis..."
if redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
    echo "✓ Redis is already running on port $REDIS_PORT"
else
    echo "Starting Redis server..."
    if command -v redis-server > /dev/null 2>&1; then
        if [ "$BACKGROUND" = true ]; then
            redis-server --port "$REDIS_PORT" --daemonize yes
            sleep 2
            echo "✓ Redis started in background"
        else
            redis-server --port "$REDIS_PORT" &
            REDIS_PID=$!
            echo "✓ Redis started (PID: $REDIS_PID)"
            sleep 2
        fi
    else
        echo "⚠ Redis not found. Please install Redis or start it manually."
        echo "  Install: brew install redis (macOS) or apt-get install redis-server (Linux)"
        exit 1
    fi
fi

echo ""

# Start Celery worker
echo "Starting Celery worker..."
if [ "$BACKGROUND" = true ]; then
    cd "$PROJECT_ROOT"
    celery -A backend.src.workers.celery_app worker --loglevel=info --detach --logfile=celery.log --pidfile=celery.pid
    echo "✓ Celery worker started in background"
else
    cd "$PROJECT_ROOT"
    celery -A backend.src.workers.celery_app worker --loglevel=info &
    CELERY_PID=$!
    echo "✓ Celery worker started (PID: $CELERY_PID)"
    sleep 2
fi

echo ""

# Start FastAPI server
echo "Starting FastAPI server..."
if [ "$BACKGROUND" = true ]; then
    cd "$PROJECT_ROOT"
    nohup uvicorn backend.src.api.app:app --host "$API_HOST" --port "$API_PORT" --reload > api.log 2>&1 &
    API_PID=$!
    echo "✓ FastAPI server started in background (PID: $API_PID)"
else
    cd "$PROJECT_ROOT"
    uvicorn backend.src.api.app:app --host "$API_HOST" --port "$API_PORT" --reload &
    API_PID=$!
    echo "✓ FastAPI server started (PID: $API_PID)"
    sleep 2
fi

echo ""
echo "========================================"
echo "All services started!"
echo "========================================"
echo ""
echo "Services:"
echo "  • Redis:     localhost:$REDIS_PORT"
echo "  • Celery:    Processing tasks"
echo "  • FastAPI:   http://$API_HOST:$API_PORT"
echo "  • API Docs:  http://$API_HOST:$API_PORT/docs"
echo ""

if [ "$BACKGROUND" = false ]; then
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    # Wait for user interrupt
    trap "echo ''; echo 'Stopping services...'; kill $REDIS_PID $CELERY_PID $API_PID 2>/dev/null; exit" INT
    wait
else
    echo "Services running in background."
    echo "To stop:"
    echo "  - Redis:   redis-cli -p $REDIS_PORT shutdown"
    echo "  - Celery:  kill \$(cat celery.pid)"
    echo "  - FastAPI: kill $API_PID"
fi

