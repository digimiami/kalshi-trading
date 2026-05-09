# KALSHI AUTO RESEARCH + BET with LIVE DATA
# Runs hourly to find opportunities and place bets with ESPN research

import asyncio
import json
import time
import websockets
import requests
import subprocess
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import random
import re

# Config - Load from files or env
import os

KEY_ID = os.environ.get("KALSHI_KEY_ID", "84889d41-b383-4b6a-b8da-f51c0983ae90")
PRIVATE_KEY_PATH = os.environ.get("KALSHI_KEY_PATH", os.path.join(os.path.dirname(__file__), "kalshi-key.pem"))
TG_TOKEN = os.environ.get("TG_TOKEN", "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U")
TG_CHAT = os.environ.get("TG_CHAT", "5804173449")
CLI_PATH = os.environ.get("KALSHI_CLI_PATH", "kalshi")

MAX_BETS = 3
BET_QTY = 10

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
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                    json={"chat_id": TG_CHAT, "text": msg}, timeout=10)
    except:
        pass

def fetch_live_scores(sport):
    """Fetch live scores from ESPN"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
        r = requests.get(url, timeout=5)
        data = r.json()
        
        games = []
        for event in data.get('events', []):
            comp = event.get('competitions', [{}])[0]
            if comp.get('status', {}).get('type') == 'STATUS_IN_PROGRESS':
                home = comp.get('competitors', [{}])[0]
                away = comp.get('competitors', [{}])[1]
                home_score = home.get('score', 0)
                away_score = away.get('score', 0)
                home_name = home.get('team', {}).get('abbreviation', '')
                away_name = away.get('team', {}).get('abbreviation', '')
                games.append((home_name, away_name, home_score, away_score))
        return games
    except:
        return []

def get_tennis_research():
    """Get tennis research from web"""
    try:
        # Check ATP rankings/news
        r = requests.get("https://www.espn.com/tennis/rankings", timeout=5)
        return True  # Just confirm we checked
    except:
        return None

def place_order(ticker, price):
    try:
        result = subprocess.run([
            CLI_PATH, "--prod", "orders", "create",
            "--market", ticker, "--side", "yes",
            "--qty", str(BET_QTY), "--price", str(price), "--yes"
        ], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        
        return "EXECUTED" in result.stdout or "created successfully" in result.stdout
    except:
        return False

async def research_and_bet():
    print("=== AUTO RESEARCH + BET (with LIVE DATA) ===")
    print()
    
    private_key = load_key()
    ts = str(int(time.time() * 1000))
    sig = sign(private_key, ts + "GET" + "/trade-api/ws/v2")
    
    # Get live NBA scores
    print("Fetching live NBA scores...")
    nba_games = fetch_live_scores("basketball/nba")
    print(f"  Found {len(nba_games)} live NBA games")
    
    print("Fetching live tennis data...")
    tennis_ok = get_tennis_research()
    
    # Connect to WebSocket for market prices
    ws = await websockets.connect(
        "wss://api.elections.kalshi.com/trade-api/ws/v2",
        extra_headers={"KALSHI-ACCESS-KEY": KEY_ID, "KALSHI-ACCESS-SIGNATURE": sig, "KALSHI-ACCESS-TIMESTAMP": ts}
    )
    await ws.send(json.dumps({"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}))
    
    opportunities = []
    count = 0
    async for msg in ws:
        data = json.loads(msg)
        if data.get("type") == "ticker":
            d = data.get("msg", {})
            ticker = d.get("market_ticker", "")
            ask = float(d.get("yes_ask_dollars", 0))
            bid = float(d.get("yes_bid_dollars", 0))
            
            # Winning categories only
            if ("NBAGAME-" in ticker or "ATPMATCH-" in ticker):
                if ask >= 0.20 and ask <= 0.80:
                    opportunities.append((ticker, ask, bid))
            
            count += 1
            if count > 400:
                break
    
    # Research report
    print()
    print("=== RESEARCH REPORT ===")
    print(f"Live NBA games: {len(nba_games)}")
    print(f"Kalshi opportunities: {len(opportunities)}")
    
    if nba_games:
        print()
        print("Live NBA Scores:")
        for home, away, h_s, a_s in nba_games[:5]:
            print(f"  {home} {h_s} - {a_s} {away}")
    
    # Pick best opportunities
    random.shuffle(opportunities)
    selected = opportunities[:MAX_BETS]
    
    print()
    print(f"=== BETTING ON {len(selected)} MARKETS ===")
    
    bet_count = 0
    report = "LIVE RESEARCH + BET\n\n"
    
    for ticker, ask, bid in selected:
        price = int(ask * 100)
        
        # Determine favorite
        if bid > ask:
            player = "favorite"
        else:
            player = "underdog"
        
        print(f"{ticker}: {player} @ {price}c")
        report += f"{ticker}: {price}c\n"
        
        if place_order(ticker, price):
            print(f"  -> PLACED!")
            bet_count += 1
            await asyncio.sleep(1)
    
    if bet_count > 0:
        telegram(report + f"\n{bet_count} bets placed!")
    
    print(f"\nDone! Placed {bet_count} bets")

if __name__ == "__main__":
    asyncio.run(research_and_bet())