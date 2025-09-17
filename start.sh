#!/bin/bash
echo "PORT environment variable: $PORT"
echo "Starting Gunicorn on port $PORT"
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --log-level info --access-logfile - --error-logfile - debug_app:app