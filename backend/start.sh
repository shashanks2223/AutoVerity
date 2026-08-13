#!/bin/bash

# Exit on command errors
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Celery worker in the background..."
celery -A app.worker.celery_app worker --loglevel=info &
CELERY_PID=$!

# Give Celery a moment to start and verify it is running
sleep 2
if ! kill -0 "$CELERY_PID" 2>/dev/null; then
    echo "Error: Celery worker failed to start or died immediately."
    exit 1
fi

echo "Starting FastAPI server on port ${PORT:-8000}..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
UVICORN_PID=$!

cleanup() {
    # Disable exit on error during cleanup
    set +e
    echo "Received termination signal. Stopping Celery (PID: $CELERY_PID) and Uvicorn (PID: $UVICORN_PID)..."
    kill -TERM "$UVICORN_PID" 2>/dev/null || true
    kill -TERM "$CELERY_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
    wait "$CELERY_PID" 2>/dev/null || true
    echo "All processes stopped cleanly."
    exit 0
}

# Trap shutdown signals
trap cleanup SIGINT SIGTERM EXIT

# Wait for either process to exit
wait -n "$UVICORN_PID" "$CELERY_PID"

echo "One of the services exited. Initiating shutdown..."
cleanup
