import json
import threading
import time
import requests
from websocket import WebSocketApp
from modules.logger import setup_logger

class BinanceWebSocket:
    def __init__(self, symbol, on_price_update, on_candle_close, on_error=None):
        self.symbol = symbol.lower()
        self.on_price_update = on_price_update
        self.on_candle_close = on_candle_close
        self.on_error = on_error
        self.logger = setup_logger()
        self.ws = None
        self.running = False
        self.current_price = 0
        self.last_pong = time.time()
        
        # WebSocket URL
        self.ws_url = "wss://stream.testnet.binance.vision/ws"
        
    def start(self):
        """Start WebSocket connection"""
        self.running = True
        
        # Subscribe to multiple streams
        streams = [
            f"{self.symbol}@trade",
            f"{self.symbol}@kline_1m",
            f"{self.symbol}@kline_5m",
            f"{self.symbol}@ticker",
        ]
        
        stream_names = '/'.join(streams)
        full_url = f"{self.ws_url}/{stream_names}"
        
        self.logger.info(f"🔌 Connecting to WebSocket: {self.symbol}")
        
        self.ws = WebSocketApp(
            full_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_pong=self._on_pong
        )
        
        # Run in background thread
        wst = threading.Thread(target=self.ws.run_forever, kwargs={
            'ping_interval': 30,
            'ping_timeout': 10
        }, daemon=True)
        wst.start()
        
    def _on_open(self, ws):
        """WebSocket opened"""
        self.logger.info("✅ WebSocket connected - receiving real-time data")
        
    def _on_message(self, ws, message):
        """Handle incoming messages"""
        try:
            data = json.loads(message)
            
            # Handle different stream types
            if 'e' in data:
                event_type = data['e']
                
                if event_type == 'trade':
                    # Real-time trade
                    price = float(data['p'])
                    quantity = float(data['q'])
                    self.current_price = price
                    
                    if self.on_price_update:
                        self.on_price_update({
                            'price': price,
                            'quantity': quantity,
                            'time': data['T'],
                            'type': 'trade'
                        })
                        
                elif event_type == 'kline':
                    # Candlestick data
                    kline = data['k']
                    is_closed = kline['x']
                    
                    if is_closed:
                        # Candle just closed - trigger analysis
                        candle = {
                            'open': float(kline['o']),
                            'high': float(kline['h']),
                            'low': float(kline['l']),
                            'close': float(kline['c']),
                            'volume': float(kline['v']),
                            'interval': kline['i'],
                            'close_time': kline['T']
                        }
                        
                        self.logger.info(f"📊 Candle closed: {candle['interval']} @ ${candle['close']:.2f}")
                        
                        if self.on_candle_close:
                            self.on_candle_close(candle)
                            
                elif event_type == '24hrTicker':
                    # 24hr ticker update
                    price_change = float(data.get('P', 0))
                    self.logger.debug(f"📈 24h change: {price_change:.2f}%")
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {e}")
        except Exception as e:
            self.logger.error(f"Message handler error: {e}")
            if self.on_error:
                self.on_error(str(e))
    
    def _on_error(self, ws, error):
        """Handle errors"""
        self.logger.error(f"WebSocket error: {error}")
        if self.on_error:
            self.on_error(str(error))
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle closure"""
        self.logger.warning(f"WebSocket closed (code: {close_status_code})")
        self.running = False
        
        # Auto-reconnect
        if self.running is False:
            self.logger.info("🔄 Reconnecting in 5 seconds...")
            time.sleep(5)
            if not self.running:  # Check if not manually stopped
                self.start()
    
    def _on_pong(self, ws, message):
        """Handle pong response"""
        self.last_pong = time.time()
    
    def get_current_price(self):
        """Get latest price"""
        return self.current_price
    
    def stop(self):
        """Stop WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
        self.logger.info("WebSocket stopped")
    
    def is_connected(self):
        """Check if WebSocket is connected"""
        return self.ws and self.ws.sock and self.ws.sock.connected