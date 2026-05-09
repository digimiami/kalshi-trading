# KALSHI P&L REPORT - 24hr monitoring
import subprocess
import requests
import json
import datetime
import sys
import os

# Fix unicode
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

TG_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TG_CHAT = "5804173449"

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     json={"chat_id": TG_CHAT, "text": msg}, timeout=10)
    except:
        pass

def run_report():
    report = []
    report.append("=== KALSHI P&L REPORT ===")
    report.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    
    # Balance
    try:
        bal = subprocess.run([
            "C:\\Users\\digim\\go\\bin\\kalshi-cli.exe",
            "--prod", "portfolio", "balance"
        ], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        
        for line in bal.stdout.split('\n'):
            if 'Balance' in line or 'Available' in line or 'Portfolio' in line or 'Total' in line:
                report.append(line.strip())
    except:
        report.append("Balance: ERROR")
    
    report.append("")
    
    # Settlements today
    try:
        settlements = subprocess.run([
            "C:\\Users\\digim\\go\\bin\\kalshi-cli.exe",
            "--prod", "portfolio", "settlements",
            "--limit", "10"
        ], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        
        count = 0
        for line in settlements.stdout.split('\n'):
            if '2026-04-02' in line or '2026-04-03' in line:
                report.append(line.strip())
                count += 1
        if count == 0:
            report.append("No settlements today")
    except:
        report.append("Settlements: ERROR")
    
    msg = "\n".join(report)
    print(msg)
    send_telegram(msg)

if __name__ == "__main__":
    run_report()