@echo off
REM GitHub Push Script for kalshi-live-trading
REM Run this after setting up gh auth

echo === GitHub Push Script ===
echo.

REM Check if logged in
gh auth status
if %errorlevel% neq 0 (
    echo Not logged in! Run: gh auth login
    exit /b 1
)

REM Create repo
echo Creating GitHub repo...
gh repo create kalshi-live-trading --public --source=. --push

echo.
echo Done! Repo created at: https://github.com/YOUR_USERNAME/kalshi-live-trading
pause