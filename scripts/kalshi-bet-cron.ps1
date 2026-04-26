#!/usr/bin/env pwsh
# kalshi-bet-cron.ps1 — Autonomous Kalshi betting script (FIXED)
# Uses kalshi-cli.mjs (working) NOT kalshi-cli.exe (broken/hangs)
# Scans for short-term opportunities, places limit orders at current prices
# Runs via cron every 30 minutes (timeout: 120s)

$ErrorActionPreference = "Continue"
$Workspace = "{workspace}"
# Set KALSHI_API_KEY_ID in your environment (required)
$env:KALSHI_PRIVATE_KEY_PATH = "$Workspace\kalshi-key.pem"
$CliMjs = "{kalshi-trading-skill}\scripts\kalshi-cli.mjs"
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

# === 1. Check balance (uses working kalshi-cli.mjs) ===
try {
    $BalanceJson = node $CliMjs portfolio 2>&1 | ConvertFrom-Json
    $Cash = [decimal]$BalanceJson.balance_cents / 100
    $Portfolio = [decimal]$BalanceJson.portfolio_value_cents / 100
    $Total = $Cash + $Portfolio
    Write-Log "Balance: Cash=$( [math]::Round($Cash,2) ) Portfolio=$( [math]::Round($Portfolio,2) ) Total=$( [math]::Round($Total,2) )"
    
    $MaxBudget = [Math]::Min([Math]::Floor($Cash * 0.5), 100)
    Write-Log "Max budget this run: `$$MaxBudget"
} catch {
    Write-Log "ERROR getting balance: $_"
    exit 1
}

# === 2. Check existing resting orders ===
try {
    $OrdersData = node $CliMjs orders 2>&1 | ConvertFrom-Json
} catch { $OrdersData = $null }

$RestingOrders = @()
if ($OrdersData.orders) {
    $RestingOrders = $OrdersData.orders | Where-Object { $_.status -eq "resting" }
}
$PlacedTickers = @{}
foreach ($o in $RestingOrders) { $PlacedTickers[$o.ticker] = $true }
Write-Log "Existing resting orders: $($RestingOrders.Count)"

# === 3. Check existing positions (dual-bet protection) ===
try {
    $PosData = node $CliMjs portfolio 2>&1 | ConvertFrom-Json
} catch { $PosData = $null }

$PositionTickers = @{}
if ($PosData.positions) {
    foreach ($p in $PosData.positions) {
        $shares = [decimal]($p.position_fp)
        if ($shares -gt 0) {
            $base = $p.ticker -replace '-[^-]+$',''
            $PositionTickers[$base] = $shares
        }
    }
}
Write-Log "Active positions (bases): $($PositionTickers.Count)"

# === 4. Get current market prices for today/tomorrow NBA ===
function Get-MarketPrice {
    param([string]$Ticker)
    try {
        $data = node $CliMjs market $Ticker 2>&1 | ConvertFrom-Json
        return @{
            YesBid = [decimal]($data.yes_bid_dollars -replace '^"|"$','')
            YesAsk = [decimal]($data.yes_ask_dollars -replace '^"|"$','')
            OI = [decimal]($data.open_interest_fp -replace '^"|"$','')
            Status = $data.status
            Title = $data.title
        }
    } catch { return $null }
}

function Test-CanBet {
    param([string]$Ticker)
    $base = $Ticker -replace '-[^-]+$',''
    if ($PlacedTickers.ContainsKey($Ticker)) { return $false, "Already has resting order" }
    if ($PositionTickers.ContainsKey($base)) { return $false, "Position exists in $base" }
    return $true, ""
}

# === 5. Scan live markets ===
$Targets = @(
    # Tonight (Apr 25)
    @{Ticker="KXNBAGAME-26APR25NYKATL-NYK"; Desc="NYK @ ATL (Game 4, 9PM)"}
    @{Ticker="KXNBAGAME-26APR25OKCPHX-PHX"; Desc="PHX @ OKC (Game 3, 6:30PM)"}
    @{Ticker="KXNBAGAME-26APR25DENDMIN-MIN"; Desc="MIN @ DEN (Game 4, 11:30PM)"}
    # Tomorrow (Apr 26)
    @{Ticker="KXNBAGAME-26APR26BOSPHI-PHI"; Desc="PHI @ BOS (Game 5, Apr 26)"}
    @{Ticker="KXNBAGAME-26APR26SASPOR-POR"; Desc="POR @ SAS (Game 5, Apr 26)"}
    @{Ticker="KXNBAGAME-26APR26LALHOU-LAL"; Desc="LAL @ HOU (Game 5, Apr 26)"}
    @{Ticker="KXNBAGAME-26APR26CLETOR-TOR"; Desc="TOR @ CLE (Game 5, Apr 26)"}
    # BoJ (Apr 27)
    @{Ticker="KXCBDECISIONJAPAN-26APR27-C25"; Desc="BoJ Cut 25bps Apr 27"}
    @{Ticker="KXCBDECISIONJAPAN-26APR27-H25"; Desc="BoJ Hike 25bps Apr 27"}
    @{Ticker="KXCBDECISIONJAPAN-26APR27-HOLD"; Desc="BoJ Hold Apr 27"}
    # Gas/Gold (Apr 30)
    @{Ticker="KXAAAGASM-26APR30-4.05"; Desc="Gas >$4.05 Apr 30"}
    @{Ticker="KXAAAGASM-26APR30-4.60"; Desc="Gas >$4.60 Apr 30"}
)

$TotalBet = 0
$Placed = 0

foreach ($Target in $Targets) {
    if ($TotalBet -ge $MaxBudget) {
        Write-Log "Budget reached, stopping"
        break
    }
    
    $Ticker = $Target.Ticker
    $Desc = $Target.Desc
    
    # Check protection layer
    $canBet, $reason = Test-CanBet $Ticker
    if (-not $canBet) {
        Write-Log "SKIP $Desc ($Ticker): $reason"
        continue
    }
    
    # Get current price
    $price = Get-MarketPrice $Ticker
    if (-not $price) {
        Write-Log "SKIP $Desc ($Ticker): failed to get price"
        continue
    }
    
    if ($price.Status -ne "active") {
        Write-Log "SKIP $Desc ($Ticker): status=$($price.Status)"
        continue
    }
    
    $ask = $price.YesAsk
    $bid = $price.YesBid
    
    # Only trade if spread is reasonable (ask ≤ 80¢) with some liquidity
    if ($ask -eq 0 -or $ask -gt 0.80) {
        Write-Log "SKIP $Desc ($Ticker): ask=$( $ask ) out of range"
        continue
    }
    
    if ($price.OI -lt 10000) {
        Write-Log "SKIP $Desc ($Ticker): low liquidity (OI=$( $price.OI ))"
        continue
    }
    
    # Strategy: bid 1¢ below ask for value, or match bid if spread is tight
    $spread = $ask - $bid
    if ($spread -le 0.02) {
        # Tight spread — match the bid
        $bidPrice = [Math]::Round($bid * 100)
    } else {
        # Wider spread — bid at ask - 1¢
        $bidPrice = [Math]::Max([Math]::Round(($ask - 0.01) * 100), 1)
    }
    
    # Cap at 75¢ max buy price
    if ($bidPrice -gt 75) {
        Write-Log "SKIP $Desc ($Ticker): bid price $( $bidPrice )¢ too high"
        continue
    }
    
    # Position sizing: target $5-10 per bet
    $TargetShares = [Math]::Floor(7 / ($bidPrice / 100))
    $TargetShares = [Math]::Max([Math]::Min($TargetShares, 100), 5)
    $Cost = [Math]::Round(($bidPrice / 100) * $TargetShares, 2)
    
    if (($TotalBet + $Cost) -gt $MaxBudget) {
        $TargetShares = [Math]::Floor(($MaxBudget - $TotalBet) / ($bidPrice / 100))
        $TargetShares = [Math]::Max($TargetShares, 1)
        $Cost = [Math]::Round(($bidPrice / 100) * $TargetShares, 2)
        if ($TargetShares -le 0 -or $Cost -le 0.5) {
            Write-Log "SKIP $Desc ($Ticker): insufficient remaining budget"
            continue
        }
    }
    
    Write-Log "PLACING: $Desc - $TargetShares × $( $bidPrice )¢ (cost=`$$Cost, bid=$( $bid ) ask=$( $ask ))"
    
    try {
        $Result = & $Node "{workspace}\skills\kalshi-autonomous-trader\kalshi-autonomous.mjs" buy $Ticker $TargetShares $bidPrice 2>&1
        if ($Result -match '"status": "resting"' -or $Result -match '"status": "executed"') {
            Write-Log "✅ ORDER PLACED: $Ticker × $TargetShares @ $( $bidPrice )¢"
            $Placed++
            $TotalBet += $Cost
        } elseif ($Result -match '"status": "canceled"' -or $Result -match '"status": "rejected"') {
            Write-Log "ORDER REJECTED: $Ticker - $Result"
        } else {
            Write-Log "⚠️ ORDER RESPONSE: $Result"
        }
    } catch {
        Write-Log "ERROR on $Ticker : $_"
    }
}

Write-Log "=== BET CRON END: $Placed orders placed, total cost: `$$([Math]::Round($TotalBet,2)) ==="
