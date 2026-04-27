#!/usr/bin/env pwsh
# kalshi-bet-cron.ps1 — Autonomous Kalshi betting script
# Scans for short-term opportunities, places limit orders
# Runs via cron every 30 minutes

$ErrorActionPreference = "Continue"
$Workspace = "C:\Users\pablobots\.openclaw\workspace\.openclaw\workspace-bumba"
$env:KALSHI_API_KEY_ID = "844e62c0-9f24-4c13-b3ea-736ad69b64d5"
$env:KALSHI_PRIVATE_KEY_PATH = "$Workspace\kalshi-key.pem"
$Trader = "$Workspace\skills\kalshi-autonomous-trader\kalshi-autonomous.mjs"
$Node = "node"

# === Log function ===
$LogFile = "$Workspace\logs\bet-cron.log"
if (!(Test-Path "$Workspace\logs")) { New-Item -ItemType Directory -Path "$Workspace\logs" -Force | Out-Null }

function Write-Log {
    param([string]$Msg)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp | $Msg" | Out-File -FilePath $LogFile -Append
    Write-Host "$Timestamp | $Msg"
}

Write-Log "=== BET CRON START ==="

# === 1. Check balance ===
try {
    $BalanceOutput = & "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod portfolio balance --json 2>&1 | ConvertFrom-Json
    $Cash = [decimal]$BalanceOutput.balance
    $Portfolio = [decimal]$BalanceOutput.portfolio_value
    $Total = $Cash + $Portfolio
    Write-Log "Balance: Cash=$Cash Portfolio=$Portfolio Total=$Total"

    # Max budget is 50% of cash (conservative)
    $MaxBudget = [Math]::Min([Math]::Floor($Cash * 0.5), 100)
    Write-Log "Max budget this run: `$$MaxBudget"
} catch {
    Write-Log "ERROR getting balance: $_"
    exit 1
}

# === 2. Check existing resting orders ===
$RestingOrders = try {
    & "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod orders list --status resting --json 2>&1 | ConvertFrom-Json
} catch { $null }

$OrderCount = if ($RestingOrders.orders) { $RestingOrders.orders.Count } else { 0 }
Write-Log "Existing resting orders: $OrderCount"

# Build list of already-placed tickers
$PlacedTickers = @{}
if ($RestingOrders.orders) {
    foreach ($o in $RestingOrders.orders) { $PlacedTickers[$o.ticker] = $true }
}

# === 3. Check existing positions to avoid dual-betting ===
$Positions = try {
    & "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod portfolio positions --json 2>&1 | ConvertFrom-Json
} catch { $null }

$PositionTickers = @{}
# The positions JSON uses 'market_positions' key, with ticker + position_fp fields
# Only flag positions with actual active shares (position_fp > 0)
if ($Positions.market_positions) {
    foreach ($p in $Positions.market_positions) {
        $shares = [decimal]($p.position_fp)
        if ($shares -gt 0) {
            $PositionTickers[$p.ticker] = $true
            Write-Log "POSITION: $($p.ticker) = $shares shares"
        }
    }
}

# === 4. Define today's and tomorrow's target markets ===
# Today (Apr 25) — Game 3/4
# === TARGET MARKETS ===
# Protection rule: script checks ALL positions before placing each bet
# If user already holds a position with the same base market, the bet is skipped
# List only events resolving within 7 days
$Targets = @(
    # NBA today (Apr 25)
    @{Ticker="KXNBAGAME-26APR25NYKATL-NYK"; Price=35; Shares=50; Desc="NYK to beat ATL Game 4"},
    @{Ticker="KXNBAGAME-26APR25DETORL-ORL"; Price=25; Shares=30; Desc="ORL to beat DET Game 3"},
    # Tomorrow (Apr 26) — Game 4
    @{Ticker="KXNBAGAME-26APR26SASPOR-POR"; Price=40; Shares=25; Desc="POR to beat SAS Game 4"},
    @{Ticker="KXNBAGAME-26APR26BOSPHI-BOS"; Price=30; Shares=30; Desc="BOS to beat PHI Game 4"},
    # EPL
    @{Ticker="KXEPLGAME-26MAY03ARSMCI-ARS"; Price=40; Shares=30; Desc="ARS to beat MCI (EPL May 3)"},
    @{Ticker="KXEPLGAME-26MAY03ARSMCI-MCI"; Price=40; Shares=30; Desc="MCI to beat ARS (EPL May 3)"},
    # Short-term events
    @{Ticker="KXCBDECISIONJAPAN-26APR27-H25"; Price=15; Shares=30; Desc="BoJ hike 25bps Apr 27"},
    @{Ticker="KXCBDECISIONJAPAN-26APR27-C25"; Price=15; Shares=30; Desc="BoJ cut 25bps Apr 27"},
    @{Ticker="KXAAAGASM-26APR30-4.05"; Price=25; Shares=20; Desc="Gas >$4.05 Apr 30"},
    @{Ticker="KXGOLDMON-26APR3017-T5306.99"; Price=25; Shares=20; Desc="Gold >$5306 Apr 30"}
)

$TotalBet = 0
$Placed = 0
foreach ($Target in $Targets) {
    if ($TotalBet -ge $MaxBudget) {
        Write-Log "Budget reached (`$$MaxBudget), stopping"
        break
    }
    
    $Ticker = $Target.Ticker
    $Price = $Target.Price
    $Shares = $Target.Shares
    $Cost = [Math]::Round(($Price / 100) * $Shares, 2)
    
    # Skip if we already have an order for this ticker
    if ($PlacedTickers.ContainsKey($Ticker)) {
        Write-Log "SKIP $($Target.Desc): already has resting order"
        continue
    }
    
    # Skip if position exists in base market (protection layer)
    $BaseMarket = $Ticker -replace '-[^-]+$',''
    $HasPosition = $false
    foreach ($pTicker in $PositionTickers.Keys) {
        $pBase = $pTicker -replace '-[^-]+$',''
        if ($pBase -eq $BaseMarket) {
            $HasPosition = $true
            break
        }
    }
    if ($HasPosition) {
        Write-Log "SKIP $($Target.Desc): position exists in base market $BaseMarket"
        continue
    }
    
    # Skip if cost exceeds remaining budget
    if (($TotalBet + $Cost) -gt $MaxBudget) {
        Write-Log "SKIP $($Target.Desc): cost `$$Cost would exceed remaining budget $($MaxBudget - $TotalBet)"
        continue
    }
    
    # Place the order
    Write-Log "PLACING: $($Target.Desc) - $Shares shares at ${Price} cents (cost: `$$Cost)"
    try {
        $Result = & $Node $Trader buy $Ticker $Shares $Price 2>&1
        if ($Result -match '"status": "resting"' -or $Result -match '"status": "executed"') {
            Write-Log "✅ ORDER PLACED: $Ticker"
            $Placed++
            $TotalBet += $Cost
        } elseif ($Result -match '"status": "canceled"') {
            Write-Log "❌ ORDER CANCELLED/REJECTED: $Ticker"
        } else {
            Write-Log "⚠️ ORDER RESPONSE: $Result"
        }
    } catch {
        Write-Log "ERROR on $Ticker : $_"
    }
}

Write-Log "=== BET CRON END: $Placed orders placed, total cost: `$$TotalBet ==="
