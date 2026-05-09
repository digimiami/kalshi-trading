# KALSHI LIVE TRADING BOT - Production v2
import asyncio
import base64
import json
import time
import sys
import websockets
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from kalshi_api import KalshiClient
from daily_limits import get_state, can_trade, record_spend, check_loss_limit

# Config - LINUX PATHS
import os

KEY_ID = os.getenv("KALSHI_KEY_ID")
PRIVATE_KEY_PATH = os.getenv("KALSHI_KEY_PATH", "~/.kalshi/kalshi-key.pem")
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")

# Load .env
from pathlib import Path
_env = Path(__file__).parent / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

CONTRACTS = 5
DAILY_LOSS_LIMIT = 30  # $30
DAILY_TRADE_CAP = 100  # $100

# Markets to trade (game winners only - no props/parlays)
ALLOWED_MARKETS = [
    "NBAGAME-",      # NBA
    "ATPMATCH-",     # ATP Tennis
    "MLB-",          # Major League Baseball
    "UCLGAME-",      # Champions League
    "WNBAGAME-",     # WNBA
    "NFLGAME-",      # NFL (when in season)
    "NHLGAME-",      # NHL game winners (avoid props)
    "SERIEAGAME-",   # Serie A
    "EPLGAME-",      # Premier League
]

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
        from datetime import datetime
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        with open(log_dir / "alerts.log", 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        try:
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                         json={"chat_id": TG_CHAT, "text": msg}, timeout=5)
        except:
            pass
    except:
        pass

def is_allowed_market(ticker):
    for prefix in ALLOWED_MARKETS:
        if prefix.upper() in ticker.upper():
            return True
    return False

def get_balance():
    try:
        client = KalshiClient()
        bal = client.balance()
        return bal.get("balance", 0) / 100.0
    except:
        return None

def place_order(ticker, price_cents, trade_cost_cents):
    try:
        if not can_trade(trade_cost_cents):
            print(f"Daily trade cap hit - skipping {ticker}", flush=True)
            return False
        
        client = KalshiClient()
        result = client.create_order(ticker, "yes", CONTRACTS, price_cents)
        success = result.get("order", {}).get("status") in ["resting", "executed", "confirmed"]
        print(f"Order result: {success} - {result}", flush=True)
        
        if success:
            record_spend(trade_cost_cents)
        
        return success
    except Exception as e:
        print(f"Order error: {e}", flush=True)
        return False

# Track traded BASE markets (without team suffix) to prevent trading both sides
def get_base_market(ticker):
    """Extract base market from ticker (e.g., KXNBAGAME-26APR15ORLPHI from KXNBAGAME-26APR15ORLPHI-PHI)"""
    parts = ticker.rsplit('-', 1)
    return parts[0] if len(parts) > 1 else ticker

async def main():
    private_key = load_private_key(PRIVATE_KEY_PATH)
    
    print("Starting...", flush=True)
    send_telegram(f"🚀 KALSHI LIVE BOT STARTED!\nLimits: ${DAILY_LOSS_LIMIT} loss / ${DAILY_TRADE_CAP} spend cap")
    
    traded_markets = set()  # Track BASE markets, not full tickers
    trades_count = 0
    daily_blocked = False
    
    MAX_TRADES = 100
    while trades_count < MAX_TRADES and not daily_blocked:
        try:
            # Check loss limit at start of each connection
            client = KalshiClient()
            bal = client.balance()
            start_bal = bal.get("balance", 0)
            can_continue, current_loss = check_loss_limit(start_bal)
            
            if not can_continue:
                send_telegram(f"🛑 DAILY LOSS LIMIT HIT! Loss: ${current_loss:.2f} / ${DAILY_LOSS_LIMIT}")
                print(f"Daily loss limit hit: ${current_loss}", flush=True)
                daily_blocked = True
                break
            
            state = get_state()
            remaining_spend = DAILY_TRADE_CAP - (state["spent_cents"] / 100.0)
            
            timestamp = str(int(time.time() * 1000))
            signature = sign_message(private_key, timestamp + "GET" + "/trade-api/ws/v2")
            
            headers = {
                "KALSHI-ACCESS-KEY": KEY_ID,
                "KALSHI-ACCESS-SIGNATURE": signature,
                "KALSHI-ACCESS-TIMESTAMP": timestamp
            }
            
            print("Connecting to WS...", flush=True)
            ws = await websockets.connect(WS_URL, additional_headers=headers)
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
                        trade_cost = ask_cents * CONTRACTS
                        
                        if ask_cents >= 10 and ask_cents <= 90:
                            base_market = get_base_market(ticker)
                            if base_market not in traded_markets:
                                if is_allowed_market(ticker):
                                    print(f"VALUE: {ticker} @ {ask_cents}c", flush=True)
                                    send_telegram(f"OPPORTUNITY: {ticker} @ {ask_cents}c | Spend remaining: ${remaining_spend:.2f}")
                                    
                                    if place_order(ticker, ask_cents, trade_cost):
                                        send_telegram(f"✅ TRADE CONFIRMED: {ticker} @ {ask_cents}c × {CONTRACTS}")
                                        traded_markets.add(base_market)
                                        trades_count += 1
                                        remaining_spend -= trade_cost / 100.0
                                        print(f"TRADE #{trades_count} placed!", flush=True)
                                    else:
                                        if not can_trade(trade_cost):
                                            send_telegram(f"⛔ Daily trade cap reached! Stopping.")
                                            daily_blocked = True
                                            break
                                        else:
                                            send_telegram(f"❌ TRADE FAILED: {ticker} @ {ask_cents}c — order rejected")
                    
                    msg_count += 1
                    if msg_count % 100 == 0:
                        print(f"Processed {msg_count} messages", flush=True)
                
                except Exception as e:
                    print(f"Error: {e}", flush=True)
                
                await asyncio.sleep(0.1)
                
                if daily_blocked:
                    break
        
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, reconnecting...", flush=True)
            await asyncio.sleep(5)
        
        except Exception as e:
            print(f"Main error: {e}", flush=True)
            await asyncio.sleep(10)
    
    msg = f"BOT DONE! {trades_count} trades placed"
    if daily_blocked:
        msg += " (daily limit hit)"
    print(msg, flush=True)
    send_telegram(f"🏁 {msg}")

if __name__ == "__main__":
    asyncio.run(main())
