# 📡 Farsi Telegram Channel Monitor

An OSINT tool that downloads messages and photos from a Telegram channel and automatically translates them from **Farsi (Persian) → English**, generating a styled HTML report.

Built for monitoring Farsi-language Telegram channels during the Iran conflict for intelligence and research purposes.

---

## Features

- Downloads messages and photos from any Telegram channel
- Translates Farsi text to English via Google Translate
- Preserves message formatting (bold, italic, links, mentions, hashtags)
- Generates a dark-themed HTML report with embedded photos
- Saves structured JSON output for further processing
- Secure credential management via `.env` file

---

## Requirements

- Python 3.11+
- Telegram account with API credentials from [my.telegram.org](https://my.telegram.org)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/farsi-monitor.git
cd farsi-monitor

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp .env.example .env
nano .env                        # Fill in your credentials
```

---

## Getting Your Telegram API Credentials

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click **API Development Tools**
4. Create an application (platform: Other)
5. Copy your `api_id` and `api_hash` into `.env`

---

## Usage

```bash
source venv/bin/activate
python farsi_monitor.py
```

On first run, enter the OTP sent to your Telegram app. A `.session` file is created for automatic re-authentication on future runs.

---

## Output

```
output/
├── messages.html    # Open in browser
├── messages.json    # Structured data
└── media/           # Downloaded photos
```

```bash
firefox output/messages.html
```

---

## Configuration

Edit `.env` to configure:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_API_ID` | Numeric API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | API hash string from my.telegram.org |
| `TELEGRAM_PHONE` | Your phone number with country code |
| `TELEGRAM_CHANNEL` | Target channel username or invite link |

Change `LIMIT = 200` in the script to fetch more or fewer messages (`None` = all).

---

## OPSEC Warning

- Never commit `.env` or `.session` files to Git
- API credentials are permanently tied to your Telegram account
- Consider using a dedicated number for sensitive OSINT work

---

## License

MIT License — free to use, modify, and distribute for research purposes.

---

*Built by [Sigmund](https://cybernewsph.com) for OSINT monitoring of Farsi Telegram channels.*

