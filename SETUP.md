# 🚀 SentinelDuece Crypto Analysis Agent: Comprehensive Setup Guide

## 📋 Prerequisites

### System Requirements
- Python 3.9 or higher
- pip (Python package manager)
- Git
- Google Chrome
- ChromeDriver (compatible with your Chrome version)

### Required Accounts
1. Anthropic Claude API Account
2. Twitter Account
3. Google Cloud Project (Optional)
4. CoinGecko API (Optional, free tier available)

## 🔧 Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/kingraver/sentinelduece.git
cd sentinelduece
```

### 2. Create Virtual Environment
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install System Dependencies
#### macOS
```bash
brew install python3 chrome
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3 python3-venv python3-pip google-chrome-stable
```

#### Windows
1. Download and install Python from python.org
2. Download and install Google Chrome
3. Use Windows Subsystem for Linux (WSL) for easier setup

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Install ChromeDriver 🌐

#### Automatic Method (Recommended)
```bash
# This script will download the appropriate ChromeDriver
python get-chromedriver.py
```

#### Manual Method
1. Check your Chrome version (Help > About Google Chrome)
2. Download matching ChromeDriver from [ChromeDriver Downloads](https://sites.google.com/a/chromium.org/chromedriver/)
3. Place in `/usr/local/bin/` or add to system PATH

### 6. Configure API Credentials 🔑

#### Claude AI API Key
1. Visit [Anthropic Claude API](https://www.anthropic.com/product)
2. Create an account
3. Generate an API key
4. Add to `.env` file:
   ```
   CLAUDE_API_KEY=your_anthropic_api_key
   ```

#### Twitter Credentials
1. Create a Twitter account if you don't have one
2. Use your actual Twitter username and password in `.env`
   ```
   TWITTER_USERNAME=your_twitter_username
   TWITTER_PASSWORD=your_twitter_password
   ```

#### Optional: Google Sheets Integration
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API
4. Create service account credentials
5. Download JSON key
6. Extract and add to `.env`:
   ```
   GOOGLE_SHEETS_PROJECT_ID=your_project_id
   GOOGLE_SHEETS_PRIVATE_KEY=your_private_key
   GOOGLE_SHEETS_CLIENT_EMAIL=your_client_email
   GOOGLE_SHEET_ID=your_sheet_id
   ```

### 7. Configure ChromeDriver Path
In `.env`, set the correct path:
```
# macOS/Linux typical path
CHROME_DRIVER_PATH=/usr/local/bin/chromedriver

# Windows typical path
CHROME_DRIVER_PATH=C:\WebDrivers\chromedriver.exe
```

### 8. Database Initialization
```bash
# Create data directory if not exists
mkdir -p data

# The database will be automatically created on first run
```

### 9. Logging Setup
```bash
# Create logs directory
mkdir -p logs
```

### 10. Run Initial Test
```bash
python src/bot.py --test
```

## 🛡️ Security Best Practices

1. Never commit `.env` to version control
2. Use strong, unique passwords
3. Regularly rotate API keys
4. Use environment-specific configurations

## 🔍 Troubleshooting

### Common Issues
- **ChromeDriver Version Mismatch**: Ensure ChromeDriver matches Chrome version
- **API Credential Errors**: Double-check API keys
- **Missing Dependencies**: Reinstall `requirements.txt`

### Debugging
Add to `.env` for more verbose output:
```
DEBUG_MODE=true
VERBOSE_LOGGING=true
```

## 🚀 Deployment Considerations

### Production Deployment
- Use a cloud VM or dedicated server
- Set up a process manager like `systemd` or `supervisor`
- Configure automatic restarts
- Implement proper logging and monitoring

### Docker Option
A `Dockerfile` is recommended for consistent deployment across environments.

## 📄 License and Disclaimer

- Review the project's `LICENSE` file
- Cryptocurrency trading involves risks
- This tool is for educational purposes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push and create a Pull Request

---

**Happy Coding! 🌟**
