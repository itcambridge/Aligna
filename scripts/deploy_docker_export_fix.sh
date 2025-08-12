#!/bin/bash
# Script to deploy the export fix using Docker commands

# Set variables
APP_DIR="/home/cvgen/grounded-cv-generator"
BRANCH="feature/next-generation-enhancements"
GITHUB_REPO="https://github.com/itcambridge/Aligna.git"

# Display banner
echo "====================================================="
echo "Aligna Export Fix Docker Deployment Script"
echo "====================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
if ! command_exists docker; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose && ! command_exists "docker compose"; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists git; then
    echo "Error: Git is not installed. Please install Git first."
    exit 1
fi

# Determine docker compose command
if command_exists "docker compose"; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Step 1: Pull the latest changes
echo "[1/6] Pulling latest changes from GitHub..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "Directory $APP_DIR does not exist. Cloning repository..."
    mkdir -p "$APP_DIR"
    git clone "$GITHUB_REPO" "$APP_DIR"
    cd "$APP_DIR"
    git checkout "$BRANCH"
fi

# Step 2: Create exports directory with proper permissions
echo "[2/6] Creating exports directory with proper permissions..."
mkdir -p "$APP_DIR/exports"
chmod 777 "$APP_DIR/exports"

# Step 3: Check Docker status
echo "[3/6] Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

# Step 4: Stop and remove existing containers
echo "[4/6] Stopping existing containers..."
$DOCKER_COMPOSE down

# Step 5: Rebuild the Docker image
echo "[5/6] Rebuilding Docker image..."
$DOCKER_COMPOSE build --no-cache app

# Step 6: Start the containers
echo "[6/6] Starting containers..."
$DOCKER_COMPOSE up -d

# Verify deployment
echo "Verifying deployment..."
echo "Checking if containers are running:"
$DOCKER_COMPOSE ps

echo "Checking exports directory:"
ls -la "$APP_DIR/exports"

echo "====================================================="
echo "Deployment complete!"
echo "====================================================="
echo "To verify the fix, try exporting a CV in DOCX or PDF format."
echo "If you encounter any issues, check the logs with:"
echo "$DOCKER_COMPOSE logs app | grep -i export"
echo "====================================================="

# Provide additional commands for troubleshooting
echo "Useful commands for troubleshooting:"
echo "1. View logs: $DOCKER_COMPOSE logs -f app"
echo "2. Restart containers: $DOCKER_COMPOSE restart"
echo "3. Check container status: $DOCKER_COMPOSE ps"
echo "4. Check exports directory: ls -la $APP_DIR/exports"
echo "5. Check export_debug.log: cat $APP_DIR/export_debug.log"
echo "====================================================="
