from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

MIN_PRICE_CHANGE_CONFIRMED = 12.0
MIN_LIQUIDITY = 25000
MAX_RESULTS = 12

MIN_VOLUME_SPIKE_EARLY = 3.0
MAX_PRICE_CHANGE_EARLY = 8.0

MIN_PRICE_CHANGE_24H = 8.0  # Lower threshold for 24h pumps (so ALLO and recent pumps appear)

def get_potential_pumps():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tickers = response.json()
        
        confirmed = []
        early = []
        pumps_24h = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if not (symbol.endswith('USDT') or symbol.endswith('USDC')):
                continue
                
            try:
                change_1h = float(ticker.get('priceChangePercent', 0))
                volume = float(ticker.get('quoteVolume', 0))
                price = float(ticker.get('lastPrice', 0))
                
                # Confirmed pumps (1h)
                if change_1h >= MIN_PRICE_CHANGE_CONFIRMED and volume > MIN_LIQUIDITY:
                    confirmed.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': price
                    })
                
                # Early accumulation
                elif volume > MIN_LIQUIDITY * MIN_VOLUME_SPIKE_EARLY and change_1h <= MAX_PRICE_CHANGE_EARLY and change_1h > 0:
                    early.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': price
                    })
                
                # Pumps des dernières 24h (lower threshold)
                if change_1h >= MIN_PRICE_CHANGE_24H and volume > MIN_LIQUIDITY:
                    pumps_24h.append({
                        'symbol': symbol,
                        'change_24h': round(change_1h, 2),
                        'volume': round(volume),
                        'price': price
                    })
            except:
                continue
        
        confirmed = sorted(confirmed, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        early = sorted(early, key=lambda x: x['volume'], reverse=True)[:MAX_RESULTS]
        pumps_24h = sorted(pumps_24h, key=lambda x: x['change_24h'], reverse=True)[:12]
        
        return {'confirmed': confirmed, 'early': early, 'pumps_24h': pumps_24h}
    except Exception as e:
        print(f"Error: {e}")
        return {'confirmed': [], 'early': [], 'pumps_24h': []}

@app.route('/')
def dashboard():
    data = get_potential_pumps()
    return render_template('index.html', data=data)

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)