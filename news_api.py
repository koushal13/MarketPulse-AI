"""
News API Module
Fetches real-time news articles for a given stock symbol
"""

import requests
from datetime import datetime, timedelta
from config import NEWS_API_KEY, NEWS_API_BASE_URL, REQUEST_TIMEOUT


def get_news(symbol, days_back=7, max_articles=20):
    """
    Fetch recent news articles for a stock symbol
    
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL')
        days_back (int): Number of days to look back for news
        max_articles (int): Maximum number of articles to return
        
    Returns:
        dict: {
            'success': bool,
            'articles': list of dict with 'title', 'description', 'publishedAt', 'url',
            'error': str (if success=False)
        }
    """
    if not NEWS_API_KEY:
        return {
            'success': False,
            'articles': [],
            'error': 'NEWS_API_KEY not configured'
        }
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    # Build query - search for company name and ticker
    query = f"{symbol} stock OR {symbol} shares"
    
    params = {
        'q': query,
        'from': from_date.strftime('%Y-%m-%d'),
        'to': to_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': max_articles,
        'apiKey': NEWS_API_KEY
    }
    
    try:
        url = f"{NEWS_API_BASE_URL}/everything"
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        # Handle rate limiting
        if response.status_code == 429:
            return {
                'success': False,
                'articles': [],
                'error': 'Rate limit exceeded for News API'
            }
        
        response.raise_for_status()
        data = response.json()
        
        # Check API status
        if data.get('status') != 'ok':
            return {
                'success': False,
                'articles': [],
                'error': data.get('message', 'Unknown error from News API')
            }
        
        # Extract relevant article data
        articles = []
        for article in data.get('articles', []):
            articles.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'publishedAt': article.get('publishedAt', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown')
            })
        
        return {
            'success': True,
            'articles': articles,
            'count': len(articles),
            'error': None
        }
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'articles': [],
            'error': 'Request timeout while fetching news'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'articles': [],
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'articles': [],
            'error': f'Unexpected error: {str(e)}'
        }


def get_headlines_text(articles):
    """
    Extract and concatenate headlines for sentiment analysis
    
    Args:
        articles (list): List of article dictionaries
        
    Returns:
        str: Combined text of titles and descriptions
    """
    texts = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        
        if title:
            texts.append(title)
        if description:
            texts.append(description)
    
    return ' '.join(texts)
