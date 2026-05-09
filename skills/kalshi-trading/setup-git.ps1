# kalshi-live-trading GitHub Setup
# Run this in PowerShell after installing gh CLI

# 1. Initialize git (if not already)
git init
git add .
git commit -m "kalshi live trading skill"

# 2. Create repo on GitHub
gh repo create kalshi-live-trading --public --source=. --push

# 3. Done!
# Your repo is now at: https://github.com/YOUR_USERNAME/kalshi-live-trading