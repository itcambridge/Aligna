# Linode Deployment Instructions for Aligna Export Fix

This guide provides step-by-step instructions for deploying the Aligna export fix to a Linode server.

## Prerequisites

- SSH access to your Linode server
- Git installed on the server
- Docker and Docker Compose installed on the server
- Access to the GitHub repository

## Deployment Steps

### 1. Connect to Your Linode Server

```bash
ssh username@your-linode-server-ip
```

Replace `username` with your actual username and `your-linode-server-ip` with your Linode server's IP address.

### 2. Navigate to the Application Directory

```bash
cd /home/cvgen/grounded-cv-generator
```

Adjust the path if your application is installed in a different location.

### 3. Backup Current Configuration (Optional but Recommended)

```bash
cp docker-compose.yml docker-compose.yml.backup
cp -r ui/components ui/components.backup
cp -r export export.backup
```

### 4. Pull the Latest Changes from GitHub

```bash
git fetch origin
git checkout feature/next-generation-enhancements
git pull origin feature/next-generation-enhancements
```

### 5. Create the Exports Directory

```bash
mkdir -p exports
chmod 777 exports
```

This creates the exports directory and sets permissions to allow the Docker container to write to it.

### 6. Rebuild the Docker Image

```bash
docker compose down
docker compose build --no-cache app
```

The `--no-cache` flag ensures that the image is rebuilt from scratch, incorporating all the code changes.

### 7. Start the Containers

```bash
docker compose up -d
```

The `-d` flag runs the containers in detached mode (in the background).

### 8. Verify the Deployment

Check if the containers are running:

```bash
docker compose ps
```

Check the exports directory:

```bash
ls -la exports
```

Check the logs for any errors:

```bash
docker compose logs app | grep -i error
```

### 9. Test the Export Functionality

1. Open your browser and navigate to your Aligna application
2. Log in and generate a CV
3. Click on the DOCX or PDF export buttons
4. Check if the download works correctly

## Troubleshooting

### Issue: Containers Not Starting

If the containers fail to start, check the Docker logs:

```bash
docker compose logs app
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

5. Try restarting the Docker containers:
   ```bash
   docker compose restart app
   ```

### Issue: Permission Denied Errors

If you see permission denied errors in the logs:

```bash
chmod -R 777 exports
docker compose restart app
```

## Rollback Procedure

If you need to roll back the changes:

1. Stop the containers:
   ```bash
   docker compose down
   ```

2. Restore the backup files:
   ```bash
   cp docker-compose.yml.backup docker-compose.yml
   cp -r ui/components.backup/* ui/components/
   cp -r export.backup/* export/
   ```

3. Rebuild and restart:
   ```bash
   docker compose build --no-cache app
   docker compose up -d
   ```

## Monitoring

To monitor the application after deployment:

```bash
# Check container status
docker compose ps

# Check container logs
docker compose logs -f app

# Check resource usage
docker stats
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Linode Documentation](https://www.linode.com/docs/)
- [Aligna Export Fix README](./EXPORT_FIX_README.md)
