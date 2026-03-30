# SKILL.md - Kalshi Live Trader

## Overview
Live sports/esports trading on Kalshi using the `kalshi-cli` tool. This enables trading of in-play markets like ATP tennis, MLB, and other live events that aren't accessible via the standard API.

## Setup

### 1. Install kalshi-cli binary
Download from: https://github.com/6missedcalls/kalshi-cli/releases

Or it may already be installed at:
```
C:\Users\pablobots\kalshi-cli\kalshi-cli.exe
```

### 2. Configure Authentication
The tool uses the same API credentials as the standard Kalshi API:
- API Key ID: `71ff522b-2295-44d9-b9c0-f30779c4213d`
- Private Key: `C:\Users\pablobots\.openclaw\media\inbound\Pinguilo-2---1e30c2a4-95ed-4b2b-baf1-bfbeb8a6f90a.txt`

### 3. Use --prod Flag
**IMPORTANT:** Always use `--prod` for production trading:
```
kalshi-cli.exe --prod <command>
```

Without `--prod`, commands run against the demo API (no real trades).

## Usage

### View Live Markets
```powershell
# List all open markets
& "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod markets list --status open --limit 100

# Search for specific sport
& "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod markets list --status open | Select-String -Pattern "ATP|MLB|NBA|CS2"
```

### Place Orders (via Node.js script)
The CLI has a bug where order params don't pass correctly. Use the existing Node.js script instead:

```powershell
# Using the existing kalshi-cli.mjs script
$env:KALSHI_API_KEY_ID='71ff522b-2295-44d9-b9c0-f30779c4213d'
$env:KALSHI_PRIVATE_KEY_PATH='C:\Users\pablobots\.openclaw\media\inbound\Pinguilo-2---1e30c2a4-95ed-4b2b-baf1-bfbeb8a6f90a.txt'
node "C:\Users\pablobots\.openclaw\skills\skills\kalshi-trading\scripts\kalshi-cli.mjs" buy <TICKER> yes <SHARES> <PRICE_CENTS>
```

### Check Orders
```powershell
& "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod orders list
```

### Check Balance
```powershell
& "C:\Users\pablobots\kalshi-cli\kalshi-cli.exe" --prod portfolio balance
```

## Live Sports Markets Found

### ATP Tennis
- Markets: `KXATPMATCH-26MAR30...` (Molcan vs Clarke, etc.)
- Format: Winner of match
- Close time: Same day

### Esports (CS2)
- Markets: `KXCS2GAME-26MAR31...`
- Live game betting

### MLB Baseball
- Markets: `KXMLBGAME-26MAR30...` (Texas vs Baltimore, etc.)
- Game winner markets

## Tips for Live Trading

1. **Act Fast**: Live markets can disappear within minutes
2. **Check Frequently**: Polling script can catch markets as they appear
3. **Use Limit Orders**: Set price slightly above current to ensure fill
4. **Small Size**: Live markets can be volatile - start with 5-10 shares

## Polling Script
See: `skills/kalshi-autonomous-trader/poll_live_market.mjs`

Run before known game times to catch markets:
```bash
node skills/kalshi-autonomous-trader/poll_live_market.mjs <TICKER> <PRICE_CENTS> <SHARES>
```

## Troubleshooting

**"API error [401]"**: Make sure to use `--prod` flag
**"Unknown flag: --shares"**: Use the Node.js script instead for orders
**Market not found (404)**: Live market may have already expired

## Skill Info
- Binary: `bin/kalshi-cli.exe` (Windows AMD64)
- Version: 0.3.0
- Built: 2026-02-12
- Source: github.com/6missedcalls/kalshi-cli

---
*Created: 2026-03-30*
