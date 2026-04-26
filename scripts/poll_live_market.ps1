#!/usr/bin/env node
/**
 * Kalshi Live Market Poller
 * Polls for live sports markets before they expire
 */

const API_KEY_ID = process.env.KALSHI_API_KEY_ID || '71ff522b-2295-44d9-b9c0-f30779c4213d';
const PRIVATE_KEY_PATH = process.env.KALSHI_PRIVATE_KEY_PATH || process.env.KALSHI_PRIVATE_KEY_PATH;
const CLI_PATH = '{kalshi-cli-path}';

const { execSync } = require('child_process');

function run(cmd) {
  const fullCmd = `$env:KALSHI_API_KEY_ID='${API_KEY_ID}'; $env:KALSHI_PRIVATE_KEY_PATH='${PRIVATE_KEY_PATH}'; node "${CLI_PATH}" ${cmd}`;
  try {
    return JSON.parse(execSync(`powershell -Command "${fullCmd}"`, { encoding: 'utf8', maxBuffer: 10*1024*1024 }));
  } catch (e) {
    try {
      return JSON.parse(e.stdout);
    } catch {
      return e.stdout || e.message;
    }
  }
}

const TARGET_TICKER = process.argv[2] || 'KXMLBGAME-26MAR301835TEXBAL';
const BUY_PRICE = parseInt(process.argv[3] || '55');
const SHARES = parseInt(process.argv[4] || '10');

console.log(`\n🔍 POLLING FOR: ${TARGET_TICKER}`);
console.log(`💰 Will buy ${SHARES} shares @ ${BUY_PRICE}¢ when found\n`);

async function poll() {
  let attempts = 0;
  const maxAttempts = 500; // ~25 minutes of polling
  
  while (attempts < maxAttempts) {
    attempts++;
    const result = run(`market ${TARGET_TICKER}`);
    
    if (!result.error) {
      console.log(`\n✅ FOUND! ${TARGET_TICKER}`);
      console.log(`   Price: ${result.yes_bid}/${result.yes_ask}`);
      console.log(`   Volume: ${result.volume_24h}`);
      
      // Try to buy
      const buyResult = run(`buy ${TARGET_TICKER} yes ${SHARES} ${BUY_PRICE}`);
      if (buyResult.order || !buyResult.error) {
        console.log(`\n🎯 ORDER PLACED!`);
        console.log(JSON.stringify(buyResult, null, 2));
        process.exit(0);
      } else {
        console.log(`\n❌ Order failed: ${JSON.stringify(buyResult)}`);
      }
    }
    
    if (attempts % 10 === 0) {
      console.log(`...polling (${attempts} attempts)`);
    }
    
    await new Promise(r => setTimeout(r, 3000)); // 3 second delay
  }
  
  console.log(`\n⏰ Timed out after ${maxAttempts} attempts`);
}

poll().catch(console.error);
