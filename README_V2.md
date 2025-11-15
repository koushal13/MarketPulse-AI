# MarketPulse AI v2 - Setup Guide

## 🚀 Quick Start

### Prerequisites
1. **Python 3.9+** installed
2. **Ollama** installed and running locally
3. API keys configured (see below)

### Installation

```bash
# 1. Navigate to project
cd /Users/shatarupapradhan/MarketPulse

# 2. Install Ollama (if not already installed)
# macOS:
brew install ollama

# Linux:
curl https://ollama.ai/install.sh | sh

# Windows:
# Download from https://ollama.ai/download

# 3. Start Ollama service
ollama serve

# 4. Pull AI model (in a new terminal)
ollama pull llama3.2:latest
# OR for faster performance: ollama pull phi
# OR for better quality: ollama pull mistral

# 5. Run the v2 dashboard
streamlit run app_v2.py
```

The app will open at: http://localhost:8501

---

## 🔑 API Keys Setup

Your `.env` file is already configured! All keys are set:

```env
✅ ALPHA_VANTAGE_KEY=TEF64NU7N8MSNZXB
✅ FMP_KEY=IKq7QVCXFGYXhheTpAslHITCbVqXp9bD
✅ TWELVE_DATA_KEY=7e78efb8a0c7433fad9bc813e838b4e5
✅ FINNHUB_KEY=d4brlqpr01qoua318asgd4brlqpr01qoua318at0
✅ NEWS_API_KEY=3cc503aab98749b6ba12f7bbdaa3615d
```

No additional setup needed!

---

## 📊 Dashboard Layout

### Priority 1: 🤖 AI Analysis Summary (Top)
- **What:** Ollama AI analyzes all data and gives you a clear recommendation
- **Shows:** Direction (bullish/bearish/neutral), Confidence %, Reasoning, Action (BUY/HOLD/SELL)
- **Why it's #1:** Most important for decision-making - AI combines everything into one answer

### Priority 2: 📊 Technical Indicators
6 most important indicators for swing trading:
1. **RSI** - Is stock cheap or expensive? (<30 = buy, >70 = sell)
2. **MACD** - Is momentum going up or down?
3. **Moving Averages** - What's the trend direction?
4. **Volume** - Is the price move real or fake?
5. **Bollinger Bands** - Is price at extreme levels?
6. **ATR** - How volatile/risky is this stock?

### Priority 3: 📈 Price & Volume Chart
- Interactive candlestick chart with moving averages
- Volume bars below to confirm moves
- Timeframe selector: 1D, 5D, 1M, 3M

### Priority 4: 💬 Market Sentiment
- News sentiment analysis
- Recent headlines
- Sentiment score (-1 to +1)

### Priority 5: 📊 Fundamental Metrics
- Market Cap, P/E Ratio, EPS, Beta
- Quick health check of company finances

---

## 🤖 How Ollama Integration Works

### Data Flow

```
User enters stock ticker (AAPL)
    ↓
Fetch real-time data:
  - Price & Volume (Yahoo Finance)
  - Technical indicators (RSI, MACD, etc.)
  - Sentiment (News analysis)
  - Fundamentals (P/E, EPS, etc.)
    ↓
Send combined data to Ollama API
  POST http://localhost:11434/api/generate
  {
    "model": "llama3.2:latest",
    "prompt": "Analyze this stock data...",
    "format": "json"
  }
    ↓
Ollama analyzes and returns:
  {
    "direction": "bullish",
    "confidence": 85,
    "reasoning": "Strong technicals...",
    "action": "BUY",
    "key_points": ["RSI oversold", "MACD crossing up"]
  }
    ↓
Display AI analysis in purple card at top
```

### Ollama Model Recommendations

| Model | Speed | Quality | RAM | Best For |
|-------|-------|---------|-----|----------|
| `phi` | ⚡⚡⚡ Very Fast | ⭐⭐⭐ Good | 2GB | Quick analysis, low-end hardware |
| `llama3.2:latest` | ⚡⚡ Fast | ⭐⭐⭐⭐ Great | 4GB | **Recommended** - Best balance |
| `mistral` | ⚡ Moderate | ⭐⭐⭐⭐⭐ Excellent | 8GB | Detailed analysis, better reasoning |
| `mixtral` | 🐌 Slow | ⭐⭐⭐⭐⭐ Excellent | 16GB+ | Most accurate, needs powerful PC |

To switch models, edit line 165 in `app_v2.py`:
```python
"model": "llama3.2:latest",  # Change this
```

---

## 🎯 Beginner-Friendly Features

Every metric includes:

1. **Visual Color Coding**
   - 🟢 Green = Bullish (good for buying)
   - 🔴 Red = Bearish (consider selling)
   - 🟡 Orange = Neutral (wait)

2. **Plain English Explanations**
   - No jargon - "oversold" means "cheap, likely to bounce up"
   - Real-world analogies - Bollinger Bands = "rubber band stretched tight"

3. **"?" Tooltips & Expanders**
   - Click any "📚 Beginner's Guide" to learn more
   - Hover explanations on all metrics

4. **Real Examples**
   - "If RSI = 25, the stock is oversold (cheap) - good time to buy"
   - "If volume is 3x average, the price move is REAL and strong"

5. **Decision Framework**
   - ✅ Good Entry Signals box
   - ⏸️ Wait Signals box
   - ❌ Exit Signals box

---

## 🔄 Auto-Update Feature

The dashboard auto-refreshes data every **5 minutes** to keep information current without overwhelming APIs.

To change refresh interval, edit line 395 in `app_v2.py`:
```python
timedelta(minutes=5)  # Change to desired interval
```

---

## 🧪 Testing Ollama Integration

### Test if Ollama is running:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:latest",
  "prompt": "Say hello",
  "stream": false
}'
```

Expected response:
```json
{
  "model": "llama3.2:latest",
  "created_at": "...",
  "response": "Hello! How can I help you today?",
  "done": true
}
```

### Test with stock analysis:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:latest",
  "prompt": "Analyze: Stock AAPL, RSI=35 (oversold), MACD bullish, Price above SMA-50. Give trading recommendation.",
  "stream": false
}'
```

---

## 📱 Usage Guide

### Step 1: Enter Stock
1. Type ticker symbol (AAPL, MSFT, GOOGL, etc.)
2. Select exchange (US, India .NS, India .BO)
3. Choose chart timeframe (1D, 5D, 1M, 3M)
4. Click "🚀 Analyze"

### Step 2: Check AI Summary First
- Look at the purple card at top
- Read Direction: Bullish/Bearish/Neutral
- Check Confidence: >80% = strong signal
- Read Reasoning to understand why
- Note the Action: BUY/HOLD/SELL

### Step 3: Verify with Technical Indicators
- RSI: Is it oversold (<30) or overbought (>70)?
- MACD: Bullish or bearish momentum?
- Moving Averages: Uptrend or downtrend?
- Volume: Is the move confirmed by high volume?

### Step 4: Check Chart
- Look for support/resistance levels
- See if price is respecting moving averages
- Check if volume bars are increasing on price moves

### Step 5: Review Sentiment & Fundamentals
- Positive sentiment adds confidence to buy signals
- Check if P/E ratio is reasonable vs competitors
- Verify company is profitable (positive EPS)

### Step 6: Make Decision
- If AI says BUY + technicals confirm + sentiment positive = Strong buy
- If AI says HOLD + mixed signals = Wait for clarity
- If AI says SELL + technicals bearish = Exit position

---

## 🆚 v1 vs v2 Comparison

| Feature | v1 (app_enhanced.py) | v2 (app_v2.py) |
|---------|---------------------|----------------|
| **Layout** | Multi-section tabs | Single scrollable page |
| **Priority Order** | Mixed | AI-first, then technical, then chart |
| **AI Integration** | None | ✅ Local Ollama model |
| **Beginner Explanations** | Some | ✅ Comprehensive, every metric |
| **Auto-refresh** | Manual only | ✅ Every 5 minutes |
| **Live Clock** | ✅ Yes | ✅ Yes |
| **Technical Indicators** | 8 indicators | 6 most important (focused) |
| **Charts** | Complex multi-chart | Simple candlestick + volume |
| **Target User** | Experienced traders | ✅ Complete beginners |

---

## 🛠️ Troubleshooting

### "Cannot connect to Ollama"
**Fix:**
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

### "Model not found"
**Fix:**
```bash
# Pull the model first
ollama pull llama3.2:latest

# Verify it's installed
ollama list
```

### "AI analysis is slow"
**Fix:**
- Switch to faster model: `ollama pull phi`
- Or reduce context size in code (edit prompt to be shorter)

### "No data fetched"
**Fix:**
- Check internet connection
- Verify API keys in `.env` are correct
- Try different stock ticker (some tickers have limited data)

### "Chart not showing"
**Fix:**
- Some stocks have no historical data for short timeframes
- Try longer timeframe (1M or 3M instead of 1D)

---

## 📚 Learning Resources

### Stock Market Basics
- **Investopedia** - Free articles on every term
- **YouTube: The Plain Bagel** - Simple explanations
- **Reddit: r/stocks** - Community discussions

### Technical Analysis
- **TradingView** - Free charting tools
- **YouTube: Rayner Teo** - Technical indicator tutorials
- **Book: "Technical Analysis for Dummies"**

### Swing Trading
- **YouTube: Live Traders** - Swing trading strategies
- **Book: "Swing Trading for Beginners"** by Matthew R. Kratter
- **Reddit: r/swingtrading** - Strategy discussions

---

## 🚨 Important Disclaimers

⚠️ **This tool is for educational purposes only**

- Not financial advice - always do your own research
- Past performance doesn't guarantee future results
- AI analysis can be wrong - verify with your own judgment
- Start with paper trading (simulated) before real money
- Never invest more than you can afford to lose
- Consider consulting a licensed financial advisor

---

## 🔧 Advanced Customization

### Change AI Model
Edit `app_v2.py` line 165:
```python
"model": "llama3.2:latest",  # Try: phi, mistral, mixtral
```

### Adjust Auto-refresh Interval
Edit `app_v2.py` line 395:
```python
timedelta(minutes=5)  # Change to 1, 10, 15, etc.
```

### Add More Exchanges
Edit `app_v2.py` line 388:
```python
exchange = st.selectbox("Exchange", [
    "US", 
    "India (.NS)", 
    "India (.BO)",
    "UK (.L)",  # Add London Stock Exchange
    "Japan (.T)"  # Add Tokyo Stock Exchange
])
```

### Customize Indicator Thresholds
Edit `app_v2.py` around lines 550-650 to change:
- RSI oversold/overbought levels (default: 30/70)
- Volume ratio for high/low (default: 1.5x / 0.5x)
- Bollinger %B extreme levels (default: 80% / 20%)

---

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Verify all prerequisites are installed
3. Check terminal for error messages
4. Make sure Ollama is running: `ollama serve`
5. Verify API keys are correct in `.env`

---

## ✅ Final Checklist

Before running:
- [ ] Python 3.9+ installed
- [ ] Ollama installed (`brew install ollama` or from ollama.ai)
- [ ] Ollama service running (`ollama serve`)
- [ ] AI model downloaded (`ollama pull llama3.2:latest`)
- [ ] API keys in `.env` file (already set ✅)
- [ ] Dependencies installed (`pip install -r requirements.txt`)

Run the app:
```bash
streamlit run app_v2.py
```

Open: http://localhost:8501

Enter a stock ticker (AAPL) and click "🚀 Analyze"!

---

**Enjoy swing trading with AI! 🚀📈**
