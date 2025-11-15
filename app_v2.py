#!/usr/bin/env python3
"""
MarketPulse AI v2 - Single Page Swing Trading Dashboard
Priority-ordered layout with AI-first analysis and beginner-friendly explanations
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import time
import requests
import json

# Import existing modules
from multi_source_price import get_live_price, get_historical_data
from key_statistics import get_key_statistics
from enhanced_indicators import get_enhanced_technical_indicators
from sentiment_analyzer import get_sentiment_score
from news_api import get_news
from stock_search import search_stocks, get_popular_stocks_by_region, get_all_exchange_codes

# Page configuration
st.set_page_config(
    page_title="MarketPulse AI v2 - Swing Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Priority section styling */
    .priority-1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    .priority-2 {
        background: #f8f9fa;
        border-left: 5px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .priority-3 {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #666;
        text-transform: uppercase;
    }
    
    .bullish {
        color: #00ff00;
        font-weight: bold;
    }
    
    .bearish {
        color: #ff4444;
        font-weight: bold;
    }
    
    .neutral {
        color: #ffa500;
        font-weight: bold;
    }
    
    /* Tooltip styling */
    .tooltip-icon {
        display: inline-block;
        width: 18px;
        height: 18px;
        background: #2196F3;
        color: white;
        border-radius: 50%;
        text-align: center;
        font-size: 12px;
        cursor: help;
        margin-left: 5px;
    }
    
    /* Live clock */
    .live-clock {
        font-family: monospace;
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    
    /* Auto-update indicator */
    .auto-update {
        background: #4CAF50;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)


def get_ollama_analysis(symbol: str, technical_data: dict, sentiment_data: dict, price_data: dict, stats_data: dict) -> dict:
    """
    Send combined market data to local Ollama model for AI analysis
    
    Args:
        symbol: Stock ticker
        technical_data: RSI, MACD, moving averages, etc.
        sentiment_data: News and social media sentiment
        price_data: Current price, volume, change
        stats_data: Fundamentals (PE, EPS, Market Cap)
    
    Returns:
        dict with keys: direction, confidence, reasoning, action
    """
    try:
        # Ensure all data dicts exist
        price_data = price_data or {}
        technical_data = technical_data or {}
        sentiment_data = sentiment_data or {}
        stats_data = stats_data or {}
        
        # Prepare context for Ollama
        context = f"""
You are a swing trading analyst. Analyze this stock data and provide a clear recommendation.

Stock: {symbol}

PRICE DATA:
- Current Price: ${price_data.get('price', 'N/A')}
- Change: {price_data.get('change_percent', 'N/A')}%
- Volume: {price_data.get('volume', 'N/A')}

TECHNICAL INDICATORS:
- RSI: {technical_data.get('rsi', 'N/A')} (oversold <30, overbought >70)
- MACD: {technical_data.get('macd', {}).get('macd', 'N/A')} / Signal: {technical_data.get('macd', {}).get('signal', 'N/A')}
- Price vs SMA-20: {'Above' if technical_data.get('moving_averages', {}).get('above_sma_20') else 'Below'}
- Price vs SMA-50: {'Above' if technical_data.get('moving_averages', {}).get('above_sma_50') else 'Below'}
- ATR: {technical_data.get('atr', 'N/A')}

SENTIMENT:
- Overall Score: {sentiment_data.get('overall_score', 'N/A')}
- Label: {sentiment_data.get('label', 'N/A')}

FUNDAMENTALS:
- Market Cap: {stats_data.get('marketCap', 'N/A')}
- P/E Ratio: {stats_data.get('trailingPE', 'N/A')}
- Beta: {stats_data.get('beta', 'N/A')}

Provide a swing trading recommendation in this exact JSON format:
{{
  "direction": "bullish" or "bearish" or "neutral",
  "confidence": 0-100,
  "reasoning": "Brief explanation (2-3 sentences)",
  "action": "BUY" or "HOLD" or "SELL",
  "key_points": ["point 1", "point 2", "point 3"]
}}
"""

        # Call local Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",  # Using installed 1b model
                "prompt": context,
                "stream": False,
                "format": "json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = json.loads(result.get('response', '{}'))
            
            return {
                'success': True,
                'direction': analysis.get('direction', 'neutral'),
                'confidence': analysis.get('confidence', 50),
                'reasoning': analysis.get('reasoning', 'Analysis unavailable'),
                'action': analysis.get('action', 'HOLD'),
                'key_points': analysis.get('key_points', []),
                'raw_response': result.get('response', '')
            }
        else:
            return {
                'success': False,
                'error': f'Ollama API returned status {response.status_code}'
            }
            
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Cannot connect to Ollama. Make sure Ollama is running: ollama serve'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Ollama analysis failed: {str(e)}'
        }


def render_live_clock():
    """Render live ticking clock in top-right corner"""
    components.html("""
        <div style='text-align: right;'>
            <div id="clock" class="live-clock">00:00:00</div>
            <div style='font-size: 11px; color: #888;' id="tz">Loading...</div>
        </div>
        <script>
            function updateClock() {
                const now = new Date();
                const h = String(now.getHours()).padStart(2, '0');
                const m = String(now.getMinutes()).padStart(2, '0');
                const s = String(now.getSeconds()).padStart(2, '0');
                document.getElementById('clock').textContent = h + ':' + m + ':' + s;
                document.getElementById('tz').textContent = Intl.DateTimeFormat().resolvedOptions().timeZone;
            }
            updateClock();
            setInterval(updateClock, 1000);
        </script>
    """, height=60)


def render_tooltip(term: str, explanation: str):
    """Render a tooltip icon with explanation"""
    return f"""
    <span class="tooltip-icon" title="{explanation}">?</span>
    """


def main():
    """Main dashboard"""
    
    # ============================================================
    # HEADER WITH LIVE CLOCK
    # ============================================================
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.title("📈 MarketPulse AI v2")
        st.caption("🎯 Swing Trading Dashboard • AI-Powered • Real-time Data")
    with col2:
        st.write("")
    with col3:
        render_live_clock()
    
    st.markdown("---")
    
    # ============================================================
    # MINIMAL SEARCH - JUST TYPE AND GO
    # ============================================================
    
    # Initialize session state
    if 'selected_symbol' not in st.session_state:
        st.session_state['selected_symbol'] = None
    if 'selected_name' not in st.session_state:
        st.session_state['selected_name'] = None
    if 'start_analysis' not in st.session_state:
        st.session_state['start_analysis'] = False
    
    # Single search box - suggestions appear as you type
    search_query = st.text_input(
        "🔍 Type to search stocks",
        placeholder="Type company name: Apple, Reliance, Tesla, TD Bank...",
        key="stock_search",
        help="🇮🇳 NSE/BSE • 🇨🇦 TSX • 🇺🇸 NYSE/NASDAQ"
    )
    
    # Show autocomplete suggestions dynamically as user types (no Enter needed)
    if search_query and len(search_query) >= 2 and not st.session_state.get('start_analysis'):
        with st.spinner("🔍 Searching..."):
            all_results = search_stocks(search_query, limit=50)
        
        # Debug: Show what we found
        if all_results:
            # Filter to NSE, BSE, TSX, NYSE/NASDAQ only
            target_exchanges = ['NSE', 'BSE', 'TSX', 'NAS', 'NYQ', 'NSI', 'BSI', 'NMS', 'TOR']
            filtered = [r for r in all_results if r.get('exchange', '').upper() in target_exchanges]
            
            # If filtered list is empty, show all results instead
            display_results = filtered if filtered else all_results
            
            if display_results:
                st.markdown(f"**💡 Suggestions:** ({len(display_results)} found)")
                for stock in display_results:
                    exch = stock.get('exchange', 'N/A').upper()
                    exch_map = {
                        'NSE': '🇮🇳 NSE', 'BSE': '🇮🇳 BSE', 'NSI': '🇮🇳 NSE', 'BSI': '🇮🇳 BSE',
                        'TSX': '🇨🇦 TSX', 'TOR': '🇨🇦 TSX',
                        'NAS': '🇺🇸 NASDAQ', 'NYQ': '🇺🇸 NYSE', 'NMS': '🇺🇸 NASDAQ'
                    }
                    exch_display = exch_map.get(exch, f"📍 {exch}")
                    
                    if st.button(
                        f"**{stock['symbol']}** — {stock['name'][:50]} ({exch_display})",
                        key=f"sel_{stock['symbol']}_{exch}_{stock.get('name', '')[:10]}",
                        use_container_width=True
                    ):
                        st.session_state['selected_symbol'] = stock['symbol']
                        st.session_state['selected_name'] = stock['name']
                        st.session_state['start_analysis'] = True
                        st.rerun()
            else:
                st.warning(f"Found {len(all_results)} results but none matched expected format")
        else:
            st.info(f"No stocks found for '{search_query}'. Try: 'Apple', 'Microsoft', 'Reliance', 'TCS'")
    
    # Trigger analysis on Enter or button click
    analyze_btn = st.session_state.get('start_analysis', False)
    full_symbol = st.session_state.get('selected_symbol')
    timeframe = "1M"  # Default timeframe
    
    # If no stock selected yet, stop here
    if not full_symbol:
        st.info("👆 Type a company name and select from suggestions to start analysis")
        return
    
    # Show what we're analyzing
    st.markdown(f"### 📊 Analyzing: **{st.session_state.get('selected_name', full_symbol)}** ({full_symbol})")
    st.markdown("---")
    
    # Auto-update indicator
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    next_update = st.session_state.last_update + timedelta(minutes=5)
    time_until_update = (next_update - datetime.now()).total_seconds()
    
    if time_until_update <= 0 or analyze_btn:
        st.session_state.last_update = datetime.now()
        time_until_update = 300  # 5 minutes
    
    st.markdown(f"""
        <div style='text-align: center; margin: 10px 0;'>
            <span class='auto-update'>⏱️ Auto-refresh in {int(time_until_update // 60)}m {int(time_until_update % 60)}s</span>
        </div>
    """, unsafe_allow_html=True)
    
    if not analyze_btn and 'analysis_data' not in st.session_state:
        st.info("👆 Enter a stock ticker and click 'Analyze' to start")
        return
    
    # ============================================================
    # DATA FETCHING
    # ============================================================
    if analyze_btn or 'analysis_data' not in st.session_state:
        with st.spinner('🔄 Fetching real-time data...'):
            # Fetch all data
            price_success, price_data = get_live_price(full_symbol)
            stats_result = get_key_statistics(full_symbol)
            technical_result = get_enhanced_technical_indicators(full_symbol)
            
            # Historical data for chart
            days_map = {"1D": 1, "5D": 5, "1M": 30, "3M": 90}
            hist_success, hist_data = get_historical_data(full_symbol, period=f"{days_map[timeframe]}d")
            
            # Sentiment
            news_result = get_news(full_symbol)
            sentiment_result = get_sentiment_score(news_result)
            
            # Handle results (price and hist are tuples, others are dicts)
            if not price_success:
                # All 8 price sources failed - show helpful error
                st.error(f"""
                **❌ Unable to fetch data for {full_symbol}**
                
                All 8 data sources (Yahoo Finance, Alpha Vantage, FMP, Twelve Data, Finnhub, Polygon, IEX, Yahoo Direct) failed to return data.
                
                **Possible reasons:**
                1. **Symbol format issue** - Try these alternatives:
                   - For NSE: Add `.NS` (e.g., `TCS.NS` instead of `TCS.BO`)
                   - For BSE: Add `.BO` (e.g., `RELIANCE.BO`)
                   - For TSX: Add `.TO` (e.g., `TD.TO`)
                   - For US stocks: Use plain symbol (e.g., `AAPL`, `MSFT`)
                
                2. **Rate limits** - Wait 2-3 minutes and try again
                
                3. **Stock not available** - Search for a different stock
                
                **💡 Tip:** Use the search box above to find the correct symbol
                """)
                st.session_state['start_analysis'] = False
                st.session_state['selected_symbol'] = None
                return
            
            price_data = price_data if price_success else {}
            
            stats_data = stats_result.get('data', {}) if isinstance(stats_result, dict) and stats_result.get('success') else {}
            technical_data = technical_result if technical_result else {}
            sentiment_data = sentiment_result.get('sentiment', {}) if isinstance(sentiment_result, dict) and sentiment_result.get('success') else {}
            
            # Store in session
            st.session_state.analysis_data = {
                'symbol': full_symbol,
                'price': price_data,
                'stats': stats_data,
                'technical': technical_data,
                'sentiment': sentiment_data,
                'news': news_result,
                'historical': hist_data if hist_success else None
            }
    
    data = st.session_state.analysis_data
    
    # ============================================================
    # PRIORITY 1: AI SUMMARY (HIGHEST PRIORITY)
    # ============================================================
    st.markdown("## 🤖 AI Analysis Summary")
    st.markdown("*Powered by Local Ollama Model - Most Important Section*")
    
    with st.spinner('🧠 Analyzing with AI...'):
        ollama_result = get_ollama_analysis(
            symbol=data.get('symbol', 'Unknown'),
            technical_data=data.get('technical') or {},
            sentiment_data=data.get('sentiment') or {},
            price_data=data.get('price') or {},
            stats_data=data.get('stats') or {}
        )
    
    if ollama_result.get('success'):
        direction = ollama_result['direction']
        confidence = ollama_result['confidence']
        action = ollama_result['action']
        
        # Direction styling
        if direction == 'bullish':
            direction_class = 'bullish'
            direction_emoji = '🟢'
        elif direction == 'bearish':
            direction_class = 'bearish'
            direction_emoji = '🔴'
        else:
            direction_class = 'neutral'
            direction_emoji = '🟡'
        
        st.markdown(f"""
            <div class='priority-1'>
                <h2 style='margin: 0; color: white;'>{direction_emoji} {direction.upper()} - {action}</h2>
                <p style='font-size: 20px; margin: 10px 0;'>Confidence: {confidence}%</p>
                <div style='background: rgba(255,255,255,0.2); border-radius: 10px; padding: 15px; margin: 15px 0;'>
                    <strong>AI Reasoning:</strong><br>
                    {ollama_result['reasoning']}
                </div>
                <div style='margin-top: 15px;'>
                    <strong>Key Points:</strong>
                    <ul>
                        {''.join([f'<li>{point}</li>' for point in ollama_result.get('key_points', [])])}
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("❓ What does this mean? (Beginner's Guide)"):
            st.markdown("""
            **Direction:**
            - **Bullish** 🟢 = Stock is likely to go UP. Good time to consider buying.
            - **Bearish** 🔴 = Stock is likely to go DOWN. Consider selling or waiting.
            - **Neutral** 🟡 = Stock is sideways. Wait for clearer signal.
            
            **Action:**
            - **BUY** = Strong opportunity to enter/add position
            - **HOLD** = Keep your position if you own it, but don't buy more
            - **SELL** = Exit position or avoid buying
            
            **Confidence Score:**
            - **80-100%** = Very strong signal, high conviction
            - **60-79%** = Moderate signal, decent opportunity
            - **40-59%** = Weak signal, be cautious
            - **Below 40%** = Very uncertain, avoid trading
            
            The AI analyzes all technical indicators, sentiment, and fundamentals together to give you this recommendation.
            """)
    else:
        st.error(f"❌ AI Analysis Failed: {ollama_result.get('error', 'Unknown error')}")
        st.info("""
        **How to fix:**
        1. Make sure Ollama is installed: `brew install ollama` (Mac) or download from ollama.ai
        2. Start Ollama: `ollama serve`
        3. Pull a model: `ollama pull llama3.2:latest`
        4. Refresh this page
        """)
    
    st.markdown("---")
    
    st.markdown("---")
    
    # ============================================================
    # PRIORITY 2: TECHNICAL INDICATORS
    # ============================================================
    st.markdown("## 📊 Technical Indicators")
    st.markdown("*Ordered by importance for swing trading*")
    
    # Get technical data with fallback
    tech_data = data.get('technical', {})
    price_info = data.get('price', {})
    
    with st.expander("📚 Beginner's Guide to Technical Indicators", expanded=False):
        st.markdown("""
        Technical indicators help you understand if a stock is:
        - **Expensive or cheap** (RSI, Stochastic)
        - **Trending up or down** (Moving Averages, MACD)
        - **Gaining or losing momentum** (MACD, Volume)
        - **At extreme levels** (Bollinger Bands, RSI)
        - **Volatile or stable** (ATR)
        
        🎯 For swing trading, focus on: RSI, MACD, Moving Averages, and Volume first!
        """)
    
    # Get technical data with safe fallbacks
    rsi = tech_data.get('rsi')
    macd_data = tech_data.get('macd', {})
    ma_data = tech_data.get('moving_averages', {})
    bb_data = tech_data.get('bollinger', {})
    atr = tech_data.get('atr')
    volume = price_info.get('volume')
    stats_info = data.get('stats', {})
    avg_volume = stats_info.get('averageVolume')
    
    # Display in grid - 3 columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # RSI Card
        st.markdown("### 1️⃣ RSI (Most Important)")
        if rsi:
            if rsi < 30:
                rsi_color = '#00ff00'
                rsi_signal = 'OVERSOLD - BUY Signal'
            elif rsi > 70:
                rsi_color = '#ff4444'
                rsi_signal = 'OVERBOUGHT - SELL Signal'
            else:
                rsi_color = '#ffa500'
                rsi_signal = 'NEUTRAL'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>RSI</div>
                    <div class='metric-value' style='color: {rsi_color};'>{rsi:.1f}</div>
                    <div style='font-size: 14px;'>{rsi_signal}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            **What it means:**  
            RSI = {rsi:.0f}/100. Shows if stock is "overheated" (expensive) or "oversold" (cheap).
            - Below 30 = Oversold, likely to bounce UP
            - Above 70 = Overbought, likely to pull back DOWN
            - 40-60 = Neutral, wait for clearer signal
            """)
        else:
            st.warning("RSI data unavailable")
    
    with col2:
        # MACD Card
        st.markdown("### 2️⃣ MACD (Momentum)")
        if macd_data:
            macd_line = macd_data.get('macd')
            signal_line = macd_data.get('signal')
            
            if macd_line is not None and signal_line is not None:
                if macd_line > signal_line:
                    macd_color = '#00ff00'
                    macd_signal = 'BULLISH - Upward Momentum'
                else:
                    macd_color = '#ff4444'
                    macd_signal = 'BEARISH - Downward Momentum'
                
                st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-label'>MACD</div>
                        <div class='metric-value' style='color: {macd_color};'>{macd_line:.2f}</div>
                        <div style='font-size: 14px;'>Signal: {signal_line:.2f}</div>
                        <div style='font-size: 14px;'>{macd_signal}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("MACD data unavailable")
            
            st.markdown("""
            **What it means:**  
            MACD shows if trend is gaining or losing strength.
            - MACD > Signal = Bullish, upward momentum
            - MACD < Signal = Bearish, downward momentum
            - Lines crossing = Trend is changing
            """)
        else:
            st.warning("MACD data unavailable")
    
    with col3:
        # Moving Averages Card
        st.markdown("### 3️⃣ Moving Averages")
        if ma_data:
            sma_20 = ma_data.get('sma_20')
            sma_50 = ma_data.get('sma_50')
            above_20 = ma_data.get('above_sma_20')
            above_50 = ma_data.get('above_sma_50')
            
            if above_20 and above_50:
                ma_color = '#00ff00'
                ma_signal = 'UPTREND - Bullish'
            elif not above_20 and not above_50:
                ma_color = '#ff4444'
                ma_signal = 'DOWNTREND - Bearish'
            else:
                ma_color = '#ffa500'
                ma_signal = 'MIXED - Consolidating'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Trend Direction</div>
                    <div class='metric-value' style='color: {ma_color};'>{ma_signal}</div>
                    <div style='font-size: 12px;'>SMA-20: ${sma_20:.2f}</div>
                    <div style='font-size: 12px;'>SMA-50: ${sma_50:.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **What it means:**  
            Moving averages smooth out price noise to show trend.
            - Price ABOVE both = Uptrend (buyers in control)
            - Price BELOW both = Downtrend (sellers in control)
            - In between = Sideways (wait for breakout)
            """)
        else:
            st.warning("Moving Average data unavailable")
    
    # Second row - Additional indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 4️⃣ Volume")
        if volume and avg_volume:
            vol_ratio = volume / avg_volume
            if vol_ratio > 1.5:
                vol_color = '#00ff00'
                vol_signal = f'{vol_ratio:.1f}x - HIGH (Strong Move)'
            elif vol_ratio < 0.5:
                vol_color = '#ff4444'
                vol_signal = f'{vol_ratio:.1f}x - LOW (Weak Move)'
            else:
                vol_color = '#ffa500'
                vol_signal = f'{vol_ratio:.1f}x - Normal'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Volume vs Average</div>
                    <div class='metric-value' style='color: {vol_color};'>{vol_ratio:.1f}x</div>
                    <div style='font-size: 14px;'>{vol_signal}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **What it means:**  
            Volume = how many people are trading.
            - High volume (>1.5x) = Price move is REAL
            - Low volume (<0.5x) = Price move is FAKE
            - Volume confirms trend strength
            """)
    
    with col2:
        st.markdown("### 5️⃣ Bollinger Bands")
        if bb_data:
            percent_b = bb_data.get('percent_b', 0.5)
            if percent_b > 0.8:
                bb_color = '#ff4444'
                bb_signal = 'Near Top - May Pull Back'
            elif percent_b < 0.2:
                bb_color = '#00ff00'
                bb_signal = 'Near Bottom - May Bounce'
            else:
                bb_color = '#ffa500'
                bb_signal = 'Mid-Range'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Bollinger %B</div>
                    <div class='metric-value' style='color: {bb_color};'>{percent_b*100:.0f}%</div>
                    <div style='font-size: 14px;'>{bb_signal}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **What it means:**  
            Shows if price is stretched to extremes.
            - >80% = Price at top, may snap back down
            - <20% = Price at bottom, may bounce up
            - 40-60% = Normal range
            """)
    
    with col3:
        st.markdown("### 6️⃣ ATR (Volatility)")
        if atr and price_info.get('price'):
            current_price = price_info['price']
            atr_pct = (atr / current_price) * 100
            
            if atr_pct > 3:
                atr_color = '#ff4444'
                atr_signal = 'HIGH - Risky'
            elif atr_pct < 1:
                atr_color = '#00ff00'
                atr_signal = 'LOW - Stable'
            else:
                atr_color = '#ffa500'
                atr_signal = 'NORMAL'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Average Daily Range</div>
                    <div class='metric-value' style='color: {atr_color};'>{atr_pct:.1f}%</div>
                    <div style='font-size: 14px;'>{atr_signal}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **What it means:**  
            ATR shows how much stock moves daily.
            - >3% = Very volatile, big swings, higher risk
            - <1% = Stable, small moves, lower risk
            - Helps you set stop-losses
            """)
    
    st.markdown("---")
    
    # ============================================================
    # PRIORITY 3: PRICE + VOLUME CHART
    # ============================================================
    st.markdown("## 📈 Price & Volume Chart")
    
    hist_df = data['historical']
    if hist_df is not None and not hist_df.empty:
        # Create candlestick chart with volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('Price (Candlestick)', 'Volume')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=hist_df.index,
                open=hist_df['Open'],
                high=hist_df['High'],
                low=hist_df['Low'],
                close=hist_df['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add moving averages if available
        if 'SMA_20' in hist_df.columns:
            fig.add_trace(
                go.Scatter(x=hist_df.index, y=hist_df['SMA_20'], name='SMA-20', line=dict(color='orange', width=1)),
                row=1, col=1
            )
        if 'SMA_50' in hist_df.columns:
            fig.add_trace(
                go.Scatter(x=hist_df.index, y=hist_df['SMA_50'], name='SMA-50', line=dict(color='blue', width=1)),
                row=1, col=1
            )
        
        # Volume bars
        colors = ['red' if hist_df['Close'].iloc[i] < hist_df['Open'].iloc[i] else 'green' 
                  for i in range(len(hist_df))]
        
        fig.add_trace(
            go.Bar(x=hist_df.index, y=hist_df['Volume'], name='Volume', marker_color=colors),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📖 How to read this chart"):
            st.markdown("""
            **Candlestick Chart:**
            - **Green candle** = Price went UP that day (Close > Open)
            - **Red candle** = Price went DOWN that day (Close < Open)
            - **Long wick up** = Price tried to go higher but got rejected
            - **Long wick down** = Price tried to go lower but bounced back
            
            **Moving Averages (orange & blue lines):**
            - When price is ABOVE moving averages = Uptrend
            - When price CROSSES DOWN below MA = Potential sell signal
            - When price CROSSES UP above MA = Potential buy signal
            
            **Volume Bars (bottom):**
            - Higher bars = More people trading
            - Volume should confirm price moves (high volume = strong move)
            - Low volume moves are less reliable
            """)
    else:
        st.warning("Chart data unavailable")
    
    st.markdown("---")
    
    # ============================================================
    # PRIORITY 4: MARKET SENTIMENT
    # ============================================================
    st.markdown("## 💬 Market Sentiment")
    st.markdown("*What are people saying about this stock?*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sentiment_data_section = data.get('sentiment', {})
        if sentiment_data_section:
            sentiment_score = sentiment_data_section.get('overall_score', 0)
            sentiment_label = sentiment_data_section.get('label', 'neutral')
            
            if sentiment_score > 0.3:
                sent_color = '#00ff00'
                sent_emoji = '😊'
                sent_meaning = 'Positive - People are optimistic'
            elif sentiment_score < -0.3:
                sent_color = '#ff4444'
                sent_emoji = '😟'
                sent_meaning = 'Negative - People are worried'
            else:
                sent_color = '#ffa500'
                sent_emoji = '😐'
                sent_meaning = 'Neutral - Mixed opinions'
            
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>Sentiment Score</div>
                    <div class='metric-value' style='color: {sent_color};'>{sent_emoji} {sentiment_score:.2f}</div>
                    <div style='font-size: 16px; margin-top: 10px;'>{sent_meaning}</div>
                    <div style='font-size: 14px; color: #666; margin-top: 10px;'>
                        Scale: -1.0 (Very Negative) to +1.0 (Very Positive)
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Sentiment data unavailable")
        
        with st.expander("❓ What is sentiment?"):
            st.markdown("""
            **Sentiment** = The overall mood/feeling about a stock based on:
            - News articles
            - Social media (Reddit, Twitter)
            - Analyst reports
            
            **How to use it:**
            - **Positive sentiment** + technical buy signal = Strong buy
            - **Negative sentiment** + technical sell signal = Strong sell
            - Sentiment alone is NOT enough - combine with technicals!
            
            **Score meaning:**
            - **+0.5 to +1.0** = Very bullish, people excited
            - **+0.2 to +0.5** = Moderately positive
            - **-0.2 to +0.2** = Neutral, no strong opinion
            - **-0.5 to -0.2** = Moderately negative
            - **-1.0 to -0.5** = Very bearish, people worried
            """)
    
    with col2:
        st.markdown("### Recent News Headlines")
        if data['news'].get('success') and data['news'].get('articles'):
            for i, article in enumerate(data['news']['articles'][:5]):
                st.markdown(f"""
                **{i+1}. {article.get('title', 'No title')}**  
                *{article.get('source', {}).get('name', 'Unknown')} • {article.get('publishedAt', '')[:10]}*
                """)
                if i < 4:
                    st.markdown("---")
        else:
            st.info("No recent news available")
    
    st.markdown("---")
    
    # ============================================================
    # PRIORITY 5: FUNDAMENTALS MINI-PANEL
    # ============================================================
    st.markdown("## 📊 Fundamental Metrics")
    st.markdown("*Company financial health at a glance*")
    
    stats_section = data.get('stats', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        market_cap = stats_section.get('marketCap')
        if market_cap:
            if market_cap > 200e9:
                cap_size = 'Large Cap'
            elif market_cap > 10e9:
                cap_size = 'Mid Cap'
            else:
                cap_size = 'Small Cap'
            
            st.metric("Market Cap", f"${market_cap/1e9:.2f}B", cap_size)
            st.caption("Total company value. Large cap = safer, small cap = riskier but more growth potential")
    
    with col2:
        pe_ratio = stats_section.get('trailingPE')
        if pe_ratio:
            if pe_ratio < 15:
                pe_signal = 'Cheap'
            elif pe_ratio > 30:
                pe_signal = 'Expensive'
            else:
                pe_signal = 'Fair'
            
            st.metric("P/E Ratio", f"{pe_ratio:.2f}", pe_signal)
            st.caption("Price-to-Earnings. Lower = cheaper. Compare to industry average.")
    
    with col3:
        eps = data['stats'].get('trailingEps')
        if eps:
            st.metric("EPS", f"${eps:.2f}")
            st.caption("Earnings Per Share. Higher = more profitable. Positive is good, negative is bad.")
    
    with col4:
        beta = stats_section.get('beta')
        if beta:
            if beta > 1.5:
                beta_signal = 'Very Volatile'
            elif beta > 1:
                beta_signal = 'More Volatile'
            elif beta < 0.5:
                beta_signal = 'Very Stable'
            else:
                beta_signal = 'Normal'
            
            st.metric("Beta", f"{beta:.2f}", beta_signal)
            st.caption("Volatility vs market. >1 = moves more than market, <1 = moves less")
    
    with st.expander("📖 Understanding Fundamentals"):
        st.markdown("""
        **Market Cap (Market Capitalization):**
        - = Stock Price × Total Shares
        - Shows company size
        - Large Cap (>$200B) = Stable giants like Apple, Microsoft
        - Small Cap (<$10B) = Riskier but can grow faster
        
        **P/E Ratio (Price-to-Earnings):**
        - = Stock Price ÷ Earnings Per Share
        - Shows if stock is expensive or cheap
        - High P/E = Investors expect high growth (or it's overpriced)
        - Low P/E = Stock might be undervalued (or company has problems)
        - Compare to competitors!
        
        **EPS (Earnings Per Share):**
        - = Company Profit ÷ Total Shares
        - Higher = More profitable
        - Growing EPS = Good sign
        - Negative EPS = Company losing money
        
        **Beta (Volatility):**
        - Measures how much stock moves vs overall market
        - Beta = 1.0 → Moves same as market
        - Beta = 1.5 → Moves 50% MORE than market (riskier)
        - Beta = 0.5 → Moves 50% LESS than market (safer)
        - High beta = High risk, high potential reward
        """)
    
    st.markdown("---")
    
    # ============================================================
    # FOOTER
    # ============================================================
    st.markdown("### 🎓 Swing Trading Quick Tips")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **✅ Good Entry Signals:**
        - RSI < 30 (oversold)
        - MACD crossing up
        - Price bouncing off support
        - High volume confirmation
        - Positive sentiment
        """)
    
    with col2:
        st.warning("""
        **⏸️ Wait Signals:**
        - RSI 40-60 (neutral)
        - Low volume
        - Mixed indicators
        - Price in middle of range
        - ADX < 25 (weak trend)
        """)
    
    with col3:
        st.error("""
        **❌ Exit Signals:**
        - RSI > 70 (overbought)
        - MACD crossing down
        - Price hitting resistance
        - Volume drying up
        - Negative sentiment spike
        """)
    
    st.markdown("---")
    st.caption("💡 Data sources: Yahoo Finance, Alpha Vantage, NewsAPI • AI: Local Ollama • Updates every 5 minutes")


if __name__ == "__main__":
    main()
