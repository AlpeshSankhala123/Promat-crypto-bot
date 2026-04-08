from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BN_TESTNET

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BN_TESTNET)

print("Testing API Permissions...")
print("="*50)

# Test 1: Read account info
try:
    account = client.get_account()
    print("✅ Read permission: WORKING")
except Exception as e:
    print(f"❌ Read permission: FAILED - {e}")

# Test 2: Check if can place a TEST order (doesn't execute)
try:
    test_order = client.create_test_order(
        symbol='BTCUSDT',
        side='SELL',
        type='MARKET',
        quantity=0.001
    )
    print("✅ Trading permission: WORKING (test order succeeded)")
except Exception as e:
    print(f"❌ Trading permission: FAILED - {e}")
    print("\n🔧 FIX: Enable 'Spot & Margin Trading' in Testnet API settings")
    print("   https://testnet.binance.vision/")

# Test 3: Check balance
try:
    for balance in account['balances']:
        if balance['asset'] in ['BTC', 'USDT']:
            print(f"💰 {balance['asset']}: {balance['free']}")
except:
    pass