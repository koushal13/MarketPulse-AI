"""
Signal Generation Engine
Combines technical indicators, sentiment, and news to generate Buy/Hold/Sell signals
"""

from config import SIGNAL_RULES


class SignalEngine:
    """
    Generates trading signals based on configurable rules
    """
    
    def __init__(self, rules=None):
        """
        Initialize signal engine with custom or default rules
        
        Args:
            rules (dict): Custom signal rules (optional)
        """
        self.rules = rules if rules else SIGNAL_RULES
    
    def generate_signal(self, technical_data, sentiment_data, news_data=None, price_data=None, stats_data=None):
        """
        Generate a Buy/Hold/Sell signal based on all available data with advanced logic
        
        Args:
            technical_data (dict): Technical indicators (RSI, MACD, quote)
            sentiment_data (dict): Sentiment analysis results
            news_data (dict): News articles (optional, for context)
            price_data (dict): Current price and historical data
            stats_data (dict): Key statistics (P/E, Beta, etc.)
            
        Returns:
            dict: {
                'signal': str ('BUY', 'HOLD', 'SELL'),
                'confidence': float (0-1),
                'reasons': list of str (explanation of signal),
                'metrics': dict (key metrics used in decision),
                'risk_level': str ('Low', 'Medium', 'High')
            }
        """
        reasons = []
        signal = 'HOLD'
        confidence = 0.5
        risk_level = 'Medium'
        
        # Extract technical metrics
        rsi = technical_data.get('rsi')
        macd_data = technical_data.get('macd', {})
        macd_line = macd_data.get('macd')
        signal_line = macd_data.get('signal')
        macd_histogram = macd_data.get('histogram')
        
        # Extract new indicators
        bollinger = technical_data.get('bollinger', {})
        stochastic = technical_data.get('stochastic', {})
        adx_data = technical_data.get('adx', {})
        ma_data = technical_data.get('moving_averages', {})
        
        # Extract sentiment
        sentiment_score = sentiment_data.get('sentiment', {}).get('overall_score', 0.0) if sentiment_data.get('success') else 0.0
        sentiment_label = sentiment_data.get('sentiment', {}).get('label', 'neutral') if sentiment_data.get('success') else 'neutral'
        
        # Extract price data
        current_price = None
        price_change_pct = 0
        volume = None
        avg_volume = None
        fifty_two_week_high = None
        fifty_two_week_low = None
        
        if price_data:
            current_price = price_data.get('price')
            price_change_pct = price_data.get('change_percent', 0)
            volume = price_data.get('volume')
        
        # Extract statistics
        beta = None
        pe_ratio = None
        debt_to_equity = None
        
        if stats_data and stats_data.get('success'):
            stats = stats_data.get('data', {})
            beta = stats.get('beta')
            pe_ratio = stats.get('trailingPE')
            debt_to_equity = stats.get('debtToEquity')
            fifty_two_week_high = stats.get('fiftyTwoWeekHigh')
            fifty_two_week_low = stats.get('fiftyTwoWeekLow')
            avg_volume = stats.get('averageVolume')
        
        # Collect all metrics
        metrics = {
            'rsi': rsi,
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': macd_histogram,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'price': current_price,
            'change_pct': price_change_pct,
            'volume': volume,
            'avg_volume': avg_volume,
            'beta': beta,
            'pe_ratio': pe_ratio,
            'debt_to_equity': debt_to_equity
        }
        
        # Check for missing critical data
        missing_data = []
        if rsi is None:
            missing_data.append('RSI')
        if macd_line is None or signal_line is None:
            missing_data.append('MACD')
        
        if missing_data:
            reasons.append(f"⚠️ Missing data: {', '.join(missing_data)}")
        
        # --- ADVANCED BUY SIGNAL LOGIC ---
        buy_conditions = []
        buy_score = 0
        buy_weights = {
            'sentiment': 0.20,
            'rsi': 0.25,
            'macd': 0.25,
            'momentum': 0.15,
            'value': 0.10,
            'volume': 0.05
        }
        
        # 1. Sentiment Analysis (20%)
        if sentiment_score >= self.rules['BUY']['sentiment_threshold']:
            buy_conditions.append(f"✓ Strong positive sentiment ({sentiment_score:.2f})")
            buy_score += buy_weights['sentiment']
        elif sentiment_score >= 0.1:
            buy_conditions.append(f"○ Moderately positive sentiment ({sentiment_score:.2f})")
            buy_score += buy_weights['sentiment'] * 0.5
        
        # 2. RSI - Oversold with nuance (25%)
        if rsi is not None:
            if rsi < 30:
                buy_conditions.append(f"✓ RSI strongly oversold ({rsi:.1f} - great entry point)")
                buy_score += buy_weights['rsi']
            elif rsi < 40:
                buy_conditions.append(f"○ RSI moderately oversold ({rsi:.1f})")
                buy_score += buy_weights['rsi'] * 0.7
            elif rsi < 50:
                buy_conditions.append(f"○ RSI neutral-low ({rsi:.1f})")
                buy_score += buy_weights['rsi'] * 0.3
        
        # 3. MACD - Bullish crossover and histogram (25%)
        if macd_line is not None and signal_line is not None:
            macd_diff = macd_line - signal_line
            if macd_line > signal_line:
                if macd_diff > 0.5:
                    buy_conditions.append(f"✓ Strong MACD bullish crossover (Δ {macd_diff:.2f})")
                    buy_score += buy_weights['macd']
                else:
                    buy_conditions.append(f"○ MACD bullish ({macd_diff:.2f})")
                    buy_score += buy_weights['macd'] * 0.6
                
                # Check histogram momentum
                if macd_histogram and macd_histogram > 0:
                    buy_conditions.append(f"✓ MACD histogram positive ({macd_histogram:.2f})")
                    buy_score += 0.05
        
        # 4. Price Momentum (15%)
        if current_price and fifty_two_week_high and fifty_two_week_low:
            price_range = fifty_two_week_high - fifty_two_week_low
            position_in_range = (current_price - fifty_two_week_low) / price_range if price_range > 0 else 0.5
            
            if position_in_range < 0.3:
                buy_conditions.append(f"✓ Near 52-week low ({position_in_range*100:.0f}% of range)")
                buy_score += buy_weights['momentum']
            elif position_in_range < 0.5:
                buy_conditions.append(f"○ Below midpoint of 52-week range ({position_in_range*100:.0f}%)")
                buy_score += buy_weights['momentum'] * 0.5
        
        # 5. Valuation (10%)
        if pe_ratio is not None:
            if pe_ratio < 15:
                buy_conditions.append(f"✓ Attractive P/E ratio ({pe_ratio:.1f})")
                buy_score += buy_weights['value']
            elif pe_ratio < 25:
                buy_conditions.append(f"○ Reasonable P/E ratio ({pe_ratio:.1f})")
                buy_score += buy_weights['value'] * 0.5
        
        # 6. Volume confirmation (5%)
        if volume and avg_volume and volume > avg_volume * 1.5:
            buy_conditions.append(f"✓ High volume confirmation ({volume/avg_volume:.1f}x avg)")
            buy_score += buy_weights['volume']
        
        # Additional indicators for scoring boost (not in base weights)
        additional_buy_signals = []
        
        # Bollinger Bands - oversold signal
        if bollinger and current_price:
            percent_b = bollinger.get('percent_b', 0.5)
            if percent_b < 0.2:  # Near lower band
                additional_buy_signals.append(f"✓ BB oversold (B%={percent_b*100:.0f}%)")
                buy_score += 0.05
            elif percent_b < 0.4:
                additional_buy_signals.append(f"○ BB below midpoint")
                buy_score += 0.02
        
        # Stochastic - oversold
        if stochastic:
            stoch_k = stochastic.get('k')
            if stoch_k and stoch_k < 20:
                additional_buy_signals.append(f"✓ Stochastic oversold ({stoch_k:.0f})")
                buy_score += 0.05
            elif stoch_k and stoch_k < 40:
                additional_buy_signals.append(f"○ Stochastic low ({stoch_k:.0f})")
                buy_score += 0.02
        
        # Moving Average crossovers
        if ma_data:
            above_sma_20 = ma_data.get('above_sma_20')
            above_sma_50 = ma_data.get('above_sma_50')
            
            if above_sma_20 and above_sma_50:
                additional_buy_signals.append(f"✓ Price above SMA 20 & 50")
                buy_score += 0.05
            elif above_sma_20:
                additional_buy_signals.append(f"○ Price above SMA 20")
                buy_score += 0.02
        
        # ADX - trend strength
        if adx_data:
            adx_value = adx_data.get('adx')
            di_plus = adx_data.get('di_plus')
            di_minus = adx_data.get('di_minus')
            
            if adx_value and adx_value > 25 and di_plus and di_minus and di_plus > di_minus:
                additional_buy_signals.append(f"✓ Strong uptrend (ADX={adx_value:.0f})")
                buy_score += 0.05
        
        # Add additional signals to buy conditions
        buy_conditions.extend(additional_buy_signals)
        
        # --- ADVANCED SELL SIGNAL LOGIC ---
        sell_conditions = []
        sell_score = 0
        sell_weights = {
            'sentiment': 0.20,
            'rsi': 0.25,
            'macd': 0.25,
            'momentum': 0.15,
            'risk': 0.15
        }
        
        # 1. Sentiment Analysis (20%)
        if sentiment_score <= self.rules['SELL']['sentiment_threshold']:
            sell_conditions.append(f"⚠️ Negative sentiment ({sentiment_score:.2f})")
            sell_score += sell_weights['sentiment']
        elif sentiment_score <= -0.1:
            sell_conditions.append(f"○ Moderately negative sentiment ({sentiment_score:.2f})")
            sell_score += sell_weights['sentiment'] * 0.5
        
        # 2. RSI - Overbought (25%)
        if rsi is not None:
            if rsi > 70:
                sell_conditions.append(f"⚠️ RSI overbought ({rsi:.1f} - take profits)")
                sell_score += sell_weights['rsi']
            elif rsi > 60:
                sell_conditions.append(f"○ RSI moderately high ({rsi:.1f})")
                sell_score += sell_weights['rsi'] * 0.6
        
        # 3. MACD - Bearish (25%)
        if macd_line is not None and signal_line is not None:
            if macd_line < signal_line:
                macd_diff = abs(macd_line - signal_line)
                if macd_diff > 0.5:
                    sell_conditions.append(f"⚠️ Strong MACD bearish crossover (Δ -{macd_diff:.2f})")
                    sell_score += sell_weights['macd']
                else:
                    sell_conditions.append(f"○ MACD bearish (Δ -{macd_diff:.2f})")
                    sell_score += sell_weights['macd'] * 0.6
        
        # 4. Overextension (15%)
        if current_price and fifty_two_week_high and fifty_two_week_low:
            price_range = fifty_two_week_high - fifty_two_week_low
            position_in_range = (current_price - fifty_two_week_low) / price_range if price_range > 0 else 0.5
            
            if position_in_range > 0.9:
                sell_conditions.append(f"⚠️ Near 52-week high ({position_in_range*100:.0f}% - overbought)")
                sell_score += sell_weights['momentum']
            elif position_in_range > 0.7:
                sell_conditions.append(f"○ Above 52-week midpoint ({position_in_range*100:.0f}%)")
                sell_score += sell_weights['momentum'] * 0.5
        
        # 5. Risk factors (15%)
        risk_factors = []
        if beta and beta > 1.5:
            risk_factors.append(f"High volatility (β={beta:.2f})")
            sell_score += sell_weights['risk'] * 0.5
        if debt_to_equity and debt_to_equity > 2.0:
            risk_factors.append(f"High debt/equity ({debt_to_equity:.2f})")
            sell_score += sell_weights['risk'] * 0.5
        
        if risk_factors:
            sell_conditions.append(f"⚠️ Risk: {', '.join(risk_factors)}")
        
        # Additional indicators for sell signals
        additional_sell_signals = []
        
        # Bollinger Bands - overbought
        if bollinger and current_price:
            percent_b = bollinger.get('percent_b', 0.5)
            if percent_b > 0.8:  # Near upper band
                additional_sell_signals.append(f"⚠️ BB overbought (B%={percent_b*100:.0f}%)")
                sell_score += 0.05
            elif percent_b > 0.6:
                additional_sell_signals.append(f"○ BB above midpoint")
                sell_score += 0.02
        
        # Stochastic - overbought
        if stochastic:
            stoch_k = stochastic.get('k')
            if stoch_k and stoch_k > 80:
                additional_sell_signals.append(f"⚠️ Stochastic overbought ({stoch_k:.0f})")
                sell_score += 0.05
            elif stoch_k and stoch_k > 60:
                additional_sell_signals.append(f"○ Stochastic high ({stoch_k:.0f})")
                sell_score += 0.02
        
        # Moving Average - below key levels
        if ma_data:
            above_sma_20 = ma_data.get('above_sma_20')
            above_sma_50 = ma_data.get('above_sma_50')
            
            if above_sma_20 is False and above_sma_50 is False:
                additional_sell_signals.append(f"⚠️ Price below SMA 20 & 50")
                sell_score += 0.05
            elif above_sma_20 is False:
                additional_sell_signals.append(f"○ Price below SMA 20")
                sell_score += 0.02
        
        # ADX - strong downtrend
        if adx_data:
            adx_value = adx_data.get('adx')
            di_plus = adx_data.get('di_plus')
            di_minus = adx_data.get('di_minus')
            
            if adx_value and adx_value > 25 and di_plus and di_minus and di_minus > di_plus:
                additional_sell_signals.append(f"⚠️ Strong downtrend (ADX={adx_value:.0f})")
                sell_score += 0.05
        
        # Add additional signals to sell conditions
        sell_conditions.extend(additional_sell_signals)
        
        # --- DETERMINE FINAL SIGNAL WITH DYNAMIC THRESHOLDS ---
        
        # Strong BUY: High buy score, low sell score
        if buy_score >= 0.65 and sell_score < 0.3:
            signal = 'BUY'
            confidence = min(buy_score * 0.85 + 0.15, 0.95)  # Scale to 15-95%
            reasons.extend(buy_conditions)
            risk_level = self._calculate_risk(beta, debt_to_equity, rsi)
            
        # Strong SELL: High sell score, low buy score
        elif sell_score >= 0.60 and buy_score < 0.3:
            signal = 'SELL'
            confidence = min(sell_score * 0.85 + 0.15, 0.95)
            reasons.extend(sell_conditions)
            risk_level = 'High'
            
        # Moderate BUY: More buy than sell
        elif buy_score > sell_score and buy_score >= 0.45:
            signal = 'BUY'
            confidence = min(0.55 + (buy_score - sell_score) * 0.5, 0.75)
            reasons.extend(buy_conditions[:3])
            risk_level = self._calculate_risk(beta, debt_to_equity, rsi)
            
        # Moderate SELL: More sell than buy  
        elif sell_score > buy_score and sell_score >= 0.45:
            signal = 'SELL'
            confidence = min(0.55 + (sell_score - buy_score) * 0.5, 0.75)
            reasons.extend(sell_conditions[:3])
            risk_level = 'High'
            
        # HOLD: Balanced or weak signals
        else:
            signal = 'HOLD'
            # Dynamic confidence based on how balanced it is
            score_diff = abs(buy_score - sell_score)
            if score_diff < 0.1:
                confidence = 0.35  # Very uncertain
                reasons.append("⊙ Highly uncertain - signals are balanced")
            else:
                confidence = 0.45 + score_diff * 0.2  # 45-65%
                reasons.append("⊙ Mixed signals - wait for clearer direction")
            
            # Show top signals from both sides
            if buy_conditions:
                reasons.append(f"Bullish: {buy_conditions[0]}")
            if sell_conditions:
                reasons.append(f"Bearish: {sell_conditions[0]}")
            
            risk_level = self._calculate_risk(beta, debt_to_equity, rsi)
        
        # Add price context
        if current_price and price_change_pct is not None:
            direction = "▲" if price_change_pct >= 0 else "▼"
            reasons.append(f"📊 Current: ${current_price:.2f} {direction} {abs(price_change_pct):.2f}%")
        
        # Add news context
        news_count = news_data.get('count', 0) if news_data and news_data.get('success') else 0
        if news_count > 0:
            reasons.append(f"📰 {news_count} recent articles analyzed")
        
        # Calculate swing trading recommendations
        swing_trade = self._calculate_swing_trade_levels(
            signal, current_price, technical_data, stats_data, confidence
        )
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'metrics': metrics,
            'risk_level': risk_level,
            'news_count': news_count,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'swing_trade': swing_trade
        }
    
    def _calculate_risk(self, beta, debt_to_equity, rsi):
        """Calculate risk level based on multiple factors"""
        risk_score = 0
        
        if beta and beta > 1.5:
            risk_score += 2
        elif beta and beta > 1.2:
            risk_score += 1
        
        if debt_to_equity and debt_to_equity > 2.0:
            risk_score += 2
        elif debt_to_equity and debt_to_equity > 1.0:
            risk_score += 1
        
        if rsi and (rsi > 75 or rsi < 25):
            risk_score += 1
        
        if risk_score >= 4:
            return 'High'
        elif risk_score >= 2:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_swing_trade_levels(self, signal, current_price, technical_data, stats_data, confidence):
        """
        Calculate swing trading entry, target, and stop loss levels
        
        For swing trading (5-30 day holds):
        - Entry: Current price or better (limit order suggestions)
        - Target: Based on resistance levels, Bollinger Bands, Fibonacci
        - Stop Loss: Based on support levels, ATR, recent lows
        
        Args:
            signal: BUY/SELL/HOLD
            current_price: Current stock price
            technical_data: Technical indicators
            stats_data: Key statistics
            confidence: Signal confidence
            
        Returns:
            dict: Swing trading recommendations
        """
        if not current_price:
            return None
        
        # Extract key levels
        bollinger = technical_data.get('bollinger', {})
        ma_data = technical_data.get('moving_averages', {})
        atr = technical_data.get('atr')
        rsi = technical_data.get('rsi')
        
        # Extract MACD data
        macd_data = technical_data.get('macd', {})
        macd_line = macd_data.get('macd')
        signal_line = macd_data.get('signal')
        
        # Get 52-week high/low for context
        fifty_two_week_high = None
        fifty_two_week_low = None
        if stats_data and stats_data.get('success'):
            stats = stats_data.get('data', {})
            fifty_two_week_high = stats.get('fiftyTwoWeekHigh')
            fifty_two_week_low = stats.get('fiftyTwoWeekLow')
        
        recommendation = {
            'action': signal,
            'current_price': current_price,
            'entry_price': None,
            'target_price': None,
            'stop_loss': None,
            'risk_reward_ratio': None,
            'holding_period': None,
            'notes': []
        }
        
        # Calculate ATR-based levels (if available)
        atr_value = atr if atr else current_price * 0.02  # Default 2% if no ATR
        
        if signal == 'BUY':
            # Entry Strategy for BUY
            bb_lower = bollinger.get('lower')
            sma_20 = ma_data.get('sma_20')
            
            # Entry: Current price or wait for pullback
            if rsi and rsi < 40:
                # Oversold - can enter at current price
                recommendation['entry_price'] = current_price
                recommendation['notes'].append("✓ Oversold - enter at market price")
            elif bb_lower and current_price < bb_lower * 1.02:
                # Near lower Bollinger Band
                recommendation['entry_price'] = current_price
                recommendation['notes'].append("✓ Near support - enter at market price")
            else:
                # Wait for pullback
                pullback_price = current_price * 0.98  # 2% pullback
                if sma_20:
                    pullback_price = min(pullback_price, sma_20)
                recommendation['entry_price'] = pullback_price
                recommendation['notes'].append(f"○ Wait for pullback to ${pullback_price:.2f}")
            
            # Target Price (swing trade: 5-15% gain typical)
            bb_upper = bollinger.get('upper')
            sma_50 = ma_data.get('sma_50')
            
            targets = []
            if bb_upper:
                targets.append(bb_upper)
            if sma_50 and sma_50 > current_price:
                targets.append(sma_50)
            if fifty_two_week_high:
                # Conservative target: 70% of distance to 52-week high
                targets.append(current_price + (fifty_two_week_high - current_price) * 0.5)
            
            # Use highest target or default 8-12% based on confidence
            if targets:
                recommendation['target_price'] = max(targets)
            else:
                gain_pct = 0.08 + (confidence * 0.08)  # 8-16% based on confidence
                recommendation['target_price'] = current_price * (1 + gain_pct)
            
            # Stop Loss (protect capital)
            bb_lower = bollinger.get('lower')
            sma_20 = ma_data.get('sma_20')
            
            stops = []
            # ATR-based stop (2x ATR below entry)
            stops.append(recommendation['entry_price'] - (atr_value * 2))
            
            # Support level stops
            if bb_lower:
                stops.append(bb_lower * 0.98)
            if sma_20 and sma_20 < current_price:
                stops.append(sma_20 * 0.97)
            if fifty_two_week_low:
                stops.append(max(fifty_two_week_low * 1.02, current_price * 0.90))
            
            # Use tightest reasonable stop (but not more than 8% loss)
            recommendation['stop_loss'] = max(stops) if stops else recommendation['entry_price'] * 0.94
            recommendation['stop_loss'] = max(recommendation['stop_loss'], recommendation['entry_price'] * 0.92)
            
            # Calculate risk/reward
            risk = recommendation['entry_price'] - recommendation['stop_loss']
            reward = recommendation['target_price'] - recommendation['entry_price']
            recommendation['risk_reward_ratio'] = reward / risk if risk > 0 else 0
            
            # Holding period suggestion
            if confidence > 0.7:
                recommendation['holding_period'] = "5-15 days"
            else:
                recommendation['holding_period'] = "10-30 days"
            
            # Add strategy notes
            if recommendation['risk_reward_ratio'] >= 2:
                recommendation['notes'].append(f"✓ Excellent R:R ratio {recommendation['risk_reward_ratio']:.1f}:1")
            elif recommendation['risk_reward_ratio'] >= 1.5:
                recommendation['notes'].append(f"○ Good R:R ratio {recommendation['risk_reward_ratio']:.1f}:1")
            else:
                recommendation['notes'].append(f"⚠️ Low R:R ratio {recommendation['risk_reward_ratio']:.1f}:1 - wait for better setup")
        
        elif signal == 'SELL':
            # For SELL signal in swing trading - exit existing positions
            recommendation['entry_price'] = None  # Not buying
            recommendation['target_price'] = None
            recommendation['stop_loss'] = None
            recommendation['notes'].append("⚠️ Exit long positions or avoid buying")
            recommendation['notes'].append("Consider taking profits if holding")
            
            # If already holding, suggest exit levels
            if rsi and rsi > 70:
                recommendation['notes'].append(f"RSI overbought ({rsi:.0f}) - sell at market")
            
        else:  # HOLD - provide specific entry recommendations
            # Calculate better entry points based on technical levels
            better_entries = []
            
            # Support levels to watch
            bb_lower = bollinger.get('lower')
            sma_20 = ma_data.get('sma_20')
            sma_50 = ma_data.get('sma_50')
            
            if bb_lower and bb_lower < current_price:
                better_entries.append(f"Lower Bollinger Band at ${bb_lower:.2f} ({((bb_lower-current_price)/current_price)*100:.1f}%)")
            
            if sma_20 and sma_20 < current_price:
                better_entries.append(f"SMA-20 support at ${sma_20:.2f} ({((sma_20-current_price)/current_price)*100:.1f}%)")
            
            if sma_50 and sma_50 < current_price:
                better_entries.append(f"SMA-50 support at ${sma_50:.2f} ({((sma_50-current_price)/current_price)*100:.1f}%)")
            
            # Check if oversold conditions are developing
            if rsi and 45 <= rsi <= 55:
                recommendation['notes'].append("⊙ RSI neutral - wait for oversold (below 40) or overbought (above 60)")
            elif rsi and 40 < rsi < 45:
                recommendation['notes'].append("○ RSI approaching oversold - watch for entry near support")
            elif rsi and 55 < rsi < 60:
                recommendation['notes'].append("○ RSI approaching overbought - wait for pullback")
            
            # MACD recommendations
            if macd_line is not None and signal_line is not None:
                if abs(macd_line - signal_line) < 0.3:
                    recommendation['notes'].append("⊙ MACD near crossover - wait for clear signal")
                
            # Volume recommendations
            if better_entries:
                recommendation['notes'].append(f"**Better Entry Points:**")
                for entry in better_entries[:3]:  # Show top 3
                    recommendation['notes'].append(f"  → Wait for pullback to {entry}")
            else:
                recommendation['notes'].append("⊙ No clear support levels - wait for 3-5% pullback")
            
            # Breakout recommendations
            bb_upper = bollinger.get('upper')
            if bb_upper and bb_upper > current_price:
                recommendation['notes'].append(f"**Breakout Watch:**")
                recommendation['notes'].append(f"  → Buy on break above ${bb_upper:.2f} with volume")
            
            # 52-week context
            if fifty_two_week_high and fifty_two_week_low:
                price_range = fifty_two_week_high - fifty_two_week_low
                position = (current_price - fifty_two_week_low) / price_range if price_range > 0 else 0.5
                
                if position < 0.3:
                    recommendation['notes'].append(f"○ Near 52-week low ({position*100:.0f}% of range) - may bounce from support")
                elif position > 0.7:
                    recommendation['notes'].append(f"○ Near 52-week high ({position*100:.0f}% of range) - wait for pullback")
                else:
                    recommendation['notes'].append(f"○ Mid-range ({position*100:.0f}% of 52w range) - wait for trend confirmation")
            
            # Set fields to None for HOLD
            recommendation['entry_price'] = None
            recommendation['target_price'] = None
            recommendation['stop_loss'] = None
        
        return recommendation
    
    def update_rules(self, new_rules):
        """
        Update signal generation rules
        
        Args:
            new_rules (dict): New rules configuration
        """
        self.rules.update(new_rules)


def generate_signal(symbol, technical_data, sentiment_data, news_data=None, price_data=None, stats_data=None):
    """
    Convenience function to generate a signal for a symbol
    
    Args:
        symbol (str): Stock ticker symbol
        technical_data (dict): Technical indicators
        sentiment_data (dict): Sentiment analysis results
        news_data (dict): News data (optional)
        price_data (dict): Price data (optional)
        stats_data (dict): Key statistics (optional)
        
    Returns:
        dict: Signal generation result
    """
    engine = SignalEngine()
    
    try:
        result = engine.generate_signal(technical_data, sentiment_data, news_data, price_data, stats_data)
        result['symbol'] = symbol
        result['success'] = True
        return result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Signal generation error for {symbol}: {error_details}")
        return {
            'success': False,
            'signal': 'ERROR',
            'error': f'Signal generation error: {str(e)}',
            'error_details': error_details,
            'symbol': symbol,
            'confidence': 0.5,
            'reasons': [f'Error: {str(e)}'],
            'risk_level': 'High'
        }
