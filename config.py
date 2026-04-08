import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# API CONFIGURATIONS
# ============================================

# Binance API (Testnet)
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
BN_TESTNET = os.getenv('BN_TESTNET', 'false').lower() == 'true'

# NVIDIA AI API
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "meta/llama3-70b-instruct"

# ============================================
# TRADING CONFIGURATIONS
# ============================================

SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
QUANTITY = 0.001  # 0.001 BTC for testnet
TIMEFRAME = '5m'
CHECK_INTERVAL = 60  # Fallback REST polling interval (seconds)

# ============================================
# RISK MANAGEMENT
# ============================================

STOP_LOSS_PCT = 2.0      # 2% stop loss
TAKE_PROFIT_PCT = 4.0    # 4% take profit (1:2 risk-reward)
MAX_POSITIONS = 1

# ============================================
# WEBSOCKET CONFIGURATION
# ============================================

# Testnet WebSocket URL
WEBSOCKET_URL = "wss://stream.testnet.binance.vision/ws"
# Mainnet would be: "wss://stream.binance.com:9443/ws"

# Streams to subscribe to
WEBSOCKET_STREAMS = [
    f"{SYMBOL.lower()}@trade",        # Real-time trades
    f"{SYMBOL.lower()}@kline_1m",     # 1-minute candles
    f"{SYMBOL.lower()}@kline_5m",     # 5-minute candles
    f"{SYMBOL.lower()}@ticker",       # 24hr ticker
]

# ============================================
# AI PROMPT TEMPLATE
# ============================================

AI_PROMPT = """Crypto signal needed. Real data:
Price: ${price}
RSI: ${rsi}
Trend: ${trend}

Reply EXACTLY one of these three lines:
BUY|${price}|${price*0.98}|${price*1.04}|${confidence}
SELL|${price}|${price*1.02}|${price*0.96}|${confidence}
HOLD|0|0|0|0

Rules:
- BUY: RSI < 70 and BULLISH trend
- SELL: RSI > 30 and BEARISH trend
- HOLD: uncertain
"""

# ============================================
# LOGGING
# ============================================

LOG_FILE = 'data/trades.log'
LOG_LEVEL = 'INFO'

# ============================================
# PAPER TRADING (Test mode)
# ============================================

PAPER_TRADING = False  # Set True to simulate without real orders
MIN_CONFIDENCE = 60    # Minimum confidence to execute trade

def validate_config():
    """Validate configuration"""
    errors = []
    if not BINANCE_API_KEY or BINANCE_API_KEY == 'your_testnet_api_key_here':
        errors.append("❌ BINANCE_API_KEY not set in .env")
    if not BINANCE_API_SECRET:
        errors.append("❌ BINANCE_API_SECRET not set in .env")
    if not NVIDIA_API_KEY:
        errors.append("❌ NVIDIA_API_KEY not set in .env")
    
    if errors:
        for error in errors:
            print(error)
        return False
    
    print(f"✅ Configuration validated - Trading on {'TESTNET' if BN_TESTNET else 'MAINNET'}")
    return True