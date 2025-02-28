#!/bin/bash

# Exit on error
set -e

FORCE_REBUILD=false

# Function to find a random available port
find_available_port() {
    local port=$(shuf -i 10000-65000 -n 1)
    while nc -z localhost $port; do
        port=$(shuf -i 10000-65000 -n 1)
    done
    echo $port
}

# Function to get AWS credentials directly from EC2 instance metadata
get_aws_credentials() {
    # Get an IMDSv2 token - required for metadata service v2
    TOKEN=$(curl -s -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')
    if [ -z "$TOKEN" ]; then
        echo "ERROR: Failed to get IMDSv2 token" >&2
        return 1
    fi
    
    # Get the role name
    ROLE_NAME=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    if [ -z "$ROLE_NAME" ]; then
        echo "ERROR: Failed to get IAM role name" >&2
        return 1
    fi
    
    # Print the role name to stderr instead of stdout to avoid capturing in the return value
    echo "Using IAM role: $ROLE_NAME" >&2
    
    # Get the actual credentials using the role name
    AWS_ACCESS_KEY_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME | jq -r '.AccessKeyId')
    AWS_SECRET_ACCESS_KEY=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME | jq -r '.SecretAccessKey')
    AWS_SESSION_TOKEN=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME | jq -r '.Token')
    
    # Get the availability zone and extract the region
    AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
    AWS_REGION=$(echo "$AZ" | sed 's/.$//')

    # If we couldn't determine the region, fall back to us-east-1
    if [ -z "$AWS_REGION" ]; then
        echo "WARNING: Couldn't determine AWS region, falling back to us-east-1" >&2
        AWS_REGION="us-east-1"
    else
        echo "Detected AWS Region: $AWS_REGION" >&2
    fi

    # Validate we got credentials
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ "$AWS_ACCESS_KEY_ID" = "null" ]; then
        echo "ERROR: Failed to get AWS Access Key ID" >&2
        return 1
    fi
    
    if [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ "$AWS_SECRET_ACCESS_KEY" = "null" ]; then
        echo "ERROR: Failed to get AWS Secret Access Key" >&2
        return 1
    fi
    
    if [ -z "$AWS_SESSION_TOKEN" ] || [ "$AWS_SESSION_TOKEN" = "null" ]; then
        echo "ERROR: Failed to get AWS Session Token" >&2
        return 1
    fi
    
    # Return only the environment variables, without any other output
    echo "-e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION=$AWS_REGION -e AWS_REGION=$AWS_REGION"
}

# Find running service containers
MONGO_CONTAINER="mongo-chatui"
# Detect Qdrant container automatically
QDRANT_CONTAINER=$(docker ps --filter ancestor=qdrant/qdrant --format "{{.Names}}" | head -n 1)
if [ -z "$QDRANT_CONTAINER" ]; then
    # Try finding by partial name if image search failed
    QDRANT_CONTAINER=$(docker ps --filter name=qdrant --format "{{.Names}}" | head -n 1)
    if [ -z "$QDRANT_CONTAINER" ]; then
        echo "Warning: No Qdrant container found. Vector search may not work."
    else
        echo "Found Qdrant container: $QDRANT_CONTAINER"
    fi
else
    echo "Found Qdrant container: $QDRANT_CONTAINER"
fi

# Find Ollama container - same approach as Qdrant
OLLAMA_CONTAINER=$(docker ps --filter ancestor=ollama/ollama --format "{{.Names}}" | head -n 1)
if [ -z "$OLLAMA_CONTAINER" ]; then
    OLLAMA_CONTAINER=$(docker ps --filter name=ollama --format "{{.Names}}" | head -n 1)
    if [ -z "$OLLAMA_CONTAINER" ]; then
        echo "Warning: No Ollama container found. LLM functionality may not work."
    else
        echo "Found Ollama container: $OLLAMA_CONTAINER"
    fi
else
    echo "Found Ollama container: $OLLAMA_CONTAINER"
fi

# User info and container naming
USER_NAME=$(whoami)
USER_PREFIX=$(echo $USER_NAME | tr -d -c '[:alnum:]' | cut -c1-8)
TIMESTAMP=$(date +%s | cut -c7-10)
OPSCHAT_CONTAINER="${USER_PREFIX}-opschat-${TIMESTAMP}"
NETWORK_NAME="opschat-network"
IMAGE_NAME="opschat-app-${USER_PREFIX}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to show help
show_help() {
    echo "OpsChat App - Build and Run Script"
    echo "--------------------------------"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  run         Run the container"
    echo "  all         Build and run (default)"
    echo "  clean       Remove all containers and images"
    echo "  help        Show this help message"
    echo ""
    echo "Options:"
    echo "  --new       Force a clean rebuild (ignores cache)"
    echo ""
}

# Simple function to build the Docker image
build() {
    echo "Building OpsChat App Docker image for user ${USER_NAME}..."
    
    BUILD_ARGS=""
    if [ "$FORCE_REBUILD" = true ]; then
        echo "Forcing a clean rebuild (no cache)..."
        BUILD_ARGS="--no-cache --pull"
    fi
    
    docker build $BUILD_ARGS -t $IMAGE_NAME .
    echo "Build complete: $IMAGE_NAME"
}

# Simple function to run the container
run() {
    # Create network
    if ! docker network inspect $NETWORK_NAME &>/dev/null; then
        echo "Creating Docker network: $NETWORK_NAME"
        docker network create $NETWORK_NAME
    fi
    
    # Stop and remove existing containers for this user
    echo "Checking for existing containers for user ${USER_PREFIX}..."
    EXISTING=$(docker ps -a --filter "name=${USER_PREFIX}-opschat" --format "{{.Names}}")
    if [ -n "$EXISTING" ]; then
        echo "Found existing containers, stopping and removing them:"
        echo "$EXISTING"
        docker stop $EXISTING &>/dev/null || true
        docker rm $EXISTING &>/dev/null || true
        echo "Cleanup complete."
    fi
    
    # Connect all required services to our network
    echo "Ensuring all services are connected to network: $NETWORK_NAME"
    
    # Connect MongoDB
    if docker ps | grep -q $MONGO_CONTAINER; then
        echo "MongoDB already running, connecting to our network..."
        if ! docker network inspect $NETWORK_NAME | grep -q $MONGO_CONTAINER; then
            docker network connect $NETWORK_NAME $MONGO_CONTAINER || true
        fi
    else
        echo "Starting MongoDB container..."
        docker run -d \
            --network $NETWORK_NAME \
            --name $MONGO_CONTAINER \
            mongo:latest
    fi
    
    # Connect Qdrant if it exists
    if [ -n "$QDRANT_CONTAINER" ] && docker ps | grep -q $QDRANT_CONTAINER; then
        echo "Connecting Qdrant ($QDRANT_CONTAINER) to our network..."
        if ! docker network inspect $NETWORK_NAME | grep -q "$QDRANT_CONTAINER"; then
            docker network connect $NETWORK_NAME $QDRANT_CONTAINER || true
        fi
    fi
    
    # Connect Ollama if it exists
    if [ -n "$OLLAMA_CONTAINER" ] && docker ps | grep -q $OLLAMA_CONTAINER; then
        echo "Connecting Ollama ($OLLAMA_CONTAINER) to our network..."
        if ! docker network inspect $NETWORK_NAME | grep -q "$OLLAMA_CONTAINER"; then
            docker network connect $NETWORK_NAME $OLLAMA_CONTAINER || true
        fi
    fi

    # Get container IPs for services
    MONGO_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $MONGO_CONTAINER)
    echo "MongoDB IP: $MONGO_IP"
    
    # Find random available ports
    API_PORT=$(find_available_port)
    UI_PORT=$(find_available_port)
    
    echo "Selected random ports - API: $API_PORT, UI: $UI_PORT"
    
    # Get AWS credentials directly from EC2 instance metadata
    echo "Fetching AWS credentials from EC2 instance metadata..."
    AWS_ENV_VARS=$(get_aws_credentials)
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to get AWS credentials. Cannot continue."
        exit 1
    fi
    
    # Verify credentials work before running container
    echo "Verifying AWS credentials..."
    TOKEN=$(curl -s -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')
    ROLE_NAME=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    CREDENTIALS=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME)
    AWS_ACCESS_KEY_ID=$(echo "$CREDENTIALS" | jq -r '.AccessKeyId')
    AWS_SECRET_ACCESS_KEY=$(echo "$CREDENTIALS" | jq -r '.SecretAccessKey')
    AWS_SESSION_TOKEN=$(echo "$CREDENTIALS" | jq -r '.Token')
    
    # Test credentials directly before running container
    AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN AWS_DEFAULT_REGION=$(echo "$CREDENTIALS" | jq -r '.Region // "us-east-1"') aws sts get-caller-identity
    if [ $? -ne 0 ]; then
        echo "WARNING: AWS credentials test failed. Container may not have proper AWS access."
    else
        echo "✅ AWS credentials verified."
    fi
    
    # Set environment variables for the container
    ENV_VARS="-e MONGODB_URI=mongodb://${MONGO_CONTAINER}:27017"
    ENV_VARS="$ENV_VARS -e USER_NAME=${USER_NAME}"
    ENV_VARS="$ENV_VARS -e PYTHONPATH=/app:/app/src"
    ENV_VARS="$ENV_VARS -e HOST_API_PORT=${API_PORT}"
    ENV_VARS="$ENV_VARS -e HOST_UI_PORT=${UI_PORT}"
    ENV_VARS="$ENV_VARS -e USE_AWS=true"
    
    # Only add Qdrant/Ollama vars if containers exist
    if [ -n "$QDRANT_CONTAINER" ]; then
        ENV_VARS="$ENV_VARS -e QDRANT_HOST=${QDRANT_CONTAINER} -e QDRANT_PORT=6333"
    fi
    
    if [ -n "$OLLAMA_CONTAINER" ]; then
        ENV_VARS="$ENV_VARS -e OLLAMA_HOST=${OLLAMA_CONTAINER} -e OLLAMA_PORT=11434"
    fi
    
    # Add AWS credentials to environment variables
    ENV_VARS="$ENV_VARS $AWS_ENV_VARS"
    
    # Run the container with all needed connections and restart policy
    echo "Starting OpsChat App container with AWS credentials..."
    docker run -d \
        --name $OPSCHAT_CONTAINER \
        --network $NETWORK_NAME \
        -p ${API_PORT}:1234 \
        -p ${UI_PORT}:5173 \
        --restart unless-stopped \
        $ENV_VARS \
        $IMAGE_NAME
    
    # Give container time to start
    sleep 2
    
    # Get proper hostname/IP that can be accessed from outside
    HOST_IP=$(hostname -I | awk '{print $1}')
    
    # Verify the container is running
    CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' $OPSCHAT_CONTAINER 2>/dev/null || echo "not found")
    
    # Format fixed to remove extra slash in URL
    if [ "$CONTAINER_STATUS" = "running" ]; then
        printf "==========================================================================================\n"
        printf "🚀 OpsChat App is running!\n"
        printf "🔹 Container name: ${OPSCHAT_CONTAINER}\n"
        printf "🔹 FastAPI: http://${HOST_IP}:${API_PORT} or http://localhost:${API_PORT}\n"
        printf "🔹 Chat UI: http://${HOST_IP}:${UI_PORT} or http://localhost:${UI_PORT}\n\n"
        printf "Internal ports in container:\n"
        printf "🔹 FastAPI internal port: 1234\n"
        printf "🔹 Chat UI internal port: 5173\n\n"
        printf "AWS credentials have been injected from EC2 instance metadata\n\n"
        printf "To view logs: docker logs -f ${OPSCHAT_CONTAINER}\n"
        printf "To stop: docker stop ${OPSCHAT_CONTAINER}\n"
        printf "==========================================================================================\n"
        
        # Show the first few lines of container logs to diagnose any startup issues
        echo "Container log preview:"
        docker logs $OPSCHAT_CONTAINER --tail 10
    else
        echo "ERROR: Container failed to start properly. Check docker logs for details:"
        echo "docker logs $OPSCHAT_CONTAINER"
    fi
}

# Function to clean up
clean() {
    echo "Cleaning up OpsChatUI containers and images for user ${USER_NAME}..."
    # Stop and remove containers
    CONTAINERS=$(docker ps -a --filter "name=${USER_PREFIX}-opschat" --format "{{.Names}}")
    if [ -n "$CONTAINERS" ]; then
        echo "Stopping and removing containers:"
        echo "$CONTAINERS"
        docker stop $CONTAINERS 2>/dev/null || true
        docker rm $CONTAINERS 2>/dev/null || true
    fi
    
    # Remove images
    if docker image inspect $IMAGE_NAME &>/dev/null; then
        echo "Removing image: $IMAGE_NAME"
        docker rmi $IMAGE_NAME
    fi
    
    echo "Cleanup complete."
}

# Parse command line options
COMMAND="all"
for arg in "$@"; do
    case $arg in
        build|run|all|clean|help)
            COMMAND=$arg
            ;;
        --new)
            FORCE_REBUILD=true
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
    esac
done

# Process commands
case $COMMAND in
    build)
        build
        ;;
    run)
        run
        ;;
    all)
        build
        run
        ;;
    clean)
        clean
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit 0
