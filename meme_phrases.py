# meme_phrases.py
# Contains meme phrases for crypto market analysis

from enum import Enum
from typing import Dict, List, Optional, Any

# Generic crypto meme phrases
MEME_PHRASES = {
    'bullish': [
        "Going to the moon!",
        "Diamond hands activated!",
        "Bears getting rekt!",
        "Pump it up!",
        "Green candles incoming!"
    ],
    'bearish': [
        "This is fine. (It's not fine)",
        "Bear market things",
        "Buying the dip... again",
        "Pain.",
        "Liquidation cascade incoming"
    ],
    'neutral': [
        "Boring market is boring",
        "Crab market continues",
        "Sideways action forever",
        "Waiting for volatility",
        "Consolidation phase"
    ],
    'volatile': [
        "Hold onto your hats!",
        "Traders' nightmare",
        "Epic volatility",
        "Rollercoaster mode activated",
        "Chop city"
    ],
    'recovering': [
        "Finding a bottom",
        "Green shoots appearing",
        "Relief rally time",
        "Bottom fishers rewarded",
        "Comeback season"
    ]
}

# Token-specific meme phrases templates
# {token} will be replaced with the actual token name
TOKEN_MEME_PHRASES = {
    'bullish': [
        "{token} taking off like a rocket!",
        "{token} bulls feasting today!",
        "Smart money loading up on {token}!",
        "{token} showing massive strength!",
        "{token} breaking through resistance like it's nothing!",
        "{token} whales accumulating hard!",
        "Imagine not having {token} in your portfolio right now!",
        "{token} outperforming everything in sight!"
    ],
    'bearish': [
        "{token} taking a breather after its epic run",
        "{token} discount sale! Everything must go!",
        "{token} testing HODLer conviction",
        "Paper hands shaking out of {token}",
        "{token} hitting support levels - time to buy?",
        "Weak hands folding on {token}",
        "{token} whales creating liquidity for a bigger move",
        "{token} bear trap in progress"
    ],
    'neutral': [
        "{token} accumulation phase in progress",
        "{token} coiling for the next big move",
        "Smart money quietly accumulating {token}",
        "{token} volume drying up - calm before the storm?",
        "{token} trading in a tight range",
        "{token} consolidating after recent volatility",
        "Patience is key with {token} right now",
        "{token} building a solid base"
    ],
    'volatile': [
        "{token} going absolutely crazy right now!",
        "{token} shorts and longs getting liquidated!",
        "{token} volatility through the roof!",
        "{token} making traders dizzy with these swings!",
        "{token} showing peak volatility!",
        "{token} traders need motion sickness pills!",
        "{token} chart looking like an EKG!",
        "{token} bouncing around like a pinball!"
    ],
    'recovering': [
        "{token} showing signs of life!",
        "{token} recovery phase initiated!",
        "{token} bouncing back from the lows!",
        "{token} refusing to stay down!",
        "{token} resilience on display!",
        "{token} finding its footing after the dip!",
        "{token}'s recovery catching everyone by surprise!",
        "Dip buyers saving {token}!"
    ],
    'smart_money': [
        "Unusual {token} volume detected - someone knows something",
        "{token} smart money flow indicator flashing!",
        "Institutional accumulation pattern on {token}",
        "{token} showing classic smart money footprints",
        "Whale alert on {token} - big money moving in",
        "{token} showing textbook accumulation patterns",
        "Smart money divergence on {token}",
        "{token} order flow showing hidden accumulation"
    ]
}

# Volume-specific phrase templates
VOLUME_PHRASES = {
    'significant_increase': [
        "{token} volume exploding! Something big brewing?",
        "Massive {token} volume spike detected!",
        "{token} volume through the roof - institutions loading up?",
        "Unprecedented {token} volume surge!",
        "{token} trading volume on steroids today!"
    ],
    'moderate_increase': [
        "{token} volume picking up steam",
        "Growing interest in {token} with rising volumes",
        "{token} volume ticking up - early sign of momentum?",
        "Steady increase in {token} trading activity",
        "{token} volume starting to build"
    ],
    'significant_decrease': [
        "{token} volume falling off a cliff",
        "{token} interest waning with plummeting volume",
        "{token} volume disappearing - traders moving elsewhere?",
        "Major drop in {token} trading activity",
        "{token} volume drought intensifying"
    ],
    'moderate_decrease': [
        "{token} volume cooling off slightly",
        "Modest decline in {token} trading interest",
        "{token} volume easing back to normal levels",
        "Traders taking a break from {token} action",
        "{token} volume tapering down"
    ],
    'stable': [
        "{token} volume staying consistent",
        "Steady as she goes for {token} volume",
        "{token} trading at normal volume levels",
        "No major changes in {token} trading activity",
        "{token} volume in equilibrium"
    ]
}

# Market comparison phrases
MARKET_COMPARISON_PHRASES = {
    'outperforming': [
        "{token} leaving the market in the dust!",
        "{token} outshining major crypto assets today!",
        "{token} flexing on the market!",
        "{token} showing the market how it's done!",
        "Market can't keep up with {token}'s pace!"
    ],
    'underperforming': [
        "{token} lagging behind market momentum",
        "{token} struggling while market pumps",
        "{token} needs to catch up to market performance",
        "Market strength overshadowing {token} today",
        "{token} taking a backseat to market gains"
    ],
    'correlated': [
        "{token} moving in lockstep with the market",
        "{token} and market correlation strengthening",
        "{token} riding the market wave",
        "Strong {token}-market correlation today",
        "{token} mirroring market price action"
    ],
    'diverging': [
        "{token} breaking away from market correlation",
        "{token} charting its own path away from the market",
        "{token}-market correlation weakening",
        "{token} and market going separate ways",
        "{token} decoupling from market price action"
    ]
}

# Smart money indicator phrases
SMART_MONEY_PHRASES = {
    'accumulation': [
        "Classic accumulation pattern forming on {token}",
        "Smart money quietly accumulating {token}",
        "Institutional accumulation detected on {token}",
        "Stealth accumulation phase underway for {token}",
        "Wyckoff accumulation signals on {token} chart"
    ],
    'distribution': [
        "Distribution pattern emerging on {token}",
        "Smart money distribution phase for {token}",
        "Institutional selling pressure on {token}",
        "{token} showing classic distribution signals",
        "Wyckoff distribution pattern on {token}"
    ],
    'divergence': [
        "Price-volume divergence on {token} - smart money move?",
        "{token} showing bullish divergence patterns",
        "Hidden divergence on {token} volume profile",
        "Smart money divergence signals flashing on {token}",
        "Institutional divergence pattern on {token}"
    ],
    'abnormal_volume': [
        "Highly unusual volume pattern on {token}",
        "Abnormal {token} trading activity detected",
        "{token} volume anomaly spotted - insider action?",
        "Strange {token} volume signature today",
        "Statistically significant volume anomaly on {token}"
    ]
}

# MemePhraseGenerator class for use with mood_config
class MemePhraseGenerator:
    """
    Generator for meme phrases based on context
    Provides a consistent way to generate meme phrases for any token
    """
    
    @staticmethod
    def generate_meme_phrase(chain: str, mood: Any, additional_context: Dict[str, Any] = None) -> str:
        """
        Generate a meme phrase for a specific chain and mood
        
        Args:
            chain: Token/chain symbol (e.g., 'BTC', 'ETH')
            mood: Mood object or string representing mood
            additional_context: Additional context for more specific phrases
            
        Returns:
            Generated meme phrase
        """
        # Extract mood value from object if needed
        mood_str = mood.value if hasattr(mood, 'value') else str(mood)
        
        # Special context handling
        if additional_context:
            if 'volume_trend' in additional_context:
                return get_token_meme_phrase(chain, 'volume', additional_context['volume_trend'])
            if 'market_comparison' in additional_context:
                return get_token_meme_phrase(chain, 'market_comparison', additional_context['market_comparison'])
            if 'smart_money' in additional_context:
                return get_token_meme_phrase(chain, 'smart_money', additional_context['smart_money'])
        
        # Default to mood-based phrase
        return get_token_meme_phrase(chain, 'mood', mood_str)


### LEGACY COMPATIBILITY SECTION ###
# These variables and functions are maintained for backward compatibility only

# For backward compatibility - KAITO-specific phrases
# Note: These are just pre-formatted versions of the token phrases with KAITO inserted
KAITO_MEME_PHRASES = {mood: [phrase.replace("{token}", "KAITO") for phrase in phrases] 
                     for mood, phrases in TOKEN_MEME_PHRASES.items()}

KAITO_VOLUME_PHRASES = {context: [phrase.replace("{token}", "KAITO") for phrase in phrases] 
                       for context, phrases in VOLUME_PHRASES.items()}

KAITO_VS_L1_PHRASES = {
    'outperforming': [phrase.replace("{token}", "KAITO").replace("the market", "Layer 1s") for phrase in MARKET_COMPARISON_PHRASES['outperforming']],
    'underperforming': [phrase.replace("{token}", "KAITO").replace("market", "Layer 1") for phrase in MARKET_COMPARISON_PHRASES['underperforming']],
    'correlated': [phrase.replace("{token}", "KAITO").replace("market", "Layer 1") for phrase in MARKET_COMPARISON_PHRASES['correlated']],
    'diverging': [phrase.replace("{token}", "KAITO").replace("market", "Layer 1") for phrase in MARKET_COMPARISON_PHRASES['diverging']]
}

# Get random meme phrase based on context and token
def get_token_meme_phrase(token: str, context: str, subcontext: Optional[str] = None) -> str:
    """
    Get a random token-specific meme phrase based on context
    
    Args:
        token: Token symbol or name
        context: Main context (mood, volume, market_comparison, smart_money)
        subcontext: Sub-context for more specific phrases
        
    Returns:
        Random meme phrase for the given token and context
    """
    import random
    
    # Select appropriate phrase dictionary
    if context == 'mood':
        if subcontext and subcontext in TOKEN_MEME_PHRASES:
            phrases = TOKEN_MEME_PHRASES[subcontext]
        else:
            phrases = TOKEN_MEME_PHRASES['neutral']
    elif context == 'volume':
        if subcontext and subcontext in VOLUME_PHRASES:
            phrases = VOLUME_PHRASES[subcontext]
        else:
            phrases = VOLUME_PHRASES['stable']
    elif context == 'market_comparison':
        if subcontext and subcontext in MARKET_COMPARISON_PHRASES:
            phrases = MARKET_COMPARISON_PHRASES[subcontext]
        else:
            phrases = MARKET_COMPARISON_PHRASES['correlated']
    elif context == 'smart_money':
        if subcontext and subcontext in SMART_MONEY_PHRASES:
            phrases = SMART_MONEY_PHRASES[subcontext]
        else:
            phrases = SMART_MONEY_PHRASES['accumulation']
    else:
        # Default to general TOKEN bullish phrases
        phrases = TOKEN_MEME_PHRASES['bullish']
    
    # Choose a random phrase and format it with the token name
    phrase = random.choice(phrases)
    return phrase.format(token=token)

# For backward compatibility - KAITO-specific function
def get_kaito_meme_phrase(context: str, subcontext: Optional[str] = None) -> str:
    """
    Get a random KAITO meme phrase based on context (for backward compatibility)
    
    Args:
        context: Main context (mood, volume, l1_comparison, smart_money)
        subcontext: Sub-context for more specific phrases
        
    Returns:
        Random meme phrase for KAITO
    """
    return get_token_meme_phrase("KAITO", context, subcontext)
