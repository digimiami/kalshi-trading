import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from pybit.unified_trading import UnifiedTrading

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

session = UnifiedTrading(api_key=api_key, api_secret=api_secret, testnet=False)

# Get balance
try:
    acc = session.get_account_info()
    print("=== BYBIT ACCOUNT ===")
    for coin in acc.get('result', {}).get('list', [{}])[0].get('coin', []):
        if coin.get('coin') in ['USDT', 'XAUT', 'BTC', 'ETH']:
            print(f"{coin.get('coin')}: {coin.get('availableToTrade')} avail / {coin.get('total')} total")
except Exception as e:
    print(f"Account error: {e}")

# Get positions
try:
    positions = session.get_positions(category="linear", symbol="XAUTUSDT")
    print("\n=== XAUTUSDT POSITION ===")
    for pos in positions.get('result', {}).get('list', []):
        print(f"Size: {pos.get('size')}")
        print(f"Entry: {pos.get('avgPrice')}")
        print(f"PnL: {pos.get('unrealisedPnl')}")
        print(f"Side: {pos.get('side')}")
except Exception as e:
    print(f"Position error: {e}")
