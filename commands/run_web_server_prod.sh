#!/bin/sh

# Run the web server with multiple workers (tune via WEB_CONCURRENCY)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-2}"
