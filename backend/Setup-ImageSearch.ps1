# Image Search Backend Setup for Windows
# Run this script in PowerShell as Administrator

Write-Host "Setting up Image Search Backend on Windows..." -ForegroundColor Green

# Check if Docker is running
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is available: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Docker is not installed or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop for Windows" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Desktop is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Docker Desktop is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Create necessary directories
$directories = @(
    "static\uploads\images",
    "static\uploads\thumbnails", 
    "static\uploads\faces",
    "logs",
    "chroma_db",
    "backups"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Copy environment file
if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Environment file created from example" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Please edit .env file with your configuration!" -ForegroundColor Yellow
}

# Generate secure secrets
function Generate-SecurePassword {
    param([int]$Length = 32)
    $chars = "abcdefghklmnoprstuvwxyzABCDEFGHKLMNOPRSTUVWXYZ1234567890!@#$%^&*"
    $password = ""
    1..$Length | ForEach-Object { $password += $chars[(Get-Random -Maximum $chars.Length)] }
    return $password
}

$jwtSecret = Generate-SecurePassword -Length 64
$mysqlRootPass = Generate-SecurePassword -Length 16
$mysqlAppPass = Generate-SecurePassword -Length 16
$rabbitmqPass = Generate-SecurePassword -Length 16

# Update .env file with secure secrets
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$jwtSecret"
    $envContent = $envContent -replace "MYSQL_ROOT_PASSWORD=.*", "MYSQL_ROOT_PASSWORD=$mysqlRootPass"
    $envContent = $envContent -replace "MYSQL_PASSWORD=.*", "MYSQL_PASSWORD=$mysqlAppPass"
    $envContent = $envContent -replace "RABBITMQ_PASSWORD=.*", "RABBITMQ_PASSWORD=$rabbitmqPass"
    $envContent | Set-Content ".env"
    Write-Host "✓ Updated .env with secure secrets" -ForegroundColor Green
}

Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your email configuration (MAIL_* settings)" -ForegroundColor White
Write-Host "2. Run: docker-compose up --build" -ForegroundColor White  
Write-Host "3. Wait for all services to start (this may take several minutes)" -ForegroundColor White
Write-Host "4. Access the application at http://localhost:5000" -ForegroundColor White
Write-Host "5. API documentation will be available at http://localhost:5000/api/v1/docs" -ForegroundColor White

Write-Host "`nTroubleshooting:" -ForegroundColor Cyan
Write-Host "- If you get port conflicts, stop other services using ports 3306, 5000, 6379, 5672" -ForegroundColor White
Write-Host "- For GPU support on Windows, you need Docker Desktop with WSL2 and NVIDIA Container Toolkit" -ForegroundColor White
Write-Host "- Check logs with: docker-compose logs -f" -ForegroundColor White

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')