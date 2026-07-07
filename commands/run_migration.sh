#!/bin/sh

set -e

# Apply all pending database migrations
alembic upgrade head
