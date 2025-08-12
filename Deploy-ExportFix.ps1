# PowerShell script to deploy the export fix to the Linode server via SSH

# Set variables
$RemoteUser = "cvgen"
$RemoteHost = "your-linode-server.com" # Replace with your actual server hostname or IP
$RemoteDir = "/home/cvgen/grounded-cv-generator"
$Branch = "feature/next-generation-enhancements"

# Display banner
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Aligna Export Fix Deployment Script (PowerShell)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Check if ssh command is available
try {
    $null = Get-Command ssh -ErrorAction Stop
    Write-Host "SSH command is available." -ForegroundColor Green
} catch {
    Write-Host "Error: SSH command not found. Please install OpenSSH client." -ForegroundColor Red
    exit 1
}

# Step 1: Connect to the server and pull the latest changes
Write-Host "[1/5] Pulling latest changes from GitHub..." -ForegroundColor Yellow
$pullCommand = @"
cd $RemoteDir && 
git fetch origin && 
git checkout $Branch && 
git pull origin $Branch
"@
ssh $RemoteUser@$RemoteHost $pullCommand

# Step 2: Create exports directory with proper permissions
Write-Host "[2/5] Creating exports directory with proper permissions..." -ForegroundColor Yellow
$dirCommand = @"
mkdir -p $RemoteDir/exports && 
chmod 777 $RemoteDir/exports
"@
ssh $RemoteUser@$RemoteHost $dirCommand

# Step 3: Rebuild the Docker image
Write-Host "[3/5] Rebuilding Docker image..." -ForegroundColor Yellow
$rebuildCommand = @"
cd $RemoteDir && 
docker compose down && 
docker compose build --no-cache app
"@
ssh $RemoteUser@$RemoteHost $rebuildCommand

# Step 4: Start the containers
Write-Host "[4/5] Starting containers..." -ForegroundColor Yellow
$startCommand = @"
cd $RemoteDir && 
docker compose up -d
"@
ssh $RemoteUser@$RemoteHost $startCommand

# Step 5: Verify deployment
Write-Host "[5/5] Verifying deployment..." -ForegroundColor Yellow
$verifyCommand = @"
cd $RemoteDir && 
echo "Checking if containers are running:" && 
docker compose ps && 
echo "Checking exports directory:" && 
ls -la $RemoteDir/exports
"@
ssh $RemoteUser@$RemoteHost $verifyCommand

# Display completion message
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "To verify the fix, try exporting a CV in DOCX or PDF format."
Write-Host "If you encounter any issues, check the logs with:"
Write-Host "ssh $RemoteUser@$RemoteHost 'cd $RemoteDir && docker compose logs app | grep -i export'" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
