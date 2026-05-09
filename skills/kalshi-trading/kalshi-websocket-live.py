# KALSHI WEBSOCKET - LIVE MARKET DATA
import asyncio
import base64
import json
import time
import websockets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID = "8c9e8ee8-97f0-4fd8-9dca-7f4b4f1d1744"
PRIVATE_KEY_PATH = "C:\\Users\\digim\\OneDrive\\Pictures\\auto_opener_monitor\\crypto_trader\\kalshi-key.pem"
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

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

async def main():
    print("Loading key...")
    private_key = load_private_key(PRIVATE_KEY_PATH)
    
    timestamp = str(int(time.time() * 1000))
    msg_string = timestamp + "GET" + "/trade-api/ws/v2"
    signature = sign_message(private_key, msg_string)
    
    headers = {
        "KALSHI-ACCESS-KEY": KEY_ID,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }
    
    print(f"Connecting to {WS_URL}...")
    
    ws = await websockets.connect(WS_URL, extra_headers=headers)
    
    print("Connected! Subscribing...")
    
    sub_msg = {"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker"]}}
    await ws.send(json.dumps(sub_msg))
    
    print("\n=== LIVE PRICES ===")
    
    count = 0
    async for msg in ws:
        data = json.loads(msg)
        t = data.get("type")
        
        if t == "subscribed":
            print("Subscribed to ticker channel")
        
        elif t == "ticker":
            d = data.get("msg", {})
            ticker = d.get("market_ticker", "")
            ask = float(d.get("yes_ask_dollars", 0))
            bid = float(d.get("yes_bid_dollars", 0))
            
            if ask and ask > 0 and ask < 1:
                print(f"{ticker}: Bid ${bid} | Ask ${ask}")
                count += 1
                if count >= 15:
                    break
        
        elif t == "error":
            print(f"Error: {data}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
