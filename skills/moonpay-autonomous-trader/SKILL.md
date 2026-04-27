# MoonPay Autonomous Trading Skill

## Overview
Autonomous crypto purchasing and wallet management via MoonPay CLI.

## Prerequisites
- MoonPay CLI: `npx @moonpay/cli`
- **Email verification required** - real email address for login

## Setup Commands

### 1. Login (requires real email)
```bash
npx @moonpay/cli login --email YOUR_REAL_EMAIL
```
You'll receive a verification code. Then:
```bash
npx @moonpay/cli verify --code YOUR_CODE
```

### 2. Check Status
```bash
npx @moonpay/cli wallet list
npx @moonpay/cli user
```

### 3. Buy Crypto
```bash
npx @moonpay/cli buy --currency <symbol> --amount <fiat_amount>
```

## Workflows

### Autonomous Buying
1. Check wallet balance
2. If balance > threshold, identify buy opportunities
3. Execute buy via MoonPay CLI
4. Log transaction to memory

### Passive Income Strategy
- Use MoonPay to fund wallets for Bybit deposits
- Track purchase history for tax purposes
- Monitor wallet addresses for incoming transfers

## Notes
- MoonPay is an on-ramp service (fiat → crypto)
- For actual trading, funds flow to Bybit
- Store credentials securely after login

## Files
- `scripts/buy_crypto.ps1` - Basic buy script
- `scripts/wallet_status.ps1` - Check balances
