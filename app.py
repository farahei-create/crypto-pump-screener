from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

MIN_PRICE_CHANGE_1H = float(os.getenv('MIN_PRICE_CHANGE_1H', 12.0))
MIN_LIQUIDITY = float(os.getenv('MIN_LIQUIDITY', 30000))
MAX_RESULTS = int(os.getenv('MAX_RESULTS', 15))

def get_potential_pumps():
    try:
        # Use public Binance API (no API key needed - much lighter for Vercel)
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tickers = response.json()
        
        pumps = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if symbol.endswith('USDT') or symbol.endswith('USDC'):
                try:
                    change_1h = float(ticker.get('priceChangePercent', 0))
                    volume = float(ticker.get('quoteVolume', 0))
                    price = float(ticker.get('lastPrice', 0))
                    
                    if change_1h >= MIN_PRICE_CHANGE_1H and volume > MIN_LIQUIDITY:
                        pumps.append({
                            'symbol': symbol,
                            'change_1h': round(change_1h, 2),
                            'volume': round(volume),
                            'price': price
                        })
                except:
                    continue
        
        pumps = sorted(pumps, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        return pumps
    except Exception as e:
        print(f"Error: {e}")
        return [{'error': 'Unable to fetch data from Binance. Please try again.'}]

@app.route('/')
def dashboard():
    pumps = get_potential_pumps()
    return render_template('index.html', pumps=pumps)

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)