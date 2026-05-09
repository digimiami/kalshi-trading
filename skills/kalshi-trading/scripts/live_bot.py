#!/usr/bin/env python3
"""
KALSHI LIVE BOT v2 - Edge-Aware Trading
Upgrades over v1:
- YES or NO trading based on price/value
- Category filtering (only trade historically profitable markets)
- Liquidity awareness
- Kelly-inspired position sizing
- Min EV threshold
"""
import asyncio
import json
import time
import sys
import os
from pathlib import Path

# Add kalshi-live-trading for edge calculator
_LIVE_TRADING = Path(__file__).parent.parent.parent / "kalshi-live-trading"
if str(_LIVE_TRADING) not in sys.path:
    sys.path.insert(0, str(_LIVE_TRADING))

import websockets
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

from kalshi_api import KalshiClient
from daily_limits import get_state, can_trade, record_spend, check_loss_limit
from edge_calculator import EdgeCalculator

# Load .env
_env = Path(__file__).parent / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

KEY_ID = os.getenv("KALSHI_KEY_ID")
PRIVATE_KEY_PATH = os.getenv("KALSHI_KEY_PATH", "~/.kalshi/kalshi-key.pem")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

# Risk params
MIN_EV_PER_CONTRACT = 0.05      # Min $0.05 EV per contract
MIN_EDGE_PCT = 3.0               # Min 3% edge
MAX_BETS_PER_RUN = 3
DAILY_LOSS_LIMIT = 30
DAILY_TRADE_CAP = 100
MIN_CASH_BALANCE = 2

# Category performance from historical P&L analysis
# Positive = profitable historically
CATEGORY_EDGE = {
    "EPLGAME-":   +0.63,   # +$20.76 / 33 trades
    "UCLGAME-":   +0.85,   # +$12.70 / 15 trades
    "NHLGAME-":   -1.29,   # -$68.15 / 53 trades
    "NBAGAME-":   -0.93,   # -$98.42 / 106 trades
    "ATPMATCH-":  -1.12,   # -$143.28 / 128 trades
    "SERIEAGAME-": -1.09,  # -$26.16 / 24 trades
    "MLB-":       -0.55,   # -$15.26 / 28 trades
    "WNBAGAME-":  -0.53,   # small sample
    "NFLGAME-":   -0.96,   # small sample
}

# Only trade categories with positive historical edge
ALLOWED_MARKETS = [k for k, v in CATEGORY_EDGE.items() if v > 0]

# Price ranges by category (tighter for losing cats, but we skip those)
# For winning categories: allow 15¢-75¢
MIN_PRICE = 15
MAX_PRICE = 75

sys.stdout.reconfigure(line_buffering=False)
print("=== KALSHI LIVE BOT v2 (Edge-Aware) ===", flush=True)


def load_key():
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def sign(private_key, text):
    return base64.b64encode(private_key.sign(
        text.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256()
    )).decode('utf-8')


def telegram(msg):
    try:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        from datetime import datetime
        with open(log_dir / "alerts.log", 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        if TG_TOKEN and TG_CHAT:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT, "text": msg[:4000]}, timeout=5
            )
    except:
        pass


def get_category(ticker):
    for prefix in CATEGORY_EDGE.keys():
        if prefix.upper() in ticker.upper():
            return prefix
    return None


def get_base_market(ticker):
    parts = ticker.rsplit('-', 1)
    return parts[0] if len(parts) > 1 else ticker


def estimate_true_probability(ticker, market_price_cents, category):
    """
    Estimate true win probability without external APIs.
    Key insight from P&L data: winning categories (EPL, UCL) are profitable 
    because underdogs are systematically undervalued at low prices.
    """
    market_prob = market_price_cents / 100.0
    
    # Category-specific base rate (implied from historical win rate)
    # EPL wins 42% of trades overall, UCL 33% - these are low win rates
    # but profitable because they buy cheap underdogs
    cat_rates = {
        "EPLGAME-": 0.42,
        "UCLGAME-": 0.33,
    }
    cat_base = cat_rates.get(category, 0.50)
    
    # Price-based adjustment: in profitable categories, underdogs are undervalued
    # and favorites are overvalued
    if market_price_cents <= 35:
        # Underdog at 35¢ or less: true prob is higher than market suggests
        price_adjustment = 0.08  # +8% to true probability
    elif market_price_cents <= 45:
        price_adjustment = 0.05
    elif market_price_cents >= 65:
        # Favorite at 65¢+: true prob is lower than market suggests
        price_adjustment = -0.08
    elif market_price_cents >= 55:
        price_adjustment = -0.05
    else:
        price_adjustment = 0.0
    
    # Blend market price with category base rate
    # Give market 60% weight, category base 40% weight
    blended = (market_prob * 0.6) + (cat_base * 0.4)
    
    true_prob = blended + price_adjustment
    return max(0.05, min(0.95, true_prob))


def evaluate_market(ticker, ask_cents, bankroll, calculator):
    category = get_category(ticker)
    if not category:
        return None
    
    if category not in ALLOWED_MARKETS:
        return None
    
    if ask_cents < MIN_PRICE or ask_cents > MAX_PRICE:
        return None
    
    # Estimate true probability
    true_prob = estimate_true_probability(ticker, ask_cents, category)
    
    # Check YES side edge
    has_edge_yes, ev_yes, edge_pct_yes = calculator.has_edge(ask_cents, true_prob)
    
    # Check NO side edge (price = 100 - ask)
    no_price = 100 - ask_cents
    no_true_prob = 1 - true_prob
    has_edge_no, ev_no, edge_pct_no = calculator.has_edge(no_price, no_true_prob)
    
    # Pick the better side
    if has_edge_yes and ev_yes >= has_edge_no and ev_yes >= MIN_EV_PER_CONTRACT:
        side = "yes"
        price = ask_cents
        ev = ev_yes
        edge_pct = edge_pct_yes
        contracts = min(5, max(1, calculator.kelly_criterion(bankroll, true_prob, ask_cents)))
        return {
            "ticker": ticker, "side": side, "price": price,
            "contracts": contracts, "ev": ev, "edge_pct": edge_pct,
            "true_prob": true_prob, "category": category
        }
    elif has_edge_no and ev_no >= MIN_EV_PER_CONTRACT:
        side = "no"
        price = no_price
        ev = ev_no
        edge_pct = edge_pct_no
        contracts = min(5, max(1, calculator.kelly_criterion(bankroll, no_true_prob, no_price)))
        return {
            "ticker": ticker, "side": side, "price": price,
            "contracts": contracts, "ev": ev, "edge_pct": edge_pct,
            "true_prob": no_true_prob, "category": category
        }
    
    return None


def place_order(client, rec):
    try:
        ticker = rec["ticker"]
        side = rec["side"]
        price_cents = rec["price"]
        contracts = rec["contracts"]
        trade_cost = price_cents * contracts
        
        if not can_trade(trade_cost):
            return False
        
        result = client.create_order(ticker, side, contracts, price_cents)
        success = result.get("order", {}).get("status") in ["resting", "executed", "confirmed"]
        
        if success:
            record_spend(trade_cost)
            action_str = "BUY YES" if side == "yes" else "BUY NO"
            telegram(
                f"🎯 EDGE BET PLACED\n"
                f"{ticker} ({rec['category']})\n"
                f"{action_str} @ {price_cents}¢ × {contracts}\n"
                f"Cost: ${trade_cost/100:.2f} | EV: ${rec['ev']:.2f} | Edge: {rec['edge_pct']:+.1f}%"
            )
        return success
    except Exception as e:
        print(f"Order error: {e}", flush=True)
        return False


async def main():
    private_key = load_key()
    calculator = EdgeCalculator(min_ev=MIN_EV_PER_CONTRACT)
    client = KalshiClient()
    
    bal = client.balance()
    bankroll = (bal.get("balance", 0) + bal.get("portfolio_value", 0)) / 100.0
    cash = bal.get("balance", 0) / 100.0
    
    print(f"Bankroll: ${bankroll:.2f} | Cash: ${cash:.2f}", flush=True)
    telegram(f"🚀 LIVE BOT v2 STARTED\nBankroll: ${bankroll:.2f}\nCategories: {ALLOWED_MARKETS}")
    
    if cash < MIN_CASH_BALANCE:
        telegram("🛑 Cash below minimum. Stopping.")
        return
    
    can_continue, loss = check_loss_limit(bal.get("balance", 0))
    if not can_continue:
        telegram(f"🛑 Daily loss limit hit: ${loss:.2f}")
        return
    
    traded_markets = set()
    trades_count = 0
    daily_blocked = False
    opportunities = []
    
    # Connect WebSocket
    ts = str(int(time.time() * 1000))
    sig = sign(private_key, ts + "GET" + "/trade-api/ws/v2")
    
    ws = await websockets.connect(
        WS_URL,
        additional_headers={
            "KALSHI-ACCESS-KEY": KEY_ID,
            "KALSHI-ACCESS-SIGNATURE": sig,
            "KALSHI-ACCESS-TIMESTAMP": ts
        }
    )
    
    await ws.send(json.dumps({"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}))
    print("Connected! Scanning...", flush=True)
    
    count = 0
    async for msg in ws:
        try:
            data = json.loads(msg)
            if data.get("type") == "ticker":
                d = data.get("msg", {})
                ticker = d.get("market_ticker", "")
                ask = float(d.get("yes_ask_dollars", 0))
                ask_cents = int(ask * 100)
                
                if ask_cents > 0:
                    opportunities.append((ticker, ask_cents))
                
                count += 1
                if count >= 600:
                    break
        except:
            continue
    
    await ws.close()
    
    print(f"Scanned {len(opportunities)} markets", flush=True)
    
    # Evaluate opportunities
    edges = []
    for ticker, ask_cents in opportunities:
        base = get_base_market(ticker)
        if base in traded_markets:
            continue
        
        rec = evaluate_market(ticker, ask_cents, bankroll, calculator)
        if rec:
            rec["base"] = base
            edges.append(rec)
    
    # Sort by EV, deduplicate by base market
    edges.sort(key=lambda x: x["ev"], reverse=True)
    seen_bases = set()
    final_edges = []
    for e in edges:
        if e["base"] not in seen_bases:
            seen_bases.add(e["base"])
            final_edges.append(e)
    
    top = final_edges[:MAX_BETS_PER_RUN]
    
    print(f"Found {len(final_edges)} edges, placing top {len(top)}", flush=True)
    
    for rec in top:
        if trades_count >= MAX_BETS_PER_RUN or daily_blocked:
            break
        
        print(f"Placing: {rec['ticker']} {rec['side'].upper()} @ {rec['price']}¢ EV=${rec['ev']:.2f}", flush=True)
        if place_order(client, rec):
            traded_markets.add(rec["base"])
            trades_count += 1
        else:
            if not can_trade(rec["price"] * rec["contracts"]):
                daily_blocked = True
                telegram("⛔ Daily trade cap reached!")
                break
        await asyncio.sleep(0.5)
    
    summary = f"🏁 BOT v2 DONE | {trades_count} bets placed"
    if daily_blocked:
        summary += " (cap hit)"
    print(summary, flush=True)
    telegram(summary)


if __name__ == "__main__":
    asyncio.run(main())
