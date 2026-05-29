# Configuration for Crypto Pump Screener

# Binance API (recommended for better rate limits)
BINANCE_API_KEY = ""
BINANCE_SECRET = ""

# Telegram Bot for alerts (optional but recommended)
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# === Screener Filters ===
MIN_PRICE_CHANGE_1H = 12.0      # Minimum % change in 1 hour (adjust based on market)
MIN_VOLUME_SPIKE = 3.5          # Volume must be at least X times the recent average
MIN_LIQUIDITY = 30000           # Minimum 24h volume in USDT
MAX_RESULTS = 12                # Max coins to display per scan

# Scan every X seconds
SCAN_INTERVAL = 45