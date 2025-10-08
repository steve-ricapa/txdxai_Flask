#!/bin/bash

# TxDxAI - Production Service Startup Script
# Starts both Backend and SOPHIA services in parallel for VM Deployment

echo "Starting TxDxAI services..."

# Start Backend API with Gunicorn (Port 5000)
echo "Starting Backend API on port 5000..."
gunicorn --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "txdxai.app:create_app()" &

BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start SOPHIA Service (Port 8000)
echo "Starting SOPHIA service on port 8000..."
python sophia_service/app.py &

SOPHIA_PID=$!
echo "SOPHIA started with PID: $SOPHIA_PID"

# Wait for both processes
echo "Both services are running. Press Ctrl+C to stop."
wait $BACKEND_PID $SOPHIA_PID
