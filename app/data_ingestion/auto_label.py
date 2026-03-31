"""
auto_label.py
Auto-labeling and validation pipeline for incoming news data.
- Assigns confidence scores based on source trust
- Stores labeled data for retraining
- Validates model predictions against auto-labels
- Handles noisy labels
"""

import sqlite3
import logging
from typing import List, Dict, Tuple
import numpy as np

# --- CONFIG ---
DB_PATH = "fake_news.db"
TRUSTED_SOURCES = {"BBC News", "Reuters", "The Associated Press", "NPR", "The New York Times"}
SUSPICIOUS_SOURCES = {"Before It's News", "YourNewsWire", "WorldTruth.TV"}
LABELED_TABLE = "labeled_news"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("auto_label")

CREATE_LABELED_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {LABELED_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    image_url TEXT,
    source TEXT,
    published_at TEXT,
    fetched_at TEXT,
    auto_label TEXT,
    confidence REAL
);
"""

# --- AUTO-LABELING ---
def auto_label_article(article: Dict) -> Tuple[str, float]:
    source = article.get("source", "")
    if source in TRUSTED_SOURCES:
        return ("real", 0.95)
    elif source in SUSPICIOUS_SOURCES:
        return ("uncertain", 0.5)
    else:
        return ("uncertain", 0.7)

# --- DB UTILS ---
def get_db_conn():
    return sqlite3.connect(DB_PATH)

def init_labeled_db():
    with get_db_conn() as conn:
        conn.execute(CREATE_LABELED_TABLE_SQL)
        conn.commit()

def store_labeled_articles(articles: List[Dict]):
    with get_db_conn() as conn:
        for article in articles:
            label, conf = auto_label_article(article)
            conn.execute(
                f"""
                INSERT INTO {LABELED_TABLE} (title, description, image_url, source, published_at, fetched_at, auto_label, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.get("title", ""),
                    article.get("description", ""),
                    article.get("image_url", ""),
                    article.get("source", ""),
                    article.get("published_at", ""),
                    article.get("fetched_at", ""),
                    label,
                    conf
                )
            )
        conn.commit()
        logger.info(f"Stored {len(articles)} auto-labeled articles.")


# --- MODEL PREDICTION STORAGE ---
PREDICTED_TABLE = "predicted_news"
CREATE_PREDICTED_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {PREDICTED_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    url TEXT,
    predicted_label INTEGER,
    confidence REAL
);
"""

def init_predicted_db():
    with get_db_conn() as conn:
        conn.execute(CREATE_PREDICTED_TABLE_SQL)
        conn.commit()

def store_predicted_sample(text: str, url: str, predicted_label: int, confidence: float):
    if confidence > 0.85:
        with get_db_conn() as conn:
            conn.execute(
                f"""
                INSERT INTO {PREDICTED_TABLE} (text, url, predicted_label, confidence)
                VALUES (?, ?, ?, ?)
                """,
                (text, url, predicted_label, confidence)
            )
            conn.commit()
            logger.info(f"Stored predicted sample: label={predicted_label}, confidence={confidence:.3f}")
def fetch_unvalidated_articles(limit=100) -> List[Dict]:
    with get_db_conn() as conn:
        cur = conn.execute(f"SELECT * FROM {LABELED_TABLE} WHERE auto_label IS NOT NULL LIMIT ?", (limit,))
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

def run_model_prediction(article: Dict) -> Tuple[str, float]:
    # Placeholder: Replace with actual model inference
    # Returns (pred_label, pred_confidence)
    return ("real", 0.8)  # Dummy output

def validate_predictions():
    articles = fetch_unvalidated_articles()
    correct = 0
    total = 0
    for article in articles:
        auto_label = article["auto_label"]
        auto_conf = article["confidence"]
        pred_label, pred_conf = run_model_prediction(article)
        # Only compare if auto-label is confident
        if auto_conf >= 0.9:
            total += 1
            if pred_label == auto_label:
                correct += 1
    acc = correct / total if total > 0 else None
    logger.info(f"Validation accuracy on confident auto-labels: {acc}")
    return acc

# --- NOISY LABEL HANDLING ---
def filter_noisy_labels(articles: List[Dict], min_conf: float = 0.8) -> List[Dict]:
    """
    Only keep samples with confidence >= min_conf.
    """
    return [a for a in articles if a.get("confidence", 0) >= min_conf]

# Example usage:
# init_labeled_db()
# store_labeled_articles([article1, article2, ...])
# validate_predictions()
