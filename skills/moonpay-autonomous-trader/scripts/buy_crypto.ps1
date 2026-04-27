#!/usr/bin/env pwsh
# MoonPay Buy Crypto Script
# Usage: .\buy_crypto.ps1 -Currency BTC -Amount 100

param(
    [Parameter(Mandatory=$true)]
    [string]$Currency,
    
    [Parameter(Mandatory=$true)]
    [decimal]$Amount
)

Write-Host "=== MoonPay Buy Order ===" -ForegroundColor Cyan
Write-Host "Currency: $Currency" -ForegroundColor White
Write-Host "Amount: `$$Amount" -ForegroundColor White

# Execute buy
npx @moonpay/cli buy --currency $Currency --amount $Amount
