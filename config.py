# Configuration for Crypto Pump Screener (PUBLIC MODE - no API key)

# Telegram Bot (optionnel)
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# === Screener Filters (optimisé pour USDC low-caps) ===
MIN_PRICE_CHANGE_1H = 5.0       # 5% minimum en 1h (beaucoup plus réaliste)
MIN_LIQUIDITY = 25000           # Volume 24h minimum (en USDT/USDC)
MAX_RESULTS = 15                # Nombre max de résultats

# Scan toutes les X secondes
SCAN_INTERVAL = 30
