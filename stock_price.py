"""
Real-time Stock Price Module
Fetches live stock prices from Yahoo Finance (100% free, no API key needed)
Supports multiple exchanges: NYSE, NASDAQ, TSX, BSE, NSE, and more
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import time


# Cache to avoid rate limiting
_price_cache = {}
_cache_duration = 60  # seconds


# Exchange suffix mapping for Yahoo Finance
EXCHANGE_SUFFIXES = {
    'TSX': '.TO',          # Toronto Stock Exchange
    'TSXV': '.V',          # TSX Venture Exchange
    'BSE': '.BO',          # Bombay Stock Exchange
    'NSE': '.NS',          # National Stock Exchange of India
    'LSE': '.L',           # London Stock Exchange
    'ASX': '.AX',          # Australian Securities Exchange
    'HKEX': '.HK',         # Hong Kong Exchange
    'NYSE': '',            # No suffix needed
    'NASDAQ': ''           # No suffix needed
}


def format_symbol_for_exchange(symbol, exchange='NYSE'):
    """
    Format stock symbol with proper exchange suffix for Yahoo Finance
    
    Args:
        symbol (str): Base stock ticker
        exchange (str): Exchange name
        
    Returns:
        str: Formatted symbol for Yahoo Finance
    
    Examples:
        format_symbol_for_exchange('SHOP', 'TSX') -> 'SHOP.TO'
        format_symbol_for_exchange('RELIANCE', 'NSE') -> 'RELIANCE.NS'
        format_symbol_for_exchange('AAPL', 'NASDAQ') -> 'AAPL'
    """
    symbol = symbol.upper().strip()
    exchange = exchange.upper().strip()
    
    # If symbol already has a suffix, return as is
    if any(symbol.endswith(suffix) for suffix in EXCHANGE_SUFFIXES.values() if suffix):
        return symbol
    
    # Add appropriate suffix
    suffix = EXCHANGE_SUFFIXES.get(exchange, '')
    return f"{symbol}{suffix}"


def get_live_price(symbol):
    """
    Get real-time stock price from Yahoo Finance with caching to avoid rate limits
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: {
            'success': bool,
            'data': dict with price info,
            'error': str (if success=False)
        }
    """
    # Check cache first
    cache_key = f"price_{symbol}"
    if cache_key in _price_cache:
        cached_data, cached_time = _price_cache[cache_key]
        if (datetime.now() - cached_time).seconds < _cache_duration:
            return cached_data
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Use fast_info for basic price data (less likely to be rate limited)
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            fast_info = ticker.fast_info
            current_price = fast_info.get('lastPrice') or fast_info.get('regularMarketPrice')
            previous_close = fast_info.get('previousClose')
            
            if current_price is None:
                # Fallback to history if fast_info fails
                hist = ticker.history(period='5d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        except:
            # Final fallback to history
            hist = ticker.history(period='5d')
            if hist.empty:
                return {
                    'success': False,
                    'data': None,
                    'error': f'No price data found for {symbol}'
                }
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        if current_price is None:
            return {
                'success': False,
                'data': None,
                'error': f'No price data found for {symbol}'
            }
        
        # Calculate change
        change = current_price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        # Try to get additional info (with error handling for rate limits)
        info_data = {}
        try:
            info = ticker.info
            info_data = {
                'open': info.get('open') or info.get('regularMarketOpen'),
                'high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield'),
                'company_name': info.get('longName') or info.get('shortName'),
                'exchange': info.get('exchange'),
                'currency': info.get('currency', 'USD')
            }
        except:
            # If info fails, use minimal data from history
            hist = ticker.history(period='1d')
            if not hist.empty:
                info_data = {
                    'open': hist['Open'].iloc[-1],
                    'high': hist['High'].iloc[-1],
                    'low': hist['Low'].iloc[-1],
                    'volume': hist['Volume'].iloc[-1],
                    'market_cap': None,
                    'pe_ratio': None,
                    'dividend_yield': None,
                    'company_name': symbol,
                    'exchange': 'Unknown',
                    'currency': 'USD'
                }
        
        result = {
            'success': True,
            'data': {
                'symbol': symbol,
                'price': float(current_price),
                'previous_close': float(previous_close) if previous_close else None,
                'change': float(change),
                'change_percent': float(change_percent),
                **info_data,
                'timestamp': datetime.now().isoformat()
            },
            'error': None
        }
        
        # Cache the result
        _price_cache[cache_key] = (result, datetime.now())
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            # Try to get from cache even if expired
            if cache_key in _price_cache:
                cached_data, _ = _price_cache[cache_key]
                cached_data['data']['timestamp'] = f"{cached_data['data']['timestamp']} (cached)"
                return cached_data
            
            return {
                'success': False,
                'data': None,
                'error': 'Rate limit reached. Please wait a moment and try again.'
            }
        
        return {
            'success': False,
            'data': None,
            'error': f'Error fetching price: {error_msg}'
        }


def get_historical_data(symbol, period='1mo', interval='1d'):
    """
    Get historical price data for charts with caching
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
        interval (str): '1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'
        
    Returns:
        dict: {
            'success': bool,
            'data': pandas.DataFrame with OHLCV data,
            'error': str (if success=False)
        }
    """
    # Check cache
    cache_key = f"hist_{symbol}_{period}_{interval}"
    if cache_key in _price_cache:
        cached_data, cached_time = _price_cache[cache_key]
        if (datetime.now() - cached_time).seconds < _cache_duration * 5:  # Cache longer for historical
            return cached_data
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval, timeout=10)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.3)
        
        if hist.empty:
            return {
                'success': False,
                'data': None,
                'error': f'No historical data found for {symbol}'
            }
        
        result = {
            'success': True,
            'data': hist,
            'error': None
        }
        
        # Cache the result
        _price_cache[cache_key] = (result, datetime.now())
        
        return result
        
    except Exception as e:
        # Try cache even if expired
        if cache_key in _price_cache:
            cached_data, _ = _price_cache[cache_key]
            return cached_data
        
        return {
            'success': False,
            'data': None,
            'error': f'Error fetching historical data: {str(e)}'
        }


def get_company_info(symbol):
    """
    Get detailed company information
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: Company information
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'success': True,
            'data': {
                'name': info.get('longName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'description': info.get('longBusinessSummary'),
                'website': info.get('website'),
                'employees': info.get('fullTimeEmployees'),
                'country': info.get('country'),
                'city': info.get('city')
            },
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': f'Error fetching company info: {str(e)}'
        }


def get_exchange_info(symbol):
    """
    Get exchange information for the stock
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: Exchange information
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        exchange_name = info.get('exchange', 'Unknown')
        
        # Map exchange codes to full names
        exchange_map = {
            'NMS': 'NASDAQ',
            'NYQ': 'NYSE (New York Stock Exchange)',
            'ASE': 'NYSE American',
            'PCX': 'NYSE Arca',
            'NGM': 'NASDAQ Global Market',
            'NAS': 'NASDAQ',
            'TOR': 'TSX (Toronto Stock Exchange)',
            'TSX': 'TSX (Toronto Stock Exchange)',
            'NEO': 'NEO Exchange (Canada)',
            'CNQ': 'Canadian Securities Exchange',
            'BSE': 'BSE (Bombay Stock Exchange)',
            'NSE': 'NSE (National Stock Exchange of India)',
            'NSI': 'NSE India',
            'BOM': 'BSE (Bombay Stock Exchange)',
            'LSE': 'London Stock Exchange',
            'TSE': 'Tokyo Stock Exchange',
            'HKG': 'Hong Kong Stock Exchange',
            'FRA': 'Frankfurt Stock Exchange'
        }
        
        full_exchange_name = exchange_map.get(exchange_name, exchange_name)
        
        return {
            'success': True,
            'exchange': full_exchange_name,
            'currency': info.get('currency', 'USD'),
            'timezone': info.get('exchangeTimezoneName', 'America/New_York')
        }
        
    except Exception as e:
        return {
            'success': False,
            'exchange': 'Unknown',
            'error': f'Error fetching exchange info: {str(e)}'
        }
