"""
Daily trade limits tracker for Kalshi bots
- $30 daily loss limit
- $100 daily trade cap (max spend)
"""
import json
import os
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(__file__), "logs", "daily_limits.json")

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

def get_state():
    state = _load()
    today = _today()
    if state.get("date") != today:
        state = {
            "date": today,
            "spent_cents": 0,
            "start_balance_cents": None,
        }
        _save(state)
    return state

def can_trade(spend_cents):
    """Check if trade is within daily $100 cap"""
    state = get_state()
    daily_cap = 10000  # $100 in cents
    if state["spent_cents"] + spend_cents > daily_cap:
        return False
    return True

def record_spend(spend_cents):
    """Record money spent on trades"""
    state = get_state()
    state["spent_cents"] += spend_cents
    _save(state)

def check_loss_limit(start_balance_cents):
    """Check if $30 daily loss limit hit - uses TOTAL EQUITY (cash + portfolio)"""
    from kalshi_api import KalshiClient
    state = get_state()
    today = _today()
    
    if state.get("date") != today:
        state = {
            "date": today,
            "spent_cents": 0,
            "start_balance_cents": start_balance_cents,
        }
    elif state.get("start_balance_cents") is None:
        state["start_balance_cents"] = start_balance_cents
    
    _save(state)
    
    client = KalshiClient()
    bal = client.balance()
    current_equity = bal.get("balance", 0) + bal.get("portfolio_value", 0)
    
    loss = state["start_balance_cents"] - current_equity
    daily_loss_limit = 3000  # $30 in cents
    
    if loss >= daily_loss_limit:
        return False, loss / 100.0
    return True, loss / 100.0

def reset_if_new_day():
    state = _load()
    today = _today()
    if state.get("date") != today:
        from kalshi_api import KalshiClient
        client = KalshiClient()
        bal = client.balance()
        state = {
            "date": today,
            "spent_cents": 0,
            "start_balance_cents": bal.get("balance", 0),
        }
        _save(state)
    return state

def reset_limits():
    """Manually reset daily limits - use with caution"""
    from kalshi_api import KalshiClient
    from datetime import datetime
    
    client = KalshiClient()
    bal = client.balance()
    current_equity = bal.get("balance", 0) + bal.get("portfolio_value", 0)
    
    today = datetime.now().strftime("%Y-%m-%d")
    state = {
        "date": today,
        "spent_cents": 0,
        "start_balance_cents": current_equity
    }
    _save(state)
    return state
