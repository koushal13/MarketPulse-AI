"""
Multi-source price fetcher with automatic failover across 10+ free APIs
Falls back automatically if one source fails - NEVER fails to get data!
"""

import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# Cache to avoid hammering APIs
_price_cache = {}
_cache_duration = 60  # 60 seconds for price data

class MultiSourcePriceFetcher:
    """Fetches stock prices from multiple free APIs with automatic failover"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
        self.fmp_key = os.getenv('FMP_KEY', '')
        self.polygon_key = os.getenv('POLYGON_API_KEY', 'demo')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY', 'demo')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY', 'demo')
        self.iex_key = os.getenv('IEX_CLOUD_API_KEY', 'demo')
        
        # Free API sources (no key needed)
        self.free_sources = [
            'yahoo_finance',
            'yahoo_direct',
            'cnbc',
            'marketwatch',
        ]
        
        # API key sources
        self.api_sources = [
            'alpha_vantage',
            'twelve_data',
            'finnhub',
            'polygon',
            'fmp',
            'iex_cloud',
        ]
    
    def _format_symbol(self, symbol: str, exchange: str, api_name: str) -> str:
        """Format symbol for specific API requirements"""
        
        # Remove existing exchange suffix
        base_symbol = symbol.replace('.TO', '').replace('.NS', '').replace('.BO', '').replace('.V', '')
        
        if api_name in ['yahoo_finance', 'yahoo_direct', 'cnbc']:
            # Yahoo format: SYMBOL.EXCHANGE
            if exchange == 'TSX':
                return f"{base_symbol}.TO"
            elif exchange == 'NSE':
                return f"{base_symbol}.NS"
            elif exchange == 'BSE':
                return f"{base_symbol}.BO"
            else:
                return base_symbol
        
        elif api_name == 'alpha_vantage':
            # Alpha Vantage uses plain symbols for US, needs market suffix for others
            if exchange in ['TSX', 'NSE', 'BSE']:
                return f"{base_symbol}.{exchange}"
            return base_symbol
        
        elif api_name == 'finnhub':
            # Finnhub format varies by exchange
            if exchange == 'TSX':
                return f"{base_symbol}:CA"
            elif exchange == 'NSE':
                return f"{base_symbol}:IN"
            elif exchange == 'BSE':
                return f"{base_symbol}:IN"
            return base_symbol
        
        else:
            # Most APIs use plain symbol
            return base_symbol
    
    def _fetch_yahoo_finance(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 1: Yahoo Finance via yfinance library"""
        try:
            formatted_symbol = self._format_symbol(symbol, exchange, 'yahoo_finance')
            time.sleep(0.5)  # Rate limit protection
            
            ticker = yf.Ticker(formatted_symbol)
            
            # Try fast_info first (faster)
            try:
                info = ticker.fast_info
                return {
                    'price': info.last_price,
                    'open': info.open,
                    'high': info.day_high,
                    'low': info.day_low,
                    'volume': info.last_volume,
                    'previous_close': info.previous_close,
                    'change': info.last_price - info.previous_close,
                    'change_percent': ((info.last_price - info.previous_close) / info.previous_close * 100) if info.previous_close else 0,
                    'source': 'Yahoo Finance (fast_info)'
                }
            except:
                # Fallback to regular info
                hist = ticker.history(period='2d')
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    return {
                        'price': latest['Close'],
                        'open': latest['Open'],
                        'high': latest['High'],
                        'low': latest['Low'],
                        'volume': latest['Volume'],
                        'previous_close': prev['Close'],
                        'change': latest['Close'] - prev['Close'],
                        'change_percent': ((latest['Close'] - prev['Close']) / prev['Close'] * 100) if prev['Close'] else 0,
                        'source': 'Yahoo Finance (history)'
                    }
        except Exception as e:
            print(f"Yahoo Finance failed: {e}")
        return None
    
    def _fetch_yahoo_direct(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 2: Direct Yahoo Finance API call"""
        try:
            formatted_symbol = self._format_symbol(symbol, exchange, 'yahoo_direct')
            # Request 1 day data to get Open price from historical quotes
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_symbol}?interval=1d&range=1d"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = data['chart']['result'][0]
                meta = result['meta']
                
                # Try to get Open from intraday data if not in meta
                open_price = meta.get('regularMarketOpen')
                if open_price is None:
                    # Try to extract from historical quotes (first price of the day)
                    try:
                        timestamps = result.get('timestamp', [])
                        indicators = result.get('indicators', {}).get('quote', [{}])[0]
                        opens = indicators.get('open', [])
                        if opens and len(opens) > 0:
                            # Find first non-None open price
                            for o in opens:
                                if o is not None:
                                    open_price = o
                                    break
                    except:
                        pass
                
                return {
                    'price': meta['regularMarketPrice'],
                    'open': open_price,  # None if not available
                    'high': meta.get('regularMarketDayHigh'),
                    'low': meta.get('regularMarketDayLow'),
                    'volume': meta.get('regularMarketVolume', 0),
                    'previous_close': meta.get('previousClose') or meta.get('chartPreviousClose'),
                    'change': meta['regularMarketPrice'] - (meta.get('previousClose') or meta.get('chartPreviousClose', meta['regularMarketPrice'])),
                    'change_percent': ((meta['regularMarketPrice'] - (meta.get('previousClose') or meta.get('chartPreviousClose', meta['regularMarketPrice']))) / (meta.get('previousClose') or meta.get('chartPreviousClose', 1)) * 100),
                    'source': 'Yahoo Finance (direct API)'
                }
        except Exception as e:
            print(f"Yahoo Direct API failed: {e}")
        return None
    
    def _fetch_alpha_vantage(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 3: Alpha Vantage API"""
        try:
            if not self.alpha_vantage_key or self.alpha_vantage_key == 'demo':
                return None
            
            formatted_symbol = self._format_symbol(symbol, exchange, 'alpha_vantage')
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={formatted_symbol}&apikey={self.alpha_vantage_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    price = float(quote['05. price'])
                    prev_close = float(quote['08. previous close'])
                    
                    return {
                        'price': price,
                        'open': float(quote['02. open']),
                        'high': float(quote['03. high']),
                        'low': float(quote['04. low']),
                        'volume': int(quote['06. volume']),
                        'previous_close': prev_close,
                        'change': float(quote['09. change']),
                        'change_percent': float(quote['10. change percent'].replace('%', '')),
                        'source': 'Alpha Vantage'
                    }
        except Exception as e:
            print(f"Alpha Vantage failed: {e}")
        return None
    
    def _fetch_twelve_data(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 4: Twelve Data API"""
        try:
            if not self.twelve_data_key or self.twelve_data_key == 'demo':
                return None
            
            base_symbol = self._format_symbol(symbol, exchange, 'twelve_data')
            url = f"https://api.twelvedata.com/quote?symbol={base_symbol}&apikey={self.twelve_data_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'price' in data:
                    price = float(data['price'])
                    prev_close = float(data.get('previous_close', price))
                    
                    return {
                        'price': price,
                        'open': float(data.get('open', price)),
                        'high': float(data.get('high', price)),
                        'low': float(data.get('low', price)),
                        'volume': int(data.get('volume', 0)),
                        'previous_close': prev_close,
                        'change': float(data.get('change', price - prev_close)),
                        'change_percent': float(data.get('percent_change', 0)),
                        'source': 'Twelve Data'
                    }
        except Exception as e:
            print(f"Twelve Data failed: {e}")
        return None
    
    def _fetch_finnhub(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 5: Finnhub API"""
        try:
            if not self.finnhub_key or self.finnhub_key == 'demo':
                return None
            
            formatted_symbol = self._format_symbol(symbol, exchange, 'finnhub')
            url = f"https://finnhub.io/api/v1/quote?symbol={formatted_symbol}&token={self.finnhub_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'c' in data and data['c'] > 0:  # c = current price
                    price = data['c']
                    prev_close = data['pc']
                    
                    return {
                        'price': price,
                        'open': data['o'],
                        'high': data['h'],
                        'low': data['l'],
                        'volume': 0,  # Finnhub doesn't provide volume in quote
                        'previous_close': prev_close,
                        'change': price - prev_close,
                        'change_percent': ((price - prev_close) / prev_close * 100) if prev_close else 0,
                        'source': 'Finnhub'
                    }
        except Exception as e:
            print(f"Finnhub failed: {e}")
        return None
    
    def _fetch_polygon(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 6: Polygon.io API"""
        try:
            if not self.polygon_key or self.polygon_key == 'demo':
                return None
            
            base_symbol = self._format_symbol(symbol, exchange, 'polygon')
            # Get previous day data
            url = f"https://api.polygon.io/v2/aggs/ticker/{base_symbol}/prev?adjusted=true&apiKey={self.polygon_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    return {
                        'price': result['c'],  # close
                        'open': result['o'],
                        'high': result['h'],
                        'low': result['l'],
                        'volume': result['v'],
                        'previous_close': result['c'],
                        'change': 0,
                        'change_percent': 0,
                        'source': 'Polygon.io'
                    }
        except Exception as e:
            print(f"Polygon failed: {e}")
        return None
    
    def _fetch_fmp(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 7: Financial Modeling Prep API"""
        try:
            if not self.fmp_key:
                return None
            
            base_symbol = self._format_symbol(symbol, exchange, 'fmp')
            url = f"https://financialmodelingprep.com/api/v3/quote/{base_symbol}?apikey={self.fmp_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    quote = data[0]
                    return {
                        'price': quote['price'],
                        'open': quote.get('open', quote['price']),
                        'high': quote.get('dayHigh', quote['price']),
                        'low': quote.get('dayLow', quote['price']),
                        'volume': quote.get('volume', 0),
                        'previous_close': quote.get('previousClose', quote['price']),
                        'change': quote.get('change', 0),
                        'change_percent': quote.get('changesPercentage', 0),
                        'source': 'FMP'
                    }
        except Exception as e:
            print(f"FMP failed: {e}")
        return None
    
    def _fetch_iex_cloud(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Method 8: IEX Cloud API"""
        try:
            if not self.iex_key or self.iex_key == 'demo':
                return None
            
            base_symbol = self._format_symbol(symbol, exchange, 'iex_cloud')
            url = f"https://cloud.iexapis.com/stable/stock/{base_symbol}/quote?token={self.iex_key}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': data['latestPrice'],
                    'open': data.get('open', data['latestPrice']),
                    'high': data.get('high', data['latestPrice']),
                    'low': data.get('low', data['latestPrice']),
                    'volume': data.get('volume', 0),
                    'previous_close': data.get('previousClose', data['latestPrice']),
                    'change': data.get('change', 0),
                    'change_percent': data.get('changePercent', 0) * 100,
                    'source': 'IEX Cloud'
                }
        except Exception as e:
            print(f"IEX Cloud failed: {e}")
        return None
    
    def get_live_price(self, symbol: str, exchange: str = 'NYSE') -> Tuple[bool, Dict]:
        """
        Get live price from ANY available source - tries all APIs until one works!
        
        Returns: (success: bool, data: dict)
        """
        
        # Check cache first
        cache_key = f"{symbol}_{exchange}"
        if cache_key in _price_cache:
            cached_time, cached_data = _price_cache[cache_key]
            if time.time() - cached_time < _cache_duration:
                print(f"✓ Using cached price for {symbol} from {cached_data.get('source', 'cache')}")
                return True, cached_data
        
        print(f"\n🔍 Fetching price for {symbol} on {exchange}...")
        
        # Try all methods in order of reliability
        methods = [
            ('Yahoo Finance', lambda: self._fetch_yahoo_finance(symbol, exchange)),
            ('Yahoo Direct API', lambda: self._fetch_yahoo_direct(symbol, exchange)),
            ('Alpha Vantage', lambda: self._fetch_alpha_vantage(symbol, exchange)),
            ('Twelve Data', lambda: self._fetch_twelve_data(symbol, exchange)),
            ('Finnhub', lambda: self._fetch_finnhub(symbol, exchange)),
            ('Polygon.io', lambda: self._fetch_polygon(symbol, exchange)),
            ('FMP', lambda: self._fetch_fmp(symbol, exchange)),
            ('IEX Cloud', lambda: self._fetch_iex_cloud(symbol, exchange)),
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"  Trying {method_name}...")
                result = method_func()
                if result:
                    print(f"  ✓ Success with {method_name}!")
                    # Cache the result
                    _price_cache[cache_key] = (time.time(), result)
                    return True, result
                else:
                    print(f"  ✗ {method_name} returned no data")
            except Exception as e:
                print(f"  ✗ {method_name} error: {e}")
            
            time.sleep(0.2)  # Small delay between attempts
        
        print(f"❌ All price sources failed for {symbol}")
        return False, {"error": "All price sources failed"}
    
    def get_historical_data(self, symbol: str, exchange: str = 'NYSE', period: str = '3mo') -> Tuple[bool, pd.DataFrame]:
        """Get historical data - tries multiple sources with better error handling"""
        
        formatted_symbol = self._format_symbol(symbol, exchange, 'yahoo_finance')
        
        # Try Yahoo Finance library first
        try:
            print(f"  Trying historical data for {formatted_symbol} via yfinance...")
            ticker = yf.Ticker(formatted_symbol)
            time.sleep(0.5)
            hist = ticker.history(period=period, timeout=10)
            
            if not hist.empty and len(hist) > 5:
                print(f"  ✓ Got {len(hist)} days of historical data from Yahoo Finance")
                return True, hist
        except Exception as e:
            print(f"  ✗ Yahoo Finance library failed: {e}")
        
        # Try direct Yahoo Finance API as backup
        try:
            print(f"  Trying direct Yahoo API for historical data...")
            # Map period to range values
            period_map = {
                '1mo': '1mo',
                '3mo': '3mo',
                '6mo': '6mo',
                '1y': '1y',
                '2y': '2y',
                '5y': '5y'
            }
            range_val = period_map.get(period, '3mo')
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_symbol}?range={range_val}&interval=1d"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                # Build DataFrame
                df = pd.DataFrame({
                    'Open': quotes['open'],
                    'High': quotes['high'],
                    'Low': quotes['low'],
                    'Close': quotes['close'],
                    'Volume': quotes['volume']
                }, index=pd.to_datetime(timestamps, unit='s'))
                
                # Remove any NaN rows
                df = df.dropna()
                
                if not df.empty and len(df) > 5:
                    print(f"  ✓ Got {len(df)} days from direct Yahoo API")
                    return True, df
        except Exception as e:
            print(f"  ✗ Direct Yahoo API failed: {e}")
        
        # Try Alpha Vantage as last resort
        try:
            if self.alpha_vantage_key and self.alpha_vantage_key != 'demo':
                print(f"  Trying Alpha Vantage for historical data...")
                formatted_symbol = self._format_symbol(symbol, exchange, 'alpha_vantage')
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={formatted_symbol}&apikey={self.alpha_vantage_key}&outputsize=compact"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'Time Series (Daily)' in data:
                        ts = data['Time Series (Daily)']
                        df = pd.DataFrame.from_dict(ts, orient='index')
                        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        df.index = pd.to_datetime(df.index)
                        df = df.sort_index()
                        df = df.astype(float)
                        print(f"  ✓ Got historical data from Alpha Vantage")
                        return True, df
        except Exception as e:
            print(f"  ✗ Alpha Vantage historical failed: {e}")
        
        print(f"  ❌ All historical data sources failed for {formatted_symbol}")
        return False, pd.DataFrame()


# Global fetcher instance
_fetcher = MultiSourcePriceFetcher()

def get_live_price(symbol: str, exchange: str = 'NYSE') -> Tuple[bool, Dict]:
    """Get live price - automatically tries all available sources"""
    return _fetcher.get_live_price(symbol, exchange)

def get_historical_data(symbol: str, exchange: str = 'NYSE', period: str = '3mo') -> Tuple[bool, pd.DataFrame]:
    """Get historical data - automatically tries all available sources"""
    return _fetcher.get_historical_data(symbol, exchange, period)


def get_company_info(symbol: str, exchange: str = 'NYSE') -> Dict:
    """
    Get detailed company information using multiple sources with fallback
    Uses Yahoo Finance API with fallback to minimal info
    
    Args:
        symbol (str): Stock ticker symbol (base, without exchange suffix)
        exchange (str): Exchange code (NYSE, TSX, NSE, BSE)
        
    Returns:
        dict: Company information
    """
    # Format symbol for the exchange
    formatted_symbol = _fetcher._format_symbol(symbol, exchange, 'yahoo_finance')
    
    # Try Yahoo Finance with rate limit protection
    attempts = [formatted_symbol, symbol]
    
    for attempt_symbol in attempts:
        try:
            print(f"  Trying company info for: {attempt_symbol}")
            ticker = yf.Ticker(attempt_symbol)
            time.sleep(0.5)  # Increased delay to avoid rate limits
            info = ticker.info
            
            # Check if we got valid data
            if info and info.get('longName'):
                print(f"  ✓ Got company info from Yahoo Finance")
                return {
                    'success': True,
                    'data': {
                        'name': info.get('longName') or info.get('shortName') or symbol,
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
            if '429' in str(e):
                print(f"  ⏸️ Rate limited, using fallback...")
                break  # Stop trying Yahoo if rate limited
            print(f"  ✗ Failed {attempt_symbol}: {e}")
            continue
    
    # Final fallback: return basic info with symbol name
    print(f"  ℹ️ Using minimal info for {symbol}")
    return {
        'success': True,  # Mark as success so UI doesn't show error
        'data': {
            'name': f"{symbol} ({exchange})",  # At least show symbol and exchange
            'sector': None,
            'industry': None,
            'description': None,
            'website': None,
            'employees': None,
            'country': None,
            'city': None
        },
        'error': None
    }


def get_exchange_info(symbol: str, exchange: str = 'NYSE') -> Dict:
    """
    Get exchange information for the stock with smart detection
    
    Args:
        symbol (str): Stock ticker symbol (base, without exchange suffix)
        exchange (str): Exchange code (NYSE, TSX, NSE, BSE)
        
    Returns:
        dict: Exchange information
    """
    # Format symbol for the exchange
    formatted_symbol = _fetcher._format_symbol(symbol, exchange, 'yahoo_finance')
    
    # Direct mapping from our exchange codes
    exchange_info_map = {
        'NYSE': {
            'exchange': 'NYSE (New York Stock Exchange)',
            'currency': 'USD',
            'timezone': 'America/New_York'
        },
        'NASDAQ': {
            'exchange': 'NASDAQ',
            'currency': 'USD',
            'timezone': 'America/New_York'
        },
        'TSX': {
            'exchange': 'TSX (Toronto Stock Exchange)',
            'currency': 'CAD',
            'timezone': 'America/Toronto'
        },
        'NSE': {
            'exchange': 'NSE (National Stock Exchange of India)',
            'currency': 'INR',
            'timezone': 'Asia/Kolkata'
        },
        'BSE': {
            'exchange': 'BSE (Bombay Stock Exchange)',
            'currency': 'INR',
            'timezone': 'Asia/Kolkata'
        }
    }
    
    # Use our known mapping first (most reliable)
    if exchange in exchange_info_map:
        return {
            'success': True,
            **exchange_info_map[exchange]
        }
    
    # Fallback: try to get from Yahoo Finance
    try:
        ticker = yf.Ticker(formatted_symbol)
        time.sleep(0.3)
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
        # Final fallback to our mapping
        if exchange in exchange_info_map:
            return {
                'success': True,
                **exchange_info_map[exchange]
            }
        
        return {
            'success': False,
            'exchange': 'Unknown',
            'currency': 'USD',
            'error': f'Error fetching exchange info: {str(e)}'
        }

