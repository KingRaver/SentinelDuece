# Project Structure

This document outlines the directory structure of the project, a Python-based cryptocurrency analysis and tracking system.

```
sentinelduece/
├── .env                        # Environment variables configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
├── __init__.py                 # Makes the directory a Python package
├── architecture.txt            # System architecture description
├── get-pip.py                  # Python package installer script
├── login_page_debug.png        # Debug screenshot for login interface
├── requirements.txt            # Python dependencies
│
├── data/                       # Data storage directory
│   ├── crypto_history.db       # SQLite database for crypto history
│   └── backup/                 # Database backups
│       └── crypto_history.db.bak # Backup of the database
│
├── logs/                       # Logging directory
│   ├── ETHBTCCorrelation.log   # Ethereum-Bitcoin correlation logs
│   ├── analysis/               # Analysis-specific logs
│   │   └── market_analysis.log # Market analysis logs
│   ├── claude.log              # Claude AI integration logs
│   ├── claude_api.log          # Claude API interaction logs
│   ├── clogs.log               # General application logs
│   ├── coingecko.log           # CoinGecko data logs
│   ├── coingecko_api.log       # CoinGecko API interaction logs
│   ├── eth_btc_correlation.log # ETH-BTC correlation analysis logs
│   └── google_sheets_api.log   # Google Sheets API interaction logs
│
└── src/                        # Source code directory
    ├── __init__.py             # Makes the directory a Python package
    ├── __pycache__/            # Python bytecode cache
    ├── bot.py                  # Main bot implementation
    ├── coingecko_handler.py    # CoinGecko API handler
    ├── config.py               # Configuration settings
    ├── config.pyc              # Compiled Python file
    ├── database.py             # Database interaction module
    ├── meme_phrases.py         # Meme phrases for bot responses
    ├── mood_config.py          # Configuration for mood analysis
    │
    └── utils/                  # Utility modules
        ├── __init__.py         # Makes the directory a Python package
        ├── __init__.pyc        # Compiled Python file
        ├── __pycache__/        # Python bytecode cache
        ├── browser.py          # Web browser automation utilities
        ├── browser.pyc         # Compiled Python file
        ├── logger.py           # Logging utilities
        ├── logger.pyc          # Compiled Python file
        └── sheets_handler.py   # Google Sheets integration
```

## Key Components

- **Data Storage**: SQLite database for storing cryptocurrency historical data
- **API Integrations**: CoinGecko API for cryptocurrency data, Google Sheets API for data export
- **Logging System**: Comprehensive logging for different components including market analysis
- **Browser Automation**: Utilities for browser-based operations
- **Configuration**: Environment variables and configuration files for system setup

## Development

To set up this project locally:

1. Clone the repository
2. Create a virtual environment
3. Install dependencies with `pip install -r requirements.txt`
4. Configure the `.env` file with your API keys and settings
5. Run the main bot application with `python src/bot.py`
