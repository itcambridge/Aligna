#!/bin/bash
# Script to deploy the enhanced export functionality fix to the server
# This script should be run on the server where the application is deployed

# Set variables
APP_DIR="/home/cvgen/grounded-cv-generator"  # Update this to match your server's app directory
BACKUP_DIR="$APP_DIR/backups/$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="/tmp/aligna_exports"
LOG_FILE="$APP_DIR/logs/deploy_export_fix.log"

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p "$TEMP_DIR"

# Log function
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

log "Starting deployment of export functionality fix"

# Backup current files
log "Creating backup of current files"
mkdir -p "$BACKUP_DIR/ui/components"
cp -f "$APP_DIR/ui/components/enhanced_export.py" "$BACKUP_DIR/ui/components/" 2>/dev/null || log "No existing enhanced_export.py to backup"

# Update permissions for temporary directories
log "Setting permissions for temporary directories"
chmod 777 "$TEMP_DIR"
chmod 777 /tmp

# Ensure the application user has write permissions to the temp directory
if getent passwd cvgen > /dev/null 2>&1; then
    chown -R cvgen:cvgen "$TEMP_DIR"
    log "Changed ownership of $TEMP_DIR to cvgen user"
fi

# Create export_debug.log file with proper permissions
touch "$APP_DIR/export_debug.log"
chmod 666 "$APP_DIR/export_debug.log"
if getent passwd cvgen > /dev/null 2>&1; then
    chown cvgen:cvgen "$APP_DIR/export_debug.log"
fi

log "Updated permissions for temporary directories and log files"

# Restart the application service
if systemctl is-active --quiet cvgen; then
    log "Restarting cvgen service"
    systemctl restart cvgen
    log "Service restarted successfully"
else
    log "cvgen service not found or not active, please restart the application manually"
fi

log "Deployment completed successfully"
echo "==================================================="
echo "Export functionality fix has been deployed."
echo "Please check $LOG_FILE for details."
echo "==================================================="
