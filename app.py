from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

MIN_PRICE_CHANGE_CONFIRMED = 12.0
MIN_LIQUIDITY = 30000
MAX_RESULTS = 12

MIN_VOLUME_SPIKE_EARLY = 3.5
MAX_PRICE_CHANGE_EARLY = 8.0

MIN_PRICE_CHANGE_TODAY = 25.0  # For Today's Big Movers (24h)

def get_potential_pumps():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tickers = response.json()
        
        confirmed = []
        early = []
        today_big = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if not (symbol.endswith('USDT') or symbol.endswith('USDC')):
                continue
                
            try:
                change_1h = float(ticker.get('priceChangePercent', 0))
                change_24h = float(ticker.get('priceChangePercent', 0))  # Using same field for simplicity
                volume = float(ticker.get('quoteVolume', 0))
                price = float(ticker.get('lastPrice', 0))
                
                # Confirmed pumps (last 1h)
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
                
                # Today's Big Movers (24h strong pumps)
                if change_24h >= MIN_PRICE_CHANGE_TODAY and volume > MIN_LIQUIDITY:
                    today_big.append({
                        'symbol': symbol,
                        'change_24h': round(change_24h, 2),
                        'volume': round(volume),
                        'price': price
                    })
            except:
                continue
        
        confirmed = sorted(confirmed, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        early = sorted(early, key=lambda x: x['volume'], reverse=True)[:MAX_RESULTS]
        today_big = sorted(today_big, key=lambda x: x['change_24h'], reverse=True)[:8]
        
        return {'confirmed': confirmed, 'early': early, 'today_big': today_big}
    except Exception as e:
        print(f"Error: {e}")
        return {'confirmed': [], 'early': [], 'today_big': [], 'error': str(e)}

@app.route('/')
def dashboard():
    data = get_potential_pumps()
    return render_template('index.html', data=data)

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)
