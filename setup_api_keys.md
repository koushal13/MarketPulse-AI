# 🔑 API Keys Setup Guide

## Why Do I Need API Keys?

MarketPulse uses multiple free data sources to get the most reliable stock information. When one source has issues (like rate limits), it automatically tries the next one.

## 📋 Quick Setup Checklist

### ✅ Required (System won't work without these)
- [ ] NewsAPI - For fetching news articles
- [ ] At least ONE of: Alpha Vantage OR FMP - For price data

### 🎯 Recommended (Makes the system more reliable)
- [ ] Twelve Data - Fallback for key statistics
- [ ] Finnhub - Additional fallback option

---

## 🚀 Step-by-Step Setup

### 1. Alpha Vantage (⭐ EASIEST - Instant API Key)

**Time to set up:** 1 minute  
**Free tier:** 25 requests/day  
**What it provides:** Key statistics, financial metrics

1. Go to: https://www.alphavantage.co/support/#api-key
2. Enter your email address
3. Click "GET FREE API KEY"
4. Copy the API key from your email
5. Add to your `.env` file:
   ```
   ALPHA_VANTAGE_KEY=your_key_here
   ```

---

### 2. Financial Modeling Prep (FMP)

**Time to set up:** 2 minutes  
**Free tier:** 250 requests/day  
**What it provides:** Key statistics, quarterly financials

1. Go to: https://financialmodelingprep.com/developer/docs
2. Click "Get my FREE API Key"
3. Sign up with email
4. Copy your API key from the dashboard
5. Add to your `.env` file:
   ```
   FMP_KEY=your_key_here
   ```

---

### 3. Twelve Data (Optional but Recommended)

**Time to set up:** 2 minutes  
**Free tier:** 800 requests/day  
**What it provides:** Statistics fallback

1. Go to: https://twelvedata.com/
2. Click "Start Free Trial" → "Sign Up"
3. Verify your email
4. Go to Dashboard → API Key
5. Copy your API key
6. Add to your `.env` file:
   ```
   TWELVE_DATA_KEY=your_key_here
   ```

---

### 4. Finnhub (Optional but Recommended)

**Time to set up:** 2 minutes  
**Free tier:** 60 requests/minute  
**What it provides:** Statistics fallback

1. Go to: https://finnhub.io/
2. Click "Get free API key"
3. Sign up with email
4. Copy API key from dashboard
5. Add to your `.env` file:
   ```
   FINNHUB_KEY=your_key_here
   ```

---

### 5. NewsAPI (For News Sentiment)

**Time to set up:** 2 minutes  
**Free tier:** 100 requests/day  
**What it provides:** News articles for sentiment analysis

1. Go to: https://newsapi.org/
2. Click "Get API Key"
3. Sign up for Developer plan (free)
4. Copy your API key
5. Add to your `.env` file:
   ```
   NEWS_API_KEY=your_key_here
   ```

---

## 📝 Final .env File Example

Your `.env` file should look like this:

```bash
# Required - Pick at least one
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here
FMP_KEY=your_fmp_key_here

# Optional - But highly recommended for reliability
TWELVE_DATA_KEY=your_twelve_data_key_here
FINNHUB_KEY=your_finnhub_key_here

# News sentiment
NEWS_API_KEY=your_newsapi_key_here
```

---

## 🔍 How Fallback Works

When you analyze a stock, the system tries sources in this order:

### For Key Statistics:
1. **Yahoo Finance** (built-in, no key needed) - Tries first
2. **Alpha Vantage** - If Yahoo fails
3. **FMP** - If Alpha Vantage fails
4. **Twelve Data** - If FMP fails
5. **Finnhub** - Last resort

**Example**: If Yahoo Finance has rate limits (error 429), it automatically tries Alpha Vantage. If that also fails, it tries FMP, and so on.

---

## ✅ Testing Your Setup

After adding your API keys, test them:

```bash
cd MarketPulse
streamlit run app_enhanced.py
```

Then analyze a stock like AAPL or MSFT. Check the terminal output to see which sources succeeded:

```
[1/5] Fetching key statistics from Yahoo Finance for AAPL...
✓ Got 45 statistics from Yahoo Finance
```

Or if Yahoo fails:

```
[1/5] Fetching key statistics from Yahoo Finance for AAPL...
✗ Yahoo Finance statistics failed: 429
[2/5] Trying Alpha Vantage for AAPL...
✓ Got 18 statistics from Alpha Vantage
```

---

## 💡 Pro Tips

1. **Set up at least 2-3 sources** - This ensures the system keeps working even if one service has issues

2. **Free tiers are usually enough** - For personal use, free tiers provide plenty of requests

3. **Keep your keys safe** - Never commit `.env` to git (it's already in `.gitignore`)

4. **Monitor your usage** - Each service has a dashboard showing how many requests you've used

5. **Stagger your requests** - The system automatically adds delays to avoid hitting rate limits

---

## 🆘 Troubleshooting

### "No API key (set ALPHA_VANTAGE_KEY)"
- You haven't added the API key to your `.env` file
- Make sure there are no spaces around the `=` sign
- Restart Streamlit after adding keys

### "Rate limit exceeded (429)"
- You've used up your daily quota for that service
- Wait 24 hours or set up additional fallback sources
- The system will automatically try the next source

### "All sources failed"
- Check your internet connection
- Verify all API keys are correct in `.env`
- Try a different stock symbol (some stocks may not be available)

---

## 🎉 You're All Set!

With your API keys configured, MarketPulse will now provide:
- ✅ Real-time price data
- ✅ 60+ key statistics
- ✅ Quarterly financial analysis
- ✅ Technical indicators
- ✅ Swing trading recommendations
- ✅ News sentiment analysis

Happy trading! 📈
