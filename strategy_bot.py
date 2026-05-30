import requests
import pandas as pd
import numpy as np
from datetime import datetime

class PaperTradingBot:
    def __init__(self):
        self.positions = []
        self.balance = 10000.0

    def get_real_time_data(self, symbol):
        """Simple and reliable method using public Binance API (no ccxt needed)"""
        try:
            # Get ticker
            ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            ticker = requests.get(ticker_url, timeout=8).json()
            
            if 'code' in ticker:  # Error from Binance
                return None, None
            
            # Get OHLCV (klines)
            kline_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=80"
            klines = requests.get(kline_url, timeout=8).json()
            
            if not klines or isinstance(klines, dict):
                return None, None
            
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return ticker, df
        except:
            return None, None

    def analyze_pair(self, symbol):
        ticker, df = self.get_real_time_data(symbol)
        if ticker is None or df is None:
            return None

        current_price = float(ticker.get('lastPrice', 0))
        change_1h = float(ticker.get('priceChangePercent', 0))
        volume = float(ticker.get('quoteVolume', 0))

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Volume spike
        volume_ma = df['volume'].rolling(20).mean().iloc[-1]
        volume_spike = volume / volume_ma if volume_ma > 0 else 1

        # Simple correlation (BTC)
        try:
            btc_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
            btc_ticker = requests.get(btc_url, timeout=5).json()
            btc_change = float(btc_ticker.get('priceChangePercent', 0))
            correlation = 0.3 if abs(change_1h - btc_change) > 15 else 0.7
        except:
            correlation = 0.4

        # Scoring
        score = 0
        reasons = []
        if change_1h > 10 and volume_spike > 2.2:
            score += 45
            reasons.append("Forte pompe + volume spike")
        if volume_spike > 3.5:
            score += 20
            reasons.append("Volume extrêmement élevé")
        if rsi < 38:
            score += 18
            reasons.append("RSI en zone oversold (potentiel rebond)")
        if abs(correlation) < 0.45:
            score += 12
            reasons.append("Faible corrélation BTC = opportunité indépendante")

        recommendation = "LONG" if score > 50 else ("SHORT" if change_1h < -7 else "HOLD")
        confidence = min(92, max(45, score + 15))

        return {
            'symbol': symbol,
            'price': round(current_price, 6),
            'change_1h': round(change_1h, 2),
            'volume': round(volume),
            'volume_spike': round(volume_spike, 2),
            'rsi': round(rsi, 1),
            'correlation_btc': round(correlation, 2),
            'recommendation': recommendation,
            'confidence': confidence,
            'reasons': reasons,
            'ohlcv': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(40).to_dict('records')
        }

    def simulate_trade(self, symbol, side, amount_usdc, entry_price):
        position = {
            'id': len(self.positions) + 1,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'amount_usdc': amount_usdc,
            'entry_time': datetime.now().isoformat(),
            'status': 'open'
        }
        self.positions.append(position)
        return position

    def close_position(self, position_id, exit_price):
        for pos in self.positions:
            if pos['id'] == position_id and pos['status'] == 'open':
                pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * pos['amount_usdc'] * (1 if pos['side'] == 'LONG' else -1)
                pos['exit_price'] = exit_price
                pos['pnl'] = round(pnl, 2)
                pos['status'] = 'closed'
                self.balance += pnl
                return pos
        return None

bot = PaperTradingBot()