# Kalshi Trading Protection - Architecture

## Problem Analysis

### The Both-Sides Betting Bug

**Example Scenario:**
```
Market: KXNBAGAME-26APR21HOULAL (Houston vs Lakers)
Tickers: KXNBAGAME-26APR21HOULAL-HOU
         KXNBAGAME-26APR21HOULAL-LAL

Bot A checks: "Do I own KXNBAGAME-26APR21HOULAL-HOU?" ΓåÆ No
Bot B checks: "Do I own KXNBAGAME-26APR21HOULAL-LAL?" ΓåÆ No

Both place bets:
- Bot A buys HOU for $10
- Bot B buys LAL for $10

Result: One must lose. $10 guaranteed loss.
```

### Root Causes

1. **Ticker-level checking**: Bots checked full ticker, not base market
2. **Race conditions**: Multiple bots checked simultaneously
3. **No shared state**: Each bot had isolated memory
4. **Memory loss**: Restarting bot forgot previous trades

## Solution Design

### Core Concept: Base Market

```python
# Full ticker:  KXNBAGAME-26APR21HOULAL-LAL
# Base market:  KXNBAGAME-26APR21HOULAL
# Team suffix:  LAL

def get_base_market(ticker):
    parts = ticker.rsplit('-', 1)
    return parts[0]  # Everything except last team suffix
```

### Three-Layer Protection

```
ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé  LAYER 1: Real-Time Position Check                      Γöé
Γöé  - Query Kalshi API for current positions               Γöé
Γöé  - Check if ANY position exists in base market          Γöé
Γöé  - Blocks: "Already have position: XXX"                 Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                           Γåô
ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé  LAYER 2: Persistent Daily Tracker                      Γöé
Γöé  - JSON file: logs/daily_limits.json                    Γöé
Γöé  - Records every base market traded today               Γöé
Γöé  - Survives bot restarts                                Γöé
Γöé  - Auto-resets at midnight                              Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                           Γåô
ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé  LAYER 3: Shared Position Snapshot                      Γöé
Γöé  - Load positions ONCE at bot start                     Γöé
Γöé  - Pass same data to all order attempts                 Γöé
Γöé  - Prevents race conditions                             Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
```

## Data Flow

### Normal Operation (No Conflict)

```
1. Bot starts
   Γåô
2. Load positions from Kalshi API
   Γåô
3. Find opportunity: KXNBAGAME-26APR21HOULAL-LAL @ 45c
   Γåô
4. Check Layer 1: No existing position ΓåÆ PASS
   Γåô
5. Check Layer 2: Not in daily tracker ΓåÆ PASS
   Γåô
6. Place order ΓåÆ SUCCESS
   Γåô
7. Record to daily tracker: KXNBAGAME-26APR21HOULAL
   Γåô
8. Continue to next opportunity
```

### Conflict Detected (Both-Sides Attempt)

```
1. Bot starts
   Γåô
2. Load positions from Kalshi API
   (Already have: KXNBAGAME-26APR21HOULAL-HOU)
   Γåô
3. Find opportunity: KXNBAGAME-26APR21HOULAL-LAL @ 45c
   Γåô
4. Check Layer 1: 
   - Extract base: KXNBAGAME-26APR21HOULAL
   - Check positions: FOUND KXNBAGAME-26APR21HOULAL-HOU
   ΓåÆ BLOCK: "Already have position"
   Γåô
5. Skip to next opportunity
```

## Storage Format

### daily_limits.json

```json
{
  "date": "2026-04-19",
  "spent_cents": 5000,
  "start_balance_cents": 25681,
  "traded_base_markets": [
    "KXNBAGAME-26APR21HOULAL",
    "KXATPMATCH-26APR17ZVECER",
    "KXEPLGAME-26APR25WOLTOT"
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Current date (YYYY-MM-DD) |
| `spent_cents` | int | Total spent today (cents) |
| `start_balance_cents` | int | Opening balance (cents) |
| `traded_base_markets` | array | List of base markets traded |

## Function Reference

### get_base_market(ticker)

**Purpose:** Extract base market from full ticker

**Input:** `KXNBAGAME-26APR21HOULAL-LAL`
**Output:** `KXNBAGAME-26APR21HOULAL`

### check_existing_position(ticker, positions_data)

**Purpose:** Check if position exists in base market

**Returns:** `(bool, str)`
- `(True, None)` ΓåÆ Can bet
- `(False, "Already have position: XXX")` ΓåÆ Blocked

### has_traded_base_market(base_market)

**Purpose:** Check daily tracker

**Returns:** `bool`
- `True` ΓåÆ Already traded today
- `False` ΓåÆ Safe to trade

### record_base_market_trade(base_market)

**Purpose:** Record trade to persistent storage

**Side Effects:** Updates `daily_limits.json`

## Race Condition Prevention

### Problem

```
Time    Bot A                    Bot B
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T0      Check positions          Check positions
        (none found)             (none found)
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T1      Place order HOU
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T2                               Place order LAL
                                 (both sides now held!)
```

### Solution: Shared Snapshot

```
Time    Action
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T0      Load positions ONCE at bot start
        Store in variable `positions`
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T1      Bot A checks `positions` variable
        (none found) ΓåÆ Place order HOU
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
T2      Bot B checks `positions` variable
        (none found - from snapshot at T0)
        
        But wait! Layer 2 check:
        has_traded_base_market("KXNBAGAME-26APR21HOULAL")
        ΓåÆ TRUE (Bot A recorded it)
        ΓåÆ BLOCKED!
```

## Testing

### Unit Tests

```python
# Test base market extraction
def test_get_base_market():
    assert get_base_market("A-B-C") == "A-B"
    assert get_base_market("A-B-C-D") == "A-B-C"
    assert get_base_market("A") == "A"

# Test position checking
def test_check_existing_position():
    positions = {
        'market_positions': [
            {'ticker': 'GAME-ABC-HOU', 'market_exposure_dollars': 10}
        ]
    }
    can_bet, _ = check_existing_position('GAME-ABC-LAL', positions)
    assert can_bet == False  # Same base market
```

### Integration Test

```bash
# Run dual-bet checker
python3 scripts/check_dual_bets.py

# Should return:
# - Exit code 0 if no dual bets
# - Exit code 1 if dual bets found
```

## Performance Considerations

### API Calls
- Position check: 1 API call per bot run
- Daily tracker: File I/O only (no API)
- Total overhead: ~100ms per bot run

### Storage
- File size: < 1KB per day
- Location: `logs/daily_limits.json`
- Retention: Auto-reset daily

## Edge Cases

### Same-Day Restart
- Bot crashes, restarts same day
- Daily tracker preserves state
- Won't accidentally re-trade markets

### Midnight Boundary
- Trade at 23:59:59
- Next trade at 00:00:01
- Tracker auto-resets (new date)
- Can trade same market again

### Partial Fills
- Order partially filled
- Base market still recorded
- Won't attempt to fill other side

## Future Enhancements

1. **Redis Backend**: For multi-server deployments
2. **Web Dashboard**: Visualize tracked markets
3. **Alert System**: Notify on blocked attempts
4. **Override Mode**: Emergency bypass (with confirmation)
