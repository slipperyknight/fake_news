# config.py
"""
Project configuration and constants.
"""

import os

# Paths
DATA_DIR = os.getenv("DATA_DIR", "data/")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw/")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed/")
MODEL_DIR = os.getenv("MODEL_DIR", "models/")
LOG_DIR = os.getenv("LOG_DIR", "logs/")

# Database
DB_PATH = os.getenv("DB_PATH", "fake_news.db")

# Other constants
RANDOM_SEED = 42
