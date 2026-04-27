#!/usr/bin/env python3
"""
Example Kalshi bot WITH both-sides protection
This shows the correct way to implement trading protection
"""
import os
import sys

# Add kalshi-live-trading to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'kalshi-live-trading'))

from kalshi_api import KalshiClient
from market_tracker import (
    get_base_market,
    check_existing_position,
    record_base_market_trade,
    has_traded_base_market
)

# Config
BET_QTY = 10
MAX_BETS = 3

def place_order(ticker, price, client=None, positions=None):
    """
    Place order with both-sides protection
    
    Args:
        ticker: Market ticker to bet on
        price: Price in cents (e.g., 45 for 45c)
        client: KalshiClient instance (optional)
        positions: Current positions data (optional)
    
    Returns:
        (success: bool, reason: str|None)
    """
    try:
        # Initialize client if not provided
        if client is None:
            client = KalshiClient()
        
        # CHECK 1: Don't bet if we already have position in this base market
        if positions:
            can_bet, block_reason = check_existing_position(ticker, positions)
            if not can_bet:
                print(f"  -> BLOCKED: {block_reason}")
                return False, "position_exists"
        
        # CHECK 2: Check persistent daily tracker
        base = get_base_market(ticker)
        if has_traded_base_market(base):
            print(f"  -> BLOCKED: Already traded {base} today")
            return False, "already_traded"
        
        # Place the order
        result = client.create_order(ticker, "yes", BET_QTY, price)
        success = result.get("order", {}).get("status") in ["resting", "executed", "confirmed"]
        
        if success:
            # Record trade for future protection
            record_base_market_trade(base)
            print(f"  -> PLACED! Tracked: {base}")
        
        return success, None
        
    except Exception as e:
        print(f"Order error: {e}")
        return False, f"error: {e}"

def run_bot():
    """Example bot execution"""
    print("=== KALSHI BOT WITH PROTECTION ===\n")
    
    # STEP 1: Initialize client and load positions ONCE
    client = KalshiClient()
    positions = client.get_positions()
    print(f"≡ƒôè Loaded {len(positions.get('market_positions', []))} current positions")
    
    # STEP 2: Find opportunities (example)
    # In real bot, this would scan markets via WebSocket/API
    opportunities = [
        # (ticker, price_cents)
        ("KXNBAGAME-26APR21HOULAL-LAL", 45),
        ("KXATPMATCH-26APR17ZVECER-ZVE", 52),
    ]
    
    print(f"\nFound {len(opportunities)} opportunities\n")
    
    # STEP 3: Place bets with protection
    bet_count = 0
    for ticker, price in opportunities[:MAX_BETS]:
        print(f"Evaluating: {ticker} @ {price}c")
        
        success, reason = place_order(ticker, price, client, positions)
        
        if success:
            bet_count += 1
        else:
            print(f"  -> Skipped: {reason}")
    
    print(f"\nΓ£à Done! Placed {bet_count}/{len(opportunities)} bets")

if __name__ == "__main__":
    run_bot()
