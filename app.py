#!/usr/bin/env python3
"""
Market Intelligence System - Web Dashboard
Streamlit-based web interface for real-time stock analysis
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

# Import our modules
import config
from news_api import get_news
from market_data import get_technical_indicators
from sentiment_analyzer import get_sentiment_score
from signal_engine import generate_signal

# Page configuration
st.set_page_config(
    page_title="MarketPulse - Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .buy-signal {
        color: #00ff00;
        font-size: 40px;
        font-weight: bold;
    }
    .sell-signal {
        color: #ff0000;
        font-size: 40px;
        font-weight: bold;
    }
    .hold-signal {
        color: #ffaa00;
        font-size: 40px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def create_gauge_chart(value, title, max_value=100, ranges=None):
    """Create a gauge chart for metrics like RSI"""
    if ranges is None:
        ranges = [
            {'range': [0, 30], 'color': "lightgreen"},
            {'range': [30, 70], 'color': "yellow"},
            {'range': [70, 100], 'color': "lightcoral"}
        ]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': ranges,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_sentiment_chart(sentiment_data):
    """Create a bar chart for sentiment distribution"""
    if not sentiment_data or not sentiment_data.get('success'):
        return None
    
    sentiment = sentiment_data['sentiment']
    
    fig = go.Figure(data=[
        go.Bar(
            x=['Positive', 'Neutral', 'Negative'],
            y=[
                sentiment.get('positive_count', 0),
                sentiment.get('neutral_count', 0),
                sentiment.get('negative_count', 0)
            ],
            marker_color=['green', 'gray', 'red']
        )
    ])
    
    fig.update_layout(
        title='Sentiment Distribution',
        yaxis_title='Number of Articles',
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def analyze_stock_web(symbol):
    """Perform complete stock analysis for web display"""
    symbol = symbol.upper().strip()
    
    with st.spinner(f'🔍 Analyzing {symbol}...'):
        # Fetch news
        with st.spinner('📰 Fetching news...'):
            news_result = get_news(symbol)
        
        # Analyze sentiment
        with st.spinner('💭 Analyzing sentiment...'):
            if news_result['success'] and news_result.get('count', 0) > 0:
                headlines = [article['title'] for article in news_result['articles'] if article.get('title')]
                sentiment_result = get_sentiment_score(headlines)
            else:
                sentiment_result = {'success': False, 'sentiment': {'overall_score': 0.0, 'label': 'neutral'}}
        
        # Fetch technical indicators
        with st.spinner('📊 Fetching technical indicators...'):
            technical_result = get_technical_indicators(symbol)
        
        # Generate signal
        with st.spinner('🎯 Generating signal...'):
            signal_result = generate_signal(symbol, technical_result, sentiment_result, news_result)
    
    return {
        'symbol': symbol,
        'news': news_result,
        'sentiment': sentiment_result,
        'technical': technical_result,
        'signal': signal_result
    }


def main():
    """Main Streamlit app"""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📈 MarketPulse")
        st.subheader("Real-Time Market Intelligence System")
    with col2:
        st.write("")
        st.write("")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"⏰ {current_time}")
    
    # Sidebar
    st.sidebar.header("🔍 Stock Analysis")
    
    # Stock symbol input
    symbol = st.sidebar.text_input(
        "Enter Stock Symbol",
        value="AAPL",
        help="Enter a stock ticker symbol (e.g., AAPL, TSLA, MSFT)"
    ).upper()
    
    # Analyze button
    analyze_button = st.sidebar.button("🚀 Analyze", type="primary", use_container_width=True)
    
    # Configuration check
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ API Status")
    
    if config.NEWS_API_KEY and config.NEWS_API_KEY != "demo_key_please_replace":
        st.sidebar.success("✓ NewsAPI configured")
    else:
        st.sidebar.error("✗ NewsAPI not configured")
    
    if config.FMP_API_KEY and config.FMP_API_KEY != "demo_key_please_replace":
        st.sidebar.success("✓ FMP configured")
    else:
        st.sidebar.error("✗ FMP not configured")
    
    if config.ALPHA_VANTAGE_API_KEY and config.ALPHA_VANTAGE_API_KEY != "demo_key_please_replace":
        st.sidebar.success("✓ Alpha Vantage configured")
    else:
        st.sidebar.error("✗ Alpha Vantage not configured")
    
    # Quick links
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Quick Links")
    st.sidebar.markdown("- [Get NewsAPI Key](https://newsapi.org/)")
    st.sidebar.markdown("- [Get FMP Key](https://financialmodelingprep.com/)")
    st.sidebar.markdown("- [Get Alpha Vantage Key](https://www.alphavantage.co/)")
    
    # Popular stocks
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔥 Popular Stocks")
    popular_stocks = ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL", "AMZN", "META"]
    
    cols = st.sidebar.columns(3)
    for idx, stock in enumerate(popular_stocks):
        if cols[idx % 3].button(stock, use_container_width=True):
            symbol = stock
            analyze_button = True
    
    # Main content
    if analyze_button and symbol:
        # Perform analysis
        result = analyze_stock_web(symbol)
        
        # Display signal prominently
        st.markdown("---")
        signal = result['signal']['signal']
        confidence = result['signal']['confidence']
        
        signal_colors = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        
        signal_emoji = signal_colors.get(signal, '⚪')
        
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            st.markdown(f"### Stock Symbol")
            st.markdown(f"<div class='big-font'>{symbol}</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"### Signal")
            signal_class = signal.lower() + "-signal"
            st.markdown(f"<div class='{signal_class}'>{signal_emoji} {signal}</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"### Confidence")
            st.markdown(f"<div class='big-font'>{confidence:.0%}</div>", unsafe_allow_html=True)
        
        # Reasoning
        st.markdown("### 🎯 Signal Reasoning")
        reasons = result['signal'].get('reasons', [])
        for reason in reasons:
            st.write(f"• {reason}")
        
        st.markdown("---")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        # News count
        with col1:
            news_count = result['news'].get('count', 0) if result['news']['success'] else 0
            st.metric("📰 News Articles", news_count)
        
        # Sentiment
        with col2:
            if result['sentiment']['success']:
                sentiment_score = result['sentiment']['sentiment']['overall_score']
                sentiment_label = result['sentiment']['sentiment']['label'].upper()
                st.metric("💭 Sentiment", sentiment_label, f"{sentiment_score:.3f}")
            else:
                st.metric("💭 Sentiment", "N/A", "0.000")
        
        # RSI
        with col3:
            rsi = result['technical'].get('rsi')
            if rsi is not None:
                rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Normal"
                st.metric("📊 RSI", f"{rsi:.2f}", rsi_status)
            else:
                st.metric("📊 RSI", "N/A", "No data")
        
        # MACD
        with col4:
            macd_data = result['technical'].get('macd', {})
            if macd_data.get('macd') is not None:
                macd_trend = "Bullish" if macd_data['macd'] > macd_data.get('signal', 0) else "Bearish"
                st.metric("📈 MACD", f"{macd_data['macd']:.4f}", macd_trend)
            else:
                st.metric("📈 MACD", "N/A", "No data")
        
        st.markdown("---")
        
        # Detailed sections
        tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "💭 Sentiment", "📊 Technicals", "📋 Raw Data"])
        
        # News tab
        with tab1:
            if result['news']['success'] and result['news'].get('count', 0) > 0:
                st.subheader(f"Recent News for {symbol}")
                
                for idx, article in enumerate(result['news']['articles'], 1):
                    with st.expander(f"{idx}. {article['title']}", expanded=(idx <= 3)):
                        st.write(f"**Source:** {article['source']}")
                        st.write(f"**Published:** {article['publishedAt'][:10]}")
                        if article.get('description'):
                            st.write(f"**Description:** {article['description']}")
                        st.write(f"[Read more]({article['url']})")
            else:
                st.warning("No news articles found or error fetching news.")
                if result['news'].get('error'):
                    st.error(f"Error: {result['news']['error']}")
        
        # Sentiment tab
        with tab2:
            if result['sentiment']['success']:
                sentiment = result['sentiment']['sentiment']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Sentiment Analysis")
                    st.write(f"**Overall Label:** {sentiment['label'].upper()}")
                    st.write(f"**Score:** {sentiment['overall_score']:.3f} (range: -1 to +1)")
                    st.write(f"**Total Articles:** {sentiment.get('total_articles', 0)}")
                    
                    # Sentiment score interpretation
                    if sentiment['overall_score'] > 0.3:
                        st.success("✓ Strong positive sentiment")
                    elif sentiment['overall_score'] > 0.1:
                        st.info("⊙ Slightly positive sentiment")
                    elif sentiment['overall_score'] < -0.3:
                        st.error("✗ Strong negative sentiment")
                    elif sentiment['overall_score'] < -0.1:
                        st.warning("⊙ Slightly negative sentiment")
                    else:
                        st.info("⊙ Neutral sentiment")
                
                with col2:
                    # Sentiment chart
                    sentiment_chart = create_sentiment_chart(result['sentiment'])
                    if sentiment_chart:
                        st.plotly_chart(sentiment_chart, use_container_width=True)
            else:
                st.warning("Sentiment analysis not available.")
                if result['sentiment'].get('error'):
                    st.error(f"Error: {result['sentiment']['error']}")
        
        # Technicals tab
        with tab3:
            st.subheader("Technical Indicators")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # RSI gauge
                rsi = result['technical'].get('rsi')
                if rsi is not None:
                    st.plotly_chart(create_gauge_chart(rsi, "RSI (Relative Strength Index)"), use_container_width=True)
                    
                    if rsi < 30:
                        st.success("✓ RSI indicates oversold conditions - potential buy opportunity")
                    elif rsi > 70:
                        st.error("✗ RSI indicates overbought conditions - potential sell signal")
                    else:
                        st.info("⊙ RSI in normal range")
                else:
                    st.warning("RSI data not available")
            
            with col2:
                # MACD info
                macd_data = result['technical'].get('macd', {})
                if macd_data.get('macd') is not None:
                    st.markdown("#### MACD (Moving Average Convergence Divergence)")
                    st.write(f"**MACD Line:** {macd_data['macd']:.4f}")
                    st.write(f"**Signal Line:** {macd_data.get('signal', 0):.4f}")
                    st.write(f"**Histogram:** {macd_data.get('histogram', 0):.4f}")
                    
                    if macd_data['macd'] > macd_data.get('signal', 0):
                        st.success("✓ Bullish MACD crossover")
                    else:
                        st.warning("⊙ Bearish MACD trend")
                else:
                    st.warning("MACD data not available")
            
            # Quote info
            quote = result['technical'].get('quote')
            if quote:
                st.markdown("---")
                st.markdown("#### Price Information")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Price", f"${quote['price']:.2f}")
                with col2:
                    st.metric("Change", f"${quote['change']:.2f}")
                with col3:
                    st.metric("Change %", f"{quote['changesPercentage']:.2f}%")
                with col4:
                    if quote.get('volume'):
                        st.metric("Volume", f"{quote['volume']:,}")
            
            # Errors
            if result['technical'].get('errors'):
                with st.expander("⚠️ Technical Data Warnings"):
                    for error in result['technical']['errors']:
                        st.warning(error)
        
        # Raw data tab
        with tab4:
            st.subheader("Complete Analysis Data")
            st.json(result)
    
    else:
        # Welcome screen
        st.markdown("---")
        st.markdown("""
        ## 👋 Welcome to MarketPulse!
        
        **MarketPulse** is a real-time market intelligence system that generates **Buy/Hold/Sell** signals 
        for stocks using free APIs and AI-powered sentiment analysis.
        
        ### 🚀 How to Use:
        1. Enter a stock symbol in the sidebar (e.g., AAPL, TSLA, MSFT)
        2. Click the **Analyze** button
        3. View the signal, reasoning, and detailed analysis
        
        ### 📊 What We Analyze:
        - **News Articles**: Latest news from NewsAPI
        - **Sentiment**: AI-powered analysis using HuggingFace models
        - **Technical Indicators**: RSI, MACD from multiple sources
        - **Smart Signals**: Combines all data to generate Buy/Hold/Sell recommendations
        
        ### 🎯 Signal Logic:
        - **BUY**: Positive sentiment + RSI oversold + MACD bullish
        - **SELL**: Negative sentiment OR RSI overbought
        - **HOLD**: Neutral or mixed signals
        
        ---
        
        **Ready to start?** Enter a stock symbol in the sidebar and click Analyze! 🚀
        """)
        
        # Show example stocks
        st.markdown("### 🔥 Try These Popular Stocks:")
        
        cols = st.columns(4)
        examples = [
            ("AAPL", "Apple Inc."),
            ("TSLA", "Tesla, Inc."),
            ("MSFT", "Microsoft Corp."),
            ("NVDA", "NVIDIA Corp.")
        ]
        
        for idx, (ticker, name) in enumerate(examples):
            with cols[idx]:
                st.info(f"**{ticker}**\n\n{name}")


if __name__ == '__main__':
    main()
