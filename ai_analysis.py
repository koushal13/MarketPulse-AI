"""
AI-Powered Analysis Module
Uses Ollama (free, local LLM) for advanced market analysis
"""

import json
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class AIAnalyzer:
    """
    AI analyzer using Ollama for advanced market insights
    """
    
    def __init__(self, model="llama3.2:1b"):
        """
        Initialize AI analyzer
        
        Args:
            model (str): Ollama model to use (llama3.2:1b is fast and free)
        """
        self.model = model
        self.available = OLLAMA_AVAILABLE
        
        if not OLLAMA_AVAILABLE:
            print("⚠️  Ollama not available. Install with: pip install ollama")
            print("   Also install Ollama from: https://ollama.ai")
    
    def check_ollama_running(self):
        """Check if Ollama is running"""
        if not self.available:
            return False
        
        try:
            # Try to list models to check if Ollama is running
            ollama.list()
            return True
        except Exception:
            return False
    
    def analyze_stock(self, symbol, technical_data, sentiment_data, news_data, price_data):
        """
        Perform AI-powered analysis of all stock data
        
        Args:
            symbol (str): Stock ticker
            technical_data (dict): Technical indicators
            sentiment_data (dict): Sentiment analysis
            news_data (dict): News articles
            price_data (dict): Current price data
            
        Returns:
            dict: AI analysis results
        """
        if not self.available or not self.check_ollama_running():
            return {
                'success': False,
                'analysis': None,
                'error': 'Ollama not available or not running'
            }
        
        try:
            # Prepare context for AI
            context = self._prepare_context(symbol, technical_data, sentiment_data, news_data, price_data)
            
            # Create prompt
            prompt = f"""You are an expert financial analyst. Analyze the following stock data and provide insights.

Stock: {symbol}

{context}

Provide a detailed analysis covering:
1. Key observations from the data
2. Potential risks and opportunities
3. Market sentiment interpretation
4. Technical indicator insights
5. Your expert recommendation (Buy/Hold/Sell) with reasoning

Keep your response concise but insightful (max 300 words)."""

            # Get AI response
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            analysis_text = response['message']['content']
            
            return {
                'success': True,
                'analysis': analysis_text,
                'model': self.model,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'analysis': None,
                'error': f'AI analysis error: {str(e)}'
            }
    
    def _prepare_context(self, symbol, technical_data, sentiment_data, news_data, price_data):
        """Prepare context string for AI"""
        context_parts = []
        
        # Price data
        if price_data and price_data.get('success'):
            data = price_data['data']
            context_parts.append(f"Current Price: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")
            context_parts.append(f"Market Cap: ${data.get('market_cap', 0):,.0f}")
            context_parts.append(f"P/E Ratio: {data.get('pe_ratio', 'N/A')}")
        
        # Technical indicators
        rsi = technical_data.get('rsi')
        if rsi:
            context_parts.append(f"RSI: {rsi:.2f}")
        
        macd = technical_data.get('macd', {})
        if macd.get('macd'):
            context_parts.append(f"MACD: {macd['macd']:.4f}, Signal: {macd.get('signal', 0):.4f}")
        
        # Sentiment
        if sentiment_data and sentiment_data.get('success'):
            sent = sentiment_data['sentiment']
            context_parts.append(f"News Sentiment: {sent['label']} (score: {sent['overall_score']:.3f})")
            context_parts.append(f"Sentiment Breakdown: {sent['positive_count']} positive, {sent['neutral_count']} neutral, {sent['negative_count']} negative")
        
        # Recent news headlines
        if news_data and news_data.get('success'):
            headlines = [article['title'] for article in news_data['articles'][:3]]
            if headlines:
                context_parts.append(f"Recent Headlines: {'; '.join(headlines)}")
        
        return '\n'.join(context_parts)
    
    def explain_indicator(self, indicator_name, value=None):
        """
        Get AI explanation of a technical indicator
        
        Args:
            indicator_name (str): Name of indicator (RSI, MACD, etc.)
            value (float): Current value (optional)
            
        Returns:
            str: Explanation
        """
        if not self.available or not self.check_ollama_running():
            return self._fallback_explanation(indicator_name, value)
        
        try:
            value_context = f" The current value is {value}." if value else ""
            
            prompt = f"""Explain the {indicator_name} technical indicator in simple terms.{value_context}
            
Keep it brief (2-3 sentences) and explain what it means for traders."""
            
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return response['message']['content']
            
        except Exception:
            return self._fallback_explanation(indicator_name, value)
    
    def _fallback_explanation(self, indicator_name, value=None):
        """Fallback explanations when AI is not available"""
        explanations = {
            'RSI': 'RSI (Relative Strength Index) measures momentum on a 0-100 scale. Below 30 indicates oversold (potential buy), above 70 indicates overbought (potential sell).',
            'MACD': 'MACD (Moving Average Convergence Divergence) shows trend direction and momentum. When MACD line crosses above signal line, it\'s bullish; below is bearish.',
            'Sentiment': 'Sentiment analysis uses AI to determine if news is positive, negative, or neutral. Positive sentiment can indicate bullish market perception.',
            'Volume': 'Volume shows how many shares traded. High volume during price increases suggests strong buying interest.',
            'P/E Ratio': 'Price-to-Earnings ratio compares stock price to earnings. Lower P/E may indicate undervaluation, higher P/E may suggest growth expectations.'
        }
        
        return explanations.get(indicator_name, f'{indicator_name} is a technical indicator used in market analysis.')


def get_ai_analysis(symbol, technical_data, sentiment_data, news_data, price_data):
    """
    Convenience function to get AI analysis
    
    Args:
        symbol (str): Stock ticker
        technical_data, sentiment_data, news_data, price_data: Analysis data
        
    Returns:
        dict: AI analysis result
    """
    analyzer = AIAnalyzer()
    return analyzer.analyze_stock(symbol, technical_data, sentiment_data, news_data, price_data)
