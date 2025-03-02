# 🛠 SentinelDuece Project Configuration Guide

## 📋 Configuration Overview

The SentinelDuece Crypto Analysis Agent uses a flexible configuration system that allows customization through environment variables and configuration files.

## 🔑 Configuration Sources

1. **Environment Variables** (`.env` file)
2. **Configuration Modules** (`src/config.py`)
3. **Runtime Parameters**

## 📊 Configuration Categories

### 1. API Integrations

#### Claude AI Configuration
- `CLAUDE_API_KEY`: Authentication key for Claude AI
- `CLAUDE_MODEL`: Specific Claude model version
  - Default: `claude-3-5-sonnet-20241022`
  - Options: Depends on Anthropic's current model offerings

#### Twitter Configuration
- `TWITTER_USERNAME`: Twitter account username
- `TWITTER_PASSWORD`: Twitter account password
- **Security Note**: Use app-specific passwords when possible

#### CoinGecko API
- `COINGECKO_BASE_URL`: Base API endpoint
  - Default: `https://api.coingecko.com/api/v3`
- Configurable request parameters in `config.py`

### 2. Market Analysis Parameters

#### Performance Thresholds
- `PRICE_CHANGE_THRESHOLD`: Minimum price change to trigger analysis
  - Default: `5.0%`
  - Range: `0.0` - `100.0`

- `VOLUME_CHANGE_THRESHOLD`: Minimum volume change to trigger analysis
  - Default: `10.0%`
  - Range: `0.0` - `100.0`

- `VOLUME_WINDOW_MINUTES`: Time window for volume analysis
  - Default: `60` (1 hour)
  - Range: `15` - `1440` (15 minutes to 24 hours)

### 3. Correlation and Advanced Analysis

#### Market Correlation Settings
- `CORRELATION_SENSITIVITY`: Threshold for token correlation
  - Default: `0.7`
  - Range: `0.0` - `1.0`
  - Higher values indicate stricter correlation requirements

- `VOLATILITY_THRESHOLD`: Market volatility sensitivity
  - Default: `2.0`
  - Range: `0.0` - `10.0`

- `VOLUME_SIGNIFICANCE`: Minimum volume to consider significant
  - Default: `100,000`
  - Helps filter out low-liquidity tokens

### 4. Tweet Configuration

#### Content Constraints
- `TWEET_MIN_LENGTH`: Minimum tweet length
  - Default: `220`
  - Ensures meaningful content

- `TWEET_MAX_LENGTH`: Maximum tweet length
  - Default: `270`
  - Leaves room for hashtags

- `TWEET_HARD_STOP_LENGTH`: Absolute maximum tweet length
  - Default: `280`
  - Respects Twitter's character limit

### 5. Browser and Automation

#### ChromeDriver Configuration
- `CHROME_DRIVER_PATH`: Path to ChromeDriver executable
  - Typical paths:
    - macOS/Linux: `/usr/local/bin/chromedriver`
    - Windows: `C:\WebDrivers\chromedriver.exe`

### 6. Logging and Debugging

#### Logging Configuration
- `LOG_LEVEL`: Logging verbosity
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Default: `INFO`

- `LOG_DIR`: Directory for log files
  - Default: `./logs`

#### Debugging Flags
- `DEBUG_MODE`: Enable detailed debugging
  - Options: `true`, `false`
  - Default: `false`

- `VERBOSE_LOGGING`: Increase log verbosity
  - Options: `true`, `false`
  - Default: `false`

### 7. Performance and Retry Mechanisms

#### Retry Configuration
- `MAX_RETRIES`: Maximum retry attempts for API calls
  - Default: `3`
  - Prevents infinite retry loops

#### API Request Configuration
- `REQUEST_TIMEOUT`: API request timeout in seconds
  - Default: `30`
  - Prevents hanging on slow connections

- `RATE_LIMIT_DELAY`: Delay between API requests
  - Default: `1.5` seconds
  - Helps prevent rate limiting

### 8. Optional Integrations

#### Google Sheets (Optional)
- `GOOGLE_SHEETS_PROJECT_ID`: Google Cloud Project ID
- `GOOGLE_SHEETS_PRIVATE_KEY`: Service account private key
- `GOOGLE_SHEETS_CLIENT_EMAIL`: Service account email
- `GOOGLE_SHEET_ID`: Specific spreadsheet ID for data export

## 🔒 Security Best Practices

1. Never commit `.env` to version control
2. Use strong, unique passwords
3. Rotate API keys periodically
4. Use environment-specific configurations
5. Limit access to configuration files

## 🛠 Customization Tips

- Start with default settings
- Gradually adjust thresholds based on observed performance
- Monitor logs for configuration impact
- Use `DEBUG_MODE` during initial setup

## 📈 Performance Tuning

- Lower `VOLUME_WINDOW_MINUTES` for more responsive analysis
- Adjust `CORRELATION_SENSITIVITY` to fine-tune market comparisons
- Modify `MAX_RETRIES` based on network reliability

## 🚨 Disclaimer

Configuration settings can significantly impact agent behavior. Always test changes in a controlled environment and be aware of potential trading risks.

---

**Happy Configuration! 🌟**
