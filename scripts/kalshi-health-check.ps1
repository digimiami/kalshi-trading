#!/usr/bin/env pwsh
# kalshi-health-check.ps1 — Fast cron health checker
# Reads jobs-state.json, reports if kalshi-bet has errors
# Designed to complete in <1 second

$statePath = "C:\Users\pablobots\.openclaw\cron\jobs-state.json"
$timeoutMs = 5400000  # 90 minutes

try {
    $state = Get-Content $statePath -Raw | ConvertFrom-Json
    $betState = $state.jobs.'565e0bc5-3779-44d3-85c6-2b2d9317ec9e'.state
    
    $errors = [int]$betState.consecutiveErrors
    $lastRun = [long]$betState.lastRunAtMs
    $lastStatus = $betState.lastStatus
    $nowMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $sinceLastRun = $nowMs - $lastRun
    
    $issues = @()
    
    if ($errors -gt 0) {
        $issues += "consecutiveErrors=$errors"
    }
    if ($lastStatus -eq "error") {
        $issues += "lastStatus=error ($($betState.lastError))"
    }
    if ($sinceLastRun -gt $timeoutMs) {
        $issues += "no run in $([Math]::Round($sinceLastRun/60000))min"
    }
    
    if ($issues.Count -gt 0) {
        Write-Host "⚠️ KALSHI-BET ALERT: $($issues -join ' | ')"
        exit 0
    } else {
        # Healthy — silent exit, nothing announced
        Write-Host "OK"
        exit 0
    }
} catch {
    Write-Host "❌ Health check script error: $_"
    exit 0
}
