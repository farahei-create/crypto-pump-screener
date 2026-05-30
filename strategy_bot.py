import requests
from datetime import datetime

class PaperTradingBot:
    def __init__(self):
        self.positions = []
        self.balance = 10000.0

    def analyze_pair(self, symbol):
        """Super simple and reliable - only uses public ticker API"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            data = requests.get(url, timeout=6).json()
            
            if 'code' in data:  # Binance error
                return None
            
            price = float(data.get('lastPrice', 0))
            change_1h = float(data.get('priceChangePercent', 0))
            volume = float(data.get('quoteVolume', 0))
            
            # Simple scoring
            score = 0
            reasons = []
            
            if change_1h > 12:
                score += 40
                reasons.append("Forte hausse sur 24h")
            if volume > 5000000:
                score += 25
                reasons.append("Volume élevé")
            if change_1h > 8 and volume > 1000000:
                score += 20
                reasons.append("Bon momentum + liquidité")
            
            recommendation = "LONG" if score > 45 else ("SHORT" if change_1h < -6 else "HOLD")
            confidence = min(90, max(50, score + 20))
            
            return {
                'symbol': symbol,
                'price': round(price, 6),
                'change_1h': round(change_1h, 2),
                'volume': round(volume),
                'volume_spike': 1.0,
                'rsi': 50.0,
                'correlation_btc': 0.4,
                'recommendation': recommendation,
                'confidence': confidence,
                'reasons': reasons if reasons else ["Analyse basique effectuée"],
                'ohlcv': []  # No chart for now
            }
        except Exception as e:
            print(f"API Error for {symbol}: {e}")
            return None

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