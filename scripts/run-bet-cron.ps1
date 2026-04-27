#!/usr/bin/env pwsh
# run-bet-cron.ps1 — Wrapper that runs the betting script and sends Telegram alert
$ScriptPath = "C:\Users\pablobots\.openclaw\workspace\.openclaw\workspace-bumba\skills\kalshi-auto-bet\scripts\kalshi-bet-cron.ps1"

$Result = powershell -ExecutionPolicy Bypass -File $ScriptPath 2>&1
$ExitCode = $LASTEXITCODE

# Get last line (summary)
$Summary = $Result | Select-Object -Last 1

# Get the 3 most recent lines for a concise report
$LastLines = $Result | Select-Object -Last 3
$Report = $LastLines -join " | "

Write-Host "=== BET CRON WRAPPER ==="
Write-Host "Exit: $ExitCode"
Write-Host "Result: $Report"
