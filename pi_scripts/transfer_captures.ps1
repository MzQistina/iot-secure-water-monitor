# PowerShell script to transfer capture files from Raspberry Pi to Windows
# Usage: .\transfer_captures.ps1 [test_name]

param(
    [string]$TestName = "",
    [string]$PiHost = "192.168.43.214",
    [string]$PiUser = "pi",
    [string]$RemotePath = "/home/pi/security_captures",
    [string]$LocalPath = ".\security_captures"
)

Write-Host "=== Transferring Security Test Captures ===" -ForegroundColor Cyan
Write-Host ""

# Create local directory if it doesn't exist
if (-not (Test-Path $LocalPath)) {
    New-Item -ItemType Directory -Path $LocalPath | Out-Null
    Write-Host "Created local directory: $LocalPath" -ForegroundColor Green
}

# Build remote path
if ($TestName) {
    $RemotePath = "$RemotePath/${TestName}_*"
    Write-Host "Transferring test: $TestName" -ForegroundColor Yellow
} else {
    $RemotePath = "$RemotePath/*"
    Write-Host "Transferring all captures" -ForegroundColor Yellow
}

Write-Host "From: ${PiUser}@${PiHost}:$RemotePath" -ForegroundColor Gray
Write-Host "To: $LocalPath" -ForegroundColor Gray
Write-Host ""

# Transfer files using SCP
try {
    scp -r "${PiUser}@${PiHost}:$RemotePath" "$LocalPath"
    Write-Host ""
    Write-Host "Transfer completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Files are in: $LocalPath" -ForegroundColor Cyan
    
    # List transferred files
    Get-ChildItem -Path $LocalPath -Recurse | 
        Where-Object { -not $_.PSIsContainer } | 
        Select-Object FullName, Length, LastWriteTime | 
        Format-Table -AutoSize
} catch {
    Write-Host "Error transferring files: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. Raspberry Pi is accessible" -ForegroundColor Yellow
    Write-Host "  2. SSH key is set up (or password authentication enabled)" -ForegroundColor Yellow
    Write-Host "  3. Remote path exists: $RemotePath" -ForegroundColor Yellow
}





