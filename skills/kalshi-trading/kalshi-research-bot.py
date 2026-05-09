# KALSHI RESEARCH BOT - Every 2 hours
import asyncio
import json
import time
import websockets
import requests
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

# Config
KEY_ID = "8c9e8ee8-97f0-4fd8-9dca-7f4b4f1d1744"
PRIVATE_KEY_PATH = r"C:\Users\digim\OneDrive\Pictures\auto_opener_monitor\crypto_trader\kalshi-key.pem"
TG_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TG_CHAT = "5804173449"

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

async def research():
    private_key = load_key()
    ts = str(int(time.time() * 1000))
    sig = sign(private_key, ts + "GET" + "/trade-api/ws/v2")
    
    ws = await websockets.connect(
        "wss://api.elections.kalshi.com/trade-api/ws/v2",
        extra_headers={"KALSHI-ACCESS-KEY": KEY_ID, "KALSHI-ACCESS-SIGNATURE": sig, "KALSHI-ACCESS-TIMESTAMP": ts}
    )
    await ws.send(json.dumps({"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}))
    
    plays = []
    count = 0
    async for msg in ws:
        data = json.loads(msg)
        if data.get("type") == "ticker":
            d = data.get("msg", {})
            t = d.get("market_ticker", "")
            ask = float(d.get("yes_ask_dollars", 0))
            
            # WINNING categories only: NBAGAME, ATPMATCH
            if ("NBAGAME-26APR" in t or "ATPMATCH-26APR" in t) and ask >= 0.15 and ask <= 0.80:
                plays.append((t, ask))
            
            count += 1
            if count > 400:
                break
    
    # Report
    if plays:
        msg = "RESEARCH: Found opportunities\n\n"
        for p in plays[:10]:
            msg += f"{p[0]}: {int(p[1]*100)}c\n"
        
        if len(plays) > 10:
            msg += f"...+{len(plays)-10} more"
        
        telegram(msg)
    else:
        telegram("RESEARCH: No good opportunities right now")

if __name__ == "__main__":
    asyncio.run(research())