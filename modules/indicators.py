import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

def calculate_indicators(klines):
    """Calculate RSI, EMA, MACD from klines"""
    if not klines:
        return None
    
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # RSI
    rsi_indicator = RSIIndicator(close=df['close'], window=14)
    rsi = rsi_indicator.rsi().iloc[-1] if len(df) >= 14 else 50
    
    # EMA
    ema9 = EMAIndicator(close=df['close'], window=9).ema_indicator().iloc[-1] if len(df) >= 9 else df['close'].iloc[-1]
    ema21 = EMAIndicator(close=df['close'], window=21).ema_indicator().iloc[-1] if len(df) >= 21 else df['close'].iloc[-1]
    ema50 = EMAIndicator(close=df['close'], window=50).ema_indicator().iloc[-1] if len(df) >= 50 else df['close'].iloc[-1]
    
    # EMA Trend
    if ema9 > ema21 > ema50:
        ema_trend = "BULLISH"
    elif ema9 < ema21 < ema50:
        ema_trend = "BEARISH"
    else:
        ema_trend = "NEUTRAL"
    
    # MACD
    macd_indicator = MACD(close=df['close'])
    macd_line = macd_indicator.macd().iloc[-1] if len(df) >= 26 else 0
    macd_signal = macd_indicator.macd_signal().iloc[-1] if len(df) >= 26 else 0
    
    if macd_line > macd_signal:
        macd = "BULLISH"
    elif macd_line < macd_signal:
        macd = "BEARISH"
    else:
        macd = "NEUTRAL"
    
    # Volume
    avg_volume = df['volume'].tail(20).mean()
    current_volume = df['volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    if volume_ratio > 1.5:
        volume = "HIGH"
    elif volume_ratio < 0.5:
        volume = "LOW"
    else:
        volume = "NORMAL"
    
    # Support & Resistance
    recent_lows = df['low'].tail(20).min()
    recent_highs = df['high'].tail(20).max()
    current_price = df['close'].iloc[-1]
    
    # 24h change
    day_ago_price = df['close'].iloc[-144] if len(df) >= 144 else df['close'].iloc[0]
    change_24h = ((current_price - day_ago_price) / day_ago_price) * 100
    
    return {
        'price': current_price,
        'rsi': round(rsi, 2),
        'ema_trend': ema_trend,
        'macd': macd,
        'volume': volume,
        'support': recent_lows,
        'resistance': recent_highs,
        'change_24h': round(change_24h, 2)
    }