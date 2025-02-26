#!/bin/bash
set -e

# Function to log error and keep container running for debugging
log_error() {
    echo "ERROR: $1"
    # Keep container running for debugging
    sleep infinity
}

# Extract host ports from environment variables
HOST_API_PORT=${HOST_API_PORT:-1234}
HOST_UI_PORT=${HOST_UI_PORT:-5173}

# Set proper environment variables for services
export MONGODB_URI=${MONGODB_URI:-"mongodb://mongo-chatui:27017"}
export QDRANT_HOST=${QDRANT_HOST:-"romantic_solomon"}
export QDRANT_PORT=${QDRANT_PORT:-6333}
export OLLAMA_HOST=${OLLAMA_HOST:-"ollama"}
export OLLAMA_PORT=${OLLAMA_PORT:-11434}

# For backward compatibility with existing code
export VS_SERVICE_HOST=$QDRANT_HOST
export VS_SERVICE_PORT=$QDRANT_PORT

# Set auth variables
export AUTH_ENABLED="false"
export CLIENT_ID="dummy"
export CLIENT_SECRET="dummy"
export PROVIDER_URL="dummy"
export SCOPES="dummy"
export NAME_CLAIM="dummy"
export TOLERANCE="dummy"
export RESOURCE="dummy"

echo "Starting services..."
echo "MongoDB URI: $MONGODB_URI"
echo "Qdrant Host: $QDRANT_HOST:$QDRANT_PORT"
echo "Ollama Host: $OLLAMA_HOST:$OLLAMA_PORT"
echo "User: $USER_NAME"
echo "Host Ports - API: $HOST_API_PORT, UI: $HOST_UI_PORT"

# Verify AWS credentials
if [[ -n "$AWS_ACCESS_KEY_ID" && -n "$AWS_SECRET_ACCESS_KEY" && -n "$AWS_SESSION_TOKEN" ]]; then
    echo "AWS credentials are available. Testing..."
    
    # Set AWS default region explicitly
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
    export AWS_REGION=${AWS_REGION:-us-east-1}
    
    # Create AWS config directory
    mkdir -p ~/.aws
    
    # Create AWS credentials file with proper format - no quotes
    cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
aws_session_token = $AWS_SESSION_TOKEN
EOL

    # Create AWS config file
    cat > ~/.aws/config << EOL
[default]
region = $AWS_DEFAULT_REGION
output = json
EOL

    # Test AWS credentials
    echo "Testing AWS credentials with STS..."
    if aws sts get-caller-identity; then
        echo "✅ AWS credentials verified successfully"
    else
        echo "⚠️ AWS credentials are invalid - application may not work correctly"
        exit 1
    fi
else
    echo "ERROR: AWS credentials not found. Cannot continue."
    exit 1
fi

# Add the src directory to the Python path
export PYTHONPATH=/app:/app/src

# Fix the Python import structure
cd /app
echo "Installing symbolic link for server module..."
if [ ! -L "/app/server" ]; then
    ln -s /app/src/server /app/server
fi

# Fix git issue by initializing a git repo in the chat-ui directory
cd /app/chat-ui
echo "Initializing git repository to prevent git errors..."
git init >/dev/null 2>&1
git config --global user.email "opschat@example.com"
git config --global user.name "OpsChatUI"
git add . >/dev/null 2>&1
git commit -m "Initial commit" >/dev/null 2>&1 || echo "Git commit failed but continuing"

# Start the FastAPI server
echo "Starting FastAPI server on port 1234..."
cd /app/src
python -m server.main &
SERVER_PID=$!

# Give the server some time to start
sleep 3

# Verify the server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: FastAPI server failed to start. Cannot continue."
    exit 1
fi
echo "✅ FastAPI server is running on port 1234"

# Start the Chat UI
cd /app/chat-ui
echo "Starting Chat UI on port 5173 (mapped to external port $HOST_UI_PORT)..."

# Create .env.local file with necessary environment variables
cat > .env.local <<EOL
MONGODB_URL=$MONGODB_URI
MONGO_DB_NAME="opschat-agents"

# Auth disable
AUTH_ENABLED="false"
CLIENT_ID="dummy"
CLIENT_SECRET="dummy"
PROVIDER_URL="dummy"
SCOPES="dummy"
NAME_CLAIM="dummy"
TOLERANCE="dummy"
RESOURCE="dummy"

# Model configuration
MODELS=\`[
    {
      "id": "opschat-agents",
      "name": "opschat-agents",
      "displayName": "opschat agent backend",
      "endpoints": [
        {
          "type": "openai",
          "baseURL": "http://localhost:1234/v1",
        }
      ]
    },
  ]\`
EOL

echo "Created .env.local file with connection information"

# Start the development server
if npm run dev -- --host 0.0.0.0 --port 5173; then
    echo "Development server started"
else
    echo "Error starting dev server. Trying preview mode..."
    if npm run preview -- --host 0.0.0.0; then
        echo "Preview server started"
    else
        echo "Error: Failed to start UI server"
        exit 1
    fi
fi
