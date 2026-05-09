# KALSHI AUTO RESEARCH + BETTING BOT
# Runs hourly to find opportunities and place bets automatically

import asyncio
import json
import time
import websockets
import requests
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import random

# Config
KEY_ID = "8c9e8ee8-97f0-4fd8-9dca-7f4b4f1d1744"
PRIVATE_KEY_PATH = r"C:\Users\digim\OneDrive\Pictures\auto_opener_monitor\crypto_trader\kalshi-key.pem"
TG_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TG_CHAT = "5804173449"

CLI_PATH = r"C:\Users\digim\go\bin\kalshi-cli.exe"
MAX_BETS = 3  # Max bets per hour
BET_QTY = 10
MIN_PRICE = 30  # Min price for value
MAX_PRICE = 80  # Max price to bet

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

def place_order(ticker, price):
    """Place order via CLI"""
    import subprocess
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
    print("=== AUTO RESEARCH + BET ===")
    print()
    
    private_key = load_key()
    ts = str(int(time.time() * 1000))
    sig = sign(private_key, ts + "GET" + "/trade-api/ws/v2")
    
    ws = await websockets.connect(
        "wss://api.elections.kalshi.com/trade-api/ws/v2",
        extra_headers={"KALSHI-ACCESS-KEY": KEY_ID, "KALSHI-ACCESS-SIGNATURE": sig, "KALSHI-ACCESS-TIMESTAMP": ts}
    )
    await ws.send(json.dumps({"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}))
    
    # Find opportunities
    opportunities = []
    count = 0
    async for msg in ws:
        data = json.loads(msg)
        if data.get("type") == "ticker":
            d = data.get("msg", {})
            ticker = d.get("market_ticker", "")
            ask = float(d.get("yes_ask_dollars", 0))
            bid = float(d.get("yes_bid_dollars", 0))
            
            # Winning categories only: NBA Game, ATP Match (NOT props)
            if ("NBAGAME-" in ticker or "ATPMATCH-" in ticker):
                if ask >= MIN_PRICE/100 and ask <= MAX_PRICE/100:
                    opportunities.append((ticker, ask, bid))
            
            count += 1
            if count > 400:
                break
    
    if not opportunities:
        telegram("AUTO: No opportunities found")
        return
    
    # Pick random opportunities (diversify)
    random.shuffle(opportunities)
    selected = opportunities[:MAX_BETS]
    
    print(f"Found {len(opportunities)} opportunities, betting on {len(selected)}")
    
    # Place bets
    bet_count = 0
    for ticker, ask, bid in selected:
        # Bet on favorite (higher bid)
        price = int(ask * 100)
        
        print(f"Betting: {ticker} at {price}c")
        
        if place_order(ticker, price):
            print(f"  -> PLACED!")
            bet_count += 1
            await asyncio.sleep(1)  # Rate limit
    
    # Report
    msg = f"AUTO BET: Placed {bet_count} bets\n"
    for t, a, b in selected[:bet_count]:
        msg += f"{t[:35]}\n"
    
    telegram(msg)
    print(f"Done! Placed {bet_count} bets")

if __name__ == "__main__":
    asyncio.run(research_and_bet())