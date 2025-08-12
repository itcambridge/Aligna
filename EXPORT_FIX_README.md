# Aligna Export Fix

This document explains the fix for the CV export functionality in Aligna, which addresses issues with DOCX and PDF exports.

## Problem

The original implementation used temporary files for exporting CVs, which caused issues in the Docker environment:

1. Temporary files were created inside the container but not properly accessible
2. Permission issues when trying to read/write temporary files
3. Files were lost when the container restarted

## Solution

The fix implements the following changes:

1. Created a dedicated `exports` directory for storing exported files
2. Modified `docker-compose.yml` to mount this directory in the Docker container
3. Updated `ui/components/enhanced_export.py` to use the exports directory instead of temporary files
4. Updated `export/cv_exporter.py` to use the exports directory for DOCX and PDF generation
5. Added more detailed logging for troubleshooting

## Deployment Instructions

### Option 1: Using the Deployment Script (Linux/macOS)

1. Copy the `deploy_export_fix.sh` script to your server
2. Make it executable: `chmod +x deploy_export_fix.sh`
3. Run the script: `./deploy_export_fix.sh`

### Option 2: Using the PowerShell Script (Windows)

1. Edit the `Deploy-ExportFix.ps1` script to set your server details
2. Run the script in PowerShell: `.\Deploy-ExportFix.ps1`

### Option 3: Manual Deployment

1. SSH into your Linode server
2. Navigate to the application directory:
   ```bash
   cd /home/cvgen/grounded-cv-generator
   ```

3. Pull the latest changes from GitHub:
   ```bash
   git fetch origin
   git checkout feature/next-generation-enhancements
   git pull origin feature/next-generation-enhancements
   ```

4. Create the exports directory and set permissions:
   ```bash
   mkdir -p exports
   chmod 777 exports
   ```

5. Rebuild and restart the Docker containers:
   ```bash
   docker compose down
   docker compose build --no-cache app
   docker compose up -d
   ```

## Verification

To verify that the fix is working:

1. Access the Aligna application in your browser
2. Generate a CV
3. Click on the DOCX or PDF export buttons
4. Check if the download works correctly

If you encounter any issues, check the logs:

```bash
docker compose logs app | grep -i export
```

Or check the export_debug.log file:

```bash
cat export_debug.log
```

## Technical Details

### Changes to docker-compose.yml

Added a volume mount for the exports directory:

```yaml
volumes:
  # Mount for exports
  - ./exports:/app/exports
```

### Changes to enhanced_export.py

Modified the export_cv function to use the exports directory:

```python
# Create exports directory if it doesn't exist
exports_dir = os.path.join(os.getcwd(), "exports")
os.makedirs(exports_dir, exist_ok=True)

# Generate output file path in the exports directory
output_file = os.path.join(exports_dir, f"cv_{template_id}.{extension}")
```

### Changes to cv_exporter.py

Updated the DOCX and PDF export functions to use the exports directory:

```python
# Save to the exports directory
exports_dir = os.path.join(os.getcwd(), "exports")
os.makedirs(exports_dir, exist_ok=True)
output_path = os.path.join(exports_dir, f"cv_{template['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
```

## Troubleshooting

If exports still don't work after deployment:

1. Check if the exports directory exists and has the correct permissions
2. Verify that the Docker container has access to the exports directory
3. Check the logs for any error messages
4. Ensure the application was rebuilt with the latest code changes
5. Try restarting the Docker containers
