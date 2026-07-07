#!/bin/bash

set -e


APP_DIR="${APP_DIR:-$HOME/online-cinema-api}"

cd "$APP_DIR"

echo "Pulling the latest code from origin/main..."
git fetch origin main
git reset --hard origin/main

echo "Building and starting containers..."
docker compose -f docker-compose-prod.yml up -d --build

echo "Removing dangling images..."
docker image prune -f

echo "Deployment completed successfully."
