# kalshi-live-trading
Autonomous prediction market trading on Kalshi with live research.

## What This Does
- WebSocket live market data
- LIVE ESPN research (NBA scores)
- Auto-scan for value plays (20-80c)
- Places bets automatically
- Telegram alerts

## Files

| File | Purpose |
|------|---------|
| `kalshi-websocket-live.py` | Test WebSocket |
| `kalshi-auto-bet-v2.py` | Auto-bet with LIVE research |
| `kalshi-pnl-report.py` | P&L report |

## Operating Procedure

### DAILY WORKFLOW
1. Check balance: `kalshi-cli --prod portfolio balance`
2. Research: Run `python kalshi-auto-bet-v2.py`
3. Or ask "research for opportunity"

### BETTING RULES
- **WINNING**: NBAGAME, ATPMATCH (simple winners)
- **LOSING**: NHL props, multi-game parlays, crypto, WTA

## Usage

```bash
# Auto research + bet (with live data)
python kalshi-auto-bet-v2.py
```

## Strategy
1. Only bet NBA/ATP simple game winners
2. Avoid player props
3. Add live research before bets
4. Diversify across matches

## Cron Jobs
- Auto research every 1 hour (has execution issues)
- P&L report every 24 hours

## GitHub
https://github.com/AGENT33-BOT/kalshi-live-trading