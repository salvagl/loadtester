#!/bin/bash

# Script to sync database between container and host
# This solves Docker volume mounting issues on Windows

CONTAINER_NAME="loadtester-backend"
CONTAINER_DB_PATH="/app/data/loadtester.db"
HOST_DB_PATH="./shared/database/loadtester.db"

# Function to copy database from container to host
copy_from_container() {
    echo "Copying database from container to host..."
    if docker exec $CONTAINER_NAME test -f $CONTAINER_DB_PATH; then
        docker cp $CONTAINER_NAME:$CONTAINER_DB_PATH $HOST_DB_PATH
        echo "✅ Database copied from container to host successfully"
        ls -la shared/database/loadtester.db
    else
        echo "❌ Database file not found in container"
        return 1
    fi
}

# Function to copy database from host to container
copy_to_container() {
    echo "Copying database from host to container..."
    if [ -f "$HOST_DB_PATH" ]; then
        docker cp $HOST_DB_PATH $CONTAINER_NAME:$CONTAINER_DB_PATH
        docker exec $CONTAINER_NAME chown appuser:appuser $CONTAINER_DB_PATH
        docker exec $CONTAINER_NAME chmod 664 $CONTAINER_DB_PATH
        echo "✅ Database copied from host to container successfully"
    else
        echo "❌ Database file not found on host"
        return 1
    fi
}

# Function to watch and sync changes
watch_and_sync() {
    echo "🔄 Starting database sync watcher..."
    echo "Press Ctrl+C to stop watching"

    while true; do
        sleep 10
        copy_from_container
    done
}

# Main script logic
case "${1:-}" in
    "pull")
        copy_from_container
        ;;
    "push")
        copy_to_container
        ;;
    "watch")
        watch_and_sync
        ;;
    *)
        echo "LoadTester Database Sync Script"
        echo "Usage: $0 {pull|push|watch}"
        echo ""
        echo "Commands:"
        echo "  pull   - Copy database from container to host"
        echo "  push   - Copy database from host to container"
        echo "  watch  - Continuously sync database from container to host"
        echo ""
        echo "Examples:"
        echo "  $0 pull   # Get latest database from container"
        echo "  $0 push   # Send database changes to container"
        echo "  $0 watch  # Keep local database updated"
        exit 1
        ;;
esac