#!/bin/bash
set -euo pipefail

# Pre-deployment script for Heroku
# This script runs before the main application starts

echo "Starting pre-deployment tasks..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

echo "Pre-deployment tasks completed successfully!"
