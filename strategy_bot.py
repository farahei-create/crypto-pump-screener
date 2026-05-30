import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from config import MIN_PRICE_CHANGE_1H, MIN_LIQUIDITY, MAX_RESULTS
except:
    MIN_PRICE_CHANGE_1H = 8.0
    MIN_LIQUIDITY = 25000
    MAX_RESULTS = 10

exchange = ccxt.binance({'enableRateLimit': True})

class PaperTradingBot:
    def __init__(self):
        self.positions = []
        self.balance = 10000.0
        self.equity_curve = [10000.0]

    def get_real_time_data(self, symbol):
        """Try symbol as-is, then try USDT version if USDC fails"""
        try:
            ticker = exchange.fetch_ticker(symbol)
            ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=80)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return ticker, df
        except:
            # Try USDT version if USDC failed
            if symbol.endswith('USDC'):
                try:
                    alt_symbol = symbol.replace('USDC', 'USDT')
                    ticker = exchange.fetch_ticker(alt_symbol)
                    ohlcv = exchange.fetch_ohlcv(alt_symbol, '5m', limit=80)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    return ticker, df
                except:
                    return None, None
            return None, None

    def analyze_pair(self, symbol):
        ticker, df = self.get_real_time_data(symbol)
        if ticker is None or df is None:
            return None

        current_price = ticker['last']
        change_1h = ticker.get('percentage', 0) or 0
        volume = ticker.get('quoteVolume', 0) or 0

        df['rsi'] = self.calculate_rsi(df['close'])
        volume_spike = volume / df['volume'].rolling(20).mean().iloc[-1] if df['volume'].rolling(20).mean().iloc[-1] > 0 else 1

        try:
            btc_df = pd.DataFrame(exchange.fetch_ohlcv('BTC/USDT', '5m', limit=80), columns=['ts','o','h','l','c','v'])
            correlation = df['close'].corr(btc_df['c'])
        except:
            correlation = 0.35

        score = 0
        reasons = []
        if change_1h > 10 and volume_spike > 2.2:
            score += 45
            reasons.append("Forte pompe + volume spike")
        if volume_spike > 3.5:
            score += 20
            reasons.append("Volume extrêmement élevé")
        if df['rsi'].iloc[-1] < 38:
            score += 18
            reasons.append("RSI en zone oversold")
        if abs(correlation) < 0.45:
            score += 12
            reasons.append("Faible corrélation BTC = alpha indépendant")

        recommendation = "LONG" if score > 50 else ("SHORT" if change_1h < -7 else "HOLD")
        confidence = min(92, max(45, score + 15))

        return {
            'symbol': symbol,
            'price': round(current_price, 6),
            'change_1h': round(change_1h, 2),
            'volume': round(volume),
            'volume_spike': round(volume_spike, 2),
            'rsi': round(df['rsi'].iloc[-1], 1),
            'correlation_btc': round(correlation, 2),
            'recommendation': recommendation,
            'confidence': confidence,
            'reasons': reasons,
            'ohlcv': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(40).to_dict('records')
        }

    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

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
                self.equity_curve.append(self.balance)
                return pos
        return None

bot = PaperTradingBot()