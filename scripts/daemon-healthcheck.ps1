#!/usr/bin/env pwsh
# daemon-healthcheck.ps1 — Checks if kalshi-bet-daemon is alive
# Sends alert to Telegram if down

$Workspace = "C:\Users\pablobots\.openclaw\workspace\.openclaw\workspace-bumba"
$PidFile = "$Workspace\logs\bet-daemon.pid"
$DaemonLog = "$Workspace\logs\bet-daemon.log"
$CronLog = "$Workspace\logs\bet-cron.log"

$healthy = $true
$errors = @()

# 1. Check PID file
if (Test-Path $PidFile) {
    $pidNum = Get-Content $PidFile
    $proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
    if (-not $proc) {
        $healthy = $false
        $errors += "Daemon process (PID $pidNum) not found"
    }
} else {
    $healthy = $false
    $errors += "No PID file found"
}

# 2. Check last run time
if (Test-Path $CronLog) {
    $lastLine = Get-Content $CronLog -Tail 1
    if ($lastLine -match "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})") {
        $lastRun = [datetime]::ParseExact($Matches[1], "yyyy-MM-dd HH:mm:ss", $null)
        $minutesAgo = [math]::Round(((Get-Date) - $lastRun).TotalMinutes, 0)
        if ($minutesAgo -gt 45) {
            $healthy = $false
            $errors += "Last run was ${minutesAgo}min ago (expected <45)"
        }
    }
} else {
    $healthy = $false
    $errors += "No cron log found"
}

# 3. Check daemon log
if (Test-Path $DaemonLog) {
    $lastDLog = Get-Content $DaemonLog -Tail 3
    $lastDLogLine = $lastDLog | Select-Object -Last 1
    if ($lastDLogLine -match "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})") {
        $lastDTime = [datetime]::ParseExact($Matches[1], "yyyy-MM-dd HH:mm:ss", $null)
        $dMinutesAgo = [math]::Round(((Get-Date) - $lastDTime).TotalMinutes, 0)
        if ($dMinutesAgo -gt 60) {
            $healthy = $false
            $errors += "Daemon log last entry ${dMinutesAgo}min ago"
        }
    }
}

# 4. Check portfolio via quick balance fetch
try {
    $env:KALSHI_API_KEY_ID = "844e62c0-9f24-4c13-b3ea-736ad69b64d5"
    $env:KALSHI_PRIVATE_KEY_PATH = "$Workspace\kalshi-key.pem"
    $CliMjs = "C:\Users\pablobots\.openclaw\skills\skills\kalshi-trading\scripts\kalshi-cli.mjs"
    $bal = node $CliMjs portfolio 2>&1 | ConvertFrom-Json
} catch {
    $healthy = $false
    $errors += "Kalshi API unreachable"
}

if ($healthy) {
    Write-Host "HEALTHY | Daemon OK | Last run ${minutesAgo}min ago"
    exit 0
} else {
    $msg = "DOWN | " + ($errors -join "; ")
    Write-Host $msg
    exit 1
}
