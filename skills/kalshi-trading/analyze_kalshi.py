import subprocess

result = subprocess.run([r'C:\Users\digim\go\bin\kalshi-cli.exe', '--prod', 'portfolio', 'settlements', '--limit', '200'], capture_output=True, text=True, timeout=15)
lines = result.stdout.split('\n')

# Track by category
cats = {}
for line in lines:
    if 'YES' in line and '+' in line:
        try:
            ticker = line.split('|')[2].strip()
            amt = float(line.split('+')[1].split()[0].replace('$',''))
            
            if 'NHLGOAL' in ticker: cat = 'NHL Goals'
            elif 'NHLPTS' in ticker: cat = 'NHL Points'  
            elif 'NHLAST' in ticker: cat = 'NHL Shots'
            elif 'NBA' in ticker: cat = 'NBA'
            elif 'ATP' in ticker: cat = 'ATP Tennis'
            elif 'WTA' in ticker: cat = 'WTA Tennis'
            elif 'BTC' in ticker: cat = 'Crypto'
            elif 'MVESPORTS' in ticker: cat = 'Multi-Game'
            elif 'MVECROSS' in ticker: cat = 'Cross Category'
            elif 'CS2' in ticker: cat = 'CS2 Esports'
            elif 'DIMAYOR' in ticker: cat = 'Colombia Soccer'
            elif 'XMLB' in ticker: cat = 'MLB'
            else: cat = 'Other'
            
            if cat not in cats: cats[cat] = {'wins': 0, 'losses': 0, 'profit': 0}
            cats[cat]['wins'] += 1
            cats[cat]['profit'] += amt
        except: pass
        
    elif 'NO' in line and '+' in line and '$0' in line:
        try:
            ticker = line.split('|')[2].strip()
            if 'NHLGOAL' in ticker: cat = 'NHL Goals'
            elif 'NHLPTS' in ticker: cat = 'NHL Points'  
            elif 'NHLAST' in ticker: cat = 'NHL Shots'
            elif 'NBA' in ticker: cat = 'NBA'
            elif 'ATP' in ticker: cat = 'ATP Tennis'
            elif 'WTA' in ticker: cat = 'WTA Tennis'
            elif 'BTC' in ticker: cat = 'Crypto'
            elif 'MVESPORTS' in ticker: cat = 'Multi-Game'
            elif 'MVECROSS' in ticker: cat = 'Cross Category'
            elif 'CS2' in ticker: cat = 'CS2 Esports'
            elif 'DIMAYOR' in ticker: cat = 'Colombia Soccer'
            elif 'XMLB' in ticker: cat = 'MLB'
            else: cat = 'Other'
            
            if cat not in cats: cats[cat] = {'wins': 0, 'losses': 0, 'profit': 0}
            cats[cat]['losses'] += 1
            cats[cat]['profit'] -= 5
        except: pass

print('=== P&L BY CATEGORY ===')
for cat in sorted(cats.keys()):
    c = cats[cat]
    print(f'{cat}: {c["wins"]}W/{c["losses"]}L = ${c["profit"]}')