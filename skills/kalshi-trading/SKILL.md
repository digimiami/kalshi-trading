---
name: kalshi-trading
description: Automated prediction market trading on Kalshi with live WebSocket feeds, risk management, and single-side market tracking. Use when deploying, managing, or troubleshooting Kalshi trading bots for sports markets (NBA, tennis, NHL, MLB, etc.), checking balances/positions, or implementing automated trading strategies with daily loss limits and trade caps.
---

# Kalshi Trading Skill

Automated trading system for Kalshi prediction markets with WebSocket integration and risk management.

## Features

- **Live WebSocket trading** - Real-time market scanning and execution
- **Single-side market tracking** - Prevents trading both Yes/No on same market (guaranteed loss protection)
- **Risk management** - Daily loss limits ($30) and trade caps ($100)
- **Telegram alerts** - Real-time trade notifications
- **Sports focus** - NBA, Tennis (ATP), NHL, MLB, Soccer (UCL, EPL, Serie A), NFL, WNBA

## Scripts

### live_bot.py (v2 - Edge-Aware)
Main trading bot. Connects to Kalshi WebSocket, calculates expected value, and executes edge bets on YES or NO.

**Key logic:**
- **Category filter** — Only trades EPL and UCL (historically profitable per P&L analysis)
- **Edge calculation** — Uses `EdgeCalculator` to evaluate both YES and NO sides
- **Kelly sizing** — Position size = min(5, Kelly(bankroll, true_prob, price))
- **Price range** — 15¢-75¢ (tighter than v1's 10¢-90¢)
- **Min EV threshold** — $0.05 per contract minimum
- **Dual-side protection** — Tracks base markets to prevent betting both sides

**Run:**
```bash
cd /root/.openclaw/workspace/skills/kalshi-trading/scripts
python3 live_bot.py
```

### live_bot_v1_backup.py
Original naive bot (YES-only, random 10¢-90¢ range). Kept for reference.

### kalshi_api.py
Kalshi REST API client with RSA key authentication.

**Methods:**
- `balance()` - Get cash + portfolio value
- `create_order(ticker, side, qty, price_cents)` - Place orders
- `get_positions()` - List open positions
- `settlements()` - Get settlement history

### daily_limits.py
Daily tracking for risk management.

**Functions:**
- `can_trade(spend_cents)` - Check if within $100 daily cap
- `record_spend(spend_cents)` - Log trade spend
- `check_loss_limit(start_balance)` - Check $30 daily loss limit
- `reset_limits()` - Manual reset (use with caution)

## Environment Setup

Create `.env` file in scripts directory:

```
KALSHI_KEY_ID=your-key-id
KALSHI_KEY_PATH=/path/to/kalshi-key.pem
TG_TOKEN=your-telegram-bot-token
TG_CHAT=your-chat-id
```

## Key Design Patterns

### Single-Side Market Tracking
The critical fix for preventing guaranteed losses:

```python
def get_base_market(ticker):
    """Extract base market from ticker"""
    parts = ticker.rsplit('-', 1)
    return parts[0] if len(parts) > 1 else ticker

# Track base markets only
traded_markets = set()
base_market = get_base_market(ticker)  # "KXNBAGAME-26APR15ORLPHI"
if base_market not in traded_markets:
    # Execute trade
    traded_markets.add(base_market)  # Blocks PH side after ORL trade
```

### Risk Management Flow
1. Check daily loss limit at connection start
2. Check trade cap before each order
3. Record spend on successful execution
4. Auto-stop when limits hit

## Allowed Markets

Game winners only - no props or parlays:

| Prefix | Sport |
|--------|-------|
| NBAGAME- | NBA |
| ATPMATCH- | ATP Tennis |
| MLB- | Major League Baseball |
| UCLGAME- | Champions League |
| WNBAGAME- | WNBA |
| NFLGAME- | NFL |
| NHLGAME- | NHL |
| SERIEAGAME- | Serie A |
| EPLGAME- | Premier League |

## Trading Parameters

- `CONTRACTS = 5` - Position size per trade
- `DAILY_LOSS_LIMIT = 30` - Stop after $30 loss
- `DAILY_TRADE_CAP = 100` - Max $100 spend per day
- Price range: 10¢ - 90¢ (avoids extremes)

## Common Operations

### Check Balance
```python
from kalshi_api import KalshiClient
client = KalshiClient()
print(client.balance())
```

### Reset Daily Limits
```python
from daily_limits import reset_limits
reset_limits()
```

### Get Positions
```python
from kalshi_api import KalshiClient
client = KalshiClient()
positions = client.get_positions()
```

## Background Operation

Run bot in background:
```bash
nohup python3 live_bot.py > logs/bot.log 2>&1 &
```

Check status:
```bash
tail -f logs/bot.log
tail -f logs/alerts.log
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Daily trade cap hit" | Wait for next day or call `reset_limits()` |
| Connection closed | Bot auto-reconnects after 5s |
| Order failed | Check balance and market status |
| IndentationError | Fix Python indentation in live_bot.py |

## Dependencies

```
websockets
requests
cryptography
```

Install: `pip3 install websockets requests cryptography`
