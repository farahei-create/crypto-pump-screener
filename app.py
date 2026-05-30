from flask import Flask, render_template, jsonify, request
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime, timedelta
import time
import os
from collections import defaultdict

app = Flask(__name__)

# Configuration - Utilise l'API publique sans clé (limité mais fonctionne)
# Pour plus de données, ajoutez vos clés API Binance
API_KEY = os.environ.get('BINANCE_API_KEY', '')
API_SECRET = os.environ.get('BINANCE_API_SECRET', '')

try:
    if API_KEY and API_SECRET:
        client = Client(API_KEY, API_SECRET)
        print("✅ Connecté à Binance avec API Key")
    else:
        client = Client()
        print("✅ Connecté à Binance (mode public)")
except Exception as e:
    print(f"⚠️ Erreur de connexion: {e}")
    client = None

# Cache pour éviter de surcharger l'API
cache_data = {
    'data': None,
    'timestamp': None
}
CACHE_DURATION = 30  # secondes

def get_binance_data():
    """Récupère les données des 200 meilleures paires USDT"""
    
    # Vérifier le cache
    if cache_data['timestamp'] and (datetime.now() - cache_data['timestamp']).seconds < CACHE_DURATION:
        return cache_data['data']
    
    try:
        if not client:
            return {'early': [], 'confirmed': [], 'pumps_24h': [], 'error': 'API non disponible'}
        
        # Récupérer tous les tickers
        tickers = client.get_ticker()
        
        # Filtrer uniquement les paires USDT
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        
        # Filtrer les paires avec volume minimum (éviter les paires mortes)
        active_pairs = [t for t in usdt_pairs if float(t['quoteVolume']) > 500000]
        
        # Trier par volume pour prioriser les paires actives
        active_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        
        early_signals = []
        confirmed_pumps = []
        all_pumps = []
        
        # Analyser les top 100 paires par volume
        for pair in active_pairs[:100]:
            try:
                symbol = pair['symbol']
                change_1h = float(pair['priceChangePercent'])
                change_24h = float(pair['priceChangePercent'])
                volume = float(pair['quoteVolume'])
                price = float(pair['lastPrice'])
                volume_24h = volume
                
                # Obtenir les données OHLCV pour analyse plus poussée
                try:
                    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=4)
                    if klines:
                        vol_15m_avg = sum(float(k[5]) for k in klines[:3]) / 3
                        vol_current = float(klines[-1][5])
                        volume_spike = (vol_current / vol_15m_avg) if vol_15m_avg > 0 else 1
                    else:
                        volume_spike = 1
                except:
                    volume_spike = 1
                
                # Détection EARLY : Volume en hausse mais prix encore calme
                if (volume > 1000000 and volume_spike > 1.5 and -2 < change_1h < 3):
                    early_signals.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume, 2),
                        'price': round(price, 8) if price < 1 else round(price, 4),
                        'volume_spike': round(volume_spike, 1)
                    })
                
                # Détection CONFIRMED : Hausse significative
                elif change_1h >= 4:
                    confirmed_pumps.append({
                        'symbol': symbol,
                        'change_1h': round(change_1h, 2),
                        'volume': round(volume, 2),
                        'price': round(price, 8) if price < 1 else round(price, 4),
                        'change_24h': round(change_24h, 2)
                    })
                
                # Pour les pumps 24h
                if change_24h >= 15:
                    all_pumps.append({
                        'symbol': symbol,
                        'change_24h': round(change_24h, 2),
                        'volume': round(volume, 2),
                        'price': round(price, 8) if price < 1 else round(price, 4)
                    })
                    
            except Exception as e:
                print(f"Erreur sur {pair.get('symbol', 'unknown')}: {e}")
                continue
        
        # Trier par pertinence
        early_signals.sort(key=lambda x: x['volume_spike'], reverse=True)
        confirmed_pumps.sort(key=lambda x: x['change_1h'], reverse=True)
        all_pumps.sort(key=lambda x: x['change_24h'], reverse=True)
        
        result = {
            'early': early_signals[:15],
            'confirmed': confirmed_pumps[:20],
            'pumps_24h': all_pumps[:10],
            'last_update': datetime.now().strftime('%H:%M:%S'),
            'total_pairs': len(active_pairs)
        }
        
        # Mettre en cache
        cache_data['data'] = result
        cache_data['timestamp'] = datetime.now()
        
        return result
        
    except BinanceAPIException as e:
        print(f"Erreur API Binance: {e}")
        return {'early': [], 'confirmed': [], 'pumps_24h': [], 'error': str(e)}
    except Exception as e:
        print(f"Erreur générale: {e}")
        return {'early': [], 'confirmed': [], 'pumps_24h': [], 'error': str(e)}

@app.route('/')
def index():
    """Page principale"""
    data = get_binance_data()
    return render_template('index.html', data=data)

@app.route('/api/data')
def api_data():
    """Endpoint JSON pour rafraîchissement AJAX"""
    data = get_binance_data()
    return jsonify(data)

@app.route('/api/search')
def search():
    """Recherche de paire spécifique"""
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    
    try:
        tickers = client.get_ticker()
        pairs = [t for t in tickers if t['symbol'].endswith('USDT') and query in t['symbol']]
        results = [{
            'symbol': p['symbol'],
            'price': float(p['lastPrice']),
            'change': float(p['priceChangePercent']),
            'volume': float(p['quoteVolume'])
        } for p in pairs[:10]]
        return jsonify(results)
    except:
        return jsonify([])

@app.route('/health')
def health():
    """Endpoint de vérification"""
    return jsonify({
        'status': 'ok',
        'cache_age': (datetime.now() - cache_data['timestamp']).seconds if cache_data['timestamp'] else None,
        'client_connected': client is not None
    })

if __name__ == '__main__':
    print("\n🚀 Pump Screener démarré!")
    print("📊 Accédez à l'application sur: http://localhost:5000")
    print("🔄 Rafraîchissement automatique toutes les 45 secondes\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
