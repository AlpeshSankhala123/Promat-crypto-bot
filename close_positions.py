#!/usr/bin/env python3
"""
Close all active positions on Binance Testnet
Run this to manually close any open trades
"""

import time
from binance.client import Client
from modules.binance_client import BinanceTrader
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BN_TESTNET, SYMBOL

class PositionCloser:
    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BN_TESTNET)
        self.symbol = SYMBOL
        self.trader = BinanceTrader()
        
    def get_all_balances(self):
        """Get all asset balances"""
        try:
            account = self.client.get_account()
            balances = []
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })
            return balances
        except Exception as e:
            print(f"❌ Error getting balances: {e}")
            return []
    
    def get_open_orders(self):
        """Get all open orders"""
        try:
            orders = self.client.get_open_orders(symbol=self.symbol)
            return orders
        except Exception as e:
            print(f"❌ Error getting open orders: {e}")
            return []
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            orders = self.get_open_orders()
            if orders:
                print(f"\n📋 Found {len(orders)} open orders:")
                for order in orders:
                    print(f"   - Order #{order['orderId']}: {order['side']} {order['type']} {order['quantity']} {self.symbol}")
                
                # Cancel all orders
                result = self.client.cancel_open_orders(symbol=self.symbol)
                print(f"\n✅ Cancelled all {len(orders)} open orders")
                return True
            else:
                print("✅ No open orders to cancel")
                return True
        except Exception as e:
            print(f"❌ Error cancelling orders: {e}")
            return False
    
    def close_btc_position(self):
        """Close BTC position by selling all BTC balance"""
        try:
            # Get BTC balance
            account = self.client.get_account()
            btc_balance = 0
            for balance in account['balances']:
                if balance['asset'] == 'BTC':
                    btc_balance = float(balance['free'])
                    break
            
            if btc_balance > 0.0001:  # Minimum dust amount
                print(f"\n💰 Found BTC balance: {btc_balance} BTC")
                print(f"   Current BTC price: ${self.get_current_price():.2f}")
                print(f"   Value: ${btc_balance * self.get_current_price():.2f}")
                
                # Sell all BTC
                order = self.client.order_market_sell(
                    symbol=self.symbol,
                    quantity=btc_balance
                )
                print(f"\n✅ SOLD {btc_balance} BTC at market price")
                print(f"   Order ID: {order['orderId']}")
                return True
            else:
                print("✅ No BTC position to close")
                return True
                
        except Exception as e:
            print(f"❌ Error closing BTC position: {e}")
            return False
    
    def close_usdt_position(self):
        """Close USDT position (for short positions)"""
        try:
            # This is for short positions - would need to buy BTC with USDT
            # For testnet simplicity, we just warn if USDT is low
            account = self.client.get_account()
            usdt_balance = 0
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                    break
            
            print(f"\n💰 USDT Balance: ${usdt_balance:.2f}")
            
            # Check if USDT balance is significantly lower than initial
            # This could indicate a short position
            if usdt_balance < 9000:  # Assuming started with 10000
                print("⚠️ Low USDT balance detected - possible short position")
                print("   To close short position, you would need to BUY BTC")
                response = input("   Do you want to buy BTC to close short? (y/n): ")
                if response.lower() == 'y':
                    btc_price = self.get_current_price()
                    btc_to_buy = (10000 - usdt_balance) / btc_price
                    if btc_to_buy > 0:
                        order = self.client.order_market_buy(
                            symbol=self.symbol,
                            quantity=btc_to_buy
                        )
                        print(f"✅ BOUGHT {btc_to_buy} BTC at ${btc_price:.2f}")
                        return True
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_current_price(self):
        """Get current BTC price"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except:
            return 0
    
    def show_summary(self):
        """Display current position summary"""
        print("\n" + "="*60)
        print("📊 CURRENT POSITION SUMMARY")
        print("="*60)
        
        # Show balances
        balances = self.get_all_balances()
        print("\n💼 Asset Balances:")
        for bal in balances:
            if bal['asset'] in ['BTC', 'USDT']:
                print(f"   {bal['asset']}: {bal['free']:.8f} (Free) | {bal['locked']:.8f} (Locked) | Total: {bal['total']:.8f}")
        
        # Show open orders
        orders = self.get_open_orders()
        if orders:
            print(f"\n📋 Open Orders ({len(orders)}):")
            for order in orders:
                print(f"   - {order['side']} {order['type']} {order['quantity']} @ ${float(order['price']):.2f}")
        else:
            print("\n✅ No open orders")
        
        # Check if position exists
        btc_balance = 0
        for bal in balances:
            if bal['asset'] == 'BTC':
                btc_balance = bal['total']
                break
        
        if btc_balance > 0.0001:
            current_price = self.get_current_price()
            print(f"\n⚠️ ACTIVE POSITION DETECTED:")
            print(f"   BTC Amount: {btc_balance:.8f} BTC")
            print(f"   Current Value: ${btc_balance * current_price:.2f}")
        else:
            print("\n✅ No active BTC position")
        
        print("="*60)
    
    def close_all(self):
        """Close all positions and cancel all orders"""
        print("\n" + "🔴 CLOSING ALL POSITIONS 🔴".center(60))
        
        # Show current status
        self.show_summary()
        
        # Confirm
        print("\n⚠️  WARNING: This will close ALL open positions and cancel ALL orders!")
        response = input("Are you sure? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return False
        
        print("\n🔄 Closing all positions...")
        
        # 1. Cancel all open orders
        print("\n1️⃣ Cancelling all open orders...")
        self.cancel_all_orders()
        
        # 2. Close BTC position (if any)
        print("\n2️⃣ Closing BTC position...")
        self.close_btc_position()
        
        # 3. Close USDT position (if needed)
        print("\n3️⃣ Checking USDT position...")
        self.close_usdt_position()
        
        # 4. Final summary
        time.sleep(2)
        print("\n✅ Position closing complete!")
        self.show_summary()
        
        # 5. Reset JSON state file
        reset = input("\nReset bot state file? (y/n): ")
        if reset.lower() == 'y':
            import json
            from datetime import datetime
            state = {
                "active_position": None,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "last_update": datetime.now().isoformat()
            }
            with open('data/bot_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            print("✅ Bot state file reset")
        
        return True

def main():
    print("🚀 Binance Position Closer Tool".center(60))
    print(f"🌐 Network: {'TESTNET' if BN_TESTNET else 'MAINNET'}")
    print(f"📊 Symbol: {SYMBOL}")
    
    closer = PositionCloser()
    
    # Parse command line arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            # Auto close without confirmation
            print("\n🤖 Auto-closing mode...")
            closer.cancel_all_orders()
            closer.close_btc_position()
            closer.close_usdt_position()
            closer.show_summary()
        elif sys.argv[1] == '--show':
            # Just show current status
            closer.show_summary()
        elif sys.argv[1] == '--cancel-orders':
            # Just cancel orders
            closer.cancel_all_orders()
        else:
            print("\nUsage:")
            print("  python close_positions.py           # Interactive mode")
            print("  python close_positions.py --auto     # Auto-close without confirmation")
            print("  python close_positions.py --show     # Show current status only")
            print("  python close_positions.py --cancel-orders  # Cancel orders only")
    else:
        # Interactive mode
        closer.close_all()

if __name__ == "__main__":
    main()