#!/bin/bash

# Entrypoint script for LoadTester Backend
# This script ensures proper permissions for data directories and handles volume mounting

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

    # Get the user ID and group ID from the host (if available)
    HOST_UID=${HOST_UID:-1000}
    HOST_GID=${HOST_GID:-1000}

    # Update appuser to match host UID/GID for better volume mounting
    usermod -u $HOST_UID appuser 2>/dev/null || true
    groupmod -g $HOST_GID appuser 2>/dev/null || true

    # Change ownership of data directories to appuser (with error suppression for Windows I/O issues)
    chown -R appuser:appuser /app/data 2>/dev/null || echo "Warning: Could not change ownership of /app/data (this is normal on Windows)"
    chown -R appuser:appuser /app/shared 2>/dev/null || echo "Warning: Could not change ownership of /app/shared (this is normal on Windows)"
    chown -R appuser:appuser /app/k6_scripts 2>/dev/null || echo "Warning: Could not change ownership of /app/k6_scripts (this is normal on Windows)"
    chown -R appuser:appuser /app/k6_results 2>/dev/null || echo "Warning: Could not change ownership of /app/k6_results (this is normal on Windows)"

    # Ensure directories are writable with more permissive permissions for volume mounting (with error suppression)
    chmod -R 775 /app/data 2>/dev/null || echo "Warning: Could not change permissions of /app/data (this is normal on Windows)"
    chmod -R 775 /app/shared 2>/dev/null || echo "Warning: Could not change permissions of /app/shared (this is normal on Windows)"
    chmod -R 775 /app/k6_scripts 2>/dev/null || echo "Warning: Could not change permissions of /app/k6_scripts (this is normal on Windows)"
    chmod -R 775 /app/k6_results 2>/dev/null || echo "Warning: Could not change permissions of /app/k6_results (this is normal on Windows)"

    # Special handling for database file to ensure it's created with correct permissions
    if [ ! -f /app/data/loadtester.db ]; then
        echo "Creating database file with correct permissions..."
        touch /app/data/loadtester.db
        chown appuser:appuser /app/data/loadtester.db
        chmod 664 /app/data/loadtester.db
    fi

    echo "Permissions fixed. Switching to appuser..."
    # Switch to appuser and execute the original command, preserving environment
    exec sudo -E -u appuser "$@"
else
    echo "Already running as appuser, proceeding..."
    # If already running as appuser, just execute the command
    exec "$@"
fi