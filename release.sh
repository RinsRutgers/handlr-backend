#!/bin/bash

# Pre-deployment script for Heroku
# This script runs before the main application starts

echo "Starting pre-deployment tasks..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create cache table (if using database cache)
# python manage.py createcachetable

echo "Pre-deployment tasks completed successfully!"
