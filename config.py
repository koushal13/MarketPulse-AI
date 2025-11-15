"""
Configuration module for Market Intelligence System
Loads API keys from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
FMP_KEY = os.getenv('FMP_KEY')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

# Backwards compatibility aliases (deprecated)
FMP_API_KEY = FMP_KEY
ALPHA_VANTAGE_API_KEY = ALPHA_VANTAGE_KEY

# API Endpoints
NEWS_API_BASE_URL = "https://newsapi.org/v2"
FMP_API_BASE_URL = "https://financialmodelingprep.com/api/v3"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Signal Generation Rules (configurable)
SIGNAL_RULES = {
    'BUY': {
        'sentiment_threshold': 0.3,  # Positive sentiment score
        'rsi_max': 30,  # Oversold
        'macd_signal': 'bullish'  # MACD line > signal line
    },
    'SELL': {
        'sentiment_threshold': -0.3,  # Negative sentiment score
        'rsi_min': 70  # Overbought
    }
    # HOLD is everything else
}

# Request timeouts (seconds)
REQUEST_TIMEOUT = 10

# Validate API keys
def validate_config():
    """Check if required API keys are set"""
    missing_keys = []
    
    if not NEWS_API_KEY:
        missing_keys.append('NEWS_API_KEY')
    if not FMP_API_KEY:
        missing_keys.append('FMP_API_KEY')
    if not ALPHA_VANTAGE_API_KEY:
        missing_keys.append('ALPHA_VANTAGE_API_KEY')
    
    if missing_keys:
        print(f"⚠️  Warning: Missing API keys: {', '.join(missing_keys)}")
        print("Please set them in your .env file")
        return False
    
    return True
