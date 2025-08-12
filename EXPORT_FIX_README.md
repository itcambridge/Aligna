# CV Export Functionality Fix

This document explains the issue with CV exports in the production environment and provides instructions for deploying the fix.

## Issue Description

Users are experiencing problems when trying to export CVs in various formats (particularly DOCX and PDF) in the production environment. The export functionality works correctly in the development/test environment but fails in production.

### Root Causes

1. **Temporary Directory Permissions**: The application needs write access to temporary directories to generate export files.
2. **Logging Configuration**: Enhanced logging has been added to help diagnose any remaining issues.
3. **File Handling**: Improved error handling and logging for file operations.

## Fix Implementation

The following changes have been made to the `ui/components/enhanced_export.py` file:

1. Added comprehensive logging throughout the export process
2. Improved error handling for file operations
3. Added detailed logging of the export process steps
4. Added traceback logging for exceptions

## Deployment Instructions

### Option 1: Linux Deployment Script

1. Copy the `scripts/deploy_export_fix.sh` script to the production server
2. Make it executable: `chmod +x deploy_export_fix.sh`
3. Run the script: `sudo ./deploy_export_fix.sh`

### Option 2: Windows Deployment Script

1. Copy the following files to the Windows server:
   - `ui/components/enhanced_export.py`
   - `scripts/Deploy-ExportFix.ps1`

2. Open PowerShell as Administrator

3. Run the script:
   ```powershell
   cd path\to\application
   .\scripts\Deploy-ExportFix.ps1
   ```

4. If the application is in a different directory, specify the path:
   ```powershell
   .\scripts\Deploy-ExportFix.ps1 -AppDir "C:\path\to\application"
   ```

### Option 2: Manual Deployment

1. SSH into the production server
2. Create a backup of the current file:
   ```bash
   mkdir -p /home/cvgen/grounded-cv-generator/backups/$(date +%Y%m%d_%H%M%S)/ui/components
   cp /home/cvgen/grounded-cv-generator/ui/components/enhanced_export.py /home/cvgen/grounded-cv-generator/backups/$(date +%Y%m%d_%H%M%S)/ui/components/
   ```
3. Copy the updated `ui/components/enhanced_export.py` file to the server
4. Create and set permissions for the temporary directory:
   ```bash
   mkdir -p /tmp/aligna_exports
   chmod 777 /tmp/aligna_exports
   chown -R cvgen:cvgen /tmp/aligna_exports
   ```
5. Create and set permissions for the log file:
   ```bash
   touch /home/cvgen/grounded-cv-generator/export_debug.log
   chmod 666 /home/cvgen/grounded-cv-generator/export_debug.log
   chown cvgen:cvgen /home/cvgen/grounded-cv-generator/export_debug.log
   ```
6. Restart the application:
   ```bash
   sudo systemctl restart cvgen
   ```

### Option 3: Docker Deployment

If using Docker, you have two options:

#### Option 3A: Using the Docker Deployment Script

1. Copy the following files to the production server:
   - `ui/components/enhanced_export.py`
   - `docker-compose.export-fix.yml`
   - `scripts/deploy_docker_export_fix.sh`

2. Make the script executable:
   ```bash
   chmod +x scripts/deploy_docker_export_fix.sh
   ```

3. Run the script from the application root directory:
   ```bash
   ./scripts/deploy_docker_export_fix.sh
   ```

This script will:
- Back up the current files
- Update the docker-compose.yml file with the necessary volume mounts
- Rebuild and restart the Docker containers

#### Option 3B: Manual Docker Deployment

1. Copy the updated `ui/components/enhanced_export.py` file to the server
2. Update your docker-compose.yml to include the necessary volume mounts:
   ```yaml
   # Add to the app service in docker-compose.yml
   volumes:
     - /tmp:/tmp
     - ./logs:/app/logs
     - ./export_debug.log:/app/export_debug.log
   ```
3. Rebuild and restart the Docker container:
   ```bash
   docker-compose down
   docker-compose build app
   docker-compose up -d
   ```

## Verification

After deploying the fix:

1. Log in to the application
2. Navigate to the CV export section
3. Try exporting a CV in different formats (DOCX, PDF, Text, JSON)
4. Check the logs for any errors:
   ```bash
   tail -f /home/cvgen/grounded-cv-generator/export_debug.log
   ```

## Troubleshooting

### Linux Troubleshooting

If issues persist on Linux:

1. Check the log file for detailed error messages:
   ```bash
   cat /home/cvgen/grounded-cv-generator/export_debug.log
   ```

2. Verify permissions:
   ```bash
   ls -la /tmp/aligna_exports
   ls -la /tmp
   ```

3. Check if the application service is running:
   ```bash
   sudo systemctl status cvgen
   ```

4. Check for any Docker container issues:
   ```bash
   docker-compose logs app
   ```

5. Verify the Python environment has the necessary dependencies:
   ```bash
   source /home/cvgen/grounded-cv-generator/venv/bin/activate
   pip list | grep python-docx
   pip list | grep reportlab
   ```

### Windows Troubleshooting

If issues persist on Windows:

1. Check the log file for detailed error messages:
   ```powershell
   Get-Content .\export_debug.log
   ```

2. Verify permissions on the temporary directory:
   ```powershell
   Get-Acl -Path "C:\Temp\aligna_exports" | Format-List
   ```

3. Check if the application service is running:
   ```powershell
   Get-Service -Name "Aligna" -ErrorAction SilentlyContinue
   ```

4. Verify the Python environment has the necessary dependencies:
   ```powershell
   & ".\.venv\Scripts\Activate.ps1"
   pip list | findstr "python-docx"
   pip list | findstr "reportlab"
   ```

5. Check for any file locks that might be preventing access:
   ```powershell
   # Install Handle tool from Sysinternals if needed
   # Check for locks on the temp directory
   handle.exe "C:\Temp\aligna_exports"
   ```

### Docker Troubleshooting

If using Docker:

1. Check container logs:
   ```bash
   docker-compose logs app
   ```

2. Verify volume mounts:
   ```bash
   docker-compose exec app ls -la /tmp
   ```

3. Check if the container has the necessary permissions:
   ```bash
   docker-compose exec app id
   ```

4. Inspect the container configuration:
   ```bash
   docker inspect $(docker-compose ps -q app)
   ```

## Contact

If you need assistance with this fix, please contact the development team.
