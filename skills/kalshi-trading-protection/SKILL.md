---
name: kalshi-trading-protection
description: Prevents both-sides betting on Kalshi prediction markets. Automatically blocks trades when you already have a position in the same base market (e.g., can't bet on both LAL and HOU in the same NBA game). Use when running automated Kalshi trading bots to avoid guaranteed losses from betting on opposite outcomes of the same event.
---

# Kalshi Trading Protection

Prevents the #1 killer of trading bots: **betting on both sides of the same market**.

## The Problem

Without protection, bots will happily place bets like:

```
Bet 1: KXNBAGAME-26APR21HOULAL-LAL ($10)
Bet 2: KXNBAGAME-26APR21HOULAL-HOU ($10)
Result: GUARANTEED $10 loss (one must lose)
```

This happens because:
- Multiple bots run simultaneously
- Each bot only checks its own memory
- Bots check `KXNBAGAME-26APR21HOULAL-LAL` but not `KXNBAGAME-26APR21HOULAL`

## The Solution

**Three-layer protection:**

### Layer 1: Real-Time Position Check
```python
from market_tracker import check_existing_position

can_bet, reason = check_existing_position(ticker, positions)
if not can_bet:
    return False, "position_exists"  # Blocked!
```

### Layer 2: Persistent Daily Tracker
```python
from market_tracker import has_traded_base_market, record_base_market_trade

base = get_base_market(ticker)  # "KXNBAGAME-26APR21HOULAL"
if has_traded_base_market(base):
    return False, "already_traded"  # Blocked!

# After successful trade:
record_base_market_trade(base)  # Persisted to disk
```

### Layer 3: Shared State
- Load positions ONCE at bot start
- Pass to all order attempts
- Prevents race conditions between bots

## Quick Start

### 1. Add to Your Bot

```python
from market_tracker import (
    get_base_market,
    check_existing_position,
    record_base_market_trade,
    has_traded_base_market
)

def place_order(ticker, price, client=None, positions=None):
    # Check existing positions
    if positions:
        can_bet, reason = check_existing_position(ticker, positions)
        if not can_bet:
            return False, "position_exists"
    
    # Check daily tracker
    base = get_base_market(ticker)
    if has_traded_base_market(base):
        return False, "already_traded"
    
    # Place order
    result = client.create_order(ticker, "yes", qty, price)
    success = result.get("order", {}).get("status") in ["resting", "executed", "confirmed"]
    
    if success:
        record_base_market_trade(base)
    
    return success, None
```

### 2. Load Positions Once

```python
client = KalshiClient()
positions = client.get_positions()  # Load once, use for all checks

for opportunity in opportunities:
    success, reason = place_order(ticker, price, client, positions)
```

## Functions

### `get_base_market(ticker)`
Extract base market from full ticker.

```python
get_base_market("KXNBAGAME-26APR21HOULAL-LAL")
# Returns: "KXNBAGAME-26APR21HOULAL"
```

### `check_existing_position(ticker, positions_data)`
Check if you already have ANY position in this base market.

```python
can_bet, reason = check_existing_position(
    "KXNBAGAME-26APR21HOULAL-LAL",
    client.get_positions()
)
# Returns: (False, "Already have position: KXNBAGAME-26APR21HOULAL-HOU")
```

### `has_traded_base_market(base_market)`
Check if you've traded this market today (survives restarts).

### `record_base_market_trade(base_market)`
Record that you traded this market (persisted to `daily_limits.json`).

## Storage

Tracked markets stored in:
```
logs/daily_limits.json
```

Resets automatically each day. Survives bot restarts.

## Example: Fixed Bot

See `scripts/kalshi-auto-bet-v2.py` for a complete working example.

## Verification

Check for dual bets in your account:

```bash
python3 scripts/check_dual_bets.py
```

## Files

| File | Purpose |
|------|---------|
| `scripts/market_tracker.py` | Core protection module |
| `scripts/kalshi-auto-bet-v2.py` | Example bot with protection |
| `scripts/check_dual_bets.py` | Verify no conflicts exist |
| `references/ARCHITECTURE.md` | Technical details |
