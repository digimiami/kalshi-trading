# KALSHI LIVE TRADING BOT - Production v2
import asyncio
import base64
import json
import time
import subprocess
import sys
import websockets
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Config - Load from files or env
import os

KEY_ID = os.environ.get("KALSHI_KEY_ID", "84889d41-b383-4b6a-b8da-f51c0983ae90")
PRIVATE_KEY_PATH = os.environ.get("KALSHI_KEY_PATH", os.path.join(os.path.dirname(__file__), "kalshi-key.pem"))
CLI_PATH = os.environ.get("KALSHI_CLI_PATH", "kalshi")
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

TG_TOKEN = os.environ.get("TG_TOKEN", "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U")
TG_CHAT = os.environ.get("TG_CHAT", "5804173449")

CONTRACTS = 5

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=False)
print("=== KALSHI LIVE TRADING BOT ===", flush=True)

def load_private_key(path):
    with open(path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def sign_message(private_key, text):
    message = text.encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     json={"chat_id": TG_CHAT, "text": msg}, timeout=5)
    except:
        pass

def place_order(ticker, price_cents):
    try:
        result = subprocess.run([
            CLI_PATH,
            "--prod", "orders", "create",
            "--market", ticker,
            "--side", "yes",
            "--qty", str(CONTRACTS),
            "--price", str(price_cents),  # FIXED: was not passing price correctly
            "--yes"
        ], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        
        success = "EXECUTED" in result.stdout
        print(f"Order result: {success}", flush=True)
        return success
    except Exception as e:
        print(f"Order error: {e}", flush=True)
        return False

async def main():
    private_key = load_private_key(PRIVATE_KEY_PATH)
    
    print("Starting...", flush=True)
    send_telegram("KALSHI LIVE BOT STARTED!")
    
    traded = set()
    trades_count = 0
    
    while trades_count < 30:
        try:
            timestamp = str(int(time.time() * 1000))
            signature = sign_message(private_key, timestamp + "GET" + "/trade-api/ws/v2")
            
            headers = {
                "KALSHI-ACCESS-KEY": KEY_ID,
                "KALSHI-ACCESS-SIGNATURE": signature,
                "KALSHI-ACCESS-TIMESTAMP": timestamp
            }
            
            print("Connecting to WS...", flush=True)
            ws = await websockets.connect(WS_URL, extra_headers=headers)
            print("Connected!", flush=True)
            
            sub_msg = {"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}
            await ws.send(json.dumps(sub_msg))
            print("Subscribed!", flush=True)
            
            msg_count = 0
            
            async for msg in ws:
                try:
                    data = json.loads(msg)
                    t = data.get("type")
                    
                    if t == "ticker":
                        d = data.get("msg", {})
                        ticker = d.get("market_ticker", "")
                        ask = float(d.get("yes_ask_dollars", 0))
                        
                        ask_cents = int(ask * 100)
                        
                        if ask_cents >= 10 and ask_cents <= 90 and ticker not in traded:
                            print(f"VALUE: {ticker} @ {ask_cents}c", flush=True)
                            
                            
                            if place_order(ticker, ask_cents):
                                send_telegram(f"TRADE: {ticker} @ {ask_cents}c")
                                traded.add(ticker)
                                trades_count += 1
                                print(f"TRADE #{trades_count} placed!", flush=True)
                    
                    msg_count += 1
                    if msg_count % 100 == 0:
                        print(f"Processed {msg_count} messages", flush=True)
                
                except Exception as e:
                    print(f"Error: {e}", flush=True)
                
                await asyncio.sleep(0.1)
        
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, reconnecting...", flush=True)
            await asyncio.sleep(5)
        
        except Exception as e:
            print(f"Main error: {e}", flush=True)
            await asyncio.sleep(10)
    
    print(f"Done! Placed {trades_count} trades", flush=True)
    send_telegram(f"BOT DONE! {trades_count} trades placed")

if __name__ == "__main__":
    asyncio.run(main())