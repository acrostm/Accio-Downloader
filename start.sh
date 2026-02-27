#!/bin/sh
# Accio Downloader - Container Entrypoint
# Starts FastAPI, Next.js, then Nginx in the correct order.

set -e

echo "=== Accio Downloader starting ==="

# Ensure data directories exist (volume mount may create them read-only)
mkdir -p /data/downloads
mkdir -p /data

# Database default
export DATABASE_URL="${DATABASE_URL:-sqlite:////data/sql_app.db}"
export COOKIES_FILE="${COOKIES_FILE:-/data/cookies.txt}"
export TEMP_DOWNLOAD_DIR="${TEMP_DOWNLOAD_DIR:-/data/downloads}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:8080}"

echo ">>> Starting FastAPI backend on :8000..."
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait until the backend is ready
echo ">>> Waiting for backend..."
for i in $(seq 1 30); do
    if wget -q -O /dev/null http://127.0.0.1:8000/api/v1/video/tasks 2>/dev/null; then
        echo ">>> Backend ready!"
        break
    fi
    sleep 1
done

echo ">>> Starting Next.js frontend on :3000..."
cd /app/frontend
node server.js &
FRONTEND_PID=$!

sleep 2

echo ">>> Starting Nginx on :8080..."
nginx -g "daemon off;" &
NGINX_PID=$!

echo "=== All services started. Accio available on :8080 ==="

# Trap exits to cleanly stop all child processes
trap "kill $BACKEND_PID $FRONTEND_PID $NGINX_PID 2>/dev/null; exit 0" TERM INT

wait $NGINX_PID
