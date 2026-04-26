#!/usr/bin/env node
/**
 * Kalshi Autonomous Trader
 * 
 * Researches and trades prediction markets autonomously.
 * Run without arguments for full autonomous mode.
 */

const API_KEY_ID = process.env.KALSHI_API_KEY_ID || '71ff522b-2295-44d9-b9c0-f30779c4213d';
const PRIVATE_KEY_PATH = process.env.KALSHI_PRIVATE_KEY_PATH || process.env.KALSHI_PRIVATE_KEY_PATH;

const CLI_PATH = '{kalshi-cli-path}';

import { execSync } from 'child_process';

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

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'autonomous';
  
  console.log(`\n🤖 KALSHI AUTONOMOUS TRADER`);
  console.log(`============================\n`);
  
  switch(command) {
    case 'trending': {
      console.log('📊 TOP TRENDING MARKETS:\n');
      const result = run('trending');
      if (Array.isArray(result)) {
        result.slice(0, 15).forEach(m => {
          console.log(`${m.ticker}`);
          console.log(`  ${m.title.substring(0, 70)}...`);
          console.log(`  Price: ${(parseFloat(m.yes_bid)*100).toFixed(0)}¢ | Vol: ${parseInt(m.volume_24h).toLocaleString()}\n`);
        });
      }
      break;
    }
    
    case 'search': {
      const query = args.slice(1).join(' ');
      console.log(`🔍 SEARCHING: "${query}"\n`);
      const result = run(`search "${query}"`);
      if (Array.isArray(result)) {
        if (result.length === 0) {
          console.log('No markets found.\n');
        } else {
          result.slice(0, 10).forEach(m => {
            console.log(`${m.ticker}`);
            console.log(`  ${m.title.substring(0, 70)}`);
            console.log(`  Price: ${(parseFloat(m.yes_bid)*100).toFixed(0)}¢ | Vol: ${parseInt(m.volume_24h || 0).toLocaleString()}\n`);
          });
        }
      }
      break;
    }
    
    case 'buy': {
      const [ticker, shares, price] = args.slice(1);
      if (!ticker || !shares || !price) {
        console.log('Usage: buy <ticker> <shares> <yes_price>');
        process.exit(1);
      }
      console.log(`🛒 BUYING: ${shares} shares of ${ticker} @ ${price}¢`);
      const result = run(`buy ${ticker} yes ${shares} ${price}`);
      console.log(JSON.stringify(result, null, 2));
      break;
    }
    
    case 'balance': {
      const result = run('balance');
      console.log(`💰 BALANCE: $${result.balance_dollars}`);
      console.log(`📊 PORTFOLIO: $${result.portfolio_value_dollars}`);
      break;
    }
    
    case 'portfolio': {
      const result = run('portfolio');
      console.log(`💰 BALANCE: $${result.balance_dollars}`);
      console.log(`📊 PORTFOLIO VALUE: $${result.portfolio_value_dollars}\n`);
      console.log(`📋 POSITIONS (${result.positions.length}):\n`);
      result.positions.forEach(p => {
        const val = parseFloat(p.market_exposure_dollars).toFixed(2);
        const shares = p.position_fp;
        if (parseFloat(val) > 0 || p.resting_orders_count > 0) {
          console.log(`  ${p.ticker}: ${shares} shares = $${val}`);
        }
      });
      break;
    }
    
    case 'autonomous': {
      const budget = parseFloat(args[1]) || 30;
      console.log(`🚀 AUTONOMOUS MODE (Budget: $${budget})\n`);
      
      // Get balance
      const bal = run('balance');
      console.log(`Current Balance: $${bal.balance_dollars}`);
      console.log(`Portfolio Value: $${bal.portfolio_value_dollars}`);
      console.log(`Total: $${(parseFloat(bal.balance_dollars) + parseFloat(bal.portfolio_value_dollars)).toFixed(2)}\n`);
      
      // Get trending
      console.log('📊 Scanning trending markets...\n');
      const trending = run('trending');
      
      // Search for opportunities
      const niches = ['trump', 'recession', 'tariff', 'AI', 'sec', 'impeach', 'fed', 'health', 'sports', 'crypto', 'gdp'];
      
      console.log('🔍 Searching niches...\n');
      const opportunities = [];
      
      for (const niche of niches) {
        const results = run(`search "${niche}"`);
        if (Array.isArray(results) && results.length > 0) {
          // Filter for good opportunities
          results.filter(m => parseFloat(m.volume_24h) > 100)
                .slice(0, 3)
                .forEach(m => {
                  const price = parseFloat(m.yes_bid);
                  if (price < 0.90) { // Skip very high prices
                    opportunities.push({
                      ticker: m.ticker,
                      title: m.title.substring(0, 60),
                      price: price,
                      volume: parseInt(m.volume_24h),
                      bid: m.yes_bid
                    });
                  }
                });
        }
      }
      
      // Sort by volume
      opportunities.sort((a, b) => b.volume - a.volume);
      
      console.log(`📋 FOUND ${opportunities.length} OPPORTUNITIES:\n`);
      opportunities.slice(0, 15).forEach((o, i) => {
        console.log(`${i+1}. ${o.ticker}`);
        console.log(`   ${o.title}...`);
        console.log(`   ${(o.price*100).toFixed(0)}¢ | Vol: ${o.volume.toLocaleString()}\n`);
      });
      
      console.log('💡 To place trades, use:');
      console.log('   node kalshi-autonomous.mjs buy <ticker> <shares> <price>\n');
      break;
    }
    
    case 'report': {
      const result = run('portfolio');
      const bal = run('balance');
      
      console.log('\n📊 KALSHI P&L REPORT');
      console.log('=====================\n');
      console.log(`Balance: $${bal.balance_dollars}`);
      console.log(`Portfolio: $${bal.portfolio_value_dollars}`);
      console.log(`Total: $${(parseFloat(bal.balance_dollars) + parseFloat(bal.portfolio_value_dollars)).toFixed(2)}\n`);
      
      const positions = result.positions.filter(p => parseFloat(p.market_exposure_dollars) > 0);
      console.log(`Active Positions: ${positions.length}\n`);
      
      positions.forEach(p => {
        console.log(`${p.ticker}: ${p.position_fp} @ $${(parseFloat(p.market_exposure_dollars)/parseFloat(p.position_fp)).toFixed(2)}`);
      });
      break;
    }
    
    default:
      console.log('Commands: trending | search <query> | buy <ticker> <shares> <price> | balance | portfolio | report | autonomous [budget]');
  }
}

main();
