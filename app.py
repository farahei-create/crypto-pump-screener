from flask import Flask, render_template, jsonify
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MIN_PRICE_CHANGE_1H = float(os.getenv('MIN_PRICE_CHANGE_1H', 12.0))
MIN_LIQUIDITY = float(os.getenv('MIN_LIQUIDITY', 30000))
MAX_RESULTS = int(os.getenv('MAX_RESULTS', 15))

def get_potential_pumps():
    try:
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY', ''),
            'secret': os.getenv('BINANCE_SECRET', ''),
            'enableRateLimit': True,
        })
        
        tickers = exchange.fetch_tickers()
        pumps = []
        
        for symbol, ticker in tickers.items():
            if '/USDT' in symbol or '/USDC' in symbol:
                change_1h = ticker.get('percentage', 0) or 0
                volume = ticker.get('quoteVolume', 0) or 0
                
                if change_1h >= MIN_PRICE_CHANGE_1H and volume > MIN_LIQUIDITY:
                    pumps.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': ticker['last']
                    })
        
        pumps = sorted(pumps, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        return pumps
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [{'error': 'Unable to fetch data from Binance. Please try again later.'}]

@app.route('/')
def dashboard():
    pumps = get_potential_pumps()
    return render_template('index.html', pumps=pumps)

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)