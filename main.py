#!/usr/bin/env python3
"""
Market Intelligence System - Main Entry Point
Real-time market intelligence using free APIs and AI sentiment analysis
"""

import sys
import argparse
from datetime import datetime

# Import our modules
import config
from news_api import get_news, get_headlines_text
from market_data import get_technical_indicators
from sentiment_analyzer import get_sentiment_score
from signal_engine import generate_signal


def print_banner():
    """Print application banner"""
    print("=" * 70)
    print("  📈 MARKET INTELLIGENCE SYSTEM")
    print("  Real-time Buy/Hold/Sell Signal Generator")
    print("=" * 70)
    print()


def print_section(title):
    """Print section header"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)


def analyze_stock(symbol, verbose=False):
    """
    Perform complete analysis for a stock symbol
    
    Args:
        symbol (str): Stock ticker symbol
        verbose (bool): Show detailed information
        
    Returns:
        dict: Complete analysis results
    """
    symbol = symbol.upper()
    
    print(f"🔍 Analyzing: {symbol}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Fetch News
    print_section("📰 Fetching News")
    news_result = get_news(symbol)
    
    if news_result['success']:
        article_count = news_result.get('count', 0)
        print(f"✓ Found {article_count} recent articles")
        
        if verbose and article_count > 0:
            print("\nRecent Headlines:")
            for i, article in enumerate(news_result['articles'][:5], 1):
                print(f"  {i}. {article['title']}")
                print(f"     Source: {article['source']} | {article['publishedAt'][:10]}")
    else:
        print(f"✗ News fetch failed: {news_result['error']}")
        article_count = 0
    
    # Step 2: Analyze Sentiment
    print_section("💭 Analyzing Sentiment")
    
    if article_count > 0:
        # Extract headlines for sentiment analysis
        headlines = [article['title'] for article in news_result['articles'] if article.get('title')]
        sentiment_result = get_sentiment_score(headlines)
        
        if sentiment_result['success']:
            sentiment = sentiment_result['sentiment']
            print(f"✓ Overall Sentiment: {sentiment['label'].upper()}")
            print(f"  Score: {sentiment['overall_score']:.3f} (range: -1 to +1)")
            print(f"  Positive: {sentiment['positive_count']} | "
                  f"Neutral: {sentiment['neutral_count']} | "
                  f"Negative: {sentiment['negative_count']}")
        else:
            print(f"✗ Sentiment analysis failed: {sentiment_result['error']}")
            sentiment_result = {'success': False, 'sentiment': {'overall_score': 0.0, 'label': 'neutral'}}
    else:
        print("⊙ No news available for sentiment analysis")
        sentiment_result = {'success': False, 'sentiment': {'overall_score': 0.0, 'label': 'neutral'}}
    
    # Step 3: Fetch Technical Indicators
    print_section("📊 Fetching Technical Indicators")
    technical_result = get_technical_indicators(symbol)
    
    if technical_result['success']:
        # Display quote
        quote = technical_result.get('quote')
        if quote:
            print(f"✓ Current Price: ${quote['price']:.2f}")
            change_symbol = "▲" if quote['changesPercentage'] > 0 else "▼"
            print(f"  Change: {change_symbol} ${quote['change']:.2f} ({quote['changesPercentage']:.2f}%)")
            if verbose and quote.get('volume'):
                print(f"  Volume: {quote['volume']:,}")
        
        # Display RSI
        rsi = technical_result.get('rsi')
        if rsi is not None:
            rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Normal"
            print(f"✓ RSI (14): {rsi:.2f} [{rsi_status}]")
        else:
            print("⊙ RSI: Not available")
        
        # Display MACD
        macd = technical_result.get('macd', {})
        if macd.get('macd') is not None and macd.get('signal') is not None:
            macd_trend = "Bullish" if macd['macd'] > macd['signal'] else "Bearish"
            print(f"✓ MACD: {macd['macd']:.4f} | Signal: {macd['signal']:.4f} [{macd_trend}]")
            if verbose and macd.get('histogram'):
                print(f"  Histogram: {macd['histogram']:.4f}")
        else:
            print("⊙ MACD: Not available")
        
        # Show any errors
        if technical_result.get('errors') and verbose:
            print("\n⚠️  Technical data warnings:")
            for error in technical_result['errors']:
                print(f"  • {error}")
    else:
        print("✗ Failed to fetch technical indicators")
    
    # Step 4: Generate Signal
    print_section("🎯 SIGNAL GENERATION")
    signal_result = generate_signal(symbol, technical_result, sentiment_result, news_result)
    
    if signal_result.get('success', True):
        signal = signal_result['signal']
        confidence = signal_result['confidence']
        
        # Colorful signal display
        signal_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        
        print(f"\n  {signal_emoji.get(signal, '⚪')} SIGNAL: {signal}")
        print(f"  Confidence: {confidence:.1%}")
        
        print(f"\n  Reasoning:")
        for reason in signal_result.get('reasons', []):
            print(f"    • {reason}")
        
        # Show key metrics
        if verbose:
            print(f"\n  Key Metrics:")
            metrics = signal_result.get('metrics', {})
            for key, value in metrics.items():
                if value is not None:
                    if isinstance(value, float):
                        print(f"    {key}: {value:.4f}")
                    else:
                        print(f"    {key}: {value}")
    else:
        print(f"✗ Signal generation failed: {signal_result.get('error')}")
    
    print("\n" + "=" * 70)
    
    return {
        'symbol': symbol,
        'news': news_result,
        'sentiment': sentiment_result,
        'technical': technical_result,
        'signal': signal_result
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Market Intelligence System - Generate Buy/Hold/Sell signals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL
  python main.py TSLA --verbose
  python main.py MSFT -v

Make sure to set up your .env file with API keys before running.
        """
    )
    
    parser.add_argument(
        'symbol',
        type=str,
        help='Stock ticker symbol (e.g., AAPL, TSLA, MSFT)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Market Intelligence System v1.0'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate configuration
    if not config.validate_config():
        print("\n⚠️  Some API keys are missing. Results may be limited.")
        print("Please check .env.example and create your .env file.\n")
    
    # Run analysis
    try:
        result = analyze_stock(args.symbol, verbose=args.verbose)
        
        # Exit with success
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
