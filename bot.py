#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Optional, Any, Union, List, Tuple
import sys
import os
import time
import requests
import re
import numpy as np
from datetime import datetime, timedelta
import anthropic
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import random
import statistics

from utils.logger import logger
from utils.browser import browser
from config import config
from coingecko_handler import CoinGeckoHandler
from mood_config import MoodIndicators, determine_advanced_mood, Mood, MemePhraseGenerator
from meme_phrases import MEME_PHRASES

class CryptoAnalysisBot:
    def __init__(self) -> None:
        self.browser = browser
        self.config = config
        self.claude_client = anthropic.Client(api_key=self.config.CLAUDE_API_KEY)
        self.past_predictions = []
        self.meme_phrases = MEME_PHRASES
        self.last_check_time = datetime.now()
        self.last_market_data = {}
        
        # Initialize CoinGecko handler with 60s cache duration
        self.coingecko = CoinGeckoHandler(
            base_url=self.config.COINGECKO_BASE_URL,
            cache_duration=60
        )
        
        # Target chains to analyze
        self.target_chains = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'XRP': 'ripple',
            'BNB': 'binancecoin',
            'AVAX': 'avalanche-2',
            'DOT': 'polkadot',
            'UNI': 'uniswap',
            'NEAR': 'near',
            'AAVE': 'aave',
            'FIL': 'filecoin',
            'POL': 'matic-network',
            'KAITO': 'kaito'  # Kept in the list but not given special treatment
        }

        # All tokens for reference and comparison
        self.reference_tokens = list(self.target_chains.keys())
        
        # Chain name mapping for display
        self.chain_name_mapping = self.target_chains.copy()
        
        self.CORRELATION_THRESHOLD = 0.75  
        self.VOLUME_THRESHOLD = 0.60  
        self.TIME_WINDOW = 24
        
        # Smart money thresholds
        self.SMART_MONEY_VOLUME_THRESHOLD = 1.5  # 50% above average
        self.SMART_MONEY_ZSCORE_THRESHOLD = 2.0  # 2 standard deviations
        
        logger.log_startup()

    def _get_historical_volume_data(self, chain: str, minutes: int = None) -> List[Dict[str, Any]]:
        """
        Get historical volume data for the specified window period
        """
        try:
            # Use config's window minutes if not specified
            if minutes is None:
                minutes = self.config.VOLUME_WINDOW_MINUTES
                
            window_start = datetime.now() - timedelta(minutes=minutes)
            query = """
                SELECT timestamp, volume
                FROM market_data
                WHERE chain = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
            
            conn = self.config.db.conn
            cursor = conn.cursor()
            cursor.execute(query, (chain, window_start))
            results = cursor.fetchall()
            
            volume_data = [
                {
                    'timestamp': datetime.fromisoformat(row[0]),
                    'volume': float(row[1])
                }
                for row in results
            ]
            
            logger.logger.debug(
                f"Retrieved {len(volume_data)} volume data points for {chain} "
                f"over last {minutes} minutes"
            )
            
            return volume_data
            
        except Exception as e:
            logger.log_error(f"Historical Volume Data - {chain}", str(e))
            return []
            
    def _is_duplicate_analysis(self, new_tweet: str, last_posts: List[str]) -> bool:
        """
        Enhanced duplicate detection with time-based thresholds.
        Applies different checks based on how recently similar content was posted:
        - Very recent posts (< 15 min): Check for exact matches
        - Recent posts (15-30 min): Check for high similarity
        - Older posts (> 30 min): Allow similar content
        """
        try:
            # Log that we're using enhanced duplicate detection
            logger.logger.info("Using enhanced time-based duplicate detection")
            
            # Define time windows for different levels of duplicate checking
            VERY_RECENT_WINDOW_MINUTES = 15
            RECENT_WINDOW_MINUTES = 30
            
            # Define similarity thresholds
            HIGH_SIMILARITY_THRESHOLD = 0.85  # 85% similar for recent posts
            
            # 1. Check for exact matches in very recent database entries (last 15 minutes)
            conn = self.config.db.conn
            cursor = conn.cursor()
            
            # Very recent exact duplicates check
            cursor.execute("""
                SELECT content FROM posted_content 
                WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
            """, (VERY_RECENT_WINDOW_MINUTES,))
            
            very_recent_posts = [row[0] for row in cursor.fetchall()]
            
            # Check for exact matches in very recent posts
            for post in very_recent_posts:
                if post.strip() == new_tweet.strip():
                    logger.logger.info(f"Exact duplicate detected within last {VERY_RECENT_WINDOW_MINUTES} minutes")
                    return True
            
            # 2. Check for high similarity in recent posts (15-30 minutes)
            cursor.execute("""
                SELECT content FROM posted_content 
                WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
                AND timestamp < datetime('now', '-' || ? || ' minutes')
            """, (RECENT_WINDOW_MINUTES, VERY_RECENT_WINDOW_MINUTES))
            
            recent_posts = [row[0] for row in cursor.fetchall()]
            
            # Calculate similarity for recent posts
            new_content = new_tweet.split("\n\n#")[0].lower() if "\n\n#" in new_tweet else new_tweet.lower()
            
            for post in recent_posts:
                post_content = post.split("\n\n#")[0].lower() if "\n\n#" in post else post.lower()
                
                # Calculate a simple similarity score based on word overlap
                new_words = set(new_content.split())
                post_words = set(post_content.split())
                
                if new_words and post_words:
                    overlap = len(new_words.intersection(post_words))
                    similarity = overlap / max(len(new_words), len(post_words))
                    
                    # Apply high similarity threshold for recent posts
                    if similarity > HIGH_SIMILARITY_THRESHOLD:
                        logger.logger.info(f"High similarity ({similarity:.2f}) detected within last {RECENT_WINDOW_MINUTES} minutes")
                        return True
            
            # 3. Also check exact duplicates in last posts from Twitter
            # This prevents double-posting in case of database issues
            for post in last_posts:
                if post.strip() == new_tweet.strip():
                    logger.logger.info("Exact duplicate detected in recent Twitter posts")
                    return True
            
            # If we get here, it's not a duplicate according to our criteria
            logger.logger.info("No duplicates detected with enhanced time-based criteria")
            return False
            
        except Exception as e:
            logger.log_error("Duplicate Check", str(e))
            # If the duplicate check fails, allow the post to be safe
            logger.logger.warning("Duplicate check failed, allowing post to proceed")
            return False
            
    def _login_to_twitter(self) -> bool:
        """Log into Twitter with enhanced verification"""
        try:
            logger.logger.info("Starting Twitter login")
            self.browser.driver.set_page_load_timeout(45)
            self.browser.driver.get('https://twitter.com/login')
            time.sleep(5)

            username_field = WebDriverWait(self.browser.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[autocomplete='username']"))
            )
            username_field.click()
            time.sleep(1)
            username_field.send_keys(self.config.TWITTER_USERNAME)
            time.sleep(2)

            next_button = WebDriverWait(self.browser.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()
            time.sleep(3)

            password_field = WebDriverWait(self.browser.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_field.click()
            time.sleep(1)
            password_field.send_keys(self.config.TWITTER_PASSWORD)
            time.sleep(2)

            login_button = WebDriverWait(self.browser.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            )
            login_button.click()
            time.sleep(10) 

            return self._verify_login()

        except Exception as e:
            logger.log_error("Twitter Login", str(e))
            return False

    def _verify_login(self) -> bool:
        """Verify Twitter login success"""
        try:
            verification_methods = [
                lambda: WebDriverWait(self.browser.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]'))
                ),
                lambda: WebDriverWait(self.browser.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Profile_Link"]'))
                ),
                lambda: any(path in self.browser.driver.current_url 
                          for path in ['home', 'twitter.com/home'])
            ]
            
            for method in verification_methods:
                try:
                    if method():
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.log_error("Login Verification", str(e))
            return False
            
    def _post_analysis(self, tweet_text: str) -> bool:
        """Post analysis to Twitter with robust button handling"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.browser.driver.get('https://twitter.com/compose/tweet')
                time.sleep(3)
                
                text_area = WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
                )
                text_area.click()
                time.sleep(1)
                
                text_parts = tweet_text.split('#')
                text_area.send_keys(text_parts[0])
                time.sleep(1)
                for part in text_parts[1:]:
                    text_area.send_keys(f'#{part}')
                    time.sleep(0.5)
                
                time.sleep(2)

                post_button = None
                button_locators = [
                    (By.CSS_SELECTOR, '[data-testid="tweetButton"]'),
                    (By.XPATH, "//div[@role='button'][contains(., 'Post')]"),
                    (By.XPATH, "//span[text()='Post']")
                ]

                for locator in button_locators:
                    try:
                        post_button = WebDriverWait(self.browser.driver, 5).until(
                            EC.element_to_be_clickable(locator)
                        )
                        if post_button:
                            break
                    except:
                        continue

                if post_button:
                    self.browser.driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                    time.sleep(1)
                    self.browser.driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(5)
                    logger.logger.info("Tweet posted successfully")
                    return True
                else:
                    logger.logger.error("Could not find post button")
                    retry_count += 1
                    time.sleep(2)
                    
            except Exception as e:
                logger.logger.error(f"Tweet posting error, attempt {retry_count + 1}: {str(e)}")
                retry_count += 1
                wait_time = retry_count * 10
                logger.logger.warning(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
        
        logger.log_error("Tweet Creation", "Maximum retries reached")
        return False
        
    def _cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self.browser:
                logger.logger.info("Closing browser...")
                try:
                    self.browser.close_browser()
                    time.sleep(1)
                except Exception as e:
                    logger.logger.warning(f"Error during browser close: {str(e)}")
                    
            if self.config:
                self.config.cleanup()
                
            logger.log_shutdown()
        except Exception as e:
            logger.log_error("Cleanup", str(e))

    def _get_last_posts(self) -> List[str]:
        """Get last 10 posts to check for duplicates"""
        try:
            self.browser.driver.get(f'https://twitter.com/{self.config.TWITTER_USERNAME}')
            time.sleep(3)
            
            posts = WebDriverWait(self.browser.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="tweetText"]'))
            )
            
            return [post.text for post in posts[:10]]
        except Exception as e:
            logger.log_error("Get Last Posts", str(e))
            return []

    def _get_crypto_data(self) -> Optional[Dict[str, Any]]:
        """Fetch crypto data from CoinGecko with retries"""
        try:
            params = {
                **self.config.get_coingecko_params(),
                'ids': ','.join(self.target_chains.values()), 
                'sparkline': True 
            }
            
            data = self.coingecko.get_market_data(params)
            if not data:
                logger.logger.error("Failed to fetch market data from CoinGecko")
                return None
                
            formatted_data = {
                coin['symbol'].upper(): {
                    'current_price': coin['current_price'],
                    'volume': coin['total_volume'],
                    'price_change_percentage_24h': coin['price_change_percentage_24h'],
                    'sparkline': coin.get('sparkline_in_7d', {}).get('price', []),
                    'market_cap': coin['market_cap'],
                    'market_cap_rank': coin['market_cap_rank'],
                    'total_supply': coin.get('total_supply'),
                    'max_supply': coin.get('max_supply'),
                    'circulating_supply': coin.get('circulating_supply'),
                    'ath': coin.get('ath'),
                    'ath_change_percentage': coin.get('ath_change_percentage')
                } for coin in data
            }
            
            # Map to correct symbol if needed (particularly for POL which might return as MATIC)
            symbol_corrections = {'MATIC': 'POL'}
            for old_sym, new_sym in symbol_corrections.items():
                if old_sym in formatted_data and new_sym not in formatted_data:
                    formatted_data[new_sym] = formatted_data[old_sym]
                    logger.logger.debug(f"Mapped {old_sym} data to {new_sym}")
            
            # Log API usage statistics
            stats = self.coingecko.get_request_stats()
            logger.logger.debug(
                f"CoinGecko API stats - Daily requests: {stats['daily_requests']}, "
                f"Failed: {stats['failed_requests']}, Cache size: {stats['cache_size']}"
            )
            
            # Store market data in database
            for chain, chain_data in formatted_data.items():
                self.config.db.store_market_data(chain, chain_data)
            
            # Check if all data was retrieved
            missing_tokens = [token for token in self.reference_tokens if token not in formatted_data]
            if missing_tokens:
                logger.logger.warning(f"Missing data for tokens: {', '.join(missing_tokens)}")
                
                # Try fallback mechanism for missing tokens
                if 'POL' in missing_tokens and 'MATIC' in formatted_data:
                    formatted_data['POL'] = formatted_data['MATIC']
                    missing_tokens.remove('POL')
                    logger.logger.info("Applied fallback for POL using MATIC data")
                
            logger.logger.info(f"Successfully fetched crypto data for {', '.join(formatted_data.keys())}")
            return formatted_data
                
        except Exception as e:
            logger.log_error("CoinGecko API", str(e))
            return None

    def _analyze_volume_trend(self, current_volume: float, historical_data: List[Dict[str, Any]]) -> Tuple[float, str]:
        """
        Analyze volume trend over the window period
        Returns (percentage_change, trend_description)
        """
        if not historical_data:
            return 0.0, "insufficient_data"
            
        try:
            # Calculate average volume excluding the current volume
            historical_volumes = [entry['volume'] for entry in historical_data]
            avg_volume = statistics.mean(historical_volumes) if historical_volumes else current_volume
            
            # Calculate percentage change
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100
            
            # Determine trend
            if volume_change >= self.config.VOLUME_TREND_THRESHOLD:
                trend = "significant_increase"
            elif volume_change <= -self.config.VOLUME_TREND_THRESHOLD:
                trend = "significant_decrease"
            elif volume_change >= 5:  # Smaller but notable increase
                trend = "moderate_increase"
            elif volume_change <= -5:  # Smaller but notable decrease
                trend = "moderate_decrease"
            else:
                trend = "stable"
                
            logger.logger.debug(
                f"Volume trend analysis: {volume_change:.2f}% change from average. "
                f"Current: {current_volume:,.0f}, Avg: {avg_volume:,.0f}, "
                f"Trend: {trend}"
            )
            
            return volume_change, trend
            
        except Exception as e:
            logger.log_error("Volume Trend Analysis", str(e))
            return 0.0, "error"

    def _analyze_smart_money_indicators(self, token: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze potential smart money movements in a token
        Look for unusual volume spikes, price-volume divergence, and accumulation patterns
        """
        try:
            # Get historical data over multiple timeframes
            hourly_data = self._get_historical_volume_data(token, minutes=60)
            daily_data = self._get_historical_volume_data(token, minutes=1440)
            
            current_volume = token_data['volume']
            current_price = token_data['current_price']
            
            # Volume anomaly detection
            hourly_volumes = [entry['volume'] for entry in hourly_data]
            daily_volumes = [entry['volume'] for entry in daily_data]
            
            # Calculate baselines
            avg_hourly_volume = statistics.mean(hourly_volumes) if hourly_volumes else current_volume
            avg_daily_volume = statistics.mean(daily_volumes) if daily_volumes else current_volume
            
            # Volume Z-score (how many standard deviations from mean)
            hourly_std = statistics.stdev(hourly_volumes) if len(hourly_volumes) > 1 else 1
            volume_z_score = (current_volume - avg_hourly_volume) / hourly_std if hourly_std != 0 else 0
            
            # Price-volume divergence
            # (Price going down while volume increasing suggests accumulation)
            price_direction = 1 if token_data['price_change_percentage_24h'] > 0 else -1
            volume_direction = 1 if current_volume > avg_daily_volume else -1
            
            # Divergence detected when price and volume move in opposite directions
            divergence = (price_direction != volume_direction)
            
            # Check for abnormal volume with minimal price movement (potential accumulation)
            stealth_accumulation = (abs(token_data['price_change_percentage_24h']) < 2) and (current_volume > avg_daily_volume * 1.5)
            
            # Calculate volume profile - percentage of volume in each hour
            volume_profile = {}
            if hourly_data:
                for i in range(24):
                    hour_window = datetime.now() - timedelta(hours=i+1)
                    hour_volume = sum(entry['volume'] for entry in hourly_data if hour_window <= entry['timestamp'] <= hour_window + timedelta(hours=1))
                    volume_profile[f"hour_{i+1}"] = hour_volume
            
            # Detect unusual trading hours (potential institutional activity)
            total_volume = sum(volume_profile.values()) if volume_profile else 0
            unusual_hours = []
            
            if total_volume > 0:
                for hour, vol in volume_profile.items():
                    hour_percentage = (vol / total_volume) * 100
                    if hour_percentage > 15:  # More than 15% of daily volume in a single hour
                        unusual_hours.append(hour)
            
            # Detect volume clusters (potential accumulation zones)
            volume_cluster_detected = False
            if len(hourly_volumes) >= 3:
                for i in range(len(hourly_volumes)-2):
                    if all(vol > avg_hourly_volume * 1.3 for vol in hourly_volumes[i:i+3]):
                        volume_cluster_detected = True
                        break
            
            # Results
            return {
                'volume_z_score': volume_z_score,
                'price_volume_divergence': divergence,
                'stealth_accumulation': stealth_accumulation,
                'abnormal_volume': abs(volume_z_score) > self.SMART_MONEY_ZSCORE_THRESHOLD,
                'volume_vs_hourly_avg': (current_volume / avg_hourly_volume) - 1,
                'volume_vs_daily_avg': (current_volume / avg_daily_volume) - 1,
                'unusual_trading_hours': unusual_hours,
                'volume_cluster_detected': volume_cluster_detected
            }
        except Exception as e:
            logger.log_error(f"Smart Money Analysis - {token}", str(e))
            return {}

    def _analyze_token_vs_market(self, token: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze token performance relative to the overall crypto market
        """
        try:
            token_data = market_data.get(token, {})
            if not token_data:
                return {}
                
            # Filter out the token itself from reference tokens to avoid self-comparison
            reference_tokens = [t for t in self.reference_tokens if t != token]
            
            # Compare 24h performance
            market_avg_change = statistics.mean([
                market_data.get(ref_token, {}).get('price_change_percentage_24h', 0) 
                for ref_token in reference_tokens
                if ref_token in market_data
            ])
            
            performance_diff = token_data['price_change_percentage_24h'] - market_avg_change
            
            # Compare volume growth
            market_avg_volume_change = statistics.mean([
                self._analyze_volume_trend(
                    market_data.get(ref_token, {}).get('volume', 0),
                    self._get_historical_volume_data(ref_token)
                )[0]
                for ref_token in reference_tokens
                if ref_token in market_data
            ])
            
            token_volume_change = self._analyze_volume_trend(
                token_data['volume'],
                self._get_historical_volume_data(token)
            )[0]
            
            volume_growth_diff = token_volume_change - market_avg_volume_change
            
            # Calculate correlation with each reference token
            correlations = {}
            for ref_token in reference_tokens:
                if ref_token in market_data:
                    # Simple correlation based on 24h change direction
                    token_direction = 1 if token_data['price_change_percentage_24h'] > 0 else -1
                    ref_token_direction = 1 if market_data[ref_token]['price_change_percentage_24h'] > 0 else -1
                    correlated = token_direction == ref_token_direction
                    
                    correlations[ref_token] = {
                        'correlated': correlated,
                        'token_change': token_data['price_change_percentage_24h'],
                        'ref_token_change': market_data[ref_token]['price_change_percentage_24h']
                    }
            
            # Determine if token is outperforming the market
            outperforming = performance_diff > 0
            
            # Store for any token using the generic method
            self.config.db.store_token_market_comparison(
                token,
                performance_diff,
                volume_growth_diff,
                outperforming,
                correlations
            )
            
            return {
                'vs_market_avg_change': performance_diff,
                'vs_market_volume_growth': volume_growth_diff,
                'correlations': correlations,
                'outperforming_market': outperforming
            }
            
        except Exception as e:
            logger.log_error(f"Token vs Market Analysis - {token}", str(e))
            return {}

    def _calculate_correlations(self, token: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate token correlations with the market"""
        try:
            token_data = market_data.get(token, {})
            if not token_data:
                return {}
                
            # Filter out the token itself from reference tokens to avoid self-comparison
            reference_tokens = [t for t in self.reference_tokens if t != token]
            
            correlations = {}
            
            # Calculate correlation with each reference token
            for ref_token in reference_tokens:
                if ref_token not in market_data:
                    continue
                    
                ref_data = market_data[ref_token]
                
                # Price correlation (simplified)
                price_correlation = abs(
                    token_data['price_change_percentage_24h'] - 
                    ref_data['price_change_percentage_24h']
                ) / max(abs(token_data['price_change_percentage_24h']), 
                       abs(ref_data['price_change_percentage_24h']))
                
                # Volume correlation (simplified)
                volume_correlation = abs(
                    (token_data['volume'] - ref_data['volume']) / 
                    max(token_data['volume'], ref_data['volume'])
                )
                
                correlations[f'price_correlation_{ref_token}'] = 1 - price_correlation
                correlations[f'volume_correlation_{ref_token}'] = 1 - volume_correlation
            
            # Calculate average correlations
            price_correlations = [v for k, v in correlations.items() if 'price_correlation_' in k]
            volume_correlations = [v for k, v in correlations.items() if 'volume_correlation_' in k]
            
            correlations['avg_price_correlation'] = statistics.mean(price_correlations) if price_correlations else 0
            correlations['avg_volume_correlation'] = statistics.mean(volume_correlations) if volume_correlations else 0
            
            # Store correlation data for any token using the generic method
            self.config.db.store_token_correlations(token, correlations)
            
            logger.logger.debug(
                f"{token} correlations calculated - Avg Price: {correlations['avg_price_correlation']:.2f}, "
                f"Avg Volume: {correlations['avg_volume_correlation']:.2f}"
            )
            
            return correlations
            
        except Exception as e:
            logger.log_error(f"Correlation Calculation - {token}", str(e))
            return {
                'avg_price_correlation': 0.0,
                'avg_volume_correlation': 0.0
            }

    def _track_prediction(self, token: str, prediction: Dict[str, Any], relevant_tokens: List[str]) -> None:
        """Track predictions for future spicy callbacks"""
        MAX_PREDICTIONS = 20  
        current_prices = {chain: prediction.get(f'{chain.upper()}_price', 0) for chain in relevant_tokens if f'{chain.upper()}_price' in prediction}
        
        self.past_predictions.append({
            'timestamp': datetime.now(),
            'token': token,
            'prediction': prediction['analysis'],
            'prices': current_prices,
            'sentiment': prediction['sentiment'],
            'outcome': None
        })
        
        # Keep only predictions from the last 24 hours, up to MAX_PREDICTIONS
        self.past_predictions = [p for p in self.past_predictions 
                               if (datetime.now() - p['timestamp']).total_seconds() < 86400]
        
        # Trim to max predictions if needed
        if len(self.past_predictions) > MAX_PREDICTIONS:
            self.past_predictions = self.past_predictions[-MAX_PREDICTIONS:]
            
    def _validate_past_prediction(self, prediction: Dict[str, Any], current_prices: Dict[str, float]) -> str:
        """Check if a past prediction was hilariously wrong"""
        sentiment_map = {
            'bullish': 1,
            'bearish': -1,
            'neutral': 0,
            'volatile': 0,
            'recovering': 0.5
        }
        
        wrong_tokens = []
        for token, old_price in prediction['prices'].items():
            if token in current_prices and old_price > 0:
                price_change = ((current_prices[token] - old_price) / old_price) * 100
                
                # Get sentiment for this token
                token_sentiment_key = token.upper() if token.upper() in prediction['sentiment'] else token
                token_sentiment_value = prediction['sentiment'].get(token_sentiment_key)
                
                # Handle nested dictionary structure
                if isinstance(token_sentiment_value, dict) and 'mood' in token_sentiment_value:
                    token_sentiment = sentiment_map.get(token_sentiment_value['mood'], 0)
                else:
                    token_sentiment = sentiment_map.get(token_sentiment_value, 0)
                
                # A prediction is wrong if:
                # 1. Bullish but price dropped more than 2%
                # 2. Bearish but price rose more than 2%
                if (token_sentiment * price_change) < -2:
                    wrong_tokens.append(token)
        
        return 'wrong' if wrong_tokens else 'right'
        
    def _get_spicy_callback(self, token: str, current_prices: Dict[str, float]) -> Optional[str]:
        """Generate witty callbacks to past terrible predictions"""
        recent_predictions = [p for p in self.past_predictions 
                            if p['timestamp'] > (datetime.now() - timedelta(hours=24))
                            and p['token'] == token]
        
        if not recent_predictions:
            return None
            
        for pred in recent_predictions:
            if pred['outcome'] is None:
                pred['outcome'] = self._validate_past_prediction(pred, current_prices)
                
        wrong_predictions = [p for p in recent_predictions if p['outcome'] == 'wrong']
        if wrong_predictions:
            worst_pred = wrong_predictions[-1]
            time_ago = int((datetime.now() - worst_pred['timestamp']).total_seconds() / 3600)
            
            # If time_ago is 0, set it to 1 to avoid awkward phrasing
            if time_ago == 0:
                time_ago = 1
            
            # Token-specific callbacks
            callbacks = [
                f"(Unlike my galaxy-brain take {time_ago}h ago about {worst_pred['prediction'].split('.')[0]}... this time I'm sure!)",
                f"(Looks like my {time_ago}h old prediction about {token} aged like milk. But trust me bro!)",
                f"(That awkward moment when your {time_ago}h old {token} analysis was completely wrong... but this one's different!)",
                f"(My {token} trading bot would be down bad after that {time_ago}h old take. Good thing I'm just an analyst!)",
                f"(Excuse the {time_ago}h old miss on {token}. Even the best crypto analysts are wrong sometimes... just not usually THIS wrong!)"
            ]
            return callbacks[hash(str(datetime.now())) % len(callbacks)]
            
        return None
        
    def _format_tweet_analysis(self, token: str, analysis: str, crypto_data: Dict[str, Any]) -> str:
        """Format analysis for Twitter with appropriate hashtags"""
        analysis_lower = analysis.lower()
        
        # 1. STATIC HASHTAGS - Always included
        base_hashtags = f"#{token} #CryptoAnalysis #SmartMoney #Crypto"
        
        # Store all additional hashtags
        additional_hashtags = []
        
        # 2. CONDITIONAL HASHTAGS - Based on content analysis
        # Volume and accumulation related
        if 'volume' in analysis_lower or 'accumulation' in analysis_lower:
            additional_hashtags.append("#VolumeAnalysis")
        
        # Market comparison related
        if 'market' in analysis_lower or 'correlation' in analysis_lower:
            additional_hashtags.append("#MarketTrends")
        
        # Price movement related
        if any(term in analysis_lower for term in ['surge', 'pump', 'jump', 'rocket', 'moon', 'soar']):
            additional_hashtags.append("#Momentum")
        elif any(term in analysis_lower for term in ['crash', 'dump', 'plunge', 'drop', 'fall', 'dip']):
            additional_hashtags.append("#CryptoAlert")
        
        # Technical analysis terminology
        if any(term in analysis_lower for term in ['divergence', 'resistance', 'support', 'pattern', 'indicator', 'signal']):
            additional_hashtags.append("#TechnicalAnalysis")
        
        # Market sentiment terminology
        if 'bullish' in analysis_lower:
            additional_hashtags.append("#Bullish")
        elif 'bearish' in analysis_lower:
            additional_hashtags.append("#Bearish")
        
        # Smart money and institutional terminology
        if any(term in analysis_lower for term in ['institution', 'smart money', 'whales', 'big players', 'accumulation']):
            additional_hashtags.append("#InstitutionalMoney")
        
        # Breakout and trend terminology
        if any(term in analysis_lower for term in ['breakout', 'trend', 'reversal', 'consolidation']):
            additional_hashtags.append("#TrendWatch")
            
        # Correlation terminology
        if any(term in analysis_lower for term in ['correlation', 'decoupling', 'coupled']):
            additional_hashtags.append("#MarketCorrelation")
            
        # 3. ROTATING HASHTAG SETS - Change with each post for variety
        rotating_hashtag_sets = [
            "#DeFi #Altcoins #CryptoGems",
            "#CryptoInvestor #AltSeason #CryptoTrends",
            "#CryptoTrader #TradingSignals #MarketMoves",
            "#BlockchainTech #TokenEconomy #CryptoCommunity",
            "#Web3 #NewCrypto #TokenTrends",
            "#TokenInvestor #CryptoAlpha #MarketInsights",
            "#DigitalAssets #CryptoBulls #MarketAlpha",
            "#DeepDive #CryptoResearch #TokenAnalysis"
        ]
        
        # Select a rotating set based on time and trigger
        # Use a hash of the date and token to select which set to use
        hashtag_set_index = hash(f"{datetime.now().strftime('%Y-%m-%d-%H')}-{token}") % len(rotating_hashtag_sets)
        rotating_hashtags = rotating_hashtag_sets[hashtag_set_index]
        
        # 4. MARKET CONDITION-BASED HASHTAGS - Based on actual data
        token_data = crypto_data.get(token, {})
        
        if token_data:
            # Outperformance hashtags
            vs_market = self._analyze_token_vs_market(token, crypto_data)
            if vs_market.get('outperforming_market', False):
                additional_hashtags.append("#Outperforming")
                if vs_market.get('vs_market_avg_change', 0) > 10:  # If outperforming by more than 10%
                    additional_hashtags.append("#MassiveOutperformance")
            
            # Volume-based hashtags
            smart_money = self._analyze_smart_money_indicators(token, token_data)
            if smart_money.get('abnormal_volume', False):
                additional_hashtags.append("#VolumeSpike")
            if smart_money.get('volume_z_score', 0) > 2.5:  # High Z-score
                additional_hashtags.append("#UnusualVolume")
            if smart_money.get('stealth_accumulation', False):
                additional_hashtags.append("#StealthMode")
            
            # Price action hashtags
            price_change = token_data.get('price_change_percentage_24h', 0)
            if price_change > 15:
                additional_hashtags.append("#PriceSurge")
            elif price_change > 5:
                additional_hashtags.append("#PriceAlert")
            elif price_change < -10:
                additional_hashtags.append("#PriceDrop")
                
            # Mood-based hashtags (determine from price change)
            if price_change > 8:
                additional_hashtags.append("#BullMarket")
            elif price_change < -8:
                additional_hashtags.append("#BearMarket")
            elif -3 <= price_change <= 3:
                additional_hashtags.append("#SidewaysMarket")
                
        # Combine all hashtags while respecting Twitter's constraints
        # Start with base hashtags, then add up to 5 additional hashtags
        # Finally add the rotating set if there's room
        
        # First prioritize and deduplicate additional hashtags
        additional_hashtags = list(set(additional_hashtags))  # Remove duplicates
        
        # Prioritize the most important ones (first 5)
        selected_additional = additional_hashtags[:min(5, len(additional_hashtags))]
        
        # Combine hashtags
        all_hashtags = f"{base_hashtags} {' '.join(selected_additional)}"
        
        # Add rotating hashtags if there's space
        if len(all_hashtags) + len(rotating_hashtags) + 1 <= 100:  # Stay under ~100 chars for hashtags
            all_hashtags = f"{all_hashtags} {rotating_hashtags}"
        
        # Construct the final tweet
        tweet = f"{analysis}\n\n{all_hashtags}"
        
        # Make sure to respect Twitter's character limit
        max_length = self.config.TWEET_CONSTRAINTS['HARD_STOP_LENGTH'] - 20
        if len(tweet) > max_length:
            # Trim the analysis part, not the hashtags
            chars_to_trim = len(tweet) - max_length
            trimmed_analysis = analysis[:len(analysis) - chars_to_trim - 3] + "..."
            tweet = f"{trimmed_analysis}\n\n{all_hashtags}"
        
        return tweet

    def _should_post_update(self, token: str, new_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if we should post an update based on market changes
        Returns (should_post, trigger_reason)
        """
        if not self.last_market_data:
            self.last_market_data = new_data
            return True, "initial_post"

        trigger_reason = None

        # Check token for significant changes
        if token in new_data and token in self.last_market_data:
            # Calculate immediate price change since last check
            price_change = abs(
                (new_data[token]['current_price'] - self.last_market_data[token]['current_price']) /
                self.last_market_data[token]['current_price'] * 100
            )
            
            # Calculate immediate volume change since last check
            immediate_volume_change = abs(
                (new_data[token]['volume'] - self.last_market_data[token]['volume']) /
                self.last_market_data[token]['volume'] * 100
            )

            logger.logger.debug(
                f"{token} immediate changes - Price: {price_change:.2f}%, Volume: {immediate_volume_change:.2f}%"
            )

            # Check immediate price change
            if price_change >= self.config.PRICE_CHANGE_THRESHOLD:
                trigger_reason = f"price_change_{token.lower()}"
                logger.logger.info(f"Significant price change detected for {token}: {price_change:.2f}%")
                
            # Check immediate volume change
            elif immediate_volume_change >= self.config.VOLUME_CHANGE_THRESHOLD:
                trigger_reason = f"volume_change_{token.lower()}"
                logger.logger.info(f"Significant immediate volume change detected for {token}: {immediate_volume_change:.2f}%")
                
            # Check rolling window volume trend
            else:
                historical_volume = self._get_historical_volume_data(token)
                if historical_volume:
                    volume_change_pct, trend = self._analyze_volume_trend(
                        new_data[token]['volume'],
                        historical_volume
                    )
                    
                    # Log the volume trend
                    logger.logger.debug(
                        f"{token} rolling window volume trend: {volume_change_pct:.2f}% ({trend})"
                    )
                    
                    # Check if trend is significant enough to trigger
                    if trend in ["significant_increase", "significant_decrease"]:
                        trigger_reason = f"volume_trend_{token.lower()}_{trend}"
                        logger.logger.info(
                            f"Significant volume trend detected for {token}: "
                            f"{volume_change_pct:.2f}% over {self.config.VOLUME_WINDOW_MINUTES} minutes"
                        )
            
            # Check for smart money indicators
            if not trigger_reason:
                smart_money = self._analyze_smart_money_indicators(token, new_data[token])
                if smart_money.get('abnormal_volume') or smart_money.get('stealth_accumulation'):
                    trigger_reason = f"smart_money_{token.lower()}"
                    logger.logger.info(f"Smart money movement detected for {token}")
            
            # Check for significant outperformance vs market
            if not trigger_reason:
                vs_market = self._analyze_token_vs_market(token, new_data)
                if vs_market.get('outperforming_market') and abs(vs_market.get('vs_market_avg_change', 0)) > 5.0:
                    trigger_reason = f"{token.lower()}_outperforming_market"
                    logger.logger.info(f"{token} significantly outperforming market")

        # Check if regular interval has passed
        if not trigger_reason:
            time_since_last = (datetime.now() - self.last_check_time).total_seconds()
            if time_since_last >= self.config.BASE_INTERVAL:
                trigger_reason = "regular_interval"
                logger.logger.debug("Regular interval check triggered")

        should_post = trigger_reason is not None
        if should_post:
            self.last_market_data = new_data
            logger.logger.info(f"Update triggered by: {trigger_reason}")
        else:
            logger.logger.debug("No triggers activated, skipping update")

        return should_post, trigger_reason

    def _analyze_market_sentiment(self, token: str, crypto_data: Dict[str, Any], trigger_type: str) -> Optional[str]:
        """Generate token-specific market analysis with focus on volume and smart money"""
        max_retries = 3
        retry_count = 0
        
        # Define rotating focus areas for more varied analyses
        focus_areas = [
            "Focus on volume patterns, smart money movements, and how the token is performing relative to the broader market.",
            "Emphasize technical indicators showing money flow in the market. Pay special attention to volume-to-price divergence.",
            "Analyze accumulation patterns and capital rotation. Look for subtle signs of institutional interest.",
            "Examine volume preceding price action. Note any leading indicators.",
            "Highlight the relationship between price action and significant volume changes.",
            "Investigate potential smart money positioning ahead of market moves. Note any anomalous volume signatures.",
            "Focus on recent volume clusters and their impact on price stability. Look for divergence patterns.",
            "Analyze volatility profile compared to the broader market and what this suggests about sentiment."
        ]
        
        while retry_count < max_retries:
            try:
                logger.logger.debug(f"Starting {token} market sentiment analysis (attempt {retry_count + 1})")
                
                # Get token data
                token_data = crypto_data.get(token, {})
                if not token_data:
                    logger.log_error("Market Analysis", f"Missing {token} data")
                    return None
                
                # Calculate correlations with market
                correlations = self._calculate_correlations(token, crypto_data)
                
                # Get smart money indicators
                smart_money = self._analyze_smart_money_indicators(token, token_data)
                
                # Get token vs market performance
                vs_market = self._analyze_token_vs_market(token, crypto_data)
                
                # Get spicy callback for previous predictions
                callback = self._get_spicy_callback(token, {sym: data['current_price'] 
                                                   for sym, data in crypto_data.items()})
                
                # Analyze mood
                indicators = MoodIndicators(
                    price_change=token_data['price_change_percentage_24h'],
                    trading_volume=token_data['volume'],
                    volatility=abs(token_data['price_change_percentage_24h']) / 100,
                    social_sentiment=None,
                    funding_rates=None,
                    liquidation_volume=None
                )
                
                mood = determine_advanced_mood(indicators)
                token_mood = {
                    'mood': mood.value,
                    'change': token_data['price_change_percentage_24h'],
                    'ath_distance': token_data['ath_change_percentage']
                }
                
                # Store mood data
                self.config.db.store_mood(token, mood.value, indicators)
                
                # Generate meme phrase - use the generic method for all tokens
                meme_context = MemePhraseGenerator.generate_meme_phrase(
                    chain=token,
                    mood=Mood(mood.value)
                )
                
                # Get volume trend for additional context
                historical_volume = self._get_historical_volume_data(token)
                if historical_volume:
                    volume_change_pct, trend = self._analyze_volume_trend(
                        token_data['volume'],
                        historical_volume
                    )
                    volume_trend = {
                        'change_pct': volume_change_pct,
                        'trend': trend
                    }
                else:
                    volume_trend = {'change_pct': 0, 'trend': 'stable'}

                # Get historical context from database
                stats = self.config.db.get_chain_stats(token, hours=24)
                if stats:
                    historical_context = f"24h Avg: ${stats['avg_price']:,.2f}, "
                    historical_context += f"High: ${stats['max_price']:,.2f}, "
                    historical_context += f"Low: ${stats['min_price']:,.2f}"
                else:
                    historical_context = "No historical data"
                
                # Check if this is a volume trend trigger
                volume_context = ""
                if "volume_trend" in trigger_type:
                    change = volume_trend['change_pct']
                    direction = "increase" if change > 0 else "decrease"
                    volume_context = f"\nVolume Analysis:\n{token} showing {abs(change):.1f}% {direction} in volume over last hour. This is a significant {volume_trend['trend']}."

                # Smart money context
                smart_money_context = ""
                if smart_money.get('abnormal_volume'):
                    smart_money_context += f"\nAbnormal volume detected: {smart_money['volume_z_score']:.1f} standard deviations from mean."
                if smart_money.get('stealth_accumulation'):
                    smart_money_context += f"\nPotential stealth accumulation detected with minimal price movement and elevated volume."
                if smart_money.get('volume_cluster_detected'):
                    smart_money_context += f"\nVolume clustering detected, suggesting possible institutional activity."
                if smart_money.get('unusual_trading_hours'):
                    smart_money_context += f"\nUnusual trading hours detected: {', '.join(smart_money['unusual_trading_hours'])}."

                # Market comparison context
                market_context = ""
                if vs_market.get('outperforming_market'):
                    market_context += f"\n{token} outperforming market average by {vs_market['vs_market_avg_change']:.1f}%"
                else:
                    market_context += f"\n{token} underperforming market average by {abs(vs_market['vs_market_avg_change']):.1f}%"
                
                # Market volume flow technical analysis
                reference_tokens = [t for t in self.reference_tokens if t != token and t in crypto_data]
                market_total_volume = sum([data['volume'] for sym, data in crypto_data.items() if sym in reference_tokens])
                market_volume_ratio = (token_data['volume'] / market_total_volume * 100) if market_total_volume > 0 else 0
                
                capital_rotation = "Yes" if vs_market.get('outperforming_market', False) and smart_money.get('volume_vs_daily_avg', 0) > 0.2 else "No"
                
                selling_pattern = "Detected" if vs_market.get('vs_market_volume_growth', 0) < 0 and volume_trend['change_pct'] > 5 else "Not detected"
                
                # Find top 2 correlated tokens
                price_correlations = {k.replace('price_correlation_', ''): v 
                                     for k, v in correlations.items() 
                                     if k.startswith('price_correlation_')}
                top_correlated = sorted(price_correlations.items(), key=lambda x: x[1], reverse=True)[:2]
                
                technical_context = f"""
Market Flow Analysis:
- {token}/Market volume ratio: {market_volume_ratio:.2f}%
- Potential capital rotation: {capital_rotation}
- Market selling {token} buying patterns: {selling_pattern}
"""
                if top_correlated:
                    technical_context += "- Highest correlations: "
                    for corr_token, corr_value in top_correlated:
                        technical_context += f"{corr_token}: {corr_value:.2f}, "
                    technical_context = technical_context.rstrip(", ")

                # Select a focus area using a deterministic but varied approach
                # Use a combination of date, hour, token and trigger type to ensure variety
                focus_seed = f"{datetime.now().date()}_{datetime.now().hour}_{token}_{trigger_type}"
                focus_index = hash(focus_seed) % len(focus_areas)
                selected_focus = focus_areas[focus_index]

                prompt = f"""Write a witty market analysis focusing on {token} token with attention to volume changes and smart money movements. Format as a single paragraph. Market data:
                
                {token} Performance:
                - Price: ${token_data['current_price']:,.4f}
                - 24h Change: {token_mood['change']:.1f}% ({token_mood['mood']})
                - Volume: ${token_data['volume']:,.0f}
                
                Historical Context:
                - {token}: {historical_context}
                
                Volume Analysis:
                - 24h trend: {volume_trend['change_pct']:.1f}% over last hour ({volume_trend['trend']})
                - vs hourly avg: {smart_money.get('volume_vs_hourly_avg', 0)*100:.1f}%
                - vs daily avg: {smart_money.get('volume_vs_daily_avg', 0)*100:.1f}%
                {volume_context}
                
                Smart Money Indicators:
                - Volume Z-score: {smart_money.get('volume_z_score', 0):.2f}
                - Price-Volume Divergence: {smart_money.get('price_volume_divergence', False)}
                - Stealth Accumulation: {smart_money.get('stealth_accumulation', False)}
                - Abnormal Volume: {smart_money.get('abnormal_volume', False)}
                - Volume Clustering: {smart_money.get('volume_cluster_detected', False)}
                {smart_money_context}
                
                Market Comparison:
                - vs Market avg change: {vs_market.get('vs_market_avg_change', 0):.1f}%
                - vs Market volume growth: {vs_market.get('vs_market_volume_growth', 0):.1f}%
                - Outperforming Market: {vs_market.get('outperforming_market', False)}
                {market_context}
                
                ATH Distance:
                - {token}: {token_mood['ath_distance']:.1f}%
                
                {technical_context}
                
                Token-specific context:
                - Meme: {meme_context}
                
                Trigger Type: {trigger_type}
                
                Past Context: {callback if callback else 'None'}
                
                Note: {selected_focus} Keep the analysis fresh and varied. Avoid repetitive phrases."""
                
                logger.logger.debug("Sending analysis request to Claude")
                response = self.claude_client.messages.create(
                    model=self.config.CLAUDE_MODEL,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                analysis = response.content[0].text
                logger.logger.debug("Received analysis from Claude")
                
                # Store prediction data
                prediction_data = {
                    'analysis': analysis,
                    'sentiment': {token: token_mood['mood']},
                    **{f"{sym.upper()}_price": data['current_price'] for sym, data in crypto_data.items()}
                }
                self._track_prediction(token, prediction_data, [token])
                
                formatted_tweet = self._format_tweet_analysis(token, analysis, crypto_data)
                
                # Use the improved duplicate detection 
                skip_similarity_check = False
                
                # Store the content (always store for data collection)
                self.config.db.store_posted_content(
                    content=formatted_tweet,
                    sentiment={token: token_mood},
                    trigger_type=trigger_type,
                    price_data={token: {'price': token_data['current_price'], 
                                      'volume': token_data['volume']}},
                    meme_phrases={token: meme_context}
                )
                
                return formatted_tweet
                
            except Exception as e:
                retry_count += 1
                wait_time = retry_count * 10
                logger.logger.error(f"Analysis error details: {str(e)}", exc_info=True)
                logger.logger.warning(f"Analysis error, attempt {retry_count}, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
        
        logger.log_error("Market Analysis", "Maximum retries reached")
        return None

    def _run_analysis_cycle(self) -> None:
        """Run analysis and posting cycle for all tokens"""
        try:
            market_data = self._get_crypto_data()
            if not market_data:
                logger.logger.error("Failed to fetch market data")
                return
                
            # Get available tokens and shuffle them to try in random order
            available_tokens = [token for token in self.reference_tokens if token in market_data]
            if not available_tokens:
                logger.logger.error("No token data available")
                return
                
            # Shuffle the tokens to prevent always analyzing the same ones first
            import random
            random.shuffle(available_tokens)
            
            # Try each token until we find one that's not a duplicate
            for token_to_analyze in available_tokens:
                should_post, trigger_type = self._should_post_update(token_to_analyze, market_data)
                
                if should_post:
                    logger.logger.info(f"Starting {token_to_analyze} analysis cycle - Trigger: {trigger_type}")
                    analysis = self._analyze_market_sentiment(token_to_analyze, market_data, trigger_type)
                    if not analysis:
                        logger.logger.error(f"Failed to generate {token_to_analyze} analysis")
                        continue  # Try next token instead of returning
                        
                    last_posts = self._get_last_posts()
                    if not self._is_duplicate_analysis(analysis, last_posts):
                        if self._post_analysis(analysis):
                            logger.logger.info(f"Successfully posted {token_to_analyze} analysis - Trigger: {trigger_type}")
                            
                            # Store additional smart money metrics
                            if token_to_analyze in market_data:
                                smart_money = self._analyze_smart_money_indicators(token_to_analyze, market_data[token_to_analyze])
                                self.config.db.store_smart_money_indicators(token_to_analyze, smart_money)
                                
                                # Log smart money indicators
                                logger.logger.debug(f"Smart money indicators stored for {token_to_analyze}: {smart_money}")
                                
                                # Store market comparison data
                                vs_market = self._analyze_token_vs_market(token_to_analyze, market_data)
                                if vs_market:
                                    # Store for any token using generic method
                                    self.config.db.store_token_market_comparison(
                                        token_to_analyze,
                                        vs_market.get('vs_market_avg_change', 0),
                                        vs_market.get('vs_market_volume_growth', 0),
                                        vs_market.get('outperforming_market', False),
                                        vs_market.get('correlations', {})
                                    )
                                    
                                    logger.logger.debug(f"{token_to_analyze} vs Market comparison stored")
                            
                            # Successfully posted, so we're done with this cycle
                            return
                        else:
                            logger.logger.error(f"Failed to post {token_to_analyze} analysis")
                            continue  # Try next token
                    else:
                        logger.logger.info(f"Skipping duplicate {token_to_analyze} analysis - trying another token")
                        continue  # Try next token
                else:
                    logger.logger.debug(f"No significant {token_to_analyze} changes detected, trying another token")
            
            # If we get here, we tried all tokens but couldn't post anything
            logger.logger.warning("Tried all available tokens but couldn't post any analysis")
                
        except Exception as e:
            logger.log_error("Token Analysis Cycle", str(e))

    def start(self) -> None:
        """Main bot execution loop"""
        try:
            retry_count = 0
            max_setup_retries = 3
            
            while retry_count < max_setup_retries:
                if not self.browser.initialize_driver():
                    retry_count += 1
                    logger.logger.warning(f"Browser initialization attempt {retry_count} failed, retrying...")
                    time.sleep(10)
                    continue
                    
                if not self._login_to_twitter():
                    retry_count += 1
                    logger.logger.warning(f"Twitter login attempt {retry_count} failed, retrying...")
                    time.sleep(15)
                    continue
                    
                break
            
            if retry_count >= max_setup_retries:
                raise Exception("Failed to initialize bot after maximum retries")

            logger.logger.info("Bot initialized successfully")

            while True:
                try:
                    self._run_analysis_cycle()
                    
                    # Calculate sleep time until next regular check
                    time_since_last = (datetime.now() - self.last_check_time).total_seconds()
                    sleep_time = max(0, self.config.BASE_INTERVAL - time_since_last)
                    
                    logger.logger.debug(f"Sleeping for {sleep_time:.1f}s until next check")
                    time.sleep(sleep_time)
                    
                    self.last_check_time = datetime.now()
                    
                except Exception as e:
                    logger.log_error("Analysis Cycle", str(e), exc_info=True)
                    time.sleep(60)  # Shorter sleep on error
                    continue

        except KeyboardInterrupt:
            logger.logger.info("Bot stopped by user")
        except Exception as e:
            logger.log_error("Bot Execution", str(e))
        finally:
            self._cleanup()


if __name__ == "__main__":
    try:
        bot = CryptoAnalysisBot()
        bot.start()
    except Exception as e:
        logger.log_error("Bot Startup", str(e))
