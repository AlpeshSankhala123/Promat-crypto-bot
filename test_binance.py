from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

print(f"API Key: {api_key[:20]}...")
print("Connecting to TESTNET...")

# Connect to testnet
client = Client(api_key, api_secret, testnet=True)

try:
    # Test connection by getting account info (without assuming 'accountId')
    account = client.get_account()
    print("✅ Successfully connected to TESTNET!")
    
    # Safely check for account identifier
    if hasattr(account, 'accountId'):
        print(f"   Account ID: {account['accountId']}")
    else:
        print("   Account ID: (not provided by testnet)")
    
    # Check balances (this always works)
    balances = account['balances']
    usdt_balance = next((b for b in balances if b['asset'] == 'USDT'), None)
    btc_balance = next((b for b in balances if b['asset'] == 'BTC'), None)
    
    print(f"   USDT Balance: {usdt_balance['free'] if usdt_balance else 0}")
    print(f"   BTC Balance: {btc_balance['free'] if btc_balance else 0}")
    
    # Test market data
    price = client.get_symbol_ticker(symbol='BTCUSDT')
    print(f"   BTCUSDT Price: {price['price']}")
    
    # Test trade permission with a TEST order (doesn't execute)
    try:
        order = client.create_test_order(
            symbol='BTCUSDT',
            side='BUY',
            type='MARKET',
            quantity=0.001
        )
        print("✅ Trading permission: WORKING on testnet!")
    except Exception as e:
        print(f"⚠️ Test order failed: {e}")
        
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nMake sure you're using TESTNET API keys from:")
    print("https://testnet.binance.vision/")