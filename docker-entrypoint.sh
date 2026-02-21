#!/bin/bash
# ============================================================================
# Docker Entrypoint Script
# ============================================================================
# Starts the Flask application with Gunicorn.
# Database migrations are handled manually during initial deployment.
# ============================================================================

set -e

echo "============================================"
echo "Library of Babble - Starting Server"
echo "============================================"

# Start Gunicorn with production settings
# - workers: 2 (good for 0.25-0.5 vCPU)
# - threads: 2 (handle concurrent requests)
# - timeout: 120 (allow slow requests)
# - bind: 0.0.0.0:5000 (listen on all interfaces)
exec gunicorn \
    --bind 0.0.0.0:80 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    "run:app"
