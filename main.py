import time
import threading
from datetime import datetime
from modules.binance_client import BinanceTrader
from modules.binance_websocket import BinanceWebSocket
from modules.nvidia_ai import NvidiaAI
from modules.indicators import calculate_indicators
from modules.trade_manager import TradeManager
from modules.logger import setup_logger
from config import SYMBOL, TIMEFRAME, CHECK_INTERVAL, MIN_CONFIDENCE, PAPER_TRADING

class CryptoAIBot:
    def __init__(self):
        self.logger = setup_logger()
        self.binance = BinanceTrader()
        self.ai = NvidiaAI()
        self.trade_manager = TradeManager()
        self.current_price = 0
        self.last_analysis_time = 0
        self.analysis_interval = CHECK_INTERVAL  # Fallback interval
        self.running = True
        
        # WebSocket callbacks
        self.ws = BinanceWebSocket(
            symbol=SYMBOL,
            on_price_update=self.on_price_update,
            on_candle_close=self.on_candle_close,
            on_error=self.on_ws_error
        )
        
    def on_price_update(self, price_data):
        """Real-time price update from WebSocket"""
        self.current_price = price_data['price']
        self.logger.debug(f"💰 Price: ${self.current_price:.2f}")
        
        # Check SL/TP in real-time
        if self.trade_manager.active_position:
            self.trade_manager.check_sl_tp(self.current_price)
    
    def on_candle_close(self, candle):
        """Called when a candlestick closes - trigger AI analysis"""
        # Only analyze on 5-minute candles
        if candle['interval'] != '5m':
            return
        
        self.logger.info(f"📊 5-min candle closed at ${candle['close']:.2f}")
        self.analyze_and_trade()
    
    def on_ws_error(self, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")
    
    def analyze_and_trade(self):
        """Run AI analysis and execute trade if signal"""
        try:
            # Check if we already have a position
            if self.binance.has_open_position():
                self.logger.info("Position already open - waiting for exit")
                return
            
            # Get market data
            klines = self.binance.get_klines(interval=TIMEFRAME, limit=200)
            market_data = calculate_indicators(klines)
            
            if not market_data:
                self.logger.warning("Failed to calculate indicators")
                return
            
            self.logger.info(f"📈 RSI: {market_data['rsi']} | Trend: {market_data['ema_trend']} | 24h: {market_data['change_24h']}%")
            
            # Get AI signal
            signal_data = self.ai.get_signal(market_data)
            
            if signal_data and signal_data['signal'] != 'HOLD':
                confidence = signal_data['confidence']
                
                if confidence >= MIN_CONFIDENCE:
                    self.logger.info(f"🎯 AI Signal: {signal_data['signal']} with {confidence}% confidence")
                    self.trade_manager.execute_trade(signal_data)
                else:
                    self.logger.info(f"⚠️ Signal ignored - confidence {confidence}% < {MIN_CONFIDENCE}%")
            else:
                self.logger.info("AI recommends HOLD - no action")
                
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
    
    def fallback_rest_loop(self):
        """Fallback REST polling (in case WebSocket fails)"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check every CHECK_INTERVAL seconds
                if current_time - self.last_analysis_time >= self.analysis_interval:
                    self.last_analysis_time = current_time
                    
                    # Only run if WebSocket is disconnected
                    if not self.ws.is_connected():
                        self.logger.info("Using REST fallback for analysis")
                        self.analyze_and_trade()
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Fallback loop error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the bot"""
        print("="*60)
        print("🚀 CRYPTO AI TRADING BOT - WEBSOCKET VERSION")
        print(f"📊 Trading Pair: {SYMBOL}")
        print(f"🔧 Mode: {'PAPER TRADING' if PAPER_TRADING else 'LIVE'}")
        print(f"🌐 Network: TESTNET")
        print("🤖 AI: NVIDIA " + ("(Mock)" if not hasattr(self.ai, 'api_key') else "Llama 3"))
        print("🔌 Data Source: WebSocket (Real-time)")
        print("="*60)
        
        # Validate config
        from config import validate_config
        if not validate_config():
            print("❌ Configuration error. Please fix and restart.")
            return
        
        # Start WebSocket
        self.ws.start()
        
        # Start fallback REST loop in background
        rest_thread = threading.Thread(target=self.fallback_rest_loop, daemon=True)
        rest_thread.start()
        
        # Initial analysis
        time.sleep(3)  # Wait for WebSocket to connect
        self.analyze_and_trade()
        
        # Keep bot running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("🛑 Bot stopped by user")
            self.running = False
            self.ws.stop()
            print("\n✅ Bot shutdown complete")

if __name__ == "__main__":
    bot = CryptoAIBot()
    bot.start()