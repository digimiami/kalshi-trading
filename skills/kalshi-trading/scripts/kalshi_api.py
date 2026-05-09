"""
Kalshi REST API Client - Python wrapper
Uses RSA key authentication directly
"""
import os
import json
import time
import base64
import requests
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Load .env if present
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key, val)

PROD_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_BASE = "https://demo-api.kalshi.com/trade-api/v2"

class KalshiClient:
    def __init__(self, key_id=None, key_path=None, prod=True):
        self.key_id = key_id or os.getenv("KALSHI_KEY_ID")
        self.key_path = key_path or os.getenv("KALSHI_KEY_PATH", "~/.kalshi/kalshi-key.pem")
        self.base_url = PROD_BASE if prod else DEMO_BASE
        self._load_key()

    def _load_key(self):
        with open(self.key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(f.read(), password=None)

    def _sign(self, text):
        sig = self.private_key.sign(
            text.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )
        return base64.b64encode(sig).decode("utf-8")

    def _headers(self, method, path):
        ts = str(int(time.time() * 1000))
        full_path = "/trade-api/v2" + path
        msg = ts + method + full_path
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": self._sign(msg),
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "Content-Type": "application/json",
        }

    def _get(self, path):
        url = self.base_url + path
        r = requests.get(url, headers=self._headers("GET", path), timeout=15)
        return r.json() if r.text else {}

    def _post(self, path, payload):
        url = self.base_url + path
        r = requests.post(url, headers=self._headers("POST", path), json=payload, timeout=15)
        return r.json() if r.text else {}

    def balance(self):
        """Get portfolio balance"""
        return self._get("/portfolio/balance")

    def settlements(self, limit=20):
        """Get settlements history"""
        return self._get(f"/portfolio/settlements?limit={limit}")

    def create_order(self, ticker, side, qty, price_cents, yes=True):
        """Place an order. price_cents is integer (e.g. 45 for 45c)"""
        payload = {
            "ticker": ticker,
            "action": "buy",
            "side": side,
            "type": "limit",
            "count": qty,
            "yes_price": price_cents if side.lower() == "yes" else None,
            "no_price": price_cents if side.lower() == "no" else None,
            "expiration_secs": 0,
            "buy_max_cost": None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._post("/portfolio/orders", payload)

    def get_market(self, ticker):
        """Get market details"""
        return self._get(f"/markets/{ticker}")

    def get_markets(self, event_ticker=None, status="open"):
        path = f"/markets?status={status}"
        if event_ticker:
            path += f"&event_ticker={event_ticker}"
        return self._get(path)

    def get_exchange_status(self):
        return self._get("/exchange/status")

    def get_positions(self):
        """Get all open positions"""
        return self._get("/portfolio/positions")
