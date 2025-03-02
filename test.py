#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import json
from datetime import datetime, timedelta
import tempfile
import sqlite3

# Add project source directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import modules to test
from coingecko_handler import CoinGeckoHandler
from config import config
from database import CryptoDatabase
from mood_config import determine_advanced_mood, MoodIndicators, Mood
from meme_phrases import MemePhraseGenerator

class TestCoinGeckoHandler(unittest.TestCase):
    """Test suite for CoinGecko API Handler"""
    
    def setUp(self):
        """Initialize CoinGecko handler before each test"""
        self.coingecko = CoinGeckoHandler(
            base_url=config.COINGECKO_BASE_URL,
            cache_duration=60
        )
    
    def test_market_data_retrieval(self):
        """Test retrieving market data"""
        params = config.get_coingecko_params()
        data = self.coingecko.get_market_data(params)
        
        self.assertIsNotNone(data, "Market data retrieval failed")
        self.assertTrue(len(data) > 0, "No market data returned")
        
        # Check first token has expected keys
        first_token = data[0]
        expected_keys = [
            'id', 'symbol', 'name', 'current_price', 'market_cap', 
            'market_cap_rank', 'total_volume', 'price_change_percentage_24h'
        ]
        for key in expected_keys:
            self.assertIn(key, first_token, f"Missing {key} in market data")
    
    def test_token_id_lookup(self):
        """Test token ID lookup functionality"""
        test_symbols = ['BTC', 'ETH', 'SOL', 'POL']
        token_ids = self.coingecko.get_multiple_tokens_by_symbol(test_symbols)
        
        self.assertEqual(len(token_ids), len(test_symbols), "Token ID lookup failed")
        
        # Check specific mappings
        expected_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'SOL': 'solana',
            'POL': 'matic-network'
        }
        
        for symbol, expected_id in expected_ids.items():
            self.assertEqual(
                token_ids[symbol], 
                expected_id, 
                f"Incorrect ID for {symbol}"
            )

class TestCryptoDatabase(unittest.TestCase):
    """Test suite for Cryptocurrency Database"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        # Use a temporary file for test database
        self.test_db_path = tempfile.mktemp()
        self.db = CryptoDatabase(self.test_db_path)
    
    def tearDown(self):
        """Close and remove temporary database"""
        self.db.close()
        try:
            os.unlink(self.test_db_path)
        except:
            pass
    
    def test_market_data_storage(self):
        """Test storing and retrieving market data"""
        test_data = {
            'current_price': 50000.0,
            'volume': 1000000000,
            'price_change_percentage_24h': 5.5,
            'market_cap': 1000000000000,
            'ath': 69000.0,
            'ath_change_percentage': -10.0
        }
        
        # Store market data
        self.db.store_market_data('BTC', test_data)
        
        # Retrieve recent market data
        recent_data = self.db.get_recent_market_data('BTC', hours=1)
        
        self.assertTrue(len(recent_data) > 0, "No market data retrieved")
        stored_entry = recent_data[0]
        
        # Verify stored values
        self.assertAlmostEqual(
            stored_entry['price'], 
            test_data['current_price'], 
            msg="Price not stored correctly"
        )
        self.assertAlmostEqual(
            stored_entry['volume'], 
            test_data['volume'], 
            msg="Volume not stored correctly"
        )

class TestMoodAnalysis(unittest.TestCase):
    """Test suite for Market Mood Analysis"""
    
    def test_mood_determination(self):
        """Test advanced mood determination logic"""
        test_scenarios = [
            # Bullish Scenario
            {
                'indicators': MoodIndicators(
                    price_change=8.0,
                    trading_volume=2e9,
                    volatility=0.05,
                    social_sentiment=0.8
                ),
                'expected_mood': Mood.BULLISH
            },
            # Bearish Scenario
            {
                'indicators': MoodIndicators(
                    price_change=-6.0,
                    trading_volume=1.5e9,
                    volatility=0.07,
                    social_sentiment=0.2
                ),
                'expected_mood': Mood.BEARISH
            },
            # Neutral Scenario
            {
                'indicators': MoodIndicators(
                    price_change=1.5,
                    trading_volume=500e6,
                    volatility=0.02,
                    social_sentiment=0.5
                ),
                'expected_mood': Mood.NEUTRAL
            }
        ]
        
        for scenario in test_scenarios:
            mood = determine_advanced_mood(scenario['indicators'])
            self.assertEqual(
                mood, 
                scenario['expected_mood'], 
                f"Incorrect mood for scenario: {scenario}"
            )

class TestMemePhraseGeneration(unittest.TestCase):
    """Test suite for Meme Phrase Generation"""
    
    def test_meme_phrase_generation(self):
        """Test meme phrase generation for different tokens and moods"""
        test_cases = [
            {'chain': 'BTC', 'mood': Mood.BULLISH},
            {'chain': 'ETH', 'mood': Mood.BEARISH},
            {'chain': 'SOL', 'mood': Mood.NEUTRAL},
            {'chain': 'POL', 'mood': Mood.VOLATILE}
        ]
        
        for case in test_cases:
            phrase = MemePhraseGenerator.generate_meme_phrase(
                case['chain'], 
                case['mood']
            )
            
            # Verify phrase generation
            self.assertIsNotNone(phrase, "Meme phrase generation failed")
            self.assertTrue(len(phrase) > 0, "Generated phrase is empty")
            self.assertTrue(case['chain'] in phrase, "Chain name not in phrase")

class TestConfigurationConsistency(unittest.TestCase):
    """Test configuration consistency"""
    
    def test_coingecko_params(self):
        """Verify CoinGecko parameters are consistent"""
        params = config.get_coingecko_params()
        
        # Check required keys
        required_keys = [
            'vs_currency', 'ids', 'order', 
            'per_page', 'page', 'sparkline'
        ]
        for key in required_keys:
            self.assertIn(key, params, f"Missing {key} in CoinGecko params")
        
        # Verify tokens are consistent
        tokens = params['ids'].split(',')
        self.assertTrue(len(tokens) > 0, "No tokens specified in CoinGecko params")
        
        # Check tracked crypto matches params
        tracked_tokens = list(config.TRACKED_CRYPTO.keys())
        for token in tracked_tokens:
            self.assertIn(token, params['ids'], f"{token} not in CoinGecko params")

def run_tests():
    """Run all tests and generate a report"""
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_cases = [
        TestCoinGeckoHandler,
        TestCryptoDatabase,
        TestMoodAnalysis,
        TestMemePhraseGeneration,
        TestConfigurationConsistency
    ]
    
    for case in test_cases:
        test_suite.addTests(unittest.makeSuite(case))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate test report
    report = {
        'total_tests': result.testsRun,
        'errors': len(result.errors),
        'failures': len(result.failures),
        'skipped': len(result.skipped),
        'success_rate': (result.testsRun - len(result.errors) - len(result.failures)) / result.testsRun * 100
    }
    
    # Save report to file
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return result

if __name__ == '__main__':
    # Allow running tests directly or importing for use
    result = run_tests()
    sys.exit(not result.wasSuccessful())
