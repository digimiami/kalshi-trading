# SKILL.md - Kalshi Autonomous Trader

## Purpose
Autonomous prediction market trading on Kalshi. Searches for opportunities, places trades, and manages portfolio without requiring approval.

## Setup
Requires environment variables:
- `KALSHI_API_KEY_ID`
- `KALSHI_PRIVATE_KEY_PATH` (path to private key .txt file)

## Usage
```bash
node kalshi-autonomous.mjs [command] [args]
```

## Commands

### `search <query>`
Search markets by keyword/niche
```bash
node kalshi-autonomous.mjs search "trump"
node kalshi-autonomous.mjs search "recession"
node kalshi-autonomous.mjs search "sports"
```

### `trending`
Get top trending markets by volume
```bash
node kalshi-autonomous.mjs trending
```

### `buy <ticker> <shares> <yes_price>`
Place a buy order at specified yes price
```bash
node kalshi-autonomous.mjs buy KXTRUMPWINS-28 10 55
```

### `balance`
Show account balance and portfolio value

### `portfolio`
Show all positions and pending orders

### `report`
Full P&L report with positions summary

### `autonomous <budget>`
Run full autonomous trading cycle:
1. Search trending markets
2. Identify niche opportunities
3. Place trades within budget
4. Report findings

```bash
node kalshi-autonomous.mjs autonomous 20
```

## Research Categories
When searching for opportunities, explore:
- **Political**: Trump, Congress, 2028 election
- **Economic**: Recession, GDP, Fed, inflation
- **Tech/AI**: IPOs, IPO first, trillionaires
- **Foreign Policy**: Trade wars, tariffs, NATO, Taiwan
- **Geopolitical**: Greenland, Panama, Canada
- **Supreme Court**: Appointments, resignations
- **Cabinet**: Impeachments, departures
- **Entertainment**: Awards, celebrity events
- **Sports**: NFL, NBA, elections
- **Climate**: Warming, energy

## Trading Rules
- Max $10-15 per trade
- Diversify across categories
- Look for volume > 1000
- Prefer prices 10-60¢ range
- Place limit orders slightly below current price
- Track all positions in memory

## Auto-Generated Skill
Created: 2026-03-29
