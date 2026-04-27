"""
Market tracking utilities for Kalshi bots
Prevents betting on both sides of the same market
"""
import os
import json
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "daily_limits.json")

def get_base_market(ticker):
    """Extract base market from ticker
    
    Examples:
        KXNBAGAME-26APR21HOULAL-LAL -> KXNBAGAME-26APR21HOULAL
        KXATPMATCH-26APR17ZVECER-ZVE -> KXATPMATCH-26APR17ZVECER
        KXEPLGAME-26APR25WOLTOT-TOT -> KXEPLGAME-26APR25WOLTOT
    """
    parts = ticker.rsplit('-', 1)
    return parts[0] if len(parts) > 1 else ticker

def _load():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {}

def _save(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def _today():
    return datetime.now().strftime("%Y-%m-%d")

def has_traded_base_market(base_market):
    """Check if we've already traded in this base market today"""
    state = _load()
    today = _today()
    
    # Reset if new day
    if state.get("date") != today:
        return False
    
    traded_markets = state.get("traded_base_markets", [])
    return base_market in traded_markets

def record_base_market_trade(base_market):
    """Record that we traded in this base market"""
    state = _load()
    today = _today()
    
    # Reset if new day
    if state.get("date") != today:
        state = {
            "date": today,
            "spent_cents": 0,
            "start_balance_cents": None,
            "traded_base_markets": []
        }
    
    # Add to traded markets
    if "traded_base_markets" not in state:
        state["traded_base_markets"] = []
    
    if base_market not in state["traded_base_markets"]:
        state["traded_base_markets"].append(base_market)
    
    _save(state)

def check_existing_position(ticker, positions_data):
    """Check if we already have a position in this base market
    
    Args:
        ticker: The ticker we want to bet on
        positions_data: Output from client.get_positions()
    
    Returns:
        (bool, str): (can_bet, reason_if_blocked)
    """
    target_base = get_base_market(ticker)
    
    for pos in positions_data.get('market_positions', []):
        if float(pos.get('market_exposure_dollars', 0)) > 0:
            pos_ticker = pos.get('ticker', '')
            pos_base = get_base_market(pos_ticker)
            
            if pos_base == target_base:
                return False, f"Already have position: {pos_ticker}"
    
    return True, None

def get_traded_markets_report():
    """Get a report of all base markets traded today"""
    state = _load()
    today = _today()
    
    if state.get("date") != today:
        return []
    
    return state.get("traded_base_markets", [])
