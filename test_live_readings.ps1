# Test Live Readings API
# Run this in PowerShell to diagnose why live readings aren't showing

$userId = 6  # Change to your user_id
$serverUrl = "http://localhost:5000"

Write-Host "Testing Live Readings API for user_id: $userId"
Write-Host "=" * 50
Write-Host ""

# Test 1: Check API endpoint
Write-Host "1. Testing /api/active_sensors endpoint..."
Write-Host "   Note: This endpoint requires authentication."
Write-Host "   You need to be logged in via browser first, or use curl with cookies."
Write-Host ""

# Try to get response (will fail if not authenticated, but we can see the error)
try {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $response = Invoke-WebRequest -Uri "$serverUrl/api/active_sensors" -WebSession $session -ErrorAction Stop
    $responseContent = $response.Content
    
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Response length: $($responseContent.Length) bytes"
    Write-Host "   Raw response: $responseContent"
    Write-Host ""
    
    try {
        $data = $responseContent | ConvertFrom-Json
        Write-Host "   Active sensors count: $($data.active_sensors.Count)"
        
        if ($data.active_sensors.Count -gt 0) {
            Write-Host "   ✅ Found sensors:"
            $data.active_sensors | ForEach-Object {
                Write-Host "      - $($_.device_id): value=$($_.value), location=$($_.location), type=$($_.device_type)"
            }
        } else {
            Write-Host "   ⚠️  No sensors returned (empty array)"
        }
    } catch {
        Write-Host "   ⚠️  Response is not valid JSON: $($_.Exception.Message)"
        Write-Host "   This might mean you're not authenticated or there's a server error"
    }
} catch {
    Write-Host "   ❌ Request failed: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   HTTP Status: $statusCode"
        
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            Write-Host "   Response body: $responseBody"
        } catch {
            Write-Host "   Could not read response body"
        }
        
        if ($statusCode -eq 401) {
            Write-Host "   ⚠️  Authentication required - you need to log in first"
        } elseif ($statusCode -eq 500) {
            Write-Host "   ⚠️  Server error - check Flask console for details"
        }
    }
}
Write-Host ""

# Test 2: Check database directly
Write-Host "2. Checking database for recent sensor data..."
Write-Host "   Run this SQL query:"
Write-Host "   SELECT device_id, user_id, value, recorded_at"
Write-Host "   FROM sensor_data"
Write-Host "   WHERE user_id = $userId"
Write-Host "   ORDER BY recorded_at DESC"
Write-Host "   LIMIT 10;"
Write-Host ""

# Test 3: Check if sensors are marked as active
Write-Host "3. Checking if sensors are marked as 'active'..."
Write-Host "   Run this SQL query:"
Write-Host "   SELECT device_id, status, location"
Write-Host "   FROM sensors"
Write-Host "   WHERE user_id = $userId;"
Write-Host ""

# Test 4: Check Flask server logs
Write-Host "4. Check Flask server console for debug messages:"
Write-Host "   Look for:"
Write-Host "   - DEBUG: api_active_sensors - Found X active sensors for user $userId"
Write-Host "   - DEBUG: api_active_sensors - Found database reading for..."
Write-Host "   - ERROR: api_active_sensors - ..."
Write-Host ""

Write-Host "=" * 50
Write-Host "Next steps:"
Write-Host "1. If API returns empty array, check database queries above"
Write-Host "2. If sensors exist but aren't 'active', update them:"
Write-Host "   UPDATE sensors SET status = 'active' WHERE user_id = $userId;"
Write-Host "3. Restart Flask server after making changes"
Write-Host "4. Refresh the /readings page"
