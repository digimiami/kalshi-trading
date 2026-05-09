#!/usr/bin/env bash
# Kalshi bot auto-runner — only trades when cash is available
set -euo pipefail

WORKSPACE="/root/.openclaw/workspace/skills/kalshi-trading/scripts"
LOG="$WORKSPACE/logs/auto_run.log"
MIN_CASH=2.00

mkdir -p "$WORKSPACE/logs"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking balance..." >> "$LOG"

# Check cash via Python
CASH=$(python3 -c "
import sys
sys.path.insert(0, '$WORKSPACE')
from kalshi_api import KalshiClient
c = KalshiClient()
b = c.balance()
print(b.get('balance',0)/100)
")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cash: \$${CASH}" >> "$LOG"

if (( $(echo "$CASH >= $MIN_CASH" | bc -l) )); then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cash OK — running bot..." >> "$LOG"
    cd "$WORKSPACE"
    python3 live_bot.py >> "$LOG" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot finished" >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cash too low (\$${CASH} < \$${MIN_CASH}), skipping" >> "$LOG"
fi

echo "---" >> "$LOG"
