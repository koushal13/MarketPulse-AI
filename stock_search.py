"""
Real-time stock search across global exchanges
Multi-source search: Yahoo Finance, Alpha Vantage, FMP, and manual curated lists
"""

import requests
import json
from typing import List, Dict
import pandas as pd
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
FMP_KEY = os.getenv('FMP_KEY')

# Curated list of popular Indian stocks (NSE/BSE)
INDIAN_STOCKS = [
    {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries Limited', 'exchange': 'NSE'},
    {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services Limited', 'exchange': 'NSE'},
    {'symbol': 'INFY.NS', 'name': 'Infosys Limited', 'exchange': 'NSE'},
    {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank Limited', 'exchange': 'NSE'},
    {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank Limited', 'exchange': 'NSE'},
    {'symbol': 'HINDUNILVR.NS', 'name': 'Hindustan Unilever Limited', 'exchange': 'NSE'},
    {'symbol': 'ITC.NS', 'name': 'ITC Limited', 'exchange': 'NSE'},
    {'symbol': 'SBIN.NS', 'name': 'State Bank of India', 'exchange': 'NSE'},
    {'symbol': 'BHARTIARTL.NS', 'name': 'Bharti Airtel Limited', 'exchange': 'NSE'},
    {'symbol': 'KOTAKBANK.NS', 'name': 'Kotak Mahindra Bank Limited', 'exchange': 'NSE'},
    {'symbol': 'LT.NS', 'name': 'Larsen & Toubro Limited', 'exchange': 'NSE'},
    {'symbol': 'AXISBANK.NS', 'name': 'Axis Bank Limited', 'exchange': 'NSE'},
    {'symbol': 'TATAMOTORS.NS', 'name': 'Tata Motors Limited', 'exchange': 'NSE'},
    {'symbol': 'TATASTEEL.NS', 'name': 'Tata Steel Limited', 'exchange': 'NSE'},
    {'symbol': 'BAJFINANCE.NS', 'name': 'Bajaj Finance Limited', 'exchange': 'NSE'},
    {'symbol': 'WIPRO.NS', 'name': 'Wipro Limited', 'exchange': 'NSE'},
    {'symbol': 'HCLTECH.NS', 'name': 'HCL Technologies Limited', 'exchange': 'NSE'},
    {'symbol': 'MARUTI.NS', 'name': 'Maruti Suzuki India Limited', 'exchange': 'NSE'},
    {'symbol': 'SUNPHARMA.NS', 'name': 'Sun Pharmaceutical Industries Limited', 'exchange': 'NSE'},
    {'symbol': 'ONGC.NS', 'name': 'Oil and Natural Gas Corporation Limited', 'exchange': 'NSE'},
    {'symbol': 'TECHM.NS', 'name': 'Tech Mahindra Limited', 'exchange': 'NSE'},
    {'symbol': 'TITAN.NS', 'name': 'Titan Company Limited', 'exchange': 'NSE'},
    {'symbol': 'POWERGRID.NS', 'name': 'Power Grid Corporation of India Limited', 'exchange': 'NSE'},
    {'symbol': 'NTPC.NS', 'name': 'NTPC Limited', 'exchange': 'NSE'},
    {'symbol': 'ULTRACEMCO.NS', 'name': 'UltraTech Cement Limited', 'exchange': 'NSE'},
    {'symbol': 'ASIANPAINT.NS', 'name': 'Asian Paints Limited', 'exchange': 'NSE'},
    {'symbol': 'NESTLEIND.NS', 'name': 'Nestle India Limited', 'exchange': 'NSE'},
    {'symbol': 'BAJAJFINSV.NS', 'name': 'Bajaj Finserv Limited', 'exchange': 'NSE'},
    {'symbol': 'DIVISLAB.NS', 'name': 'Divi\'s Laboratories Limited', 'exchange': 'NSE'},
    {'symbol': 'ADANIENT.NS', 'name': 'Adani Enterprises Limited', 'exchange': 'NSE'},
    {'symbol': 'ADANIPORTS.NS', 'name': 'Adani Ports and Special Economic Zone Limited', 'exchange': 'NSE'},
    {'symbol': 'M&M.NS', 'name': 'Mahindra & Mahindra Limited', 'exchange': 'NSE'},
    {'symbol': 'TATACONSUM.NS', 'name': 'Tata Consumer Products Limited', 'exchange': 'NSE'},
    {'symbol': 'TATAPOWER.NS', 'name': 'Tata Power Company Limited', 'exchange': 'NSE'},
    {'symbol': 'TATACHEM.NS', 'name': 'Tata Chemicals Limited', 'exchange': 'NSE'},
    {'symbol': 'TATAELXSI.NS', 'name': 'Tata Elxsi Limited', 'exchange': 'NSE'},
]

# Popular US stocks
US_STOCKS = [
    {'symbol': 'AAPL', 'name': 'Apple Inc.', 'exchange': 'NASDAQ'},
    {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'exchange': 'NASDAQ'},
    {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'exchange': 'NASDAQ'},
    {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'exchange': 'NASDAQ'},
    {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'exchange': 'NASDAQ'},
    {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
    {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'exchange': 'NASDAQ'},
    {'symbol': 'BRK.B', 'name': 'Berkshire Hathaway Inc.', 'exchange': 'NYSE'},
    {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'exchange': 'NYSE'},
    {'symbol': 'V', 'name': 'Visa Inc.', 'exchange': 'NYSE'},
]

# Canadian stocks
CANADIAN_STOCKS = [
    {'symbol': 'TD.TO', 'name': 'Toronto-Dominion Bank', 'exchange': 'TSX'},
    {'symbol': 'RY.TO', 'name': 'Royal Bank of Canada', 'exchange': 'TSX'},
    {'symbol': 'ENB.TO', 'name': 'Enbridge Inc.', 'exchange': 'TSX'},
    {'symbol': 'SHOP.TO', 'name': 'Shopify Inc.', 'exchange': 'TSX'},
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources Limited', 'exchange': 'TSX'},
]


def search_stocks(query: str, limit: int = 20) -> List[Dict]:
    """
    Multi-source stock search with fallbacks
    Sources: Yahoo Finance -> FMP -> Alpha Vantage -> Curated Lists
    
    Args:
        query: Search term (company name or ticker)
        limit: Maximum number of results to return
    
    Returns:
        List of dicts with keys: symbol, name, exchange, type
    """
    if not query or len(query) < 1:
        return []
    
    results = []
    seen_symbols = set()
    
    # Source 1: Yahoo Finance (Primary)
    yahoo_results = _search_yahoo(query, limit * 2)
    for r in yahoo_results:
        if r['symbol'] not in seen_symbols:
            results.append(r)
            seen_symbols.add(r['symbol'])
    
    # Source 2: Search curated lists (Indian, US, Canadian stocks)
    curated_results = _search_curated_lists(query)
    for r in curated_results:
        if r['symbol'] not in seen_symbols:
            results.append(r)
            seen_symbols.add(r['symbol'])
    
    # Source 3: Financial Modeling Prep (if API key available)
    if FMP_KEY and len(results) < limit:
        fmp_results = _search_fmp(query, limit)
        for r in fmp_results:
            if r['symbol'] not in seen_symbols:
                results.append(r)
                seen_symbols.add(r['symbol'])
    
    # Source 4: Alpha Vantage (if API key available and still need more)
    if ALPHA_VANTAGE_KEY and len(results) < limit:
        av_results = _search_alpha_vantage(query)
        for r in av_results:
            if r['symbol'] not in seen_symbols:
                results.append(r)
                seen_symbols.add(r['symbol'])
    
    return results[:limit]


def _search_curated_lists(query: str) -> List[Dict]:
    """Search through curated stock lists"""
    query_lower = query.lower()
    results = []
    
    all_curated = INDIAN_STOCKS + US_STOCKS + CANADIAN_STOCKS
    
    for stock in all_curated:
        # Match on symbol or name
        if (query_lower in stock['symbol'].lower() or 
            query_lower in stock['name'].lower()):
            results.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'exchange': stock['exchange'],
                'type': 'EQUITY',
                'score': 100  # High score for curated matches
            })
    
    return results


def _search_yahoo(query: str, limit: int = 20) -> List[Dict]:
    """Search Yahoo Finance API"""
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        
        params = {
            'q': query,
            'quotesCount': limit,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query',
            'enableNavLinks': False,
            'enableEnhancedTrivialQuery': True
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            
            results = []
            for quote in quotes:
                quote_type = quote.get('quoteType', '').upper()
                if quote_type in ['EQUITY', 'STOCK', 'FUND', 'ETF']:
                    name = quote.get('longname') or quote.get('shortname', '')
                    
                    if query.lower() in name.lower() or query.lower() in quote.get('symbol', '').lower():
                        results.append({
                            'symbol': quote.get('symbol', ''),
                            'name': name,
                            'exchange': quote.get('exchange', 'Unknown'),
                            'type': quote.get('quoteType', 'EQUITY'),
                            'score': quote.get('score', 0)
                        })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
        
        return []
    except Exception as e:
        print(f"Yahoo search error: {str(e)}")
        return []


def _search_fmp(query: str, limit: int = 20) -> List[Dict]:
    """Search Financial Modeling Prep API"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/search"
        params = {
            'query': query,
            'limit': limit,
            'apikey': FMP_KEY
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data:
                results.append({
                    'symbol': item.get('symbol', ''),
                    'name': item.get('name', ''),
                    'exchange': item.get('exchangeShortName', 'Unknown'),
                    'type': 'EQUITY',
                    'score': 50
                })
            
            return results
        
        return []
    except Exception as e:
        print(f"FMP search error: {str(e)}")
        return []


def _search_alpha_vantage(query: str) -> List[Dict]:
    """Search Alpha Vantage API"""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query,
            'apikey': ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('bestMatches', [])
            
            results = []
            for match in matches:
                results.append({
                    'symbol': match.get('1. symbol', ''),
                    'name': match.get('2. name', ''),
                    'exchange': match.get('4. region', 'Unknown'),
                    'type': match.get('3. type', 'EQUITY'),
                    'score': float(match.get('9. matchScore', 0)) * 100
                })
            
            return results
        
        return []
    except Exception as e:
        print(f"Alpha Vantage search error: {str(e)}")
        return []


def search_by_exchange(query: str, exchange_code: str, limit: int = 20) -> List[Dict]:
    """
    Search stocks filtered by specific exchange
    
    Args:
        query: Search term
        exchange_code: Exchange code (e.g., 'NAS', 'NYQ', 'NSE', 'BSE', 'LSE', 'TSE', 'JPX')
        limit: Max results
    
    Returns:
        Filtered list of stocks from that exchange
    """
    all_results = search_stocks(query, limit=50)
    
    # Filter by exchange
    filtered = [r for r in all_results if r['exchange'] == exchange_code]
    
    return filtered[:limit]


def get_popular_stocks_by_region(region: str = 'US') -> List[Dict]:
    """
    Get popular stocks by region
    
    Args:
        region: 'US', 'India', 'UK', 'Japan', 'Canada', 'Europe', 'Asia'
    
    Returns:
        List of popular stock symbols with metadata
    """
    popular_stocks = {
        'US': [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'exchange': 'NASDAQ'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'exchange': 'NYSE'},
            {'symbol': 'V', 'name': 'Visa Inc.', 'exchange': 'NYSE'},
            {'symbol': 'WMT', 'name': 'Walmart Inc.', 'exchange': 'NYSE'},
        ],
        'India': [
            {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries', 'exchange': 'NSE'},
            {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services', 'exchange': 'NSE'},
            {'symbol': 'INFY.NS', 'name': 'Infosys Limited', 'exchange': 'NSE'},
            {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank', 'exchange': 'NSE'},
            {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank', 'exchange': 'NSE'},
            {'symbol': 'BHARTIARTL.NS', 'name': 'Bharti Airtel', 'exchange': 'NSE'},
            {'symbol': 'SBIN.NS', 'name': 'State Bank of India', 'exchange': 'NSE'},
            {'symbol': 'HINDUNILVR.NS', 'name': 'Hindustan Unilever', 'exchange': 'NSE'},
            {'symbol': 'ITC.NS', 'name': 'ITC Limited', 'exchange': 'NSE'},
            {'symbol': 'LT.NS', 'name': 'Larsen & Toubro', 'exchange': 'NSE'},
        ],
        'UK': [
            {'symbol': 'SHEL.L', 'name': 'Shell plc', 'exchange': 'LSE'},
            {'symbol': 'AZN.L', 'name': 'AstraZeneca', 'exchange': 'LSE'},
            {'symbol': 'HSBA.L', 'name': 'HSBC Holdings', 'exchange': 'LSE'},
            {'symbol': 'BP.L', 'name': 'BP plc', 'exchange': 'LSE'},
            {'symbol': 'ULVR.L', 'name': 'Unilever', 'exchange': 'LSE'},
        ],
        'Japan': [
            {'symbol': '7203.T', 'name': 'Toyota Motor Corp', 'exchange': 'Tokyo'},
            {'symbol': '6758.T', 'name': 'Sony Group Corp', 'exchange': 'Tokyo'},
            {'symbol': '9984.T', 'name': 'SoftBank Group', 'exchange': 'Tokyo'},
            {'symbol': '6861.T', 'name': 'Keyence Corporation', 'exchange': 'Tokyo'},
            {'symbol': '7974.T', 'name': 'Nintendo Co Ltd', 'exchange': 'Tokyo'},
        ],
        'Canada': [
            {'symbol': 'SHOP.TO', 'name': 'Shopify Inc.', 'exchange': 'TSX'},
            {'symbol': 'RY.TO', 'name': 'Royal Bank of Canada', 'exchange': 'TSX'},
            {'symbol': 'TD.TO', 'name': 'Toronto-Dominion Bank', 'exchange': 'TSX'},
            {'symbol': 'ENB.TO', 'name': 'Enbridge Inc.', 'exchange': 'TSX'},
            {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'exchange': 'TSX'},
        ],
        'Europe': [
            {'symbol': 'ASML.AS', 'name': 'ASML Holding', 'exchange': 'Amsterdam'},
            {'symbol': 'SAP.DE', 'name': 'SAP SE', 'exchange': 'XETRA'},
            {'symbol': 'NVO', 'name': 'Novo Nordisk', 'exchange': 'NYSE (ADR)'},
            {'symbol': 'OR.PA', 'name': "L'Oréal", 'exchange': 'Euronext Paris'},
            {'symbol': 'MC.PA', 'name': 'LVMH', 'exchange': 'Euronext Paris'},
        ]
    }
    
    return popular_stocks.get(region, popular_stocks['US'])


def get_all_exchange_codes() -> Dict[str, str]:
    """
    Get mapping of exchange codes to full names
    
    Returns:
        Dict of exchange_code: full_name
    """
    return {
        # Americas
        'NAS': 'NASDAQ',
        'NYQ': 'NYSE',
        'PCX': 'NYSE Arca',
        'TSE': 'Toronto Stock Exchange',
        'TSX': 'Toronto Stock Exchange',
        'MEX': 'Mexican Stock Exchange',
        'SAO': 'B3 (Brazil)',
        'BUE': 'Buenos Aires Stock Exchange',
        
        # Europe
        'LSE': 'London Stock Exchange',
        'FGI': 'Frankfurt Stock Exchange',
        'PAR': 'Euronext Paris',
        'AMS': 'Euronext Amsterdam',
        'SWX': 'Swiss Exchange',
        'MIL': 'Borsa Italiana',
        'MCE': 'Madrid Stock Exchange',
        'CPH': 'Copenhagen Stock Exchange',
        'STO': 'Stockholm Stock Exchange',
        'OSL': 'Oslo Stock Exchange',
        
        # Asia-Pacific
        'NSE': 'National Stock Exchange of India',
        'BSE': 'Bombay Stock Exchange',
        'JPX': 'Tokyo Stock Exchange',
        'HKG': 'Hong Kong Stock Exchange',
        'SHA': 'Shanghai Stock Exchange',
        'SHE': 'Shenzhen Stock Exchange',
        'KSC': 'Korea Stock Exchange',
        'SES': 'Singapore Exchange',
        'ASX': 'Australian Securities Exchange',
        'TAI': 'Taiwan Stock Exchange',
        'THA': 'Stock Exchange of Thailand',
        'IDX': 'Indonesia Stock Exchange',
        
        # Middle East & Africa
        'SAU': 'Saudi Stock Exchange (Tadawul)',
        'DFM': 'Dubai Financial Market',
        'TLV': 'Tel Aviv Stock Exchange',
        'JNB': 'Johannesburg Stock Exchange',
    }


def format_search_results_for_display(results: List[Dict]) -> str:
    """
    Format search results as readable string
    
    Args:
        results: List of search results
    
    Returns:
        Formatted string for display
    """
    if not results:
        return "No results found"
    
    output = []
    for i, r in enumerate(results, 1):
        output.append(f"{i}. {r['symbol']} - {r['name']} ({r['exchange']})")
    
    return "\n".join(output)


# Test function
if __name__ == "__main__":
    # Test search
    print("Searching for 'Apple'...")
    results = search_stocks("Apple", limit=5)
    print(format_search_results_for_display(results))
    
    print("\n\nSearching for 'Tesla'...")
    results = search_stocks("Tesla", limit=5)
    print(format_search_results_for_display(results))
    
    print("\n\nSearching for 'Reliance' on NSE...")
    results = search_by_exchange("Reliance", "NSE", limit=5)
    print(format_search_results_for_display(results))
    
    print("\n\nPopular US stocks:")
    results = get_popular_stocks_by_region("US")
    print(format_search_results_for_display(results[:5]))
