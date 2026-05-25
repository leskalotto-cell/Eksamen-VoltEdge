# VoltEdge Test Data Generator
# Kør med: .\test-load.ps1

param(
    [int]$Iterations = 5,
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = "dev-secret-key"
)

Write-Host "🔋 VoltEdge Test Data Generator" -ForegroundColor Cyan
Write-Host "API URL: $ApiUrl" -ForegroundColor Gray
Write-Host "Iterations: $Iterations" -ForegroundColor Gray
Write-Host ""

$chargers = @("CHG-01", "CHG-02", "CHG-03")
$users = @("USR-42", "USR-99", "USR-88", "USR-77")
$energyValues = @(10.0, 15.0, 20.0, 25.0, 30.0)
$rates = @(2.50, 2.75, 3.00)

for ($i = 1; $i -le $Iterations; $i++) {
    $charger = $chargers | Get-Random
    $user = $users | Get-Random
    $energy = $energyValues | Get-Random
    $rate = $rates | Get-Random
    
    Write-Host "[$i/$Iterations] Opret session..." -ForegroundColor Yellow
    
    try {
        # 1. Opret
        $response = Invoke-WebRequest -Uri "$ApiUrl/sessions/" `
          -Method POST `
          -Headers @{"X-API-Key"=$ApiKey; "Content-Type"="application/json"} `
          -Body "{`"charger_id`":`"$charger`",`"connector_id`":`"CON-1`",`"user_id`":`"$user`"}" `
          -SkipHttpsValidation -ErrorAction Stop
        
        $session = $response.Content | ConvertFrom-Json
        $sessionId = $session.session_id
        Write-Host "  ✓ Session oprettet: $sessionId" -ForegroundColor Green
        
        # 2. Start
        Invoke-WebRequest -Uri "$ApiUrl/sessions/$sessionId/start" `
          -Method POST `
          -Headers @{"X-API-Key"=$ApiKey} `
          -SkipHttpsValidation -ErrorAction Stop | Out-Null
        Write-Host "  ✓ Session startet" -ForegroundColor Green
        
        # 3. Afslut
        Invoke-WebRequest -Uri "$ApiUrl/sessions/$sessionId/end" `
          -Method POST `
          -Headers @{"X-API-Key"=$ApiKey; "Content-Type"="application/json"} `
          -Body "{`"energy_kwh`":$energy,`"tariff_rate`":$rate}" `
          -SkipHttpsValidation -ErrorAction Stop | Out-Null
        Write-Host "  ✓ Session afsluttet - $energy kWh @ $rate DKK/kWh = $($energy * $rate) DKK" -ForegroundColor Green
        
        Start-Sleep -Milliseconds 500
    }
    catch {
        Write-Host "  ✗ Fejl: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📊 Henter statistik..." -ForegroundColor Yellow
try {
    $stats = Invoke-WebRequest -Uri "$ApiUrl/sessions/stats/summary" `
      -SkipHttpsValidation -ErrorAction Stop | Select-Object -ExpandProperty Content | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "📈 Statistik:" -ForegroundColor Cyan
    Write-Host "  Total sessioner: $($stats.total_sessions)" -ForegroundColor White
    Write-Host "  Fuldførte: $($stats.completed_sessions)" -ForegroundColor Green
    Write-Host "  Fejlede: $($stats.faulted_sessions)" -ForegroundColor Red
    Write-Host "  Total energi: $($stats.total_energy_kwh) kWh" -ForegroundColor White
    Write-Host "  Total indtægt: $($stats.total_revenue_dkk) DKK" -ForegroundColor Green
    Write-Host "  Gns. pris: $($stats.avg_session_cost_dkk) DKK" -ForegroundColor White
}
catch {
    Write-Host "✗ Fejl ved hentning af statistik: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Test gennemført!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Se dataene på:" -ForegroundColor Cyan
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host "  Prometheus:  http://localhost:9090" -ForegroundColor Gray
Write-Host "  Grafana:     http://localhost:3001 (admin/admin)" -ForegroundColor Gray
