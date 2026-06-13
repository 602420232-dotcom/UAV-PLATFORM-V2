$base = "d:\Developer\workplace\py\iteam\trae\uav-platform-v2"
$services = @(
    @{name="platform-api"; jar="$base\services\platform-api\target\platform-api-2.0.0.jar"; port=18081},
    @{name="weather-api"; jar="$base\services\weather-api\target\weather-api-2.0.0.jar"; port=18082},
    @{name="assimilation-api"; jar="$base\services\assimilation-api\target\assimilation-api-2.0.0.jar"; port=18083},
    @{name="risk-api"; jar="$base\services\risk-api\target\risk-api-2.0.0.jar"; port=18084},
    @{name="observation-api"; jar="$base\services\observation-api\target\observation-api-2.0.0.jar"; port=18085},
    @{name="planning-api"; jar="$base\services\planning-api\target\planning-api-2.0.0.jar"; port=18086},
    @{name="utm-api"; jar="$base\services\utm-api\target\utm-api-2.0.0.jar"; port=18087},
    @{name="api-gateway"; jar="$base\gateway\api-gateway\target\api-gateway-2.0.0.jar"; port=18080}
)

foreach ($svc in $services) {
    Write-Output "Starting $($svc.name) on port $($svc.port)..."
    Start-Process -FilePath "java" -ArgumentList "-jar", $svc.jar, "--server.port=$($svc.port)" -WindowStyle Minimized -WorkingDirectory $base
}

Write-Output "`nAll 8 services launched. Waiting 60s for startup..."
Start-Sleep -Seconds 60

$allOk = $true
foreach ($svc in $services) {
    $conn = Test-NetConnection -ComputerName localhost -Port $svc.port -WarningAction SilentlyContinue
    $status = if ($conn.TcpTestSucceeded) { "OK" } else { "FAIL" }
    if (-not $conn.TcpTestSucceeded) { $allOk = $false }
    Write-Output "  $($svc.name) ($($svc.port)): $status"
}

if ($allOk) {
    Write-Output "`nAll services started successfully!"
} else {
    Write-Output "`nSome services failed to start."
}
