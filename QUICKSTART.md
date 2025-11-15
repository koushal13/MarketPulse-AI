# 🚀 Quick Start - Get Running in 5 Minutes!

## Step 1: Create Your .env File (30 seconds)

```bash
cd /Users/shatarupapradhan/MarketPulse
cp .env.example .env
```

Now open `.env` in any text editor.

---

## Step 2: Get Your First API Key (1-2 minutes)

### ⭐ Alpha Vantage (EASIEST!)

**Why this one?** Instant API key, no credit card, works immediately.

1. **Go to**: https://www.alphavantage.co/support/#api-key
2. **Enter your email** in the box
3. **Click** "GET FREE API KEY"
4. **Check your email** and copy the key
5. **Open** `/Users/shatarupapradhan/MarketPulse/.env`
6. **Paste** your key like this:
   ```
   ALPHA_VANTAGE_KEY=YOUR_KEY_HERE
   ```
7. **Save** the file

**That's it!** You can now run the app.

---

## Step 3: Run the App (30 seconds)

```bash
cd /Users/shatarupapradhan/MarketPulse
streamlit run app_enhanced.py
```

The app will open in your browser at `http://localhost:8504`

Try analyzing: **AAPL**, **MSFT**, or **GOOGL**

---

## 🎉 You're Done!

The app is now working with Alpha Vantage. You'll see in the terminal:

```
[1/5] Fetching key statistics from Yahoo Finance...
✗ Yahoo Finance failed: 429
[2/5] Trying Alpha Vantage for AAPL...
✓ Got 18 statistics from Alpha Vantage
```

---

## 🔥 Want More Reliability? (Optional - 5 more minutes)

Add these API keys to make the system super reliable:

### Financial Modeling Prep (2 minutes)
1. Go to: https://financialmodelingprep.com/developer/docs
2. Click "Get my FREE API Key"
3. Sign up with email
4. Copy your key from dashboard
5. Add to `.env`:
   ```
   FMP_KEY=your_key_here
   ```

### Twelve Data (2 minutes)
1. Go to: https://twelvedata.com/
2. Sign up free
3. Go to Dashboard → API Key
4. Copy your key
5. Add to `.env`:
   ```
   TWELVE_DATA_KEY=your_key_here
   ```

### Finnhub (2 minutes)
1. Go to: https://finnhub.io/
2. Click "Get free API key"
3. Sign up and copy key
4. Add to `.env`:
   ```
   FINNHUB_KEY=your_key_here
   ```

**Restart Streamlit** after adding new keys:
- Press `Ctrl+C` in terminal
- Run `streamlit run app_enhanced.py` again

---

## 📍 Your .env File Location

```
/Users/shatarupapradhan/MarketPulse/.env
```

Open it with:
```bash
open /Users/shatarupapradhan/MarketPulse/.env
```

Or use any text editor (VS Code, TextEdit, etc.)

---

## ✅ Verify Your Setup

After adding API keys, check the terminal output when you analyze a stock:

**Good** ✓
```
✓ Got 18 statistics from Alpha Vantage
```

**Needs API Key** ❌
```
✗ Alpha Vantage: No API key (set ALPHA_VANTAGE_KEY)
```

---

## 🆘 Having Issues?

### "No API key found"
- Make sure you saved the `.env` file
- Check there are **no spaces** around the `=` sign
- Restart Streamlit after adding keys

### "Rate limit exceeded"
- You hit the daily limit for that service
- Add more fallback API keys
- Wait 24 hours for the limit to reset

### "Module not found"
```bash
pip install -r requirements.txt
```

---

## 🎯 What You Get

With just **Alpha Vantage** configured, you get:
- ✅ Real-time price data
- ✅ Key statistics (P/E, Market Cap, etc.)
- ✅ Technical indicators (RSI, MACD, Bollinger Bands)
- ✅ Swing trading recommendations
- ✅ Buy/Sell/Hold signals

With **all fallback sources** configured:
- ✅ Everything above
- ✅ **99% uptime** - almost never fails
- ✅ Quarterly financial analysis
- ✅ Automatic failover between sources

---

## 🚀 Start Analyzing!

```bash
streamlit run app_enhanced.py
```

**Try these stocks:**
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- TSLA (Tesla)
- NVDA (NVIDIA)

**For Indian stocks:**
- TCS.BO (TCS on BSE)
- RELIANCE.NS (Reliance on NSE)
- INFY.NS (Infosys)

Happy trading! 📈
