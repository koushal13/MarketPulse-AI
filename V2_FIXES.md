# MarketPulse AI v2 - Recent Fixes

## Fixed Issues (Nov 14, 2024)

### 1. AttributeError: Tuple vs Dict Mismatch ✅
**Problem:** App crashed with `AttributeError: 'tuple' object has no attribute 'get'`

**Root Cause:** 
- `get_live_price()` returns `Tuple[bool, Dict]`
- `get_historical_data()` returns `Tuple[bool, pd.DataFrame]`
- Code was treating them as dicts with `.get()` method

**Fix Applied:**
```python
# BEFORE (Line ~400)
price_result = get_live_price(full_symbol)
price_data = price_result.get('data', {})  # ❌ CRASH!

# AFTER
price_success, price_data = get_live_price(full_symbol)
if not price_success:
    price_data = {}
```

**Files Modified:**
- `app_v2.py` lines 382-418 (data fetching section)
- `app_v2.py` lines 730-748 (historical chart section)

---

### 2. Simplified Search UI ✅
**Problem:** Search interface too complex with 40+ exchanges, multiple columns, regional filters

**User Request:** 
> "simple text box with google like feature to show intelligency as I type name of company - it should show market symbols of NSE, BSE of india, toronto and new-york stock exhange listed organizations. Just this and search button - that's all"

**Fix Applied:**
- Removed complex multi-column layout
- Created simple 2-column layout: Search box + Button
- Added real-time autocomplete showing suggestions as user types
- **Filtered to 4 exchanges only**: NSE, BSE (India) • TSX (Toronto) • NYSE/NASDAQ (New York)
- Limit to 8 suggestions max
- Clean display with country flags: 🇮🇳 🇨🇦 🇺🇸

**Example:**
```
🔍 Type: "reliance"
💡 Suggestions:
  RELIANCE.NS — Reliance Industries Limited (🇮🇳 NSE)
  RELIANCE.BO — Reliance Industries Limited (🇮🇳 BSE)
```

**Files Modified:**
- `app_v2.py` lines 278-357 (search section)

---

## Current Features

### ✅ Working
1. **Google-like autocomplete search**
   - NSE, BSE, TSX, NYSE/NASDAQ only
   - Live suggestions as you type (min 2 chars)
   - Clean layout with flags

2. **Data fetching fixed**
   - Proper tuple unpacking for price/historical data
   - Multi-source fallback working (5 sources)
   - Error handling improved

3. **AI Analysis**
   - Ollama integration (llama3.2:1b model)
   - Real-time analysis generation
   - Beginner-friendly explanations

4. **Live updates**
   - JavaScript clock with timezone
   - Auto-refresh indicator (5 min)
   - Real-time price/volume charts

### 🎯 Supported Exchanges
| Exchange | Code | Country | Examples |
|----------|------|---------|----------|
| NSE | NSE, NSI | 🇮🇳 India | RELIANCE.NS, TCS.NS |
| BSE | BSE, BSI | 🇮🇳 India | RELIANCE.BO, TCS.BO |
| TSX | TSX | 🇨🇦 Canada | TD.TO, RY.TO |
| NYSE | NYQ | 🇺🇸 USA | IBM, KO |
| NASDAQ | NAS | 🇺🇸 USA | AAPL, MSFT, TSLA |

---

## How to Use

1. **Search for Stock:**
   - Type company name (e.g., "Apple", "Reliance", "TD Bank")
   - Click on suggestion from dropdown
   - Or manually enter ticker symbol

2. **Analyze:**
   - Select timeframe (1D, 5D, 1M, 3M)
   - Click "🚀 Analyze" button
   - Wait for AI analysis and charts

3. **View Results:**
   - **AI Summary** (top priority) - Beginner-friendly analysis
   - **Technical Indicators** - RSI, MACD, Moving Averages
   - **Price Chart** - Candlestick + Volume
   - **Sentiment** - News-based sentiment analysis
   - **Fundamentals** - Key statistics (P/E, Market Cap, etc.)

---

## Running the App

```bash
cd /Users/shatarupapradhan/MarketPulse
python3 -m streamlit run app_v2.py --server.port 8505
```

Open browser: http://localhost:8505

---

## Dependencies

- ✅ Streamlit 1.28.0
- ✅ Ollama (llama3.2:1b model)
- ✅ yfinance 0.2.32
- ✅ pandas, requests, python-dotenv
- ✅ 5 API keys configured in .env

---

## Notes

⚠️ **SSL Warning (Non-critical):** 
```
urllib3 v2 only supports OpenSSL 1.1.1+, currently using LibreSSL 2.8.3
```
This is a warning, not an error. App functions normally.

📊 **Rate Limits:**
Yahoo Finance may return 429 errors during heavy usage. Multi-source fallback handles this automatically (Alpha Vantage → FMP → Twelve Data → Finnhub).

🔄 **Auto-refresh:**
Data refreshes every 5 minutes automatically, or click "Analyze" for immediate update.
