from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

# Confirmed pumps (already moving)
MIN_PRICE_CHANGE_CONFIRMED = 12.0
MIN_LIQUIDITY = 30000
MAX_RESULTS = 12

# Early accumulation signals (volume spike but price still quiet)
MIN_VOLUME_SPIKE_EARLY = 3.5   # Volume at least 3.5x average
MAX_PRICE_CHANGE_EARLY = 8.0   # Price still calm (<8%)

def get_potential_pumps():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tickers = response.json()
        
        confirmed = []
        early = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if not (symbol.endswith('USDT') or symbol.endswith('USDC')):
                continue
                
            try:
                change_1h = float(ticker.get('priceChangePercent', 0))
                volume = float(ticker.get('quoteVolume', 0))
                price = float(ticker.get('lastPrice', 0))
                
                # Confirmed pumps (already exploding)
                if change_1h >= MIN_PRICE_CHANGE_CONFIRMED and volume > MIN_LIQUIDITY:
                    confirmed.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': price
                    })
                
                # Early accumulation (volume spike but price still calm)
                elif volume > MIN_LIQUIDITY * MIN_VOLUME_SPIKE_EARLY and change_1h <= MAX_PRICE_CHANGE_EARLY and change_1h > 0:
                    early.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': price
                    })
            except:
                continue
        
        confirmed = sorted(confirmed, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        early = sorted(early, key=lambda x: x['volume'], reverse=True)[:MAX_RESULTS]
        
        return {'confirmed': confirmed, 'early': early}
    except Exception as e:
        print(f"Error: {e}")
        return {'confirmed': [], 'early': [], 'error': 'Unable to fetch data'}

@app.route('/')
def dashboard():
    data = get_potential_pumps()
    return render_template('index.html', data=data)

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)