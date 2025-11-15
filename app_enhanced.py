#!/usr/bin/env python3
"""
MarketPulse - Enhanced Web Dashboard
Real-time stock analysis with AI insights, live prices, and educational tooltips
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pandas as pd
import time

# Import our modules
import config
from news_api import get_news
from market_data import get_technical_indicators
from sentiment_analyzer import get_sentiment_score
from signal_engine import generate_signal
from multi_source_price import get_live_price, get_historical_data, get_company_info, get_exchange_info
from key_statistics import get_key_statistics, format_large_number, format_percentage, format_ratio
from ai_analysis import get_ai_analysis, AIAnalyzer
from enhanced_indicators import get_enhanced_technical_indicators

# Page configuration
st.set_page_config(
    page_title="MarketPulse - AI Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling
st.markdown("""
    <style>
    .big-font {
        font-size: 50px !important;
        font_weight: bold;
    }
    .price-display {
        font-size: 45px !important;
        font-weight: bold;
        line-height: 1.2;
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
    .tooltip-text {
        font-size: 14px;
        color: #666;
        font-style: italic;
    }
    .metric-explanation {
        background-color: #e8f4f8;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .ai-insight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .exchange-badge {
        background-color: #2196F3;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Educational content
INDICATOR_EXPLANATIONS = {
    'RSI': {
        'name': 'RSI (Relative Strength Index)',
        'description': 'Measures the speed and magnitude of price changes on a scale of 0-100.',
        'interpretation': '• Below 30 = Oversold (potential buy opportunity)\n• Above 70 = Overbought (potential sell signal)\n• 30-70 = Normal range',
        'why_important': 'RSI helps identify when a stock might be overvalued or undervalued based on recent price movements.',
        'emoji': '📊'
    },
    'MACD': {
        'name': 'MACD (Moving Average Convergence Divergence)',
        'description': 'Shows the relationship between two moving averages of a stock\'s price.',
        'interpretation': '• MACD > Signal line = Bullish (upward momentum)\n• MACD < Signal line = Bearish (downward momentum)\n• Histogram shows strength of trend',
        'why_important': 'MACD reveals changes in trend direction, strength, and momentum, helping time entry and exit points.',
        'emoji': '📈'
    },
    'Sentiment': {
        'name': 'AI Sentiment Analysis',
        'description': 'Uses machine learning to analyze the tone and emotion in news articles.',
        'interpretation': '• Positive (>0.1) = Bullish news coverage\n• Neutral (-0.1 to 0.1) = Mixed or balanced news\n• Negative (<-0.1) = Bearish news coverage',
        'why_important': 'Market sentiment often precedes price movements as it reflects collective investor psychology.',
        'emoji': '💭'
    },
    'Volume': {
        'name': 'Trading Volume',
        'description': 'The number of shares traded during a specific time period.',
        'interpretation': '• High volume + price increase = Strong buying pressure\n• High volume + price decrease = Strong selling pressure\n• Low volume = Weak conviction in price movement',
        'why_important': 'Volume confirms price trends. Large volume changes can signal trend reversals or continuations.',
        'emoji': '📊'
    },
    'PE_Ratio': {
        'name': 'P/E Ratio (Price-to-Earnings)',
        'description': 'Compares a company\'s stock price to its earnings per share.',
        'interpretation': '• Low P/E = Potentially undervalued or slow growth\n• High P/E = Potentially overvalued or high growth expectations\n• Compare to industry average',
        'why_important': 'P/E ratio helps determine if a stock is fairly valued relative to its earnings.',
        'emoji': '💰'
    }
}


def show_indicator_explanation(indicator_key):
    """Display educational explanation for an indicator"""
    if indicator_key in INDICATOR_EXPLANATIONS:
        info = INDICATOR_EXPLANATIONS[indicator_key]
        with st.expander(f"{info['emoji']} Learn: {info['name']}", expanded=False):
            st.markdown(f"**What it is:**\n{info['description']}")
            st.markdown(f"**How to read it:**\n{info['interpretation']}")
            st.markdown(f"**Why it matters:**\n{info['why_important']}")


def create_price_chart(hist_data, symbol):
    """Create interactive candlestick chart with volume"""
    if hist_data is None or hist_data.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{symbol} Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Volume bars
    colors = ['red' if hist_data['Close'][i] < hist_data['Open'][i] else 'green' 
              for i in range(len(hist_data))]
    
    fig.add_trace(
        go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name='Volume',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig


def create_gauge_chart(value, title, max_value=100, ranges=None):
    """Create a gauge chart for metrics like RSI"""
    if ranges is None:
        ranges = [
            {'range': [0, 30], 'color': "lightgreen"},
            {'range': [30, 70], 'color': "yellow"},
            {'range': [70, 100], 'color': "lightcoral"}
        ]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
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
            marker_color=['#00ff00', '#888888', '#ff0000'],
            text=[
                sentiment.get('positive_count', 0),
                sentiment.get('neutral_count', 0),
                sentiment.get('negative_count', 0)
            ],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='News Sentiment Distribution',
        yaxis_title='Number of Articles',
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def analyze_stock_web(symbol, exchange='NYSE'):
    """Perform complete stock analysis for web display"""
    from stock_price import format_symbol_for_exchange
    
    # Format symbol for the selected exchange
    formatted_symbol = format_symbol_for_exchange(symbol, exchange)
    
    with st.spinner(f'🔍 Analyzing {symbol} on {exchange}...'):
        # Fetch live price (tries all available APIs automatically!)
        with st.spinner('💰 Fetching live price from multiple sources...'):
            price_success, price_data_result = get_live_price(symbol, exchange)
            price_result = {'success': price_success, 'data': price_data_result if price_success else {}}
        
        # Fetch news
        with st.spinner('📰 Fetching news...'):
            news_result = get_news(symbol)  # Use base symbol for news
        
        # Analyze sentiment
        with st.spinner('💭 Analyzing sentiment...'):
            if news_result['success'] and news_result.get('count', 0) > 0:
                headlines = [article['title'] for article in news_result['articles'] if article.get('title')]
                sentiment_result = get_sentiment_score(headlines)
            else:
                sentiment_result = {'success': False, 'sentiment': {'overall_score': 0.0, 'label': 'neutral'}}
        
        # Get historical data for charts (tries all available APIs automatically!)
        with st.spinner('📈 Fetching historical data from multiple sources...'):
            hist_success, hist_data = get_historical_data(symbol, exchange, period='3mo')
            hist_result = {'success': hist_success, 'data': hist_data if hist_success else pd.DataFrame()}
        
        # Fetch technical indicators with enhanced calculation
        with st.spinner('📊 Fetching technical indicators...'):
            hist_data_for_calc = hist_result['data'] if hist_result['success'] else None
            technical_result = get_enhanced_technical_indicators(symbol, hist_data_for_calc)
        
        # Get key statistics (comprehensive financial metrics) - BEFORE signal generation
        with st.spinner('📊 Fetching key statistics...'):
            stats_result = get_key_statistics(symbol, exchange)
        
        # Generate signal (pass price and stats for better accuracy)
        with st.spinner('🎯 Generating signal...'):
            signal_result = generate_signal(symbol, technical_result, sentiment_result, news_result, price_result.get('data'), stats_result)
        
        # Get AI analysis (if available)
        with st.spinner('🤖 Getting AI insights...'):
            ai_result = get_ai_analysis(symbol, technical_result, sentiment_result, news_result, price_result)
        
        # Get company info (with exchange for proper symbol formatting)
        company_result = get_company_info(symbol, exchange)
        
        # Get exchange info (with exchange parameter for accurate currency/timezone)
        exchange_result = get_exchange_info(symbol, exchange)
    
    return {
        'symbol': symbol,
        'price': price_result,
        'news': news_result,
        'sentiment': sentiment_result,
        'technical': technical_result,
        'signal': signal_result,
        'ai': ai_result,
        'company': company_result,
        'exchange': exchange_result,
        'historical': hist_result,
        'statistics': stats_result
    }


def main():
    """Main Streamlit app"""
    
    # Header with live clock
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.title("📈 MarketPulse AI")
        st.caption("Powered by AI • Real-time Data • Free Forever")
    with col2:
        st.write("")
        st.write("")
    with col3:
        # Live clock using HTML/JS that updates independently
        import streamlit.components.v1 as components
        
        components.html("""
            <div style='text-align: right; padding: 10px;'>
                <div id="clock-time" style='font-size: 28px; font-weight: bold; font-family: monospace; color: #1f77b4; letter-spacing: 2px;'>00:00:00</div>
                <div id="clock-tz" style='font-size: 11px; color: #888;'>Loading...</div>
            </div>
            <script>
                function updateClock() {
                    const now = new Date();
                    const hours = String(now.getHours()).padStart(2, '0');
                    const minutes = String(now.getMinutes()).padStart(2, '0');
                    const seconds = String(now.getSeconds()).padStart(2, '0');
                    const timeStr = hours + ':' + minutes + ':' + seconds;
                    
                    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    
                    const timeEl = document.getElementById('clock-time');
                    const tzEl = document.getElementById('clock-tz');
                    
                    if (timeEl) timeEl.textContent = timeStr;
                    if (tzEl) tzEl.textContent = tz;
                }
                
                updateClock();
                setInterval(updateClock, 1000);
            </script>
        """, height=70)
    
    # Sidebar
    st.sidebar.header("🔍 Stock Analysis")
    # === PROFESSIONAL SIDEBAR ===
    st.sidebar.markdown("### 📈 Market Intelligence")
    
    # Exchange selector - Clean and minimal
    exchange = st.sidebar.selectbox(
        "Stock Exchange",
        options=[
            "NYSE/NASDAQ (USA)",
            "TSX (Toronto, Canada)",
            "NSE (India)",
            "BSE (India)"
        ],
        label_visibility="collapsed"
    )
    
    # Map selection to exchange code
    exchange_map = {
        "NYSE/NASDAQ (USA)": "NYSE",
        "TSX (Toronto, Canada)": "TSX",
        "NSE (India)": "NSE",
        "BSE (India)": "BSE"
    }
    
    selected_exchange = exchange_map[exchange]
    
    # Stock symbol input - Clean
    default_symbol = "AAPL" if selected_exchange == "NYSE" else "RY" if selected_exchange == "TSX" else "RELIANCE"
    symbol = st.sidebar.text_input(
        "Stock Symbol",
        value=default_symbol,
        placeholder="Enter ticker"
    ).upper()
    
    st.sidebar.markdown("---")
    
    # Portfolio Position (for HOLD/SELL recommendations)
    st.sidebar.markdown("**📊 Your Position** (optional)")
    holding_position = st.sidebar.checkbox("I own this stock", key=f"holding_{symbol}")
    
    purchase_price = None
    purchase_quantity = None
    if holding_position:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            purchase_price = st.number_input("Buy Price", min_value=0.01, value=100.0, step=0.01, key=f"price_{symbol}")
        with col2:
            purchase_quantity = st.number_input("Shares", min_value=1, value=10, step=1, key=f"qty_{symbol}")
    
    # Analyze button - Prominent
    analyze_button = st.sidebar.button("⚡ Analyze", type="primary", use_container_width=True)
    
    st.sidebar.markdown("---")
    
    # Quick picks - Professional
    st.sidebar.markdown("**Quick Select**")
    
    if selected_exchange == "TSX":
        popular_stocks = [("RY", "Royal Bank"), ("SHOP", "Shopify"), ("TD", "TD Bank"), ("ENB", "Enbridge")]
    elif selected_exchange == "NSE":
        popular_stocks = [("RELIANCE", "Reliance"), ("TCS", "TCS"), ("INFY", "Infosys"), ("HDFCBANK", "HDFC")]
    elif selected_exchange == "BSE":
        popular_stocks = [("RELIANCE", "Reliance"), ("TCS", "TCS"), ("INFY", "Infosys"), ("HDFCBANK", "HDFC")]
    else:  # NYSE/NASDAQ
        popular_stocks = [("AAPL", "Apple"), ("TSLA", "Tesla"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA")]
    
    cols = st.sidebar.columns(2)
    for idx, (stock, name) in enumerate(popular_stocks):
        if cols[idx % 2].button(stock, use_container_width=True, key=f"q_{stock}"):
            symbol = stock
            analyze_button = True
    
    # Advanced options - Collapsed
    with st.sidebar.expander("⚙️ Settings", expanded=False):
        chart_period = st.selectbox("Chart Period", ['1mo', '3mo', '6mo', '1y'], index=1)
        show_ai = st.checkbox("AI Analysis", value=True)
        show_education = st.checkbox("Learning Tips", value=True)
    
    st.sidebar.markdown("---")
    
    # Data sources - Minimal
    with st.sidebar.expander("📡 Data Sources"):
        st.caption("✓ Multi-source price data")
        st.caption("✓ 8+ API fallbacks")
        st.caption("✓ Real-time news")
    
    # Main content
    if analyze_button and symbol:
        # Perform analysis
        result = analyze_stock_web(symbol, selected_exchange)
        
        # Extract price data early to avoid UnboundLocalError
        price_data = result['price']['data'] if result['price']['success'] else None
        
        # Get currency info
        exchange_info = result['exchange']
        exchange_name = exchange_info.get('exchange', 'Unknown')
        currency = exchange_info.get('currency', 'USD')
        
        # Map currency codes to symbols
        currency_symbols = {
            'USD': '$',
            'CAD': 'C$',
            'INR': '₹',
            'GBP': '£',
            'EUR': '€',
            'JPY': '¥',
            'CNY': '¥',
            'HKD': 'HK$',
            'AUD': 'A$'
        }
        currency_symbol = currency_symbols.get(currency, '$')
        
        # Company header with exchange badge
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if result['company']['success'] and result['company']['data'].get('name'):
                company_name = result['company']['data']['name']
                st.markdown(f"# {company_name}")
            else:
                st.markdown(f"# {symbol}")
            
            st.markdown(f"<span class='exchange-badge'>{exchange_name}</span> • **{symbol}** • {currency}", unsafe_allow_html=True)
        
        with col2:
            # Show live price prominently in header with local currency
            if result['price']['success'] and price_data:
                change_color = "#00ff00" if price_data['change'] >= 0 else "#ff0000"
                change_symbol = "▲" if price_data['change'] >= 0 else "▼"
                st.markdown(
                    f"<div style='text-align: right;'>"
                    f"<div style='font-size: 36px; font-weight: bold; color: {change_color};'>"
                    f"{currency_symbol}{price_data['price']:.2f}"
                    f"</div>"
                    f"<div style='font-size: 14px; color: {change_color};'>"
                    f"{change_symbol} {abs(price_data['change']):.2f} ({price_data['change_percent']:+.2f}%)"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        # Live Price Section
        if result['price']['success'] and price_data:
            st.markdown("### 📊 Trading Information")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Open", f"{currency_symbol}{price_data.get('open', 0):.2f}" if price_data.get('open') else "N/A")
            
            with col2:
                st.metric("Close", f"{currency_symbol}{price_data.get('price', 0):.2f}" if price_data.get('price') else "N/A")
            
            with col3:
                st.metric("High", f"{currency_symbol}{price_data.get('high', 0):.2f}" if price_data.get('high') else "N/A")
            
            with col4:
                st.metric("Low", f"{currency_symbol}{price_data.get('low', 0):.2f}" if price_data.get('low') else "N/A")
            
            with col5:
                st.metric("Prev Close", f"{currency_symbol}{price_data.get('previous_close', 0):.2f}" if price_data.get('previous_close') else "N/A")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if price_data.get('volume'):
                    volume_m = price_data['volume'] / 1_000_000
                    st.metric("Volume", f"{volume_m:.1f}M")
                else:
                    st.metric("Volume", "N/A")
            
            with col2:
                # Get market cap from stats data, not price data
                market_cap = None
                if result['statistics']['success']:
                    market_cap = result['statistics']['data'].get('marketCap')
                
                if market_cap:
                    if market_cap >= 1e12:  # Trillions
                        mcap_display = f"{currency_symbol}{market_cap/1e12:.2f}T"
                    elif market_cap >= 1e9:  # Billions
                        mcap_display = f"{currency_symbol}{market_cap/1e9:.2f}B"
                    else:  # Millions
                        mcap_display = f"{currency_symbol}{market_cap/1e6:.2f}M"
                    st.metric("Market Cap", mcap_display)
                else:
                    st.metric("Market Cap", "N/A")
            
            with col3:
                # Get P/E from stats data
                pe_ratio = None
                if result['statistics']['success']:
                    pe_ratio = result['statistics']['data'].get('trailingPE')
                
                if pe_ratio:
                    st.metric("P/E Ratio", f"{pe_ratio:.2f}")
                else:
                    st.metric("P/E Ratio", "N/A")
            
            with col4:
                # Get dividend yield from stats data
                div_yield = None
                if result['statistics']['success']:
                    div_yield = result['statistics']['data'].get('dividendYield')
                
                if div_yield:
                    st.metric("Dividend Yield", f"{div_yield*100:.2f}%")
                else:
                    st.metric("Dividend Yield", "N/A")
        else:
            st.warning(f"⚠️ Unable to fetch live price data")
            st.info("💡 **Tip:** Yahoo Finance may be experiencing issues. The data shown is from historical prices. Try again in a moment or use historical price data below.")
            
            # Try to get basic price from historical data
            if result['historical']['success'] and not result['historical']['data'].empty:
                hist = result['historical']['data']
                latest_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                change = latest_price - prev_price
                change_pct = (change / prev_price * 100) if prev_price else 0
                
                st.markdown("### 📊 Latest Available Price (from history)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Price", f"{currency_symbol}{latest_price:.2f}")
                with col2:
                    st.metric("Change", f"{currency_symbol}{change:.2f}", f"{change_pct:+.2f}%")
                with col3:
                    st.metric("High", f"{currency_symbol}{hist['High'].iloc[-1]:.2f}")
                with col4:
                    st.metric("Low", f"{currency_symbol}{hist['Low'].iloc[-1]:.2f}")
        
        st.markdown("---")
        
        # Signal Display
        signal = result['signal'].get('signal', 'HOLD') if isinstance(result['signal'], dict) else 'HOLD'
        confidence = result['signal'].get('confidence', 0.5) if isinstance(result['signal'], dict) else 0.5
        
        # Ensure confidence is never None
        if confidence is None:
            confidence = 0.5
        
        # Check for error in signal generation
        if signal == 'ERROR':
            st.error("⚠️ **Signal Generation Error**")
            error_msg = result['signal'].get('error', 'Unknown error occurred')
            st.error(f"Error details: {error_msg}")
            st.info("💡 The system will continue to show other data available.")
        
        signal_colors = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡', 'WAIT': '⏸️', 'ERROR': '⚪'}
        signal_emoji = signal_colors.get(signal, '⚪')
        
        # Adjust signal based on position
        original_signal = signal
        if holding_position and purchase_price:
            current_price = result['price']['data'].get('price') if result['price']['success'] else None
            if current_price:
                position_pnl_pct = ((current_price - purchase_price) / purchase_price) * 100
                
                # If signal is HOLD but user doesn't own it, change to suggestion
                if signal == 'HOLD' and not holding_position:
                    signal = 'WAIT'
                    signal_emoji = '⏸️'
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"### Signal")
            signal_class = signal.lower() + "-signal"
            st.markdown(f"<div class='{signal_class}'>{signal_emoji} {signal}</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"### Confidence")
            st.markdown(f"<div class='big-font'>{confidence:.0%}</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"### Risk Level")
            risk_level = result['signal'].get('risk_level', 'Medium')
            risk_color = "green" if risk_level == "Low" else "orange" if risk_level == "Medium" else "red"
            st.markdown(f"<div class='big-font' style='color: {risk_color};'>{risk_level}</div>", unsafe_allow_html=True)
        
        # Show position P&L if user owns this stock
        if holding_position and purchase_price:
            current_price = result['price']['data'].get('price') if result['price']['success'] else None
            if current_price and purchase_quantity:
                st.markdown("---")
                st.markdown("### 💼 Your Position")
                
                position_value = current_price * purchase_quantity
                cost_basis = purchase_price * purchase_quantity
                pnl = position_value - cost_basis
                pnl_pct = ((current_price - purchase_price) / purchase_price) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Purchase Price", f"{currency_symbol}{purchase_price:.2f}")
                with col2:
                    st.metric("Current Price", f"{currency_symbol}{current_price:.2f}")
                with col3:
                    pnl_color = "normal" if pnl >= 0 else "inverse"
                    st.metric("P&L", f"{currency_symbol}{abs(pnl):.2f}", f"{pnl_pct:+.2f}%", delta_color=pnl_color)
                with col4:
                    st.metric("Position Value", f"{currency_symbol}{position_value:.2f}")
                
                # Position-specific advice
                if original_signal == 'SELL':
                    st.warning(f"⚠️ **Recommendation:** Consider selling your {purchase_quantity} shares")
                elif original_signal == 'HOLD':
                    if pnl_pct > 15:
                        st.success(f"✓ **Strong Position:** Up {pnl_pct:.1f}% - consider taking partial profits")
                    elif pnl_pct < -10:
                        st.error(f"⚠️ **Review Position:** Down {pnl_pct:.1f}% - monitor stop loss levels")
                    else:
                        st.info(f"⊙ **Hold Position:** Monitor for exit signals")
        
        # Reasoning
        st.markdown("### 🎯 Signal Reasoning")
        
        # Adjust reasoning if no position and signal is HOLD
        if not holding_position and original_signal == 'HOLD':
            st.info("**💡 You don't own this stock yet**")
            st.write("• Wait for a clearer BUY signal before entering")
            st.write("• No action needed - monitor for better entry opportunity")
        
        reasons = result['signal'].get('reasons', [])
        for reason in reasons:
            st.write(f"• {reason}")
        
        # Technical Indicators Summary Table
        st.markdown("---")
        st.markdown("### 📊 Technical Indicators Summary")
        
        # Add beginner's guide expander
        with st.expander("📚 **New to Trading? Click here to learn what these indicators mean**"):
            st.markdown("""
            ### Understanding Technical Indicators (Beginner's Guide)
            
            **What are Technical Indicators?**  
            Technical indicators are mathematical calculations based on price, volume, or both. They help you understand:
            - Is the stock **expensive or cheap** right now?
            - Is the price **going up or down** (trend)?
            - Is the price movement **strong or weak** (momentum)?
            - Should I **buy, sell, or wait**?
            
            ---
            
            #### 1️⃣ **RSI (Relative Strength Index)** - *"Is it too expensive or too cheap?"*
            - **What it measures:** How overbought (expensive) or oversold (cheap) a stock is
            - **Scale:** 0 to 100
            - **Simple Rule:**
              - **Below 30:** Oversold = Stock is cheap, likely to bounce up soon (BUY signal)
              - **Above 70:** Overbought = Stock is expensive, likely to pull back (SELL signal)
              - **Between 40-60:** Neutral zone, no extreme conditions
            - **Example:** If RSI = 25, the stock has fallen a lot and is "oversold" - good time to buy
            
            ---
            
            #### 2️⃣ **MACD (Moving Average Convergence Divergence)** - *"Is the trend gaining or losing strength?"*
            - **What it measures:** Momentum of the trend (is the price move accelerating or slowing down?)
            - **How it works:** Compares two moving averages (fast vs slow)
            - **Simple Rule:**
              - **MACD line ABOVE signal line:** Bullish = Upward momentum (BUY)
              - **MACD line BELOW signal line:** Bearish = Downward momentum (SELL)
              - **Lines crossing:** Trend is changing direction
            - **Histogram (the bars):** Shows strength - bigger bars = stronger momentum
            - **Example:** MACD 1.5 / Signal 1.2 means bullish (1.5 > 1.2) with positive momentum
            
            ---
            
            #### 3️⃣ **Bollinger Bands** - *"Is the price at an extreme level?"*
            - **What it measures:** Price volatility and extreme price levels
            - **How it works:** Creates an upper and lower band around the price
            - **Simple Rule:**
              - **Price near UPPER band (>80%):** Stock has risen a lot, may pull back (SELL)
              - **Price near LOWER band (<20%):** Stock has fallen a lot, may bounce (BUY)
              - **Price in MIDDLE (40-60%):** Normal range, no extreme
            - **Why it matters:** Prices tend to "bounce" between the bands like a rubber band
            - **Example:** 85% means price is near the top band - it's stretched high and risky
            
            ---
            
            #### 4️⃣ **Moving Averages (SMA-20, SMA-50)** - *"What direction is the trend?"*
            - **What it measures:** Average price over last 20 or 50 days - smooths out noise
            - **How it works:** Shows the overall trend direction
            - **Simple Rule:**
              - **Price ABOVE both MAs:** Uptrend = Stock is rising (BULLISH)
              - **Price BELOW both MAs:** Downtrend = Stock is falling (BEARISH)
              - **Price between MAs:** Consolidating = Wait for clearer direction
            - **Why it matters:** Trends tend to continue - "the trend is your friend"
            - **Example:** Price at $150, SMA-20 at $145, SMA-50 at $140 = Strong uptrend
            
            ---
            
            #### 5️⃣ **Stochastic Oscillator** - *"Where is the price relative to recent highs/lows?"*
            - **What it measures:** Current price vs recent price range (last 14 days)
            - **Scale:** 0 to 100
            - **Simple Rule:**
              - **Above 80:** Overbought = Price very high, may reverse down (SELL)
              - **Below 20:** Oversold = Price very low, may bounce up (BUY)
              - **40-60:** Neutral zone
            - **Similar to RSI but more sensitive** (changes faster)
            - **Example:** Stoch = 15 means price is at the bottom of recent range - likely to bounce
            
            ---
            
            #### 6️⃣ **ADX (Average Directional Index)** - *"How strong is the trend?"*
            - **What it measures:** Strength of the trend (NOT direction, just how strong)
            - **Scale:** 0 to 100
            - **Simple Rule:**
              - **Above 25:** Strong trend = Trade with the trend (follow it)
              - **Below 25:** Weak/no trend = Sideways market, avoid trading
            - **DI+ vs DI-:** Shows if strong trend is UP (DI+ higher) or DOWN (DI- higher)
            - **Why it matters:** Strong trends are easier to profit from
            - **Example:** ADX = 35 with DI+ > DI- means strong uptrend - safe to buy
            
            ---
            
            #### 7️⃣ **ATR (Average True Range)** - *"How much does this stock move daily?"*
            - **What it measures:** Average daily price movement (volatility)
            - **Scale:** Dollars (absolute) or % of price
            - **Simple Rule:**
              - **High ATR (>3%):** Stock is volatile = Bigger moves, higher risk, use wider stop-losses
              - **Low ATR (<1%):** Stock is stable = Smaller moves, lower risk, tighter stop-losses
            - **Why it matters:** Helps you set realistic profit targets and stop-losses
            - **Example:** ATR = $5 on a $150 stock = 3.3% daily range (moderately volatile)
            
            ---
            
            #### 8️⃣ **Volume** - *"How many people are trading?"*
            - **What it measures:** Number of shares traded
            - **Simple Rule:**
              - **High volume (>1.5x average):** Strong conviction = Price move is real/reliable
              - **Low volume (<0.5x average):** Weak participation = Price move may not last
              - **Normal volume (0.5x-1.5x):** Average interest
            - **Why it matters:** High volume confirms price moves - "volume confirms trend"
            - **Example:** If price rises 5% on 3x volume, it's a strong move. If on 0.3x volume, it's weak.
            
            ---
            
            ### 🎯 **How to Use These Together:**
            1. **Check the TREND first** (Moving Averages, ADX) - Is it going up or down?
            2. **Check if price is EXTREME** (RSI, Stochastic, Bollinger) - Too high or too low?
            3. **Check MOMENTUM** (MACD) - Is the trend getting stronger or weaker?
            4. **Check VOLUME** - Are people actually trading or is it just noise?
            5. **Check VOLATILITY** (ATR) - How risky is this stock?
            
            ### ✅ **Strong BUY Example:**
            - RSI = 28 (oversold ✓)
            - MACD crossing up (momentum turning ✓)
            - Price at lower Bollinger Band (extreme low ✓)
            - Above SMA-50 (still in uptrend ✓)
            - High volume (people buying ✓)
            
            ### ❌ **Strong SELL Example:**
            - RSI = 78 (overbought ✓)
            - MACD crossing down (momentum turning ✓)
            - Price at upper Bollinger Band (extreme high ✓)
            - Below SMA-20 (breaking down ✓)
            - High volume (people selling ✓)
            
            ### ⏸️ **HOLD/Wait Example:**
            - RSI = 50 (neutral)
            - MACD flat (no momentum)
            - Price in middle of Bollinger Bands (no extreme)
            - ADX = 18 (weak trend)
            - Low volume (not much happening)
            
            **Remember:** No single indicator is perfect. Use multiple indicators together for confirmation!
            """)
        
        # Get current price for calculations (use existing price_data from line 437)
        current_price = price_data.get('price') if price_data else None
        
        # Prepare indicators data
        indicators_data = []
        
        # 1. RSI - Most important for overbought/oversold
        rsi = result['technical'].get('rsi')
        if rsi is not None:
            if rsi < 30:
                rsi_signal = "🟢 Oversold"
                rsi_meaning = "Strong buy signal - stock is cheap, likely to bounce up soon"
            elif rsi > 70:
                rsi_signal = "🔴 Overbought"
                rsi_meaning = "Strong sell signal - stock is expensive, likely to pull back"
            elif rsi < 40:
                rsi_signal = "🟡 Approaching Oversold"
                rsi_meaning = "Getting cheap - potential buy opportunity developing"
            elif rsi > 60:
                rsi_signal = "🟡 Approaching Overbought"
                rsi_meaning = "Getting expensive - consider taking profits soon"
            else:
                rsi_signal = "⚪ Neutral"
                rsi_meaning = "No extreme conditions - wait for clearer buy/sell signal"
            
            indicators_data.append({
                "Indicator": "RSI (Relative Strength Index)",
                "Value": f"{rsi:.1f}",
                "Signal": rsi_signal,
                "Interpretation": rsi_meaning
            })
        
        # 2. MACD - Trend momentum
        macd_data = result['technical'].get('macd', {})
        if macd_data:
            macd_line = macd_data.get('macd')
            signal_line = macd_data.get('signal')
            histogram = macd_data.get('histogram')
            
            if macd_line is not None and signal_line is not None:
                if macd_line > signal_line:
                    macd_signal = "🟢 Bullish"
                    macd_meaning = "Upward momentum - trend is accelerating higher (good for buying)"
                else:
                    macd_signal = "🔴 Bearish"
                    macd_meaning = "Downward momentum - trend is accelerating lower (consider selling)"
                
                # Check if lines are close (potential crossover)
                if abs(macd_line - signal_line) < 0.5:
                    macd_meaning += " | ⚠️ Lines close together - trend may be changing soon"
                
                if histogram:
                    if abs(histogram) > 1.0:
                        macd_meaning += f" | Strong force ({histogram:.2f})"
                    else:
                        macd_meaning += f" | Weak force ({histogram:.2f})"
                
                indicators_data.append({
                    "Indicator": "MACD (Moving Avg Convergence Divergence)",
                    "Value": f"{macd_line:.2f} / {signal_line:.2f}",
                    "Signal": macd_signal,
                    "Interpretation": macd_meaning
                })
        
        # 3. Bollinger Bands - Volatility and price levels
        bollinger = result['technical'].get('bollinger', {})
        if bollinger:
            percent_b = bollinger.get('percent_b')
            bb_upper = bollinger.get('upper')
            bb_lower = bollinger.get('lower')
            
            if percent_b is not None:
                if percent_b > 0.8:
                    bb_signal = "🔴 Near Upper Band"
                    bb_meaning = f"Price stretched to top ({percent_b*100:.0f}%) - like a rubber band pulled tight, likely to snap back down"
                elif percent_b < 0.2:
                    bb_signal = "🟢 Near Lower Band"
                    bb_meaning = f"Price stretched to bottom ({percent_b*100:.0f}%) - oversold, likely to bounce back up"
                else:
                    bb_signal = "⚪ Mid-Range"
                    bb_meaning = f"Price in normal range ({percent_b*100:.0f}%) - no extreme stretch, room to move either way"
                
                indicators_data.append({
                    "Indicator": "Bollinger Bands (Volatility)",
                    "Value": f"{percent_b*100:.0f}% ({bb_lower:.2f} - {bb_upper:.2f})",
                    "Signal": bb_signal,
                    "Interpretation": bb_meaning
                })
        
        # 4. Moving Averages - Trend direction
        ma_data = result['technical'].get('moving_averages', {})
        if ma_data:
            sma_20 = ma_data.get('sma_20')
            sma_50 = ma_data.get('sma_50')
            above_sma_20 = ma_data.get('above_sma_20')
            above_sma_50 = ma_data.get('above_sma_50')
            
            if sma_20 and sma_50:
                if above_sma_20 and above_sma_50:
                    ma_signal = "🟢 Bullish Trend"
                    ma_meaning = "Stock trading above both 20-day & 50-day averages - healthy uptrend (buyers in control)"
                elif not above_sma_20 and not above_sma_50:
                    ma_signal = "🔴 Bearish Trend"
                    ma_meaning = "Stock trading below both averages - downtrend confirmed (sellers in control)"
                else:
                    ma_signal = "🟡 Mixed"
                    ma_meaning = "Price between averages - trend unclear, market consolidating (wait for breakout)"
                
                indicators_data.append({
                    "Indicator": "Moving Averages (Trend)",
                    "Value": f"SMA20: {sma_20:.2f}, SMA50: {sma_50:.2f}",
                    "Signal": ma_signal,
                    "Interpretation": ma_meaning
                })
        
        # 5. Stochastic Oscillator
        stochastic = result['technical'].get('stochastic', {})
        if stochastic:
            stoch_k = stochastic.get('k')
            stoch_d = stochastic.get('d')
            
            if stoch_k is not None:
                if stoch_k > 80:
                    stoch_signal = "🔴 Overbought"
                    stoch_meaning = f"At {stoch_k:.0f}/100 - price is at top of recent range, very high chance of reversal down (sell signal)"
                elif stoch_k < 20:
                    stoch_signal = "🟢 Oversold"
                    stoch_meaning = f"At {stoch_k:.0f}/100 - price is at bottom of recent range, very high chance of bounce up (buy signal)"
                else:
                    stoch_signal = "⚪ Neutral"
                    stoch_meaning = f"At {stoch_k:.0f}/100 - mid-range, no extreme buying/selling pressure yet"
                
                indicators_data.append({
                    "Indicator": "Stochastic Oscillator (Momentum)",
                    "Value": f"K: {stoch_k:.1f}, D: {stoch_d:.1f}" if stoch_d else f"K: {stoch_k:.1f}",
                    "Signal": stoch_signal,
                    "Interpretation": stoch_meaning
                })
        
        # 6. ADX - Trend strength
        adx_data = result['technical'].get('adx', {})
        if adx_data:
            adx_value = adx_data.get('adx')
            di_plus = adx_data.get('di_plus')
            di_minus = adx_data.get('di_minus')
            
            if adx_value is not None:
                if adx_value > 25:
                    if di_plus and di_minus:
                        if di_plus > di_minus:
                            adx_signal = "🟢 Strong Uptrend"
                            adx_meaning = f"ADX {adx_value:.0f} - powerful uptrend in motion (safe to ride the trend up)"
                        else:
                            adx_signal = "🔴 Strong Downtrend"
                            adx_meaning = f"ADX {adx_value:.0f} - powerful downtrend in motion (avoid buying, trend is strong)"
                    else:
                        adx_signal = "🟡 Strong Trend"
                        adx_meaning = f"ADX {adx_value:.0f} - trending market (trade with the trend, not against it)"
                else:
                    adx_signal = "⚪ Weak/No Trend"
                    adx_meaning = f"ADX {adx_value:.0f} - sideways/choppy market (harder to trade, wait for ADX >25)"
                
                indicators_data.append({
                    "Indicator": "ADX (Trend Strength)",
                    "Value": f"{adx_value:.1f}",
                    "Signal": adx_signal,
                    "Interpretation": adx_meaning
                })
        
        # 7. ATR - Volatility
        atr = result['technical'].get('atr')
        if atr is not None and current_price:
            atr_pct = (atr / current_price) * 100
            if atr_pct > 3:
                atr_signal = "🔴 High Volatility"
                atr_meaning = f"{atr_pct:.1f}% average daily swing - stock moves a lot! Higher risk but bigger profit potential. Use wider stop-losses."
            elif atr_pct < 1:
                atr_signal = "🟢 Low Volatility"
                atr_meaning = f"{atr_pct:.1f}% average daily swing - stock is stable and predictable. Lower risk, smaller moves. Use tighter stop-losses."
            else:
                atr_signal = "⚪ Normal Volatility"
                atr_meaning = f"{atr_pct:.1f}% average daily swing - moderate price movement, typical for most stocks"
            
            indicators_data.append({
                "Indicator": "ATR (Average True Range)",
                "Value": f"{atr:.2f} ({atr_pct:.1f}%)",
                "Signal": atr_signal,
                "Interpretation": atr_meaning
            })
        
        # 8. Volume (if available)
        if price_data:
            volume = price_data.get('volume')
            if volume:
                # Get average volume from stats if available
                avg_volume = None
                if result['statistics']['success']:
                    avg_volume = result['statistics']['data'].get('averageVolume')
                
                if avg_volume:
                    vol_ratio = volume / avg_volume
                    if vol_ratio > 1.5:
                        vol_signal = "🟢 High Volume"
                        vol_meaning = f"{vol_ratio:.1f}x average - lots of people trading! Price move is REAL and backed by strong conviction. Trust this signal."
                    elif vol_ratio < 0.5:
                        vol_signal = "🔴 Low Volume"
                        vol_meaning = f"{vol_ratio:.1f}x average - few people trading. Price move is WEAK and may not last. Don't trust it."
                    else:
                        vol_signal = "⚪ Normal Volume"
                        vol_meaning = f"{vol_ratio:.1f}x average - typical trading activity, nothing unusual"
                    
                    indicators_data.append({
                        "Indicator": "Volume (Participation)",
                        "Value": f"{volume:,.0f}",
                        "Signal": vol_signal,
                        "Interpretation": vol_meaning
                    })
        
        # Display table
        if indicators_data:
            import pandas as pd
            df_indicators = pd.DataFrame(indicators_data)
            
            # Style the dataframe
            st.dataframe(
                df_indicators,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Indicator": st.column_config.TextColumn("Indicator", width="medium"),
                    "Value": st.column_config.TextColumn("Current Value", width="small"),
                    "Signal": st.column_config.TextColumn("Signal", width="small"),
                    "Interpretation": st.column_config.TextColumn("What It Means", width="large")
                }
            )
        else:
            st.warning("No technical indicators available")
        
        # Overall Summary Section
        st.markdown("---")
        st.markdown("### 📋 Overall Market Summary")
        
        # Create summary based on all available data
        summary_parts = []
        
        # Price action summary
        if price_data:
            price = price_data.get('price')
            change_pct = price_data.get('change_percent', 0)
            if change_pct > 0:
                summary_parts.append(f"**Price Action:** {currency_symbol}{price:.2f} is up {change_pct:+.2f}% today, showing positive momentum.")
            elif change_pct < 0:
                summary_parts.append(f"**Price Action:** {currency_symbol}{price:.2f} is down {change_pct:.2f}% today, under selling pressure.")
            else:
                summary_parts.append(f"**Price Action:** {currency_symbol}{price:.2f} is unchanged today, consolidating.")
        
        # Trend summary
        trend_indicators = []
        if rsi is not None:
            if rsi < 40:
                trend_indicators.append("oversold conditions (RSI)")
            elif rsi > 60:
                trend_indicators.append("overbought conditions (RSI)")
        
        if ma_data:
            above_sma_20 = ma_data.get('above_sma_20')
            above_sma_50 = ma_data.get('above_sma_50')
            if above_sma_20 and above_sma_50:
                trend_indicators.append("bullish trend (above MAs)")
            elif not above_sma_20 and not above_sma_50:
                trend_indicators.append("bearish trend (below MAs)")
        
        if trend_indicators:
            summary_parts.append(f"**Technical Setup:** The stock is showing {', '.join(trend_indicators)}.")
        
        # Momentum summary
        momentum_summary = []
        if macd_line is not None and signal_line is not None:
            if macd_line > signal_line:
                momentum_summary.append("bullish MACD crossover")
            else:
                momentum_summary.append("bearish MACD crossover")
        
        if adx_data.get('adx', 0) > 25:
            momentum_summary.append("strong trending conditions")
        elif adx_data.get('adx', 0) < 20:
            momentum_summary.append("weak/choppy market")
        
        if momentum_summary:
            summary_parts.append(f"**Momentum:** {', '.join(momentum_summary).capitalize()}.")
        
        # Sentiment summary
        if result['sentiment']['success']:
            sentiment_score = result['sentiment']['sentiment']['overall_score']
            sentiment_label = result['sentiment']['sentiment']['label']
            news_count = result['news'].get('count', 0) if result['news']['success'] else 0
            
            if sentiment_score > 0.3:
                summary_parts.append(f"**Market Sentiment:** {sentiment_label.capitalize()} sentiment ({sentiment_score:.2f}) based on {news_count} recent articles - positive news flow.")
            elif sentiment_score < -0.3:
                summary_parts.append(f"**Market Sentiment:** {sentiment_label.capitalize()} sentiment ({sentiment_score:.2f}) based on {news_count} recent articles - negative news coverage.")
            else:
                summary_parts.append(f"**Market Sentiment:** {sentiment_label.capitalize()} sentiment ({sentiment_score:.2f}) based on {news_count} recent articles.")
        
        # Risk assessment
        risk_factors = []
        if result['statistics']['success']:
            stats = result['statistics']['data']
            beta = stats.get('beta')
            debt_equity = stats.get('debtToEquity')
            
            if beta and beta > 1.5:
                risk_factors.append(f"high volatility (β={beta:.2f})")
            if debt_equity and debt_equity > 2.0:
                risk_factors.append(f"elevated debt levels ({debt_equity:.2f})")
            
            if atr and current_price:
                atr_pct = (atr / current_price) * 100
                if atr_pct > 3:
                    risk_factors.append(f"wide daily swings ({atr_pct:.1f}%)")
        
        risk_level = result['signal'].get('risk_level', 'Medium')
        if risk_factors:
            summary_parts.append(f"**Risk Assessment:** {risk_level} risk - {', '.join(risk_factors)}.")
        else:
            summary_parts.append(f"**Risk Assessment:** {risk_level} risk level for this position.")
        
        # Trading recommendation
        if signal == 'BUY':
            action_summary = f"**Recommendation:** BUY signal with {confidence:.0%} confidence. "
            swing_trade = result['signal'].get('swing_trade')
            if swing_trade and swing_trade.get('entry_price'):
                entry = swing_trade.get('entry_price')
                target = swing_trade.get('target_price')
                stop = swing_trade.get('stop_loss')
                rr_ratio = swing_trade.get('risk_reward_ratio', 0)
                action_summary += f"Entry around {currency_symbol}{entry:.2f}, target {currency_symbol}{target:.2f}, stop {currency_symbol}{stop:.2f} (R:R {rr_ratio:.1f}:1)."
            summary_parts.append(action_summary)
        elif signal == 'SELL':
            action_summary = f"**Recommendation:** SELL signal with {confidence:.0%} confidence. Consider exiting long positions or avoiding new entries."
            summary_parts.append(action_summary)
        elif signal == 'WAIT':
            action_summary = f"**Recommendation:** WAIT - No clear setup yet. Monitor for better entry points or stronger signals before entering."
            summary_parts.append(action_summary)
        else:  # HOLD
            if holding_position:
                action_summary = f"**Recommendation:** HOLD your position with {confidence:.0%} confidence. Monitor for exit signals."
            else:
                action_summary = f"**Recommendation:** No clear signal yet. Wait for stronger buy or sell conditions to develop."
            summary_parts.append(action_summary)
        
        # Display summary
        for part in summary_parts:
            st.markdown(part)
        
        st.info("💡 **Summary:** This overview combines price action, technical indicators, sentiment analysis, and risk factors to give you a complete picture of the current market situation.")

        
        # Swing Trading Recommendations
        swing_trade = result['signal'].get('swing_trade')
        if swing_trade:
            st.markdown("---")
            st.markdown("### 📈 Swing Trading Strategy")
            
            if swing_trade.get('action') == 'BUY' and swing_trade.get('entry_price'):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    entry = swing_trade.get('entry_price')
                    if entry:
                        st.metric("Entry Price", f"{currency_symbol}{entry:.2f}")
                
                with col2:
                    target = swing_trade.get('target_price')
                    if target and entry:
                        gain = ((target - entry) / entry) * 100
                        st.metric("Target Price", f"{currency_symbol}{target:.2f}", f"+{gain:.1f}%")
                
                with col3:
                    stop = swing_trade.get('stop_loss')
                    if stop and entry:
                        loss = ((stop - entry) / entry) * 100
                        st.metric("Stop Loss", f"{currency_symbol}{stop:.2f}", f"{loss:.1f}%")
                
                with col4:
                    rr = swing_trade.get('risk_reward_ratio')
                    if rr:
                        rr_color = "green" if rr >= 2 else "orange" if rr >= 1.5 else "red"
                        st.markdown(f"<div style='text-align: center;'><p style='color: gray; font-size: 14px; margin: 0;'>Risk:Reward</p><p style='color: {rr_color}; font-size: 24px; font-weight: bold; margin: 0;'>{rr:.1f}:1</p></div>", unsafe_allow_html=True)
                
                # Holding period
                if swing_trade.get('holding_period'):
                    st.info(f"⏱️ **Suggested Holding Period:** {swing_trade['holding_period']}")
                
                # Strategy notes
                if swing_trade.get('notes'):
                    st.markdown("**Strategy Notes:**")
                    for note in swing_trade['notes']:
                        st.write(f"• {note}")
                
                # Visual trade plan
                if entry and target and stop:
                    st.markdown("**Trade Plan:**")
                    potential_gain = target - entry
                    potential_loss = entry - stop
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"✓ **Max Profit:** {currency_symbol}{potential_gain:.2f} ({((target-entry)/entry)*100:.1f}%)")
                    with col2:
                        st.error(f"⚠️ **Max Loss:** {currency_symbol}{potential_loss:.2f} ({((stop-entry)/entry)*100:.1f}%)")
            
            elif swing_trade.get('action') == 'SELL':
                st.warning("⚠️ **Sell Signal Active**")
                if swing_trade.get('notes'):
                    for note in swing_trade['notes']:
                        st.write(f"• {note}")
            
            else:  # HOLD signal - show detailed entry recommendations
                st.info("⊙ **No Trade Setup - Wait for Better Entry**")
                
                if swing_trade.get('notes'):
                    has_entry_section = False
                    has_breakout_section = False
                    
                    for note in swing_trade['notes']:
                        # Check for section headers
                        if "**Better Entry Points:**" in note:
                            st.markdown("#### 📉 Better Entry Points")
                            has_entry_section = True
                            continue
                        elif "**Breakout Watch:**" in note:
                            st.markdown("#### 📈 Breakout Opportunity")
                            has_breakout_section = True
                            continue
                        
                        # Display notes with proper formatting
                        if note.startswith("  →"):
                            # Indented sub-points
                            st.write(note)
                        elif "⊙" in note or "○" in note or "⚠️" in note or "✓" in note:
                            # Regular bullet points
                            st.write(f"• {note}")
                        else:
                            st.write(f"• {note}")
        
        # AI Analysis (WOW FACTOR!)
        if show_ai and result['ai']['success']:
            st.markdown("---")
            st.markdown("<div class='ai-insight'>", unsafe_allow_html=True)
            st.markdown("### 🤖 AI Expert Analysis")
            st.markdown(result['ai']['analysis'])
            st.caption(f"Powered by {result['ai']['model']}")
            st.markdown("</div>", unsafe_allow_html=True)
        elif show_ai:
            st.info("💡 **Enable AI Analysis:** Install Ollama from https://ollama.ai and run `ollama pull llama3.2:1b` for free AI insights!")
        
        st.markdown("---")
        
        # Price Chart (MEGA WOW FACTOR!)
        if result['historical']['success']:
            st.markdown("### 📊 Price History & Volume")
            chart = create_price_chart(result['historical']['data'], symbol)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            if show_education:
                show_indicator_explanation('Volume')
        
        st.markdown("---")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            news_count = result['news'].get('count', 0) if result['news']['success'] else 0
            st.metric("📰 News Articles", news_count)
        
        with col2:
            if result['sentiment']['success']:
                sentiment_score = result['sentiment']['sentiment']['overall_score']
                sentiment_label = result['sentiment']['sentiment']['label'].upper()
                st.metric("💭 Sentiment", sentiment_label, f"{sentiment_score:.3f}")
            else:
                st.metric("💭 Sentiment", "N/A")
        
        with col3:
            rsi = result['technical'].get('rsi')
            if rsi is not None:
                rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Normal"
                st.metric("📊 RSI", f"{rsi:.2f}", rsi_status)
            else:
                st.metric("📊 RSI", "N/A")
        
        with col4:
            if price_data and price_data.get('pe_ratio'):
                st.metric("💰 P/E Ratio", f"{price_data['pe_ratio']:.2f}")
            else:
                st.metric("💰 P/E Ratio", "N/A")
        
        st.markdown("---")
        
        # Detailed tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Technicals", "📈 Key Stats", "💭 Sentiment", "📰 News", "🏢 Company", "💾 Export"])
        
        # Technicals tab
        with tab1:
            st.subheader("Technical Indicators")
            
            if show_education:
                st.info("📚 **New to trading?** Expand the 'Learn' sections below to understand each indicator!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rsi = result['technical'].get('rsi')
                if rsi is not None:
                    st.plotly_chart(create_gauge_chart(rsi, "RSI (Relative Strength Index)"), use_container_width=True)
                    
                    if rsi < 30:
                        st.success("✓ RSI indicates oversold conditions - potential buy opportunity")
                    elif rsi > 70:
                        st.error("✗ RSI indicates overbought conditions - potential sell signal")
                    else:
                        st.info("⊙ RSI in normal range")
                    
                    if show_education:
                        show_indicator_explanation('RSI')
                else:
                    st.warning("RSI data not available")
            
            with col2:
                macd_data = result['technical'].get('macd', {})
                if macd_data.get('macd') is not None:
                    st.markdown("#### MACD Indicator")
                    st.write(f"**MACD Line:** {macd_data['macd']:.4f}")
                    st.write(f"**Signal Line:** {macd_data.get('signal', 0):.4f}")
                    st.write(f"**Histogram:** {macd_data.get('histogram', 0):.4f}")
                    
                    if macd_data['macd'] > macd_data.get('signal', 0):
                        st.success("✓ Bullish MACD crossover - upward momentum")
                    else:
                        st.warning("⊙ Bearish MACD - downward pressure")
                    
                    if show_education:
                        show_indicator_explanation('MACD')
                else:
                    st.warning("MACD data not available")
            
            # Additional metrics
            if price_data and price_data.get('pe_ratio'):
                st.markdown("---")
                st.markdown("#### Fundamental Metrics")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("P/E Ratio", f"{price_data['pe_ratio']:.2f}")
                with col2:
                    if price_data.get('dividend_yield'):
                        st.metric("Dividend Yield", f"{price_data['dividend_yield']*100:.2f}%")
                with col3:
                    if price_data.get('market_cap'):
                        mcap_b = price_data['market_cap'] / 1_000_000_000
                        st.metric("Market Cap", f"${mcap_b:.1f}B")
                
                if show_education:
                    show_indicator_explanation('PE_Ratio')
        
        # Key Statistics tab (NEW!)
        with tab2:
            st.subheader("📈 Key Statistics & Financial Metrics")
            
            if result['statistics']['success']:
                stats = result['statistics']['data']
                
                # Valuation Metrics
                st.markdown("### 💰 Valuation Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if stats.get('marketCap'):
                        st.metric("Market Cap", format_large_number(stats['marketCap'], currency_symbol))
                    if stats.get('enterpriseValue'):
                        st.metric("Enterprise Value", format_large_number(stats['enterpriseValue'], currency_symbol))
                
                with col2:
                    if stats.get('trailingPE'):
                        st.metric("P/E Ratio (TTM)", format_ratio(stats['trailingPE']))
                    if stats.get('forwardPE'):
                        st.metric("Forward P/E", format_ratio(stats['forwardPE']))
                
                with col3:
                    if stats.get('priceToBook'):
                        st.metric("Price/Book", format_ratio(stats['priceToBook']))
                    if stats.get('priceToSales'):
                        st.metric("Price/Sales", format_ratio(stats['priceToSales']))
                
                with col4:
                    if stats.get('pegRatio'):
                        st.metric("PEG Ratio", format_ratio(stats['pegRatio']))
                    if stats.get('beta'):
                        st.metric("Beta", format_ratio(stats['beta']))
                
                st.markdown("---")
                
                # Profitability & Returns
                st.markdown("### 💵 Profitability & Returns")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if stats.get('profitMargins'):
                        st.metric("Profit Margin", format_percentage(stats['profitMargins']))
                    if stats.get('operatingMargins'):
                        st.metric("Operating Margin", format_percentage(stats['operatingMargins']))
                
                with col2:
                    if stats.get('returnOnEquity'):
                        st.metric("ROE", format_percentage(stats['returnOnEquity']))
                    if stats.get('returnOnAssets'):
                        st.metric("ROA", format_percentage(stats['returnOnAssets']))
                
                with col3:
                    if stats.get('grossMargins'):
                        st.metric("Gross Margin", format_percentage(stats['grossMargins']))
                    if stats.get('ebitdaMargins'):
                        st.metric("EBITDA Margin", format_percentage(stats['ebitdaMargins']))
                
                with col4:
                    if stats.get('earningsGrowth'):
                        st.metric("Earnings Growth", format_percentage(stats['earningsGrowth']))
                    if stats.get('revenueGrowth'):
                        st.metric("Revenue Growth", format_percentage(stats['revenueGrowth']))
                
                st.markdown("---")
                
                # Dividend Information
                if stats.get('dividendYield') or stats.get('dividendRate'):
                    st.markdown("### 💸 Dividend Information")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if stats.get('dividendYield'):
                            st.metric("Dividend Yield", format_percentage(stats['dividendYield']))
                    
                    with col2:
                        if stats.get('dividendRate'):
                            st.metric("Annual Dividend", f"{currency_symbol}{stats['dividendRate']:.2f}")
                    
                    with col3:
                        if stats.get('payoutRatio'):
                            st.metric("Payout Ratio", format_percentage(stats['payoutRatio']))
                    
                    with col4:
                        if stats.get('fiveYearAvgDividendYield'):
                            st.metric("5Y Avg Yield", format_percentage(stats['fiveYearAvgDividendYield']))
                    
                    st.markdown("---")
                
                # Financial Health
                st.markdown("### 🏦 Financial Health")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if stats.get('currentRatio'):
                        st.metric("Current Ratio", format_ratio(stats['currentRatio']))
                    if stats.get('quickRatio'):
                        st.metric("Quick Ratio", format_ratio(stats['quickRatio']))
                
                with col2:
                    if stats.get('debtToEquity'):
                        st.metric("Debt/Equity", format_ratio(stats['debtToEquity']))
                    if stats.get('totalDebt'):
                        st.metric("Total Debt", format_large_number(stats['totalDebt'], currency_symbol))
                
                with col3:
                    if stats.get('totalCash'):
                        st.metric("Total Cash", format_large_number(stats['totalCash'], currency_symbol))
                    if stats.get('freeCashflow'):
                        st.metric("Free Cash Flow", format_large_number(stats['freeCashflow'], currency_symbol))
                
                with col4:
                    if stats.get('operatingCashflow'):
                        st.metric("Operating CF", format_large_number(stats['operatingCashflow'], currency_symbol))
                    if stats.get('totalCashPerShare'):
                        st.metric("Cash/Share", f"{currency_symbol}{stats['totalCashPerShare']:.2f}")
                
                st.markdown("---")
                
                # Trading Information
                st.markdown("### 📊 Trading Information")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if stats.get('fiftyTwoWeekHigh'):
                        st.metric("52 Week High", f"{currency_symbol}{stats['fiftyTwoWeekHigh']:.2f}")
                    if stats.get('fiftyTwoWeekLow'):
                        st.metric("52 Week Low", f"{currency_symbol}{stats['fiftyTwoWeekLow']:.2f}")
                
                with col2:
                    if stats.get('fiftyDayAverage'):
                        st.metric("50 Day Avg", f"{currency_symbol}{stats['fiftyDayAverage']:.2f}")
                    if stats.get('twoHundredDayAverage'):
                        st.metric("200 Day Avg", f"{currency_symbol}{stats['twoHundredDayAverage']:.2f}")
                
                with col3:
                    if stats.get('averageVolume'):
                        st.metric("Avg Volume", f"{stats['averageVolume']/1e6:.1f}M")
                    if stats.get('sharesOutstanding'):
                        st.metric("Shares Out", f"{stats['sharesOutstanding']/1e6:.1f}M")
                
                with col4:
                    if stats.get('floatShares'):
                        st.metric("Float", f"{stats['floatShares']/1e6:.1f}M")
                    if stats.get('shortPercentOfFloat'):
                        st.metric("Short % of Float", format_percentage(stats['shortPercentOfFloat']))
                
                # Analyst Ratings
                if stats.get('recommendationKey') or stats.get('targetMeanPrice'):
                    st.markdown("---")
                    st.markdown("### 👨‍💼 Analyst Ratings")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if stats.get('recommendationKey'):
                            rec = stats['recommendationKey'].upper()
                            color = "green" if rec in ["BUY", "STRONG_BUY"] else "orange" if rec == "HOLD" else "red"
                            st.markdown(f"**Recommendation:** :{color}[{rec}]")
                    
                    with col2:
                        if stats.get('numberOfAnalystOpinions'):
                            st.metric("Analyst Count", stats['numberOfAnalystOpinions'])
                    
                    with col3:
                        if stats.get('targetMeanPrice'):
                            st.metric("Target Price", f"{currency_symbol}{stats['targetMeanPrice']:.2f}")
                    
                    with col4:
                        if stats.get('targetHighPrice') and stats.get('targetLowPrice'):
                            st.metric("Target Range", f"{currency_symbol}{stats['targetLowPrice']:.0f} - {currency_symbol}{stats['targetHighPrice']:.0f}")
                
                # Quarterly Financials Section
                st.markdown("---")
                st.markdown("### 📊 Quarterly Financials Analysis")
                
                # Try to fetch quarterly financials from yfinance
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    
                    # Get quarterly financials
                    quarterly_financials = ticker.quarterly_financials
                    quarterly_income_stmt = ticker.quarterly_income_stmt
                    
                    if quarterly_income_stmt is not None and not quarterly_income_stmt.empty:
                        st.markdown("#### 💵 Income Statement (Last 4 Quarters)")
                        
                        # Prepare data for display
                        df_financials = quarterly_income_stmt.head(20)  # Top 20 rows
                        
                        # Format the dataframe
                        if not df_financials.empty:
                            # Convert to readable format
                            df_display = df_financials.copy()
                            
                            # Format numbers
                            for col in df_display.columns:
                                df_display[col] = df_display[col].apply(lambda x: f"{x/1000000:.1f}M" if pd.notna(x) and abs(x) >= 1000000 else (f"{x/1000:.1f}K" if pd.notna(x) and abs(x) >= 1000 else (f"{x:.2f}" if pd.notna(x) else "N/A")))
                            
                            st.dataframe(df_display, use_container_width=True)
                            
                            # Key metrics analysis
                            st.markdown("#### 🔍 Quarterly Performance Analysis")
                            
                            # Get latest quarter data
                            latest_quarter = quarterly_income_stmt.columns[0]
                            prev_quarter = quarterly_income_stmt.columns[1] if len(quarterly_income_stmt.columns) > 1 else None
                            
                            analysis_points = []
                            
                            # Revenue analysis
                            if 'Total Revenue' in quarterly_income_stmt.index:
                                latest_rev = quarterly_income_stmt.loc['Total Revenue', latest_quarter]
                                if prev_quarter and 'Total Revenue' in quarterly_income_stmt.index:
                                    prev_rev = quarterly_income_stmt.loc['Total Revenue', prev_quarter]
                                    if pd.notna(latest_rev) and pd.notna(prev_rev) and prev_rev != 0:
                                        rev_growth = ((latest_rev - prev_rev) / prev_rev) * 100
                                        if rev_growth > 5:
                                            analysis_points.append(f"🟢 **Revenue Growth:** {rev_growth:+.1f}% QoQ - Strong top-line growth ({currency_symbol}{latest_rev/1e6:.1f}M)")
                                        elif rev_growth > 0:
                                            analysis_points.append(f"🟡 **Revenue Growth:** {rev_growth:+.1f}% QoQ - Modest growth ({currency_symbol}{latest_rev/1e6:.1f}M)")
                                        else:
                                            analysis_points.append(f"🔴 **Revenue Decline:** {rev_growth:.1f}% QoQ - Revenue contracted ({currency_symbol}{latest_rev/1e6:.1f}M)")
                            
                            # Gross Profit Margin
                            if 'Gross Profit' in quarterly_income_stmt.index and 'Total Revenue' in quarterly_income_stmt.index:
                                latest_gp = quarterly_income_stmt.loc['Gross Profit', latest_quarter]
                                latest_rev = quarterly_income_stmt.loc['Total Revenue', latest_quarter]
                                if pd.notna(latest_gp) and pd.notna(latest_rev) and latest_rev != 0:
                                    gp_margin = (latest_gp / latest_rev) * 100
                                    if gp_margin > 40:
                                        analysis_points.append(f"🟢 **Gross Margin:** {gp_margin:.1f}% - Excellent profitability")
                                    elif gp_margin > 20:
                                        analysis_points.append(f"🟡 **Gross Margin:** {gp_margin:.1f}% - Healthy margins")
                                    else:
                                        analysis_points.append(f"🔴 **Gross Margin:** {gp_margin:.1f}% - Thin margins, pricing pressure")
                            
                            # Operating Income
                            if 'Operating Income' in quarterly_income_stmt.index and 'Total Revenue' in quarterly_income_stmt.index:
                                latest_oi = quarterly_income_stmt.loc['Operating Income', latest_quarter]
                                latest_rev = quarterly_income_stmt.loc['Total Revenue', latest_quarter]
                                if pd.notna(latest_oi) and pd.notna(latest_rev) and latest_rev != 0:
                                    op_margin = (latest_oi / latest_rev) * 100
                                    if op_margin > 15:
                                        analysis_points.append(f"🟢 **Operating Margin:** {op_margin:.1f}% - Strong operational efficiency")
                                    elif op_margin > 5:
                                        analysis_points.append(f"🟡 **Operating Margin:** {op_margin:.1f}% - Moderate efficiency")
                                    elif op_margin > 0:
                                        analysis_points.append(f"🟡 **Operating Margin:** {op_margin:.1f}% - Low but positive")
                                    else:
                                        analysis_points.append(f"🔴 **Operating Loss:** {op_margin:.1f}% - Company losing money operationally")
                            
                            # Net Income
                            if 'Net Income' in quarterly_income_stmt.index:
                                latest_ni = quarterly_income_stmt.loc['Net Income', latest_quarter]
                                if pd.notna(latest_ni):
                                    if prev_quarter and 'Net Income' in quarterly_income_stmt.index:
                                        prev_ni = quarterly_income_stmt.loc['Net Income', prev_quarter]
                                        if pd.notna(prev_ni):
                                            if latest_ni > 0 and prev_ni > 0:
                                                ni_growth = ((latest_ni - prev_ni) / abs(prev_ni)) * 100
                                                if ni_growth > 10:
                                                    analysis_points.append(f"🟢 **Earnings Growth:** {ni_growth:+.1f}% QoQ - Accelerating profits ({currency_symbol}{latest_ni/1e6:.1f}M)")
                                                elif ni_growth > 0:
                                                    analysis_points.append(f"🟡 **Earnings Growth:** {ni_growth:+.1f}% QoQ - Growing profits ({currency_symbol}{latest_ni/1e6:.1f}M)")
                                                else:
                                                    analysis_points.append(f"🔴 **Earnings Decline:** {ni_growth:.1f}% QoQ - Profits falling ({currency_symbol}{latest_ni/1e6:.1f}M)")
                                            elif latest_ni > 0 and prev_ni <= 0:
                                                analysis_points.append(f"🟢 **Returned to Profitability:** {currency_symbol}{latest_ni/1e6:.1f}M - Turnaround in progress")
                                            elif latest_ni <= 0:
                                                analysis_points.append(f"🔴 **Net Loss:** {currency_symbol}{latest_ni/1e6:.1f}M - Company not profitable")
                            
                            # EPS analysis
                            if 'Diluted EPS' in quarterly_income_stmt.index or 'Basic EPS' in quarterly_income_stmt.index:
                                eps_label = 'Diluted EPS' if 'Diluted EPS' in quarterly_income_stmt.index else 'Basic EPS'
                                latest_eps = quarterly_income_stmt.loc[eps_label, latest_quarter]
                                if pd.notna(latest_eps):
                                    if prev_quarter and eps_label in quarterly_income_stmt.index:
                                        prev_eps = quarterly_income_stmt.loc[eps_label, prev_quarter]
                                        if pd.notna(prev_eps) and prev_eps != 0:
                                            eps_growth = ((latest_eps - prev_eps) / abs(prev_eps)) * 100
                                            if latest_eps > prev_eps and latest_eps > 0:
                                                analysis_points.append(f"🟢 **EPS Growth:** ${latest_eps:.2f} ({eps_growth:+.1f}% QoQ) - Earnings per share improving")
                                            elif latest_eps > 0:
                                                analysis_points.append(f"🟡 **EPS:** ${latest_eps:.2f} - Positive earnings per share")
                                            else:
                                                analysis_points.append(f"🔴 **EPS:** ${latest_eps:.2f} - Negative earnings per share")
                            
                            # Operating Expenses vs Revenue
                            if 'Operating Expense' in quarterly_income_stmt.index and 'Total Revenue' in quarterly_income_stmt.index:
                                latest_opex = quarterly_income_stmt.loc['Operating Expense', latest_quarter]
                                latest_rev = quarterly_income_stmt.loc['Total Revenue', latest_quarter]
                                if pd.notna(latest_opex) and pd.notna(latest_rev) and latest_rev != 0:
                                    opex_ratio = (latest_opex / latest_rev) * 100
                                    if opex_ratio < 30:
                                        analysis_points.append(f"🟢 **OpEx Efficiency:** {opex_ratio:.1f}% of revenue - Well-controlled costs")
                                    elif opex_ratio < 50:
                                        analysis_points.append(f"🟡 **OpEx Ratio:** {opex_ratio:.1f}% of revenue - Moderate cost structure")
                                    else:
                                        analysis_points.append(f"🔴 **High OpEx:** {opex_ratio:.1f}% of revenue - Cost management concerns")
                            
                            # EBITDA analysis
                            if 'EBITDA' in quarterly_income_stmt.index and 'Total Revenue' in quarterly_income_stmt.index:
                                latest_ebitda = quarterly_income_stmt.loc['EBITDA', latest_quarter]
                                latest_rev = quarterly_income_stmt.loc['Total Revenue', latest_quarter]
                                if pd.notna(latest_ebitda) and pd.notna(latest_rev) and latest_rev != 0:
                                    ebitda_margin = (latest_ebitda / latest_rev) * 100
                                    if ebitda_margin > 20:
                                        analysis_points.append(f"🟢 **EBITDA Margin:** {ebitda_margin:.1f}% - Strong cash generation capacity")
                                    elif ebitda_margin > 10:
                                        analysis_points.append(f"🟡 **EBITDA Margin:** {ebitda_margin:.1f}% - Decent cash flow potential")
                                    else:
                                        analysis_points.append(f"🔴 **EBITDA Margin:** {ebitda_margin:.1f}% - Weak cash generation")
                            
                            # Display analysis
                            if analysis_points:
                                for point in analysis_points:
                                    st.markdown(point)
                            else:
                                st.info("Insufficient data for detailed quarterly analysis")
                            
                            # Overall Financial Health Summary
                            st.markdown("#### 💡 Financial Health Summary")
                            
                            health_summary = []
                            
                            # Determine overall health
                            green_count = sum(1 for p in analysis_points if p.startswith("🟢"))
                            red_count = sum(1 for p in analysis_points if p.startswith("🔴"))
                            yellow_count = sum(1 for p in analysis_points if p.startswith("🟡"))
                            
                            if green_count > red_count:
                                health_summary.append("**Overall Assessment:** The company shows strong financial performance with growing revenues and improving profitability. Good operational efficiency.")
                            elif red_count > green_count:
                                health_summary.append("**Overall Assessment:** Financial performance shows warning signs with declining metrics or profitability concerns. Exercise caution.")
                            else:
                                health_summary.append("**Overall Assessment:** Mixed financial performance with both strengths and weaknesses. Monitor upcoming quarters closely.")
                            
                            # What investors should watch
                            health_summary.append("**Key Things to Watch:**")
                            health_summary.append("• **Revenue Trends:** Is the company growing its top line quarter-over-quarter?")
                            health_summary.append("• **Margin Expansion:** Are profit margins improving or compressing?")
                            health_summary.append("• **EPS Growth:** Is the company becoming more profitable per share?")
                            health_summary.append("• **Operating Leverage:** Is operating income growing faster than revenue?")
                            
                            for summary in health_summary:
                                st.markdown(summary)
                        else:
                            st.info("No quarterly financial data available for detailed analysis")
                    else:
                        st.info("Quarterly financials not available. This may be due to the stock type or data access limitations.")
                    
                except ImportError:
                    st.warning("yfinance package required for quarterly financials. Install with: pip install yfinance")
                except Exception as e:
                    st.warning(f"Unable to fetch quarterly financials: {str(e)}")
                
                st.caption(f"📡 Data source: {result['statistics'].get('source', 'Unknown')}")
            else:
                st.warning("⚠️ Key statistics not available at the moment.")
                
                # Show error details if available
                if result['statistics'].get('error'):
                    error_msg = result['statistics']['error']
                    
                    # Check if it's a multi-source failure
                    if 'attempted_sources' in result['statistics']:
                        st.error("**All data sources failed to load statistics:**")
                        
                        attempted = result['statistics']['attempted_sources']
                        for source, error in attempted:
                            if 'No API key' in error:
                                st.warning(f"❌ {source}: {error}")
                            elif '429' in error or 'rate limit' in error.lower():
                                st.error(f"⏱️ {source}: Rate limited")
                            else:
                                st.info(f"⚠️ {source}: {error}")
                        
                        st.markdown("---")
                        st.info("""
### 💡 How to Fix This

**Option 1: Wait and Retry** (If you see rate limits)
- Wait 2-3 minutes for Yahoo Finance rate limits to reset
- Click the 'Analyze' button again

**Option 2: Set Up Fallback API Keys** (Recommended)
- Get free API keys from: Alpha Vantage, FMP, Twelve Data, or Finnhub
- See `setup_api_keys.md` for step-by-step instructions
- With fallback keys configured, the system automatically tries other sources when one fails

**Option 3: Try Different Stock**
- Some stocks may not be available on all exchanges
- Try a major stock like AAPL, MSFT, or GOOGL
                        """)
                        
                    elif '429' in str(error_msg) or 'rate limit' in str(error_msg).lower():
                        st.error("**Rate Limit Error:** Yahoo Finance is temporarily limiting requests. This is common and usually resolves in a few minutes.")
                        st.info("💡 **What you can do:**\n- Wait 2-3 minutes and refresh the page\n- Try analyzing a different stock symbol\n- Use the 'Analyze' button again\n- **OR** Set up fallback API keys (see `setup_api_keys.md`) so the system can automatically try other sources\n- Technical analysis, price data, and news are still working fine")
                    elif 'timeout' in str(error_msg).lower():
                        st.error("**Timeout Error:** The request took too long to complete.")
                        st.info("💡 Try clicking 'Analyze' again - this usually works on the second try.")
                    else:
                        with st.expander("🔍 Error Details"):
                            st.code(error_msg)
                        st.info("💡 This may be a temporary issue. Try refreshing or selecting a different stock. See `setup_api_keys.md` to set up fallback data sources.")
                else:
                    st.info("💡 Try refreshing the page or selecting a different stock. Technical indicators and price data are still available.")
                
                # Show basic metrics from price data as fallback
                st.markdown("---")
                st.markdown("### 📊 Available Data")
                st.info("While we wait for statistics to load, here's what we have:")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if price_data and price_data.get('price'):
                        st.metric("Current Price", f"{currency_symbol}{price_data['price']:.2f}")
                
                with col2:
                    if price_data and price_data.get('volume'):
                        st.metric("Volume", f"{price_data['volume']/1e6:.1f}M")
                
                with col3:
                    if price_data and price_data.get('change_percent'):
                        change = price_data['change_percent']
                        st.metric("Daily Change", f"{change:+.2f}%")
                
                with col4:
                    rsi_val = result['technical'].get('rsi')
                    if rsi_val:
                        st.metric("RSI", f"{rsi_val:.1f}")
                
                st.markdown("💡 **Tip:** Most analysis features are still working! Check out the Technical Indicators Summary, Overall Market Summary, and Swing Trading sections above.")
        
        # Sentiment tab
        with tab3:

            if result['sentiment']['success']:
                sentiment = result['sentiment']['sentiment']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Sentiment Analysis")
                    st.write(f"**Overall Label:** {sentiment['label'].upper()}")
                    st.write(f"**Score:** {sentiment['overall_score']:.3f} (range: -1 to +1)")
                    st.write(f"**Total Articles:** {sentiment.get('total_articles', 0)}")
                    
                    if sentiment['overall_score'] > 0.3:
                        st.success("✓ Strong positive sentiment - bullish news coverage")
                    elif sentiment['overall_score'] > 0.1:
                        st.info("⊙ Slightly positive sentiment")
                    elif sentiment['overall_score'] < -0.3:
                        st.error("✗ Strong negative sentiment - bearish news coverage")
                    elif sentiment['overall_score'] < -0.1:
                        st.warning("⊙ Slightly negative sentiment")
                    else:
                        st.info("⊙ Neutral sentiment - balanced coverage")
                    
                    if show_education:
                        show_indicator_explanation('Sentiment')
                
                with col2:
                    sentiment_chart = create_sentiment_chart(result['sentiment'])
                    if sentiment_chart:
                        st.plotly_chart(sentiment_chart, use_container_width=True)
            else:
                st.warning("Sentiment analysis not available.")
        
        # News tab
        with tab4:
            if result['news']['success'] and result['news'].get('count', 0) > 0:
                st.subheader(f"Recent News for {symbol}")
                
                for idx, article in enumerate(result['news']['articles'], 1):
                    with st.expander(f"{idx}. {article['title']}", expanded=(idx <= 3)):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if article.get('description'):
                                st.write(article['description'])
                        with col2:
                            st.caption(f"**Source:** {article['source']}")
                            st.caption(f"**Date:** {article['publishedAt'][:10]}")
                        st.link_button("Read Full Article", article['url'])
            else:
                st.warning("No news articles found.")
        
        # Company tab
        with tab5:
            if result['company']['success'] and result['company']['data']:
                company_data = result['company']['data']
                
                st.subheader("Company Information")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if company_data.get('name'):
                        st.write(f"**Company:** {company_data['name']}")
                    if company_data.get('sector'):
                        st.write(f"**Sector:** {company_data['sector']}")
                    if company_data.get('industry'):
                        st.write(f"**Industry:** {company_data['industry']}")
                    if company_data.get('country'):
                        location = company_data.get('city', '')
                        if location:
                            st.write(f"**Location:** {location}, {company_data['country']}")
                        else:
                            st.write(f"**Country:** {company_data['country']}")
                
                with col2:
                    if company_data.get('employees'):
                        st.write(f"**Employees:** {company_data['employees']:,}")
                    if company_data.get('website'):
                        st.link_button("🌐 Visit Website", company_data['website'])
                
                if company_data.get('description'):
                    st.markdown("---")
                    st.markdown("**About:**")
                    st.write(company_data['description'])
            else:
                st.info("Company information not available.")
        
        # Export tab (WOW FACTOR!)
        with tab6:
            st.subheader("📥 Export Analysis")
            
            st.write("Download your complete analysis for further review or record-keeping.")
            
            # Create export data
            export_data = {
                'Symbol': symbol,
                'Analysis Date': datetime.now().isoformat(),
                'Signal': signal,
                'Confidence': f"{confidence:.2%}",
                'Price': f"${price_data['price']:.2f}" if price_data and result['price']['success'] else 'N/A',
                'Change': f"{price_data['change_percent']:+.2f}%" if price_data and result['price']['success'] else 'N/A',
                'RSI': f"{rsi:.2f}" if rsi else 'N/A',
                'Sentiment': sentiment_label if result['sentiment']['success'] else 'N/A',
                'Sentiment Score': f"{sentiment_score:.3f}" if result['sentiment']['success'] else 'N/A'
            }
            
            # JSON export
            import json
            json_data = json.dumps(result, indent=2, default=str)
            st.download_button(
                label="📄 Download as JSON",
                data=json_data,
                file_name=f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # CSV export
            df = pd.DataFrame([export_data])
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download as CSV",
                data=csv_data,
                file_name=f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            st.markdown("---")
            st.info("💡 **Pro Tip:** Export your analyses to track signal accuracy over time!")
    
    else:
        # Welcome screen
        st.markdown("---")
        st.markdown("""
        ## 👋 Welcome to MarketPulse AI!
        
        **The most advanced FREE stock analysis platform** powered by AI and real-time data.
        
        ### ✨ NEW Features:
        - 💰 **Live Stock Prices** from Yahoo Finance (100% free, no API key needed!)
        - 🤖 **AI Analysis** using Ollama (optional - install locally for free)
        - 📊 **Interactive Price Charts** with candlesticks and volume
        - 📚 **Educational Tooltips** - learn what each indicator means
        - 📥 **Export Analysis** - download your reports as JSON or CSV
        - 🌍 **Global Markets** - analyze stocks from any exchange
        
        ### 🚀 How to Use:
        1. Enter a stock symbol in the sidebar (e.g., AAPL, TSLA, GOOGL)
        2. Click **Analyze Now**
        3. Get instant Buy/Hold/Sell signal with AI insights!
        
        ### 📊 What We Analyze:
        - **Live Prices**: Real-time from Yahoo Finance
        - **News**: Latest articles from NewsAPI
        - **Sentiment**: AI-powered analysis using HuggingFace
        - **Technical Indicators**: RSI, MACD, and more
        - **AI Insights**: Advanced analysis using Ollama
        
        ---
        
        ### 🔥 Try These Popular Stocks:
        """)
        
        st.markdown("**🇺🇸 USA (NYSE/NASDAQ)**")
        cols = st.columns(4)
        us_stocks = [
            ("AAPL", "Apple Inc.", "Technology giant"),
            ("TSLA", "Tesla, Inc.", "Electric vehicles"),
            ("NVDA", "NVIDIA", "AI chips"),
            ("MSFT", "Microsoft", "Cloud & software")
        ]
        for idx, (ticker, name, desc) in enumerate(us_stocks):
            with cols[idx]:
                st.info(f"**{ticker}**\n{name}\n{desc}")
        
        st.markdown("**🇨🇦 Canada (TSX)**")
        cols = st.columns(4)
        ca_stocks = [
            ("SHOP.TO", "Shopify", "E-commerce platform"),
            ("RY.TO", "Royal Bank", "Banking"),
            ("ENB.TO", "Enbridge", "Energy infrastructure"),
            ("TD.TO", "TD Bank", "Financial services")
        ]
        for idx, (ticker, name, desc) in enumerate(ca_stocks):
            with cols[idx]:
                st.info(f"**{ticker}**\n{name}\n{desc}")
        
        st.markdown("**🇮🇳 India (NSE/BSE)**")
        cols = st.columns(4)
        in_stocks = [
            ("RELIANCE.NS", "Reliance", "Conglomerate"),
            ("TCS.NS", "Tata Consultancy", "IT services"),
            ("INFY.NS", "Infosys", "Technology"),
            ("HDFCBANK.NS", "HDFC Bank", "Banking")
        ]
        for idx, (ticker, name, desc) in enumerate(in_stocks):
            with cols[idx]:
                st.info(f"**{ticker}**\n{name}\n{desc}")
        
        st.markdown("---")
        st.success("**Ready to start?** Enter a symbol in the sidebar and click Analyze! 🚀")


if __name__ == '__main__':
    main()
