# Script to identify unused .md files
$referencedFiles = @(
    "README.md",
    "RASPBIAN_QUICK_START.md",
    "RASPBERRY_PI_SETUP.md",
    "RASPBERRY_PI_5_SD_CARD_SETUP.md",
    "FILES_TO_UPDATE_RASPBIAN.md",
    "RASPBIAN_SIMULATION_GUIDE.md",
    "VIRTUALBOX_SIMULATION_SETUP.md",
    "HOW_TO_SIMULATE_READINGS.md",
    "DOCKER_DEPLOYMENT_GUIDE.md",
    "LOCAL_DOCKER_TESTING.md",
    "RENDER_DEPLOYMENT_GUIDE.md",
    "PYTHONANYWHERE_DEPLOYMENT_GUIDE.md",
    "FILEZILLA_DEPLOYMENT_GUIDE.md",
    "LITESPEED_DEPLOYMENT_GUIDE.md",
    "VIRTUALBOX_SERVER_DEPLOYMENT.md",
    "APACHE_SETUP.md",
    "HIVEMQ_CLOUD_SETUP.md",
    "MQTT_BROKER_SETUP.md",
    "MQTT_TLS_SETUP.md",
    "PROVISION_AGENT_GUIDE.md",
    "PROVISION_AGENT_AUTOMATION.md",
    "RASPBIAN_TROUBLESHOOTING.md",
    "TROUBLESHOOTING.md",
    "RASPBERRY_PI_ARCHITECTURE.md",
    "CPU_USAGE_ANALYSIS.md",
    "SAME_DEVICE_ID_DIFFERENT_USERS.md",
    "PRE_DEPLOYMENT_CHECKLIST.md",
    "RENDER_DATABASE_SETUP.md"
)

$allMdFiles = Get-ChildItem -Filter *.md | Select-Object -ExpandProperty Name
$unusedFiles = $allMdFiles | Where-Object { $referencedFiles -notcontains $_ }

Write-Host "Unused .md files:" -ForegroundColor Yellow
$unusedFiles | ForEach-Object { Write-Host "  $_" }

Write-Host "`nTotal unused files: $($unusedFiles.Count)" -ForegroundColor Cyan









