from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

MIN_PRICE_CHANGE_CONFIRMED = 12.0
MIN_LIQUIDITY = 25000
MAX_RESULTS = 12

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
            if not (symbol.endswith('USDT') or symbol.endswith('USDC')): continue
            try:
                change_1h = float(ticker.get('priceChangePercent', 0))
                volume = float(ticker.get('quoteVolume', 0))
                price = float(ticker.get('lastPrice', 0))
                
                if change_1h >= MIN_PRICE_CHANGE_CONFIRMED and volume > MIN_LIQUIDITY:
                    confirmed.append({'symbol': symbol, 'change_1h': round(change_1h, 2), 'volume': round(volume), 'price': price})
                elif volume > MIN_LIQUIDITY * 3.0 and change_1h <= 8.0 and change_1h > 0:
                    early.append({'symbol': symbol, 'change_1h': round(change_1h, 2), 'volume': round(volume), 'price': price})
                if change_1h >= 8.0 and volume > MIN_LIQUIDITY:
                    pumps_24h.append({'symbol': symbol, 'change_24h': round(change_1h, 2), 'volume': round(volume), 'price': price})
            except: continue
        
        confirmed = sorted(confirmed, key=lambda x: x['change_1h'], reverse=True)[:MAX_RESULTS]
        early = sorted(early, key=lambda x: x['volume'], reverse=True)[:MAX_RESULTS]
        pumps_24h = sorted(pumps_24h, key=lambda x: x['change_24h'], reverse=True)[:12]
        return {'confirmed': confirmed, 'early': early, 'pumps_24h': pumps_24h}
    except:
        return {'confirmed': [], 'early': [], 'pumps_24h': []}

@app.route('/')
def dashboard():
    data = get_potential_pumps()
    return render_template('index.html', data=data)

@app.route('/bot')
def strategy_bot_page():
    return render_template('bot.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_pair():
    data = request.get_json()
    symbol = data.get('symbol', '').upper()
    
    # Try USDC first, then USDT
    for suffix in ['USDC', 'USDT']:
        test_symbol = symbol if symbol.endswith(('USDC', 'USDT')) else symbol + suffix
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={test_symbol}"
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                ticker = r.json()
                if 'lastPrice' in ticker:
                    price = float(ticker.get('lastPrice', 0))
                    change = float(ticker.get('priceChangePercent', 0))
                    volume = float(ticker.get('quoteVolume', 0))
                    
                    score = 0
                    reasons = []
                    if change > 12: 
                        score += 40
                        reasons.append("Forte hausse")
                    if volume > 5000000:
                        score += 25
                        reasons.append("Volume élevé")
                    
                    rec = "LONG" if score > 45 else ("SHORT" if change < -6 else "HOLD")
                    conf = min(90, max(50, score + 20))
                    
                    return jsonify({
                        'symbol': test_symbol,
                        'price': round(price, 6),
                        'change_1h': round(change, 2),
                        'volume': round(volume),
                        'volume_spike': 1.0,
                        'rsi': 50,
                        'correlation_btc': 0.4,
                        'recommendation': rec,
                        'confidence': conf,
                        'reasons': reasons if reasons else ["Analyse effectuée"],
                        'ohlcv': []
                    })
        except:
            continue
    
    return jsonify({'error': 'Paire non trouvée sur Binance. Essaie BTCUSDT, ETHUSDT, SOLUSDT...'})

@app.route('/api/trade', methods=['POST'])
def execute_paper_trade():
    data = request.get_json()
    # Simple simulation
    return jsonify({'success': True, 'new_balance': 10000.0})

@app.route('/api/close_all', methods=['POST'])
def close_all():
    return jsonify({'success': True, 'new_balance': 10000.0})

@app.route('/api/balance')
def get_balance():
    return jsonify({'balance': 10000.0})

@app.route('/api/pumps')
def api_pumps():
    return jsonify(get_potential_pumps())

if __name__ == '__main__':
    app.run(debug=True)