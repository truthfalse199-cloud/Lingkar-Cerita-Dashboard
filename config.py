import os
from dotenv import load_dotenv

load_dotenv()

# Google Sheets CSV export URL
# Replace with your own public Google Sheet CSV URL, or set via .env
SHEET_CSV_URL = os.getenv(
    "SHEET_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/YOUR_SHEET_ID/pub?output=csv"
)

# Flask settings
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
PORT = int(os.getenv("PORT", 5000))

# Cache timeout in seconds (re-fetch data from Google Sheets after this period)
CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", 300))
