#!/bin/bash

# Set -e to stop the script if any command fails
set -e

echo "Activating virtual environment ..."
source venv/bin/activate
echo "Virtual environment activated successfully ..."

# Install new dependencies
echo "Installing dependencies... "
if ! pip install -r requirements.txt; then
    echo "Failed to install dependencies" >&2
    exit 1
fi

# Apply database migrations
echo "Applying database migrations..."
if ! python manage.py migrate; then
    echo "Failed to apply database migrations" >&2
    exit 1
fi

# Collect static files
echo "Collecting static files..."
if ! python manage.py collectstatic --noinput; then
    echo "Failed to collect static files" >&2
    exit 1
fi

# Restart the service
echo "Restarting service..."
if ! sudo service original_software_backend restart; then
    echo "Failed to restart the service" >&2
    exit 1
fi


echo "Deployment completed successfully!"
