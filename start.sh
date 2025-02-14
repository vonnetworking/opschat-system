#!/bin/bash

# Configuration
MONGO_CONTAINER="mongo-chatui"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start MongoDB
echo "Starting MongoDB..."
if ! docker ps | grep -q $MONGO_CONTAINER; then
    docker run -d -p 27017:27017 --name $MONGO_CONTAINER mongo:latest || docker start $MONGO_CONTAINER
fi

# Start backend server
echo "Starting backend server..."
cd "$SCRIPT_DIR/src"
pkill -f "python -m server.main" || true
python -m server.main &
sleep 2

# Start frontend
echo "Starting frontend..."
cd "$SCRIPT_DIR/chat-ui"
npm install && npm run dev