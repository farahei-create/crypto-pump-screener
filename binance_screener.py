import ccxt
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Load config (on garde tes variables de config.py)
from config import *

# Version PUBLIQUE (sans clé API)
exchange = ccxt.binance({
    'enableRateLimit': True,
})

def get_potential_pumps():
    tickers = exchange.fetch_tickers()
    pumps = []
    
    for symbol, ticker in tickers.items():
        if '/USDT' in symbol or '/USDC' in symbol:
            change_1h = ticker.get('percentage', 0) or 0
            volume = ticker.get('quoteVolume', 0) or 0
            
            if (change_1h >= MIN_PRICE_CHANGE_1H and 
                volume > MIN_LIQUIDITY):
                
                pumps.append({
                    'symbol': symbol,
                    'change_1h': round(change_1h, 2),
                    'volume': volume,
                    'price': ticker['last']
                })
    
    pumps = sorted(pumps, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
    return pumps

def send_telegram_alert(message):
    try:
        import telegram
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print("🚀 Crypto Pump Screener started (PUBLIC MODE)...")
    print(f"Scanning every {SCAN_INTERVAL} seconds...\n")
    
    while True:
        try:
            pumps = get_potential_pumps()
            
            if pumps:
                print("\n📈 Top Pump Candidates:")
                for p in pumps:
                    print(f"{p['symbol']}: +{p['change_1h']}% | Vol: ${p['volume']:,.0f}")
                
                if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                    msg = "📈 Pump Alert:\n" + "\n".join([f"{p['symbol']}: +{p['change_1h']}%" for p in pumps[:5]])
                    send_telegram_alert(msg)
            
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
