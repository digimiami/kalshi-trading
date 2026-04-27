#!/usr/bin/env pwsh
# kalshi-bet-daemon.ps1 — Continuous loop daemon
# Runs the betting script every 30 minutes forever.
# Launch with: powershell -ExecutionPolicy Bypass -File scripts\kalshi-bet-daemon.ps1
# View log at logs\bet-daemon.log

param(
    [int]$IntervalMinutes = 30
)

$Workspace = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BetScript = "$Workspace\skills\kalshi-auto-bet\scripts\kalshi-bet-cron.ps1"
$DaemonLog = "$Workspace\logs\bet-daemon.log"
$PidFile = "$Workspace\logs\bet-daemon.pid"

if (!(Test-Path "$Workspace\logs")) { New-Item -ItemType Directory -Path "$Workspace\logs" -Force | Out-Null }

# Write our PID so we can find/kill the daemon later
$PID | Out-File -FilePath $PidFile -Force

$Interval = [TimeSpan]::FromMinutes($IntervalMinutes)
$RunCount = 0

Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DAEMON STARTED | PID=$PID | Interval=${IntervalMinutes}min" | Tee-Object -FilePath $DaemonLog -Append

while ($true) {
    $RunCount++
    $StartTime = Get-Date
    
    Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RUN #$RunCount starting..." | Tee-Object -FilePath $DaemonLog -Append
    
    try {
        & powershell.exe -ExecutionPolicy Bypass -File $BetScript 2>&1 | Tee-Object -FilePath $DaemonLog -Append
    } catch {
        Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $_" | Tee-Object -FilePath $DaemonLog -Append
    }
    
    $Elapsed = [math]::Round(((Get-Date) - $StartTime).TotalSeconds, 1)
    Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RUN #$RunCount complete (${Elapsed}s). Next in ${IntervalMinutes}min." | Tee-Object -FilePath $DaemonLog -Append
    
    # Sleep for the interval
    Start-Sleep -Seconds ($Interval.TotalSeconds)
}
