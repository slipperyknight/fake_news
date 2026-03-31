"""
news_api.py
News data ingestion module using NewsAPI (or free alternative).
- Fetches latest articles
- Normalizes and stores in SQLite
- Handles rate limits, failures, and logging
- Modular and production-ready
"""

import requests
import sqlite3
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

# --- CONFIG ---
NEWS_API_KEY = "YOUR_NEWSAPI_KEY"  # Replace with your key or load from env
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
DB_PATH = "fake_news.db"
FETCH_INTERVAL = 6 * 60 * 60  # 6 hours in seconds

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("news_ingestion")

# --- DB SCHEMA ---
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    image_url TEXT,
    source TEXT,
    published_at TEXT,
    fetched_at TEXT
);
"""

# --- DATA NORMALIZATION ---
def normalize_article(article: Dict) -> Dict:
    return {
        "title": article.get("title", ""),
        "description": article.get("description", ""),
        "image_url": article.get("urlToImage", ""),
        "source": article.get("source", {}).get("name", ""),
        "published_at": article.get("publishedAt", ""),
        "fetched_at": datetime.utcnow().isoformat()
    }

# --- DB UTILS ---
def get_db_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_db_conn() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()

# --- INGESTION ---
def fetch_latest_articles(country: str = "us", page_size: int = 50) -> Optional[List[Dict]]:
    params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "pageSize": page_size
    }
    try:
        resp = requests.get(NEWS_API_URL, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("articles", [])
        elif resp.status_code == 429:
            logger.warning("Rate limit hit. Backing off.")
            time.sleep(60)  # Wait a minute before retry
        else:
            logger.error(f"API error: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Request failed: {e}")
    return None

def store_articles(articles: List[Dict]):
    with get_db_conn() as conn:
        for article in articles:
            norm = normalize_article(article)
            conn.execute(
                """
                INSERT INTO news_articles (title, description, image_url, source, published_at, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (norm["title"], norm["description"], norm["image_url"], norm["source"], norm["published_at"], norm["fetched_at"])
            )
        conn.commit()
        logger.info(f"Stored {len(articles)} articles.")

def ingest_news():
    logger.info("Starting news ingestion...")
    init_db()
    articles = fetch_latest_articles()
    if articles:
        store_articles(articles)
    else:
        logger.warning("No articles fetched.")

# --- SCHEDULING ---
def schedule_ingestion():
    """
    Run ingestion every 6 hours using a simple loop.
    For production, use APScheduler or cron.
    """
    while True:
        ingest_news()
        logger.info(f"Sleeping for {FETCH_INTERVAL // 3600} hours...")
        time.sleep(FETCH_INTERVAL)

# Example: To run once, call ingest_news().
# To schedule, call schedule_ingestion() in a background process.
