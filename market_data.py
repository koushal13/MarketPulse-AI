"""
Market Data Module
Fetches real-time price data and technical indicators using FMP and Alpha Vantage APIs
"""

import requests
from config import (
    FMP_KEY, FMP_API_BASE_URL,
    ALPHA_VANTAGE_KEY, ALPHA_VANTAGE_BASE_URL,
    REQUEST_TIMEOUT
)

# Backwards compatibility
FMP_API_KEY = FMP_KEY
ALPHA_VANTAGE_API_KEY = ALPHA_VANTAGE_KEY


def get_quote_fmp(symbol):
    """
    Fetch current price quote from Financial Modeling Prep
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: {
            'success': bool,
            'data': dict with 'price', 'change', 'changesPercentage', 'volume',
            'error': str (if success=False)
        }
    """
    if not FMP_API_KEY:
        return {
            'success': False,
            'data': None,
            'error': 'FMP_API_KEY not configured'
        }
    
    try:
        url = f"{FMP_API_BASE_URL}/quote/{symbol}"
        params = {'apikey': FMP_API_KEY}
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 429:
            return {
                'success': False,
                'data': None,
                'error': 'Rate limit exceeded for FMP API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                'success': False,
                'data': None,
                'error': f'No quote data found for {symbol}'
            }
        
        quote = data[0]
        return {
            'success': True,
            'data': {
                'symbol': quote.get('symbol'),
                'price': quote.get('price'),
                'change': quote.get('change'),
                'changesPercentage': quote.get('changesPercentage'),
                'volume': quote.get('volume'),
                'marketCap': quote.get('marketCap'),
                'timestamp': quote.get('timestamp')
            },
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'data': None,
            'error': f'FMP API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': f'Unexpected error: {str(e)}'
        }


def get_rsi_fmp(symbol, period='1day', timeperiod=14):
    """
    Fetch RSI (Relative Strength Index) from FMP
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): Time period ('1min', '5min', '15min', '30min', '1hour', '4hour', '1day')
        timeperiod (int): RSI calculation period (default 14)
        
    Returns:
        dict: {
            'success': bool,
            'rsi': float (current RSI value),
            'error': str (if success=False)
        }
    """
    if not FMP_API_KEY:
        return {
            'success': False,
            'rsi': None,
            'error': 'FMP_API_KEY not configured'
        }
    
    try:
        url = f"{FMP_API_BASE_URL}/technical_indicator/{period}/{symbol}"
        params = {
            'type': 'rsi',
            'period': timeperiod,
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 429:
            return {
                'success': False,
                'rsi': None,
                'error': 'Rate limit exceeded for FMP API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                'success': False,
                'rsi': None,
                'error': f'No RSI data available for {symbol}'
            }
        
        # Get the most recent RSI value
        latest_rsi = data[0].get('rsi')
        
        return {
            'success': True,
            'rsi': float(latest_rsi) if latest_rsi is not None else None,
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'rsi': None,
            'error': f'FMP API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'rsi': None,
            'error': f'Unexpected error: {str(e)}'
        }


def get_macd_fmp(symbol, period='1day'):
    """
    Fetch MACD (Moving Average Convergence Divergence) from FMP
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): Time period
        
    Returns:
        dict: {
            'success': bool,
            'macd': float (MACD line),
            'signal': float (Signal line),
            'histogram': float (MACD - Signal),
            'error': str (if success=False)
        }
    """
    if not FMP_API_KEY:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': 'FMP_API_KEY not configured'
        }
    
    try:
        url = f"{FMP_API_BASE_URL}/technical_indicator/{period}/{symbol}"
        params = {
            'type': 'macd',
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 429:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': 'Rate limit exceeded for FMP API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': f'No MACD data available for {symbol}'
            }
        
        # Get the most recent MACD values
        latest = data[0]
        macd_line = latest.get('macd')
        signal_line = latest.get('signal')
        histogram = latest.get('histogram')
        
        return {
            'success': True,
            'macd': float(macd_line) if macd_line is not None else None,
            'signal': float(signal_line) if signal_line is not None else None,
            'histogram': float(histogram) if histogram is not None else None,
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': f'FMP API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': f'Unexpected error: {str(e)}'
        }


def get_rsi_alpha_vantage(symbol, interval='daily', time_period=14):
    """
    Fetch RSI from Alpha Vantage (fallback if FMP fails)
    
    Args:
        symbol (str): Stock ticker symbol
        interval (str): 'daily', 'weekly', 'monthly', '1min', '5min', '15min', '30min', '60min'
        time_period (int): RSI calculation period
        
    Returns:
        dict: {
            'success': bool,
            'rsi': float,
            'error': str (if success=False)
        }
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            'success': False,
            'rsi': None,
            'error': 'ALPHA_VANTAGE_API_KEY not configured'
        }
    
    try:
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 429:
            return {
                'success': False,
                'rsi': None,
                'error': 'Rate limit exceeded for Alpha Vantage API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Check for error messages
        if 'Error Message' in data:
            return {
                'success': False,
                'rsi': None,
                'error': f'Alpha Vantage error: {data["Error Message"]}'
            }
        
        if 'Note' in data:
            return {
                'success': False,
                'rsi': None,
                'error': 'Alpha Vantage API call frequency limit reached'
            }
        
        # Extract RSI data
        technical_data = data.get('Technical Analysis: RSI', {})
        if not technical_data:
            return {
                'success': False,
                'rsi': None,
                'error': 'No RSI data available'
            }
        
        # Get the most recent date's RSI
        latest_date = sorted(technical_data.keys(), reverse=True)[0]
        rsi_value = technical_data[latest_date].get('RSI')
        
        return {
            'success': True,
            'rsi': float(rsi_value) if rsi_value else None,
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'rsi': None,
            'error': f'Alpha Vantage API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'rsi': None,
            'error': f'Unexpected error: {str(e)}'
        }


def get_macd_alpha_vantage(symbol, interval='daily'):
    """
    Fetch MACD from Alpha Vantage (fallback if FMP fails)
    
    Args:
        symbol (str): Stock ticker symbol
        interval (str): Time interval
        
    Returns:
        dict: {
            'success': bool,
            'macd': float,
            'signal': float,
            'histogram': float,
            'error': str (if success=False)
        }
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': 'ALPHA_VANTAGE_API_KEY not configured'
        }
    
    try:
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'series_type': 'close',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 429:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': 'Rate limit exceeded for Alpha Vantage API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Check for error messages
        if 'Error Message' in data:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': f'Alpha Vantage error: {data["Error Message"]}'
            }
        
        if 'Note' in data:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': 'Alpha Vantage API call frequency limit reached'
            }
        
        # Extract MACD data
        technical_data = data.get('Technical Analysis: MACD', {})
        if not technical_data:
            return {
                'success': False,
                'macd': None,
                'signal': None,
                'histogram': None,
                'error': 'No MACD data available'
            }
        
        # Get the most recent date's MACD
        latest_date = sorted(technical_data.keys(), reverse=True)[0]
        latest = technical_data[latest_date]
        
        macd_line = latest.get('MACD')
        signal_line = latest.get('MACD_Signal')
        histogram = latest.get('MACD_Hist')
        
        return {
            'success': True,
            'macd': float(macd_line) if macd_line else None,
            'signal': float(signal_line) if signal_line else None,
            'histogram': float(histogram) if histogram else None,
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': f'Alpha Vantage API error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'macd': None,
            'signal': None,
            'histogram': None,
            'error': f'Unexpected error: {str(e)}'
        }


def get_technical_indicators(symbol):
    """
    Fetch all technical indicators (RSI and MACD) with fallback logic
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: {
            'success': bool,
            'rsi': float,
            'macd': dict with 'macd', 'signal', 'histogram',
            'quote': dict with price info,
            'errors': list of error messages
        }
    """
    errors = []
    
    # Get current quote
    quote_result = get_quote_fmp(symbol)
    quote_data = quote_result.get('data') if quote_result['success'] else None
    if not quote_result['success']:
        errors.append(f"Quote: {quote_result['error']}")
    
    # Try to get RSI from FMP first
    rsi_result = get_rsi_fmp(symbol)
    rsi_value = rsi_result.get('rsi')
    
    # If FMP fails, try Alpha Vantage
    if not rsi_result['success']:
        errors.append(f"RSI (FMP): {rsi_result['error']}")
        rsi_result_av = get_rsi_alpha_vantage(symbol)
        rsi_value = rsi_result_av.get('rsi')
        if not rsi_result_av['success']:
            errors.append(f"RSI (Alpha Vantage): {rsi_result_av['error']}")
    
    # Try to get MACD from FMP first
    macd_result = get_macd_fmp(symbol)
    macd_data = {
        'macd': macd_result.get('macd'),
        'signal': macd_result.get('signal'),
        'histogram': macd_result.get('histogram')
    }
    
    # If FMP fails, try Alpha Vantage
    if not macd_result['success']:
        errors.append(f"MACD (FMP): {macd_result['error']}")
        macd_result_av = get_macd_alpha_vantage(symbol)
        macd_data = {
            'macd': macd_result_av.get('macd'),
            'signal': macd_result_av.get('signal'),
            'histogram': macd_result_av.get('histogram')
        }
        if not macd_result_av['success']:
            errors.append(f"MACD (Alpha Vantage): {macd_result_av['error']}")
    
    # Determine overall success
    success = (rsi_value is not None or 
               macd_data['macd'] is not None or 
               quote_data is not None)
    
    return {
        'success': success,
        'rsi': rsi_value,
        'macd': macd_data,
        'quote': quote_data,
        'errors': errors if errors else None
    }
