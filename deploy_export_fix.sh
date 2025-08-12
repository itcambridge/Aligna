#!/bin/bash
# Script to deploy the export fix to the Linode server

# Set variables
APP_DIR="/home/cvgen/grounded-cv-generator"
BRANCH="feature/next-generation-enhancements"

# Display banner
echo "====================================================="
echo "Aligna Export Fix Deployment Script"
echo "====================================================="

# Step 1: Pull the latest changes
echo "[1/5] Pulling latest changes from GitHub..."
cd $APP_DIR
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

# Step 2: Create exports directory with proper permissions
echo "[2/5] Creating exports directory with proper permissions..."
mkdir -p $APP_DIR/exports
chmod 777 $APP_DIR/exports

# Step 3: Rebuild the Docker image
echo "[3/5] Rebuilding Docker image..."
docker compose down
docker compose build --no-cache app

# Step 4: Start the containers
echo "[4/5] Starting containers..."
docker compose up -d

# Step 5: Verify deployment
echo "[5/5] Verifying deployment..."
echo "Checking if containers are running:"
docker compose ps

echo "Checking exports directory:"
ls -la $APP_DIR/exports

echo "====================================================="
echo "Deployment complete!"
echo "====================================================="
echo "To verify the fix, try exporting a CV in DOCX or PDF format."
echo "If you encounter any issues, check the logs with:"
echo "docker compose logs app | grep -i export"
echo "====================================================="
