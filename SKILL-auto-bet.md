---
name: kalshi-auto-bet
description: Autonomous Kalshi prediction market betting with cron-based scanning, short-term opportunity detection, and automated limit order placement. Handles NBA playoffs, EPL, BoJ decisions, commodities (gold, gas), and other events resolving within 7 days. Prevents dual-betting via base market tracking. Use for hands-off passive Kalshi trading.
---

# Kalshi Auto Bet

Autonomous betting on Kalshi short-term prediction markets. Scans, analyzes, and places limit orders on events resolving within 7 days.

## Setup

Requires env vars set before any command:
- `KALSHI_API_KEY_ID` — Kalshi API key ID (UUID)
- `KALSHI_PRIVATE_KEY_PATH` — Path to RSA private key `.txt` file

## Files

| File | Purpose |
|------|---------|
| `scripts/kalshi-bet-cron.ps1` | Autonomous betting script — runs scan + place cycle |
| `scripts/kalshi-bet-loop.ps1` | One-shot scan and bet (no cron dependency) |

## Commands

### Run One-Shot Bet Cycle
```powershell
powershell -ExecutionPolicy Bypass -File scripts/kalshi-bet-loop.ps1
```

Scans current balance, existing positions, resting orders. Places limit orders on short-term opportunities. Logs to `logs/bet-cron.log`.

### Set Up Cron

The cron checks every 30 minutes and auto-announces results:

```bash
openclaw cron add --name kalshi-bet --every 30m --agent kalshi-trading-protection --message "Run betting script: powershell -ExecutionPolicy Bypass -File {workspace}\skills\kalshi-auto-bet\scripts\kalshi-bet-cron.ps1. Report what happened." --timeout-seconds 180 --tools exec --announce --to telegram:{telegram-user-id}
```

### View Cron
```bash
openclaw cron list
openclaw cron show kalshi-bet
```

### Disable Cron
```bash
openclaw cron disable kalshi-bet
```

## Betting Strategy

### Position Filter
- Skip markets where user already has a position in the same base market (prevents dual-betting)
- Skip markets with existing resting orders
- Max 50% of cash balance, capped at $100 per cycle

### Target Markets
Today/tomorrow sports (NBA playoffs, EPL), BoJ decisions, monthly commodity closes (gold, silver, gas). Only events resolving within 7 days.

### Order Limits
- All orders are LIMIT orders (resting on book)
- Prices set below market probability for value
- Scales: 20-50 shares per bet, $5-17.50 per order

## Kalshi CLI Workaround

The `kalshi-cli.exe` has a known bug where `--price` and `--qty` flags display correct preview but create orders at 0¢/0qty. **Always use the Node.js autonomous trader** (`kalshi-autonomous.mjs` buy command) for order creation. The CLI can be used for balance/position queries with `--json` flag.
