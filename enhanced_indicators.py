"""
Enhanced Technical Indicators Module
Uses TA library for better MACD and other indicators when API data is unavailable
"""

import pandas as pd
try:
    from ta.trend import MACD, ADXIndicator, EMAIndicator, SMAIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.volatility import BollingerBands, AverageTrueRange
    from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


def calculate_macd_from_prices(prices_df):
    """
    Calculate MACD from price data using TA library
    
    Args:
        prices_df: DataFrame with 'Close' prices
        
    Returns:
        dict: MACD data or None
    """
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        macd = MACD(close=prices_df['Close'])
        
        # Get the most recent values
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        histogram = macd.macd_diff().iloc[-1]
        
        return {
            'macd': float(macd_line),
            'signal': float(signal_line),
            'histogram': float(histogram)
        }
    except Exception as e:
        print(f"Error calculating MACD: {e}")
        return None


def calculate_rsi_from_prices(prices_df, period=14):
    """
    Calculate RSI from price data using TA library
    
    Args:
        prices_df: DataFrame with 'Close' prices
        period: RSI period (default 14)
        
    Returns:
        float: RSI value or None
    """
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        rsi = RSIIndicator(close=prices_df['Close'], window=period)
        rsi_value = rsi.rsi().iloc[-1]
        return float(rsi_value)
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return None


def calculate_bollinger_bands(prices_df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        bb = BollingerBands(close=prices_df['Close'], window=period, window_dev=std_dev)
        return {
            'upper': float(bb.bollinger_hband().iloc[-1]),
            'middle': float(bb.bollinger_mavg().iloc[-1]),
            'lower': float(bb.bollinger_lband().iloc[-1]),
            'percent_b': float(bb.bollinger_pband().iloc[-1])  # Position within bands
        }
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {e}")
        return None


def calculate_stochastic(prices_df, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        if 'High' not in prices_df.columns or 'Low' not in prices_df.columns:
            return None
        stoch = StochasticOscillator(
            high=prices_df['High'], 
            low=prices_df['Low'], 
            close=prices_df['Close'],
            window=k_period,
            smooth_window=d_period
        )
        return {
            'k': float(stoch.stoch().iloc[-1]),
            'd': float(stoch.stoch_signal().iloc[-1])
        }
    except Exception as e:
        print(f"Error calculating Stochastic: {e}")
        return None


def calculate_adx(prices_df, period=14):
    """Calculate ADX (Average Directional Index) - trend strength"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        if 'High' not in prices_df.columns or 'Low' not in prices_df.columns:
            return None
        adx = ADXIndicator(
            high=prices_df['High'],
            low=prices_df['Low'],
            close=prices_df['Close'],
            window=period
        )
        return {
            'adx': float(adx.adx().iloc[-1]),
            'di_plus': float(adx.adx_pos().iloc[-1]),
            'di_minus': float(adx.adx_neg().iloc[-1])
        }
    except Exception as e:
        print(f"Error calculating ADX: {e}")
        return None


def calculate_moving_averages(prices_df):
    """Calculate key moving averages"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        current_price = float(prices_df['Close'].iloc[-1])
        
        # EMAs
        ema_12 = EMAIndicator(close=prices_df['Close'], window=12).ema_indicator().iloc[-1]
        ema_26 = EMAIndicator(close=prices_df['Close'], window=26).ema_indicator().iloc[-1]
        ema_50 = EMAIndicator(close=prices_df['Close'], window=50).ema_indicator().iloc[-1] if len(prices_df) >= 50 else None
        
        # SMAs
        sma_20 = SMAIndicator(close=prices_df['Close'], window=20).sma_indicator().iloc[-1]
        sma_50 = SMAIndicator(close=prices_df['Close'], window=50).sma_indicator().iloc[-1] if len(prices_df) >= 50 else None
        sma_200 = SMAIndicator(close=prices_df['Close'], window=200).sma_indicator().iloc[-1] if len(prices_df) >= 200 else None
        
        return {
            'ema_12': float(ema_12),
            'ema_26': float(ema_26),
            'ema_50': float(ema_50) if ema_50 else None,
            'sma_20': float(sma_20),
            'sma_50': float(sma_50) if sma_50 else None,
            'sma_200': float(sma_200) if sma_200 else None,
            'price': current_price,
            'above_sma_20': current_price > sma_20,
            'above_sma_50': current_price > sma_50 if sma_50 else None,
            'above_sma_200': current_price > sma_200 if sma_200 else None
        }
    except Exception as e:
        print(f"Error calculating Moving Averages: {e}")
        return None


def calculate_atr(prices_df, period=14):
    """Calculate Average True Range (volatility)"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        if 'High' not in prices_df.columns or 'Low' not in prices_df.columns:
            return None
        atr = AverageTrueRange(
            high=prices_df['High'],
            low=prices_df['Low'],
            close=prices_df['Close'],
            window=period
        )
        return float(atr.average_true_range().iloc[-1])
    except Exception as e:
        print(f"Error calculating ATR: {e}")
        return None


def calculate_obv(prices_df):
    """Calculate On-Balance Volume"""
    if not TA_AVAILABLE or prices_df is None or prices_df.empty:
        return None
    
    try:
        if 'Volume' not in prices_df.columns:
            return None
        obv = OnBalanceVolumeIndicator(close=prices_df['Close'], volume=prices_df['Volume'])
        return float(obv.on_balance_volume().iloc[-1])
    except Exception as e:
        print(f"Error calculating OBV: {e}")
        return None


def get_enhanced_technical_indicators(symbol, hist_data=None):
    """
    Get technical indicators with fallback to calculated values
    ALWAYS calculates from price data when available for reliability
    
    Args:
        symbol: Stock symbol
        hist_data: Historical price DataFrame (optional)
        
    Returns:
        dict: Enhanced technical indicators
    """
    from market_data import get_technical_indicators
    
    # Initialize result structure
    result = {
        'success': False,
        'rsi': None,
        'macd': {},
        'bollinger': None,
        'stochastic': None,
        'adx': None,
        'moving_averages': None,
        'atr': None,
        'obv': None,
        'errors': []
    }
    
    # Track calculation sources
    calculated = []
    
    # If we have historical data, ALWAYS calculate from it (most reliable!)
    if hist_data is not None and not hist_data.empty and len(hist_data) >= 26:
        print(f"📊 Calculating indicators from {len(hist_data)} price points...")
        
        # Calculate MACD
        calculated_macd = calculate_macd_from_prices(hist_data)
        if calculated_macd:
            result['macd'] = calculated_macd
            calculated.append('MACD')
            result['success'] = True
        
        # Calculate RSI
        calculated_rsi = calculate_rsi_from_prices(hist_data)
        if calculated_rsi:
            result['rsi'] = calculated_rsi
            calculated.append('RSI')
            result['success'] = True
        
        # Calculate Bollinger Bands
        bollinger = calculate_bollinger_bands(hist_data)
        if bollinger:
            result['bollinger'] = bollinger
            calculated.append('BB')
            result['success'] = True
        
        # Calculate Stochastic
        stochastic = calculate_stochastic(hist_data)
        if stochastic:
            result['stochastic'] = stochastic
            calculated.append('Stoch')
            result['success'] = True
        
        # Calculate ADX
        adx = calculate_adx(hist_data)
        if adx:
            result['adx'] = adx
            calculated.append('ADX')
            result['success'] = True
        
        # Calculate Moving Averages
        ma = calculate_moving_averages(hist_data)
        if ma:
            result['moving_averages'] = ma
            calculated.append('MA')
            result['success'] = True
        
        # Calculate ATR
        atr = calculate_atr(hist_data)
        if atr:
            result['atr'] = atr
            calculated.append('ATR')
            result['success'] = True
        
        # Calculate OBV
        obv = calculate_obv(hist_data)
        if obv:
            result['obv'] = obv
            calculated.append('OBV')
            result['success'] = True
    
    # Try API as backup only if we couldn't calculate core indicators
    if not result['success'] or result.get('rsi') is None or not result.get('macd'):
        print("  Trying API for missing indicators...")
        api_result = get_technical_indicators(symbol)
        
        # Use API data for what we're missing
        if result.get('rsi') is None and api_result.get('rsi'):
            result['rsi'] = api_result['rsi']
            calculated.append('RSI (API)')
        
        if not result.get('macd') and api_result.get('macd'):
            result['macd'] = api_result['macd']
            calculated.append('MACD (API)')
        
        if api_result.get('success'):
            result['success'] = True
    
    # Status message
    if calculated:
        result['calculation_source'] = ', '.join(calculated)
        print(f"  ✓ Got indicators from: {', '.join(calculated)}")
    
    # Clean up errors
    if result['success']:
        result['errors'] = None
    elif not result.get('rsi') and not result.get('macd'):
        result['errors'] = ['Unable to calculate indicators - insufficient data']
    
    return result
