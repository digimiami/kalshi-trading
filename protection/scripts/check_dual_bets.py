#!/usr/bin/env python3
"""
Check for dual-sided bets in Kalshi account
Run this to verify no both-sides betting exists
"""
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'kalshi-live-trading'))

from kalshi_api import KalshiClient
from collections import defaultdict

def get_base_market(ticker):
    """Extract base market from ticker"""
    parts = ticker.rsplit('-', 1)
    return parts[0] if len(parts) > 1 else ticker

def main():
    client = KalshiClient()
    pos = client.get_positions()
    
    # Group positions by base market
    base_markets = defaultdict(list)
    
    for p in pos.get('market_positions', []):
        exposure = float(p.get('market_exposure_dollars', 0))
        if exposure > 0:
            ticker = p.get('ticker', '')
            base = get_base_market(ticker)
            base_markets[base].append({
                'ticker': ticker,
                'exposure': exposure,
                'cost': float(p.get('total_traded_dollars', 0))
            })
    
    print("="*60)
    print("DUAL-SIDES BETTING DETECTION")
    print("="*60)
    print()
    
    dual_bets = []
    for base, positions in base_markets.items():
        if len(positions) > 1:
            teams = set()
            for p in positions:
                team = p['ticker'].rsplit('-', 1)[1] if '-' in p['ticker'] else 'UNKNOWN'
                teams.add(team)
            
            if len(teams) > 1:  # Different teams = both sides
                total_cost = sum(p['cost'] for p in positions)
                dual_bets.append({
                    'base': base,
                    'positions': positions,
                    'teams': teams,
                    'total_cost': total_cost
                })
    
    if dual_bets:
        print(f"≡ƒÜ¿ FOUND {len(dual_bets)} MARKETS WITH BOTH-SIDES BETS:\n")
        total_waste = 0
        for db in sorted(dual_bets, key=lambda x: x['total_cost'], reverse=True):
            print(f"≡ƒö┤ {db['base']}")
            print(f"   Teams: {', '.join(db['teams'])}")
            for p in db['positions']:
                print(f"     ΓåÆ {p['ticker']}: ${p['exposure']:.2f}")
            print(f"   Total Cost: ${db['total_cost']:.2f}")
            print(f"   ≡ƒÆÇ Guaranteed loss: ~${db['total_cost'] * 0.85:.2f}")
            total_waste += db['total_cost']
            print()
        
        print(f"{'='*60}")
        print(f"≡ƒöÑ TOTAL DUAL BETS: {len(dual_bets)}")
        print(f"≡ƒÆ╕ Total Cost: ${total_waste:.2f}")
        print(f"ΓÜá∩╕Å  Realistic Loss: ~${total_waste * 0.85:.2f}")
        return 1
    else:
        print("Γ£à NO DUAL-SIDES BETS DETECTED")
        print("All positions are single-sided.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
