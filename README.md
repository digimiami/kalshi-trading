# Kalshi Trading Toolkit ⚡

A self-contained toolkit for trading on [Kalshi](https://kalshi.com) prediction markets — CFTC-regulated binary options on sports, economics, politics, and more.

## What's Inside

```
├── scripts/
│   ├── kalshi-cli.mjs           # Main CLI — market search, portfolio, orders
│   ├── kalshi-autonomous.mjs    # Autonomous trading bot w/ dual-bet protection
│   ├── quick-analysis.mjs       # Fast market + orderbook combo
│   ├── poll_live_market.mjs     # Poll a market until it opens/updates
│   ├── kalshi-bet-cron.ps1      # Cron betting script (30min intervals)
│   ├── kalshi-bet-loop.ps1      # Continuous betting loop
│   └── poll_live_market.ps1     # PowerShell polling helper
├── protection/
│   ├── SKILL.md                 # Dual-bet protection agent docs
│   ├── scripts/
│   │   ├── market_tracker.py    # Position tracking module
│   │   ├── check_dual_bets.py   # Conflict detection
│   │   └── example_bot.py       # Protected bot example
│   └── references/
│       └── ARCHITECTURE.md
├── references/
│   ├── api-notes.md             # Kalshi v2 API field mapping
│   ├── setup-guide.md           # Environment setup
│   └── trading-guide.md         # Strategy reference
└── SKILL.md                     # OpenClaw skill definition
```

## Quick Start

### 1. Prerequisites
- Node.js 18+
- Kalshi account with API credentials
- Environment variables:
  ```
  KALSHI_API_KEY_ID=your_key_id
  KALSHI_PRIVATE_KEY_PATH=path/to/your/private_key.pem
  ```

### 2. Check Your Portfolio
```bash
node scripts/kalshi-cli.mjs portfolio
```

### 3. Search Markets
```bash
node scripts/kalshi-cli.mjs search "NBA"
```

### 4. Place a Bet
```bash
node scripts/kalshi-autonomous.mjs buy KXNBAGAME-26APR25NYKATL-NYK 50 0.55
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `portfolio` | Account balance + positions |
| `orders` | List resting orders |
| `market <ticker>` | Get market details |
| `search <query>` | Search markets |
| `orderbook <ticker>` | Full order book |
| `buy <ticker> <count> <price>` | Place limit order |
| `cancel <order_id>` | Cancel order |
| `trending` | Top markets by volume |

## Features

- ✅ **RSA-PSS authentication** — matches Kalshi v2 API signing requirements
- ✅ **Dual-bet protection** — prevents betting both sides of the same market
- ✅ **Autonomous scanning** — cron-ready bot that finds and places bets
- ✅ **Short-term focus** — filters for events resolving within 7 days
- ✅ **Budget management** — configurable max risk per run

## Related

- [Kalshi API Docs](https://kalshi.com/docs/api)
- [ClawHub Registry](https://clawhub.ai)

---

*Built for the trenches. No fluff.*
