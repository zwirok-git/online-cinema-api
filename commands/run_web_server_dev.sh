#!/bin/sh

# Run the web server with autoreload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/src
