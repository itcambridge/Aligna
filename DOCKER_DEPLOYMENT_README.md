# Docker Deployment Instructions

This document provides simplified instructions for deploying the CV export functionality fix to the Linode server using Docker.

## Overview of Changes

1. Updated `ui/components/enhanced_export.py` with:
   - Enhanced logging throughout the export process
   - Improved error handling for file operations
   - Detailed logging of export process steps
   - Traceback logging for exceptions

2. Updated `docker-compose.yml` to include necessary volume mounts:
   - `/tmp:/tmp` for temporary directories
   - `./logs:/app/logs` for application logs
   - `./export_debug.log:/app/export_debug.log` for export debug logs
   - `.:/app` to ensure the container uses the current code from the filesystem

## Deployment Steps

1. SSH into the Linode server:
   ```bash
   ssh username@your-linode-server-ip
   ```

2. Navigate to the application directory:
   ```bash
   cd /home/cvgen/grounded-cv-generator
   ```

3. Pull the latest changes from GitHub:
   ```bash
   git pull origin feature/next-generation-enhancements
   ```

4. Create necessary directories and files:
   ```bash
   mkdir -p logs
   touch export_debug.log
   chmod 666 export_debug.log
   ```

5. Restart the Docker containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Verification

1. Check if the containers are running:
   ```bash
   docker-compose ps
   ```

2. Test the export functionality:
   - Log in to the application
   - Navigate to the CV export section
   - Try exporting a CV in different formats (DOCX, PDF, Text, JSON)

3. Check the logs for any errors:
   ```bash
   tail -f export_debug.log
   ```

## Troubleshooting

If issues persist:

1. Check container logs:
   ```bash
   docker-compose logs app
   ```

2. Verify volume mounts:
   ```bash
   docker-compose exec app ls -la /tmp
   docker-compose exec app ls -la /app/logs
   docker-compose exec app ls -la /app/export_debug.log
   ```

3. Check if the container has the necessary permissions:
   ```bash
   docker-compose exec app id
   ```

4. Inspect the container configuration:
   ```bash
   docker inspect $(docker-compose ps -q app)
