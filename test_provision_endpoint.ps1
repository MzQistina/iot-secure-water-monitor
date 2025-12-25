# Test script to verify provision endpoint is working
# Run this while Flask is running

Write-Host "Testing /api/provision/update endpoint..." -ForegroundColor Cyan
Write-Host ""

# You need to be logged in first - get session cookie
Write-Host "Note: You must be logged in to the web interface first!" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:5000 in your browser" -ForegroundColor Yellow
Write-Host "2. Log in" -ForegroundColor Yellow
Write-Host "3. Open browser DevTools (F12) -> Network tab" -ForegroundColor Yellow
Write-Host "4. Copy the 'session' cookie value" -ForegroundColor Yellow
Write-Host "5. Run this command with your session cookie:" -ForegroundColor Yellow
Write-Host ""
Write-Host '   $session = "YOUR_SESSION_COOKIE_HERE"' -ForegroundColor Green
Write-Host '   Invoke-WebRequest -Uri "http://localhost:5000/api/provision/update" -Method POST -Headers @{"Cookie"="session=$session"} -ContentType "application/json" -Body ''{"device_id":"sal01"}''' -ForegroundColor Green
Write-Host ""
Write-Host "OR use curl:" -ForegroundColor Yellow
Write-Host '   curl -X POST http://localhost:5000/api/provision/update -H "Content-Type: application/json" -H "Cookie: session=YOUR_SESSION_COOKIE" -d ''{"device_id":"sal01"}''' -ForegroundColor Green
Write-Host ""
Write-Host "Check the Flask console for debug output!" -ForegroundColor Cyan
