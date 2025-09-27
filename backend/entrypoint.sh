#!/bin/bash

# Entrypoint script for LoadTester Backend
# This script ensures proper permissions for data directories

set -e

echo "Starting LoadTester Backend..."

# Ensure data directories exist and have correct permissions
echo "Setting up data directories..."

# Create directories if they don't exist
mkdir -p /app/data
mkdir -p /app/shared/data/uploads
mkdir -p /app/shared/data/mocked
mkdir -p /app/shared/reports/generated
mkdir -p /app/k6_scripts
mkdir -p /app/k6_results

# Fix permissions for the mounted volumes
# We need to do this as root first, then switch to appuser
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, fixing permissions..."

    # Change ownership of data directories to appuser
    chown -R appuser:appuser /app/data
    chown -R appuser:appuser /app/shared
    chown -R appuser:appuser /app/k6_scripts
    chown -R appuser:appuser /app/k6_results

    # Ensure directories are writable
    chmod -R 755 /app/data
    chmod -R 755 /app/shared
    chmod -R 755 /app/k6_scripts
    chmod -R 755 /app/k6_results

    echo "Permissions fixed. Switching to appuser..."
    # Switch to appuser and execute the original command
    exec sudo -u appuser "$@"
else
    echo "Already running as appuser, proceeding..."
    # If already running as appuser, just execute the command
    exec "$@"
fi