# Docker Deployment Guide for Aligna Export Fix

This guide provides instructions for deploying the Aligna export fix using Docker and Docker Compose.

## Overview

The export fix addresses issues with DOCX and PDF exports in the Aligna application by:

1. Using a dedicated exports directory instead of temporary files
2. Ensuring proper volume mounting in Docker
3. Adding detailed logging for troubleshooting

## Prerequisites

- Docker installed on your server
- Docker Compose installed on your server
- Git installed on your server
- Access to the GitHub repository

## Deployment Options

### Option 1: Using the Automated Deployment Script

We've provided a deployment script that automates the entire process:

1. Copy the `scripts/deploy_docker_export_fix.sh` script to your server
2. Make it executable:
   ```bash
   chmod +x deploy_docker_export_fix.sh
   ```
3. Run the script:
   ```bash
   ./deploy_docker_export_fix.sh
   ```

The script will:
- Pull the latest changes from GitHub
- Create the exports directory with proper permissions
- Rebuild the Docker image
- Start the containers
- Verify the deployment

### Option 2: Manual Deployment

If you prefer to deploy manually, follow these steps:

1. Pull the latest changes from GitHub:
   ```bash
   cd /path/to/your/app
   git fetch origin
   git checkout feature/next-generation-enhancements
   git pull origin feature/next-generation-enhancements
   ```

2. Create the exports directory:
   ```bash
   mkdir -p exports
   chmod 777 exports
   ```

3. Stop the existing containers:
   ```bash
   docker compose down
   ```

4. Rebuild the Docker image:
   ```bash
   docker compose build --no-cache app
   ```

5. Start the containers:
   ```bash
   docker compose up -d
   ```

6. Verify the deployment:
   ```bash
   docker compose ps
   ls -la exports
   ```

## Docker Compose Configuration

The `docker-compose.yml` file has been updated to include a volume mount for the exports directory:

```yaml
services:
  app:
    build: .
    # ... other configuration ...
    volumes:
      # ... other volumes ...
      # Mount for exports
      - ./exports:/app/exports
```

This ensures that the exports directory on the host is mounted to the `/app/exports` directory in the container, allowing files to be shared between the host and the container.

## Troubleshooting

### Issue: Container Fails to Start

If the container fails to start, check the Docker logs:

```bash
docker compose logs app
```

### Issue: Permission Denied Errors

If you see permission denied errors when trying to write to the exports directory:

```bash
chmod -R 777 exports
docker compose restart app
```

### Issue: Exports Still Not Working

If exports still don't work after deployment:

1. Check if the exports directory exists and has the correct permissions:
   ```bash
   ls -la exports
   ```

2. Verify that the Docker container has access to the exports directory:
   ```bash
   docker compose exec app ls -la /app/exports
   ```

3. Check the logs for any error messages:
   ```bash
   docker compose logs app | grep -i export
   ```

4. Check the export_debug.log file:
   ```bash
   cat export_debug.log
   ```

### Issue: Docker Compose Command Not Found

If you get a "command not found" error when running `docker compose`:

1. Try using `docker-compose` (with a hyphen) instead
2. Make sure Docker Compose is installed
3. If using Docker Compose V2, make sure you have the Docker Compose plugin installed

## Docker Commands Reference

Here are some useful Docker commands for managing the application:

```bash
# View container logs
docker compose logs -f app

# Restart containers
docker compose restart

# Stop containers
docker compose down

# Start containers
docker compose up -d

# Check container status
docker compose ps

# Execute command inside container
docker compose exec app <command>

# View container resource usage
docker stats
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Aligna Export Fix README](./EXPORT_FIX_README.md)
- [Linode Deployment Instructions](./LINODE_DEPLOYMENT_INSTRUCTIONS.md)
