from binance.client import Client
from binance.exceptions import BinanceAPIException
from config import BINANCE_API_KEY, BINANCE_API_SECRET, SYMBOL, QUANTITY, BN_TESTNET
import time

class BinanceTrader:
    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BN_TESTNET)
        self.symbol = SYMBOL
        self.network = "TESTNET" if BN_TESTNET else "MAINNET"
        print(f"💰 Binance Trader initialized on {self.network}")
    
    def get_klines(self, interval='5m', limit=200):
        """Get candlestick data (fallback for WebSocket)"""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            return klines
        except Exception as e:
            print(f"Error getting klines: {e}")
            return []
    
    def get_current_price(self):
        """Get current price (fallback)"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"Error getting price: {e}")
            return 0
    
    def get_account_balance(self):
        """Get USDT balance"""
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            return 0
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0
    
    def has_open_position(self):
        """Check if there's an open position"""
        try:
            # Check BTC balance
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == 'BTC':
                    btc_free = float(balance['free'])
                    if btc_free > 0.0001:  # Has BTC (long position)
                        return True
            
            # Check open orders
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            return len(open_orders) > 0
            
        except Exception as e:
            print(f"Error checking position: {e}")
            return False
    
    def place_market_order(self, side):
        """Place market order"""
        try:
            if side.upper() == 'BUY':
                order = self.client.order_market_buy(
                    symbol=self.symbol,
                    quantity=QUANTITY
                )
            elif side.upper() == 'SELL':
                # Sell all BTC balance
                account = self.client.get_account()
                btc_balance = 0
                for balance in account['balances']:
                    if balance['asset'] == 'BTC':
                        btc_balance = float(balance['free'])
                        break
                
                if btc_balance > 0:
                    order = self.client.order_market_sell(
                        symbol=self.symbol,
                        quantity=btc_balance
                    )
                else:
                    print("No BTC to sell")
                    return None
            else:
                return None
            
            print(f"✅ Order placed: {side} {QUANTITY} {self.symbol}")
            return order
            
        except BinanceAPIException as e:
            print(f"❌ Order failed: {e}")
            return None
    
    def close_position(self):
        """Close current position"""
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == 'BTC':
                    btc_balance = float(balance['free'])
                    if btc_balance > 0:
                        order = self.client.order_market_sell(
                            symbol=self.symbol,
                            quantity=btc_balance
                        )
                        print(f"✅ Position closed: sold {btc_balance} BTC")
                        return order
            print("No position to close")
            return None
        except Exception as e:
            print(f"Error closing position: {e}")
            return None