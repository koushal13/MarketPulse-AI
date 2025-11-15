"""
Sentiment Analysis Module
Uses HuggingFace transformer models to analyze sentiment from news headlines
"""

import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SentimentAnalyzer:
    """
    Sentiment analyzer using HuggingFace's pre-trained models
    """
    
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment"):
        """
        Initialize the sentiment analyzer
        
        Args:
            model_name (str): HuggingFace model identifier
        """
        self.model_name = model_name
        self.pipeline = None
        self.initialized = False
        
        if not TRANSFORMERS_AVAILABLE:
            print("⚠️  Warning: transformers library not available. Sentiment analysis will be limited.")
            return
        
        try:
            print(f"Loading sentiment model: {model_name}...")
            # Initialize the sentiment analysis pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                truncation=True,
                max_length=512
            )
            self.initialized = True
            print("✓ Sentiment model loaded successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not load sentiment model: {str(e)}")
            print("   Sentiment analysis will use fallback method.")
            self.initialized = False
    
    def analyze_text(self, text):
        """
        Analyze sentiment of a single text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: {
                'label': str ('positive', 'negative', 'neutral'),
                'score': float (confidence score),
                'normalized_score': float (-1 to 1, where -1 is very negative, 1 is very positive)
            }
        """
        if not text or not text.strip():
            return {
                'label': 'neutral',
                'score': 0.0,
                'normalized_score': 0.0
            }
        
        # If model is not initialized, use simple fallback
        if not self.initialized or not self.pipeline:
            return self._fallback_sentiment(text)
        
        try:
            # Truncate text if too long
            text = text[:512]
            
            # Run sentiment analysis
            result = self.pipeline(text)[0]
            label = result['label'].lower()
            score = result['score']
            
            # Map labels to standardized format
            # cardiffnlp model outputs: LABEL_0 (negative), LABEL_1 (neutral), LABEL_2 (positive)
            if 'negative' in label or label == 'label_0':
                normalized_label = 'negative'
                normalized_score = -score  # Negative sentiment
            elif 'positive' in label or label == 'label_2':
                normalized_label = 'positive'
                normalized_score = score  # Positive sentiment
            else:  # neutral or LABEL_1
                normalized_label = 'neutral'
                normalized_score = 0.0
            
            return {
                'label': normalized_label,
                'score': score,
                'normalized_score': normalized_score
            }
            
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return self._fallback_sentiment(text)
    
    def _fallback_sentiment(self, text):
        """
        Simple keyword-based sentiment fallback
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Sentiment result
        """
        text_lower = text.lower()
        
        # Simple positive/negative keyword lists
        positive_words = [
            'gain', 'profit', 'surge', 'rise', 'growth', 'boost', 'up', 'increase',
            'positive', 'beat', 'strong', 'outperform', 'bullish', 'rally', 'soar',
            'success', 'record', 'high', 'upgrade', 'buy', 'optimistic'
        ]
        
        negative_words = [
            'loss', 'decline', 'fall', 'drop', 'plunge', 'crash', 'down', 'decrease',
            'negative', 'miss', 'weak', 'underperform', 'bearish', 'sell', 'downgrade',
            'concern', 'risk', 'low', 'poor', 'worst', 'cut', 'pessimistic'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            score = min(pos_count / (pos_count + neg_count + 1), 0.8)
            return {
                'label': 'positive',
                'score': score,
                'normalized_score': score
            }
        elif neg_count > pos_count:
            score = min(neg_count / (pos_count + neg_count + 1), 0.8)
            return {
                'label': 'negative',
                'score': score,
                'normalized_score': -score
            }
        else:
            return {
                'label': 'neutral',
                'score': 0.5,
                'normalized_score': 0.0
            }
    
    def analyze_batch(self, texts):
        """
        Analyze sentiment of multiple texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            list: List of sentiment results
        """
        return [self.analyze_text(text) for text in texts]
    
    def get_aggregate_sentiment(self, texts):
        """
        Get aggregate sentiment across multiple texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            dict: {
                'overall_score': float (-1 to 1),
                'positive_count': int,
                'negative_count': int,
                'neutral_count': int,
                'label': str
            }
        """
        if not texts:
            return {
                'overall_score': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'label': 'neutral'
            }
        
        results = self.analyze_batch(texts)
        
        positive_count = sum(1 for r in results if r['label'] == 'positive')
        negative_count = sum(1 for r in results if r['label'] == 'negative')
        neutral_count = sum(1 for r in results if r['label'] == 'neutral')
        
        # Calculate weighted average score
        overall_score = sum(r['normalized_score'] for r in results) / len(results)
        
        # Determine overall label
        if overall_score > 0.1:
            overall_label = 'positive'
        elif overall_score < -0.1:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        return {
            'overall_score': overall_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'label': overall_label,
            'total_articles': len(texts)
        }


def get_sentiment_score(news_headlines):
    """
    Convenience function to get sentiment score from news headlines
    
    Args:
        news_headlines (list or str): List of headlines or single concatenated text
        
    Returns:
        dict: {
            'success': bool,
            'sentiment': dict with sentiment analysis results,
            'error': str (if success=False)
        }
    """
    try:
        analyzer = SentimentAnalyzer()
        
        # Handle both string and list inputs
        if isinstance(news_headlines, str):
            # Split into chunks if it's a single long text
            chunks = [news_headlines[i:i+500] for i in range(0, len(news_headlines), 500)]
            sentiment = analyzer.get_aggregate_sentiment(chunks)
        elif isinstance(news_headlines, list):
            sentiment = analyzer.get_aggregate_sentiment(news_headlines)
        else:
            return {
                'success': False,
                'sentiment': None,
                'error': 'Invalid input type for news_headlines'
            }
        
        return {
            'success': True,
            'sentiment': sentiment,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'sentiment': None,
            'error': f'Sentiment analysis error: {str(e)}'
        }
