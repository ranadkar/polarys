"""Configuration and constants for the application."""
import os
from dotenv import load_dotenv
from scrapers.cnn import fetch_cnn
from scrapers.fox import fetch_fox
from scrapers.cbs import fetch_cbs
from scrapers.nbc import fetch_nbc
from scrapers.abc import fetch_abc
from scrapers.breitbart import fetch_breitbart
from scrapers.nypost import fetch_nypost
from scrapers.oann import fetch_oann

load_dotenv()

# API Keys and credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

# Outlet configuration mapping
OUTLETS = {
    "cnn.com": {"source": "CNN", "bias": "left", "scraper": fetch_cnn},
    "cbsnews.com": {"source": "CBS News", "bias": "left", "scraper": fetch_cbs},
    "nbcnews.com": {"source": "NBC News", "bias": "left", "scraper": fetch_nbc},
    "abcnews.go.com": {"source": "ABC News", "bias": "left", "scraper": fetch_abc},
    "foxnews.com": {"source": "Fox News", "bias": "right", "scraper": fetch_fox},
    "breitbart.com": {"source": "Breitbart", "bias": "right", "scraper": fetch_breitbart},
    "nypost.com": {"source": "NY Post", "bias": "right", "scraper": fetch_nypost},
    "oann.com": {"source": "OANN", "bias": "right", "scraper": fetch_oann},
}

# News sources for search
NEWS_DOMAINS = "cnn.com, cbsnews.com, nbcnews.com, abcnews.go.com, foxnews.com, breitbart.com, nypost.com, oann.com"

# Bias limits
MAX_LEFT_ARTICLES = 20
MAX_RIGHT_ARTICLES = 20
MAX_TOTAL_ARTICLES = 50

# Content limits
MIN_CONTENT_LENGTH = 100
