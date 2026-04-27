#!/usr/bin/env pwsh
# MoonPay Wallet Status Check

Write-Host "=== MoonPay Wallet Status ===" -ForegroundColor Cyan

# Check login status
Write-Host "`n[1] Checking login status..." -ForegroundColor Yellow
npx @moonpay/cli user

Write-Host "`n[2] Listing wallets..." -ForegroundColor Yellow
npx @moonpay/cli wallet list

Write-Host "`n[3] Recent transactions..." -ForegroundColor Yellow
npx @moonpay/cli transaction list --limit 10
