"""
Key Statistics Module - Comprehensive financial metrics
Fetches detailed statistics like P/E ratio, Market Cap, EPS, Dividends, Beta, etc.
Multi-source with fallback: Yahoo Finance → Alpha Vantage → FMP → Twelve Data → Finnhub
"""

import yfinance as yf
import time
import requests
import os
from typing import Dict, Optional


def get_key_statistics(symbol: str, exchange: str = 'NYSE') -> Dict:
    """
    Get comprehensive key statistics for a stock with multi-source fallback
    
    Sources tried in order:
    1. Yahoo Finance (yfinance)
    2. Alpha Vantage
    3. Financial Modeling Prep (FMP)
    4. Twelve Data
    5. Finnhub
    
    Args:
        symbol (str): Stock ticker symbol (base, without exchange suffix)
        exchange (str): Exchange code (NYSE, TSX, NSE, BSE)
        
    Returns:
        dict: Key statistics data
    """
    from multi_source_price import _fetcher
    
    # Format symbol for the exchange
    formatted_symbol = _fetcher._format_symbol(symbol, exchange, 'yahoo_finance')
    
    # Track which sources were tried and why they failed
    attempted_sources = []
    
    # Source 1: Try Yahoo Finance API
    result = _try_yahoo_finance(formatted_symbol, symbol)
    attempted_sources.append(('Yahoo Finance', result.get('error', 'Failed')))
    if result['success']:
        return result
    
    print(f"  → Trying alternate sources for {symbol}...")
    
    # Source 2: Try Alpha Vantage
    result = _try_alpha_vantage(symbol)
    attempted_sources.append(('Alpha Vantage', result.get('error', 'No API key or failed')))
    if result['success']:
        return result
    
    # Source 3: Try Financial Modeling Prep (FMP)
    result = _try_fmp(symbol)
    attempted_sources.append(('FMP', result.get('error', 'No API key or failed')))
    if result['success']:
        return result
    
    # Source 4: Try Twelve Data
    result = _try_twelve_data(symbol)
    attempted_sources.append(('Twelve Data', result.get('error', 'No API key or failed')))
    if result['success']:
        return result
    
    # Source 5: Try Finnhub
    result = _try_finnhub(symbol)
    attempted_sources.append(('Finnhub', result.get('error', 'No API key or failed')))
    if result['success']:
        return result
    
    # Build detailed error message
    error_details = "\n".join([f"  • {source}: {error}" for source, error in attempted_sources])
    
    # All sources failed
    return {
        'success': False,
        'data': {},
        'source': 'All sources failed',
        'error': f'Unable to fetch statistics from any source:\n{error_details}\n\n💡 Set up API keys to enable fallback sources (see README.md for instructions)',
        'attempted_sources': attempted_sources
    }


def _try_yahoo_finance(formatted_symbol: str, base_symbol: str) -> Dict:
    """
    Get comprehensive key statistics for a stock
    
    Args:
        formatted_symbol (str): Formatted symbol for Yahoo Finance (e.g., TCS.BO)
        base_symbol (str): Base ticker symbol
        
    Returns:
        dict: Key statistics data
    """
    # Try Yahoo Finance API
    try:
        print(f"  [1/5] Fetching key statistics from Yahoo Finance for {formatted_symbol}...")
        ticker = yf.Ticker(formatted_symbol)
        time.sleep(0.5)  # Rate limit protection
        info = ticker.info
        
        if info and len(info) > 5:  # Check if we got meaningful data
            stats_data = {
                # Valuation metrics
                'marketCap': info.get('marketCap'),
                'enterpriseValue': info.get('enterpriseValue'),
                'trailingPE': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'priceToBook': info.get('priceToBook'),
                'priceToSales': info.get('priceToSalesTrailing12Months'),
                'pegRatio': info.get('pegRatio'),
                'enterpriseToRevenue': info.get('enterpriseToRevenue'),
                'enterpriseToEbitda': info.get('enterpriseToEbitda'),
                
                # Profitability metrics
                'profitMargins': info.get('profitMargins'),
                'operatingMargins': info.get('operatingMargins'),
                'returnOnAssets': info.get('returnOnAssets'),
                'returnOnEquity': info.get('returnOnEquity'),
                'grossMargins': info.get('grossMargins'),
                'ebitdaMargins': info.get('ebitdaMargins'),
                
                # Growth metrics
                'earningsGrowth': info.get('earningsGrowth'),
                'revenueGrowth': info.get('revenueGrowth'),
                'earningsQuarterlyGrowth': info.get('earningsQuarterlyGrowth'),
                
                # Per share metrics
                'trailingEps': info.get('trailingEps'),
                'forwardEps': info.get('forwardEps'),
                'bookValue': info.get('bookValue'),
                'revenuePerShare': info.get('revenuePerShare'),
                'totalCashPerShare': info.get('totalCashPerShare'),
                
                # Dividend metrics
                'dividendRate': info.get('dividendRate'),
                'dividendYield': info.get('dividendYield'),
                'payoutRatio': info.get('payoutRatio'),
                'fiveYearAvgDividendYield': info.get('fiveYearAvgDividendYield'),
                'trailingAnnualDividendRate': info.get('trailingAnnualDividendRate'),
                'trailingAnnualDividendYield': info.get('trailingAnnualDividendYield'),
                
                # Financial health
                'totalDebt': info.get('totalDebt'),
                'debtToEquity': info.get('debtToEquity'),
                'currentRatio': info.get('currentRatio'),
                'quickRatio': info.get('quickRatio'),
                'totalCash': info.get('totalCash'),
                'totalCashPerShare': info.get('totalCashPerShare'),
                'freeCashflow': info.get('freeCashflow'),
                'operatingCashflow': info.get('operatingCashflow'),
                
                # Trading metrics
                'beta': info.get('beta'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'fiftyDayAverage': info.get('fiftyDayAverage'),
                'twoHundredDayAverage': info.get('twoHundredDayAverage'),
                'averageVolume': info.get('averageVolume'),
                'averageVolume10days': info.get('averageVolume10days'),
                'sharesOutstanding': info.get('sharesOutstanding'),
                'floatShares': info.get('floatShares'),
                'sharesShort': info.get('sharesShort'),
                'shortRatio': info.get('shortRatio'),
                'shortPercentOfFloat': info.get('shortPercentOfFloat'),
                'heldPercentInsiders': info.get('heldPercentInsiders'),
                'heldPercentInstitutions': info.get('heldPercentInstitutions'),
                
                # Target prices
                'targetHighPrice': info.get('targetHighPrice'),
                'targetLowPrice': info.get('targetLowPrice'),
                'targetMeanPrice': info.get('targetMeanPrice'),
                'targetMedianPrice': info.get('targetMedianPrice'),
                'recommendationKey': info.get('recommendationKey'),
                'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions'),
            }
            
            # Remove None values
            stats_data = {k: v for k, v in stats_data.items() if v is not None}
            
            print(f"  ✓ Got {len(stats_data)} statistics from Yahoo Finance")
            return {
                'success': True,
                'data': stats_data,
                'source': 'Yahoo Finance'
            }
        else:
            print(f"  ✗ Yahoo Finance returned insufficient data (only {len(info)} fields)")
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': f'Insufficient data returned - got {len(info)} fields (expected > 5). The stock symbol may be invalid or data temporarily unavailable.'
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Yahoo Finance statistics failed: {error_msg}")
        
        # Provide specific error messages
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': 'Rate limit exceeded (429) - Yahoo Finance is temporarily blocking requests. Wait 2-3 minutes and try again.'
            }
        elif 'timeout' in error_msg.lower():
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': f'Request timeout - Yahoo Finance took too long to respond. Try again in a moment. ({error_msg})'
            }
        elif 'ConnectionError' in error_msg or 'connection' in error_msg.lower():
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': f'Network connection error - Check your internet connection. ({error_msg})'
            }
        elif 'not found' in error_msg.lower() or '404' in error_msg:
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': f'Stock symbol "{formatted_symbol}" not found. Please verify the ticker symbol and exchange are correct.'
            }
        else:
            return {
                'success': False,
                'data': {},
                'source': 'Yahoo Finance',
                'error': f'Error fetching statistics: {error_msg}'
            }


def format_large_number(num: float, currency_symbol: str = '$') -> str:
    """Format large numbers for display (e.g., 145B, 2.5M)"""
    if num is None:
        return 'N/A'
    
    abs_num = abs(num)
    if abs_num >= 1e12:  # Trillions
        return f"{currency_symbol}{num/1e12:.2f}T"
    elif abs_num >= 1e9:  # Billions
        return f"{currency_symbol}{num/1e9:.2f}B"
    elif abs_num >= 1e6:  # Millions
        return f"{currency_symbol}{num/1e6:.2f}M"
    elif abs_num >= 1e3:  # Thousands
        return f"{currency_symbol}{num/1e3:.2f}K"
    else:
        return f"{currency_symbol}{num:.2f}"


def format_percentage(num: float) -> str:
    """Format as percentage"""
    if num is None:
        return 'N/A'
    return f"{num*100:.2f}%"


def format_ratio(num: float) -> str:
    """Format ratio numbers"""
    if num is None:
        return 'N/A'
    return f"{num:.2f}"


def _try_alpha_vantage(symbol: str) -> Dict:
    """Try fetching stats from Alpha Vantage"""
    api_key = os.getenv('ALPHA_VANTAGE_KEY')
    if not api_key:
        print(f"  [2/5] Alpha Vantage: No API key configured")
        return {'success': False, 'data': {}, 'error': 'No API key (set ALPHA_VANTAGE_KEY)'}
    
    try:
        print(f"  [2/5] Trying Alpha Vantage for {symbol}...")
        
        # Get company overview
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and 'Symbol' in data:
            stats_data = {
                'marketCap': float(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else None,
                'trailingPE': float(data.get('TrailingPE', 0)) if data.get('TrailingPE') else None,
                'forwardPE': float(data.get('ForwardPE', 0)) if data.get('ForwardPE') else None,
                'priceToBook': float(data.get('PriceToBookRatio', 0)) if data.get('PriceToBookRatio') else None,
                'priceToSales': float(data.get('PriceToSalesRatioTTM', 0)) if data.get('PriceToSalesRatioTTM') else None,
                'pegRatio': float(data.get('PEGRatio', 0)) if data.get('PEGRatio') else None,
                'beta': float(data.get('Beta', 0)) if data.get('Beta') else None,
                'dividendYield': float(data.get('DividendYield', 0)) if data.get('DividendYield') else None,
                'profitMargins': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') else None,
                'operatingMargins': float(data.get('OperatingMarginTTM', 0)) if data.get('OperatingMarginTTM') else None,
                'returnOnAssets': float(data.get('ReturnOnAssetsTTM', 0)) if data.get('ReturnOnAssetsTTM') else None,
                'returnOnEquity': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') else None,
                'revenuePerShare': float(data.get('RevenuePerShareTTM', 0)) if data.get('RevenuePerShareTTM') else None,
                'trailingEps': float(data.get('EPS', 0)) if data.get('EPS') else None,
                'bookValue': float(data.get('BookValue', 0)) if data.get('BookValue') else None,
                'sharesOutstanding': float(data.get('SharesOutstanding', 0)) if data.get('SharesOutstanding') else None,
                'fiftyTwoWeekHigh': float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') else None,
                'fiftyTwoWeekLow': float(data.get('52WeekLow', 0)) if data.get('52WeekLow') else None,
                'fiftyDayAverage': float(data.get('50DayMovingAverage', 0)) if data.get('50DayMovingAverage') else None,
                'twoHundredDayAverage': float(data.get('200DayMovingAverage', 0)) if data.get('200DayMovingAverage') else None,
            }
            
            stats_data = {k: v for k, v in stats_data.items() if v is not None and v != 0}
            
            if len(stats_data) > 3:
                print(f"  ✓ Got {len(stats_data)} statistics from Alpha Vantage")
                return {'success': True, 'data': stats_data, 'source': 'Alpha Vantage'}
        
        print(f"  ✗ Alpha Vantage: Insufficient data")
        return {'success': False, 'data': {}, 'error': 'Insufficient data returned'}
    except Exception as e:
        print(f"  ✗ Alpha Vantage failed: {e}")
        return {'success': False, 'data': {}, 'error': str(e)}
    
    return {'success': False, 'data': {}, 'error': 'Unknown error'}


def _try_fmp(symbol: str) -> Dict:
    """Try fetching stats from Financial Modeling Prep"""
    api_key = os.getenv('FMP_KEY')
    if not api_key:
        print(f"  [3/5] FMP: No API key configured")
        return {'success': False, 'data': {}, 'error': 'No API key (set FMP_KEY)'}
    
    try:
        print(f"  [3/5] Trying Financial Modeling Prep for {symbol}...")
        
        # Get key metrics
        url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?apikey={api_key}"
        response = requests.get(url, timeout=10)
        metrics = response.json()
        
        # Get profile for additional data
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
        profile_response = requests.get(profile_url, timeout=10)
        profile = profile_response.json()
        
        if metrics and isinstance(metrics, list) and len(metrics) > 0:
            latest = metrics[0]
            profile_data = profile[0] if profile and isinstance(profile, list) else {}
            
            stats_data = {
                'marketCap': profile_data.get('mktCap'),
                'trailingPE': latest.get('peRatio'),
                'priceToBook': latest.get('pbRatio'),
                'beta': profile_data.get('beta'),
                'dividendYield': profile_data.get('lastDiv'),
                'earningsGrowth': latest.get('revenuePerShareGrowth'),
                'returnOnEquity': latest.get('roe'),
                'debtToEquity': latest.get('debtToEquity'),
                'currentRatio': latest.get('currentRatio'),
                'freeCashflow': latest.get('freeCashFlowPerShare'),
                'enterpriseValue': latest.get('enterpriseValue'),
                'priceToSales': latest.get('priceToSalesRatio'),
            }
            
            stats_data = {k: v for k, v in stats_data.items() if v is not None}
            
            if len(stats_data) > 3:
                print(f"  ✓ Got {len(stats_data)} statistics from FMP")
                return {'success': True, 'data': stats_data, 'source': 'Financial Modeling Prep'}
        
        print(f"  ✗ FMP: Insufficient data")
        return {'success': False, 'data': {}, 'error': 'Insufficient data returned'}
    except Exception as e:
        print(f"  ✗ FMP failed: {e}")
        return {'success': False, 'data': {}, 'error': str(e)}
    
    return {'success': False, 'data': {}, 'error': 'Unknown error'}


def _try_twelve_data(symbol: str) -> Dict:
    """Try fetching stats from Twelve Data"""
    api_key = os.getenv('TWELVE_DATA_KEY')
    if not api_key:
        print(f"  [4/5] Twelve Data: No API key configured")
        return {'success': False, 'data': {}, 'error': 'No API key (set TWELVE_DATA_KEY)'}
    
    try:
        print(f"  [4/5] Trying Twelve Data for {symbol}...")
        
        # Get statistics
        url = f"https://api.twelvedata.com/statistics?symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and data.get('status') == 'ok' and 'statistics' in data:
            stats = data['statistics']
            
            stats_data = {
                'marketCap': stats.get('valuations_metrics', {}).get('market_capitalization'),
                'trailingPE': stats.get('valuations_metrics', {}).get('trailing_pe'),
                'forwardPE': stats.get('valuations_metrics', {}).get('forward_pe'),
                'priceToBook': stats.get('valuations_metrics', {}).get('price_to_book_mrq'),
                'priceToSales': stats.get('valuations_metrics', {}).get('price_to_sales_ttm'),
                'beta': stats.get('stock_statistics', {}).get('beta'),
                'fiftyTwoWeekHigh': stats.get('stock_statistics', {}).get('fifty_two_week_high'),
                'fiftyTwoWeekLow': stats.get('stock_statistics', {}).get('fifty_two_week_low'),
                'averageVolume': stats.get('stock_statistics', {}).get('average_volume_10d'),
                'sharesOutstanding': stats.get('stock_statistics', {}).get('shares_outstanding'),
            }
            
            stats_data = {k: v for k, v in stats_data.items() if v is not None}
            
            if len(stats_data) > 3:
                print(f"  ✓ Got {len(stats_data)} statistics from Twelve Data")
                return {'success': True, 'data': stats_data, 'source': 'Twelve Data'}
        
        print(f"  ✗ Twelve Data: Insufficient data")
        return {'success': False, 'data': {}, 'error': 'Insufficient data returned'}
    except Exception as e:
        print(f"  ✗ Twelve Data failed: {e}")
        return {'success': False, 'data': {}, 'error': str(e)}
    
    return {'success': False, 'data': {}, 'error': 'Unknown error'}


def _try_finnhub(symbol: str) -> Dict:
    """Try fetching stats from Finnhub"""
    api_key = os.getenv('FINNHUB_KEY')
    if not api_key:
        print(f"  [5/5] Finnhub: No API key configured")
        return {'success': False, 'data': {}, 'error': 'No API key (set FINNHUB_KEY)'}
    
    try:
        print(f"  [5/5] Trying Finnhub for {symbol}...")
        
        # Get company metrics
        url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and 'metric' in data:
            metrics = data['metric']
            
            stats_data = {
                'marketCap': metrics.get('marketCapitalization'),
                'trailingPE': metrics.get('peBasicExclExtraTTM'),
                'priceToBook': metrics.get('pbQuarterly'),
                'priceToSales': metrics.get('psAnnual'),
                'beta': metrics.get('beta'),
                'dividendYield': metrics.get('dividendYieldIndicatedAnnual'),
                'returnOnEquity': metrics.get('roeTTM'),
                'returnOnAssets': metrics.get('roaTTM'),
                'profitMargins': metrics.get('netProfitMarginTTM'),
                'operatingMargins': metrics.get('operatingMarginTTM'),
                'currentRatio': metrics.get('currentRatioQuarterly'),
                'quickRatio': metrics.get('quickRatioQuarterly'),
                'debtToEquity': metrics.get('totalDebt/totalEquityQuarterly'),
                'fiftyTwoWeekHigh': metrics.get('52WeekHigh'),
                'fiftyTwoWeekLow': metrics.get('52WeekLow'),
            }
            
            stats_data = {k: v for k, v in stats_data.items() if v is not None}
            
            if len(stats_data) > 3:
                print(f"  ✓ Got {len(stats_data)} statistics from Finnhub")
                return {'success': True, 'data': stats_data, 'source': 'Finnhub'}
        
        print(f"  ✗ Finnhub: Insufficient data")
        return {'success': False, 'data': {}, 'error': 'Insufficient data returned'}
    except Exception as e:
        print(f"  ✗ Finnhub failed: {e}")
        return {'success': False, 'data': {}, 'error': str(e)}
    
    return {'success': False, 'data': {}, 'error': 'Unknown error'}
