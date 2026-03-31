"""
database.py
SQLite database schema and operations for fake news detection.
- Auto-creates tables on startup
- Stores predictions with detailed metadata
- Supports training data collection
"""

import sqlite3
import os
import math
from datetime import datetime
from typing import Optional, Dict, Any, List


class DatabaseManager:
    """
    Manages SQLite database for fake news detection system.
    Auto-creates tables and provides CRUD operations.
    """
    
    def __init__(self, db_path: str = "fake_news.db"):
        """
        Initialize database connection and create tables.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            print(f"Connected to database: {self.db_path}")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Create predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                url TEXT,
                predicted_label INTEGER NOT NULL,
                confidence REAL NOT NULL,
                text_score REAL,
                meta_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_high_confidence BOOLEAN DEFAULT FALSE,
                is_used_for_training BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
            ON predictions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_confidence 
            ON predictions(confidence)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_high_confidence 
            ON predictions(is_high_confidence)
        """)
        
        self.connection.commit()
        print("Database tables created/verified successfully")
    
    def insert_prediction(self, 
                       text: str,
                       predicted_label: int,
                       confidence: float,
                       url: Optional[str] = None,
                       text_score: Optional[float] = None,
                       meta_score: Optional[float] = None,
                       is_high_confidence: Optional[bool] = None) -> int:
        """
        Insert a new prediction into the database.
        
        Args:
            text (str): The predicted text
            predicted_label (int): 0 (fake) or 1 (real)
            confidence (float): Overall confidence score (0-1)
            url (Optional[str]): URL if provided
            text_score (Optional[float]): Text model confidence
            meta_score (Optional[float]): Metadata model confidence
            is_high_confidence (Optional[bool]): Auto-calculated if None
            
        Returns:
            int: ID of inserted record
        """
        cursor = self.connection.cursor()
        
        # Auto-calculate high confidence if not provided
        if is_high_confidence is None:
            is_high_confidence = confidence >= 0.85
        
        cursor.execute("""
            INSERT INTO predictions 
            (text, url, predicted_label, confidence, text_score, meta_score, is_high_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            text, url, predicted_label, confidence, 
            text_score, meta_score, is_high_confidence
        ))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_predictions(self, 
                     limit: Optional[int] = None,
                     high_confidence_only: bool = False,
                     unused_for_training_only: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve predictions from database.
        
        Args:
            limit (Optional[int]): Maximum number of records to return
            high_confidence_only (bool): Filter for high confidence predictions only
            unused_for_training_only (bool): Filter for predictions not used in training
            
        Returns:
            List[Dict]: List of prediction records
        """
        cursor = self.connection.cursor()
        
        query = "SELECT * FROM predictions WHERE 1=1"
        params = []
        
        if high_confidence_only:
            query += " AND is_high_confidence = ?"
            params.append(True)
        
        if unused_for_training_only:
            query += " AND is_used_for_training = ?"
            params.append(False)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_training_data(self, 
                      limit: Optional[int] = None,
                      min_confidence: float = 0.85) -> List[Dict[str, Any]]:
        """
        Get training data with recency weights.
        
        Args:
            limit (Optional[int]): Maximum number of records to return
            min_confidence (float): Minimum confidence threshold for training data
            
        Returns:
            List[Dict]: Training data with recency weights
        """
        cursor = self.connection.cursor()
        
        # Get high confidence predictions not used for training
        query = """
            SELECT *, 
                   julianday('now') - julianday(timestamp) as age_in_days
            FROM predictions 
            WHERE is_high_confidence = TRUE 
            AND is_used_for_training = FALSE
            ORDER BY timestamp DESC
        """
        
        params = []
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        training_data = []
        for row in rows:
            record = dict(row)
            age_in_days = record.get('age_in_days', 0)
            
            # Calculate recency weight: weight = exp(-0.01 * age_in_days)
            import math
            recency_weight = math.exp(-0.01 * age_in_days)
            
            record['recency_weight'] = recency_weight
            training_data.append(record)
        
        return training_data
    
    def mark_as_used_for_training(self, prediction_ids: List[int]):
        """
        Mark predictions as used for training.
        
        Args:
            prediction_ids (List[int]): List of prediction IDs to mark
        """
        cursor = self.connection.cursor()
        
        placeholders = ','.join(['?' for _ in prediction_ids])
        cursor.execute(f"""
            UPDATE predictions 
            SET is_used_for_training = TRUE 
            WHERE id IN ({placeholders})
        """, prediction_ids)
        
        self.connection.commit()
        print(f"Marked {len(prediction_ids)} predictions as used for training")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dict: Statistics about predictions
        """
        cursor = self.connection.cursor()
        
        # Total predictions
        cursor.execute("SELECT COUNT(*) as total FROM predictions")
        total = cursor.fetchone()['total']
        
        # High confidence predictions
        cursor.execute("SELECT COUNT(*) as high_conf FROM predictions WHERE is_high_confidence = TRUE")
        high_conf = cursor.fetchone()['high_conf']
        
        # Average confidence
        cursor.execute("SELECT AVG(confidence) as avg_conf FROM predictions")
        avg_conf = cursor.fetchone()['avg_conf'] or 0
        
        # Label distribution
        cursor.execute("""
            SELECT predicted_label, COUNT(*) as count 
            FROM predictions 
            GROUP BY predicted_label
        """)
        label_dist = {row['predicted_label']: row['count'] for row in cursor.fetchall()}
        
        return {
            "total_predictions": total,
            "high_confidence_predictions": high_conf,
            "average_confidence": round(avg_conf, 4),
            "label_distribution": label_dist,
            "fake_news_count": label_dist.get(0, 0),
            "real_news_count": label_dist.get(1, 0)
        }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database instance
db_manager = None


def get_db() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


# Example usage and testing
if __name__ == "__main__":
    # Test database operations
    with DatabaseManager("test_fake_news.db") as db:
        print("Testing database operations...")
        
        # Insert test predictions
        test_predictions = [
            {
                "text": "Breaking news about something important",
                "predicted_label": 1,
                "confidence": 0.85,
                "url": "https://example.com/news",
                "text_score": 0.9,
                "meta_score": 0.7
            },
            {
                "text": "Fake news with low confidence",
                "predicted_label": 0,
                "confidence": 0.65,
                "text_score": 0.6,
                "meta_score": 0.7
            }
        ]
        
        for pred in test_predictions:
            pred_id = db.insert_prediction(**pred)
            print(f"Inserted prediction with ID: {pred_id}")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Get high confidence predictions
        high_conf = db.get_predictions(high_confidence_only=True, limit=5)
        print(f"\nHigh confidence predictions: {len(high_conf)}")
        
        # Clean up test database
        os.remove("test_fake_news.db")
        print("Test database cleaned up")
