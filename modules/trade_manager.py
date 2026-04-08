import time
import threading
from modules.binance_client import BinanceTrader
from modules.logger import setup_logger
from config import PAPER_TRADING
from modules.trade_history import TradeHistory
from datetime import datetime

class TradeManager:
    def __init__(self):
        self.binance = BinanceTrader()
        self.logger = setup_logger()
        self.active_position = None
        self.monitoring = False
        self.trade_history = TradeHistory()
        
    def execute_trade(self, signal_data):
        """Execute trade with dynamic SL/TP"""
        
        signal = signal_data['signal']
        
        if signal == 'HOLD':
            self.logger.info("HOLD signal - no action taken")
            return False
        
        if self.binance.has_open_position():
            self.logger.info("Position already open - closing first")
            self._close_position()
        
        entry_price = signal_data.get('entry', self.binance.get_current_price())
        sl = signal_data.get('sl', 0)
        tp = signal_data.get('tp', 0)
        
        # Calculate SL/TP if not provided
        if sl == 0 or tp == 0:
            if signal == 'BUY':
                sl = entry_price * (1 - 0.02)
                tp = entry_price * (1 + 0.04)
            else:
                sl = entry_price * (1 + 0.02)
                tp = entry_price * (1 - 0.04)
        
        if PAPER_TRADING:
            self.logger.info(f"📝 [PAPER] {signal} position at {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            self.active_position = {
                'side': 'LONG' if signal == 'BUY' else 'SHORT',
                'entry': entry_price,
                'sl': sl,
                'tp': tp,
                'confidence': signal_data['confidence'],
                'paper': True,
                'entry_time': datetime.now().isoformat(),
                'signal': signal
            }
            
            # Save to JSON
            self.trade_history.update_position(self.active_position)
            self.start_monitoring()
            return True
        
        # Real order
        order = self.binance.place_market_order(signal)
        if order:
            self.active_position = {
                'side': 'LONG' if signal == 'BUY' else 'SHORT',
                'entry': entry_price,
                'sl': sl,
                'tp': tp,
                'confidence': signal_data['confidence'],
                'paper': False,
                'entry_time': datetime.now().isoformat(),
                'signal': signal,
                'order_id': order.get('orderId')
            }
            
            # Save to JSON
            self.trade_history.update_position(self.active_position)
            
            self.logger.info(f"✅ {signal} position opened at {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            self.start_monitoring()
            return True
        
        return False
    
    def check_sl_tp(self, current_price):
        """Check if SL or TP is hit (called from WebSocket)"""
        if not self.active_position:
            return
        
        position = self.active_position
        
        if position['side'] == 'LONG':
            if current_price <= position['sl']:
                self.logger.info(f"🔴 STOP LOSS HIT at {current_price:.2f}")
                self._close_position()
            elif current_price >= position['tp']:
                self.logger.info(f"🟢 TAKE PROFIT HIT at {current_price:.2f}")
                self._close_position()
        else:  # SHORT
            if current_price >= position['sl']:
                self.logger.info(f"🔴 STOP LOSS HIT at {current_price:.2f}")
                self._close_position()
            elif current_price <= position['tp']:
                self.logger.info(f"🟢 TAKE PROFIT HIT at {current_price:.2f}")
                self._close_position()
    
    def start_monitoring(self):
        """Start monitoring in background (for REST fallback)"""
        if self.monitoring:
            return
        
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def _monitor_loop(self):
        """Monitor loop for REST fallback (every 5 seconds)"""
        while self.monitoring and self.active_position:
            try:
                current_price = self.binance.get_current_price()
                self.check_sl_tp(current_price)
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _close_position(self):
        """Close the current position and record to JSON"""
        if not self.active_position:
            return
        
        current_price = self.binance.get_current_price()
        
        # Calculate PnL
        if self.active_position['side'] == 'LONG':
            pnl = (current_price - self.active_position['entry']) * QUANTITY
        else:  # SHORT
            pnl = (self.active_position['entry'] - current_price) * QUANTITY
        
        # Determine exit reason
        if current_price <= self.active_position.get('sl', 0) or current_price >= self.active_position.get('sl', float('inf')):
            exit_reason = 'STOP_LOSS'
        elif current_price >= self.active_position.get('tp', float('inf')) or current_price <= self.active_position.get('tp', 0):
            exit_reason = 'TAKE_PROFIT'
        else:
            exit_reason = 'MANUAL'
        
        # Record to JSON history
        trade_record = self.trade_history.close_position(
            exit_price=current_price,
            pnl=pnl,
            exit_reason=exit_reason
        )
        
        # Close real position
        if not self.active_position.get('paper', False):
            self.binance.close_position()
        
        # Log to text file
        self.logger.info(f"🔒 Position closed | Exit: ${current_price:.2f} | PnL: ${pnl:.2f} | Reason: {exit_reason}")
        
        # Clear active position
        self.active_position = None
        self.monitoring = False