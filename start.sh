#!/bin/bash
echo "🚀 PRISMY Starting..."
echo "Port: $PORT"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Files in current dir: $(ls -la | head -10)"
echo "Files in src: $(ls -la src/ | head -5)"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start server
echo "Starting uvicorn..."
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --log-level debug
