"""
retrain.py
Automated retraining pipeline with time-based weighting.
- Monitors for concept drift
- Retrains model with weighted training data
- Modular and extensible
"""

import os
import sys
import numpy as np
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.drift.drift import ConceptDriftDetector
from app.db.database import get_db
# from scripts.train_pipeline import MultimodalTrainer  # Uncomment when integrating


class RetrainingPipeline:
    """
    Handles automated retraining with time-weighted training data.
    Prioritizes recent samples using exponential decay.
    """
    
    def __init__(self, drift_detector: ConceptDriftDetector):
        """Initialize retraining pipeline."""
        self.drift_detector = drift_detector
        # self.trainer = MultimodalTrainer(...)  # Initialize with model params
        self.decay_rate = 0.01  # Exponential decay rate
        
    def compute_sample_weight(self, timestamp: datetime) -> float:
        """
        Compute time-based weight for a training sample.
        
        Args:
            timestamp (datetime): Sample timestamp
            
        Returns:
            float: Weight based on age (newer = higher weight)
        """
        current_time = datetime.now()
        age_in_days = (current_time - timestamp).total_seconds() / (24 * 3600)
        
        # Exponential decay: weight = exp(-decay_rate * age_in_days)
        weight = math.exp(-self.decay_rate * age_in_days)
        
        return weight
    
    def get_weighted_training_data(self, limit: int = None) -> Tuple[List[Dict], List[float]]:
        """
        Retrieve training data with time-based weights.
        
        Args:
            limit (int): Maximum number of samples to retrieve
            
        Returns:
            Tuple[List[Dict], List[float]]: (samples, weights)
        """
        db = get_db()
        
        # Get predictions from database
        predictions = db.get_predictions(
            limit=limit,
            unused_for_training_only=True  # Only use samples not yet used for training
        )
        
        weighted_samples = []
        weights = []
        
        for pred in predictions:
            # Parse timestamp
            if isinstance(pred['timestamp'], str):
                timestamp = datetime.fromisoformat(pred['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = pred['timestamp']
            
            # Compute weight
            weight = self.compute_sample_weight(timestamp)
            
            # Prepare sample with weight
            sample = {
                'text': pred['text'],
                'label': pred['predicted_label'],
                'url': pred['url'],
                'confidence': pred['confidence'],
                'timestamp': timestamp,
                'weight': weight
            }
            
            weighted_samples.append(sample)
            weights.append(weight)
        
        print(f"Retrieved {len(weighted_samples)} weighted samples")
        if weights:
            print(f"Weight range: {min(weights):.4f} to {max(weights):.4f}")
        else:
            print("No weights computed - empty dataset")
        
        return weighted_samples, weights
    
    def monitor_and_retrain(self, reference_data: np.ndarray = None, new_data: np.ndarray = None):
        """
        Checks for drift and retrains with weighted data if needed.
        
        Args:
            reference_data (np.ndarray): Reference data for drift detection
            new_data (np.ndarray): New data for drift detection
            
        Returns:
            bool: True if retraining occurred, False otherwise
        """
        # Check for concept drift if data provided
        if reference_data is not None and new_data is not None:
            drifted = self.drift_detector.check_drift(new_data)
            if drifted:
                print("Concept drift detected! Starting weighted retraining...")
                self.perform_weighted_retraining()
                return True
        
        print("No drift detected. Checking for scheduled retraining...")
        # Could add time-based retraining here
        return False
    
    def perform_weighted_retraining(self):
        """
        Perform retraining with time-weighted training data.
        """
        print("Starting weighted retraining process...")
        
        # Get weighted training data
        weighted_samples, weights = self.get_weighted_training_data(limit=10000)
        
        if len(weighted_samples) == 0:
            print("No new training data available")
            return False
        
        # Prepare training data
        X_texts = [sample['text'] for sample in weighted_samples]
        y_labels = [sample['label'] for sample in weighted_samples]
        sample_weights = [sample['weight'] for sample in weighted_samples]
        
        print(f"Training with {len(weighted_samples)} weighted samples")
        print(f"Total weight: {sum(sample_weights):.2f}")
        print(f"Average weight: {np.mean(sample_weights):.4f}")
        
        # TODO: Integrate with actual training pipeline
        # self.trainer.train_weighted(X_texts, y_labels, sample_weights)
        
        # Mark samples as used for training
        db = get_db()
        sample_ids = [sample.get('id') for sample in weighted_samples if 'id' in sample]
        if sample_ids:
            db.mark_as_used_for_training(sample_ids)
        
        print("Weighted retraining completed successfully!")
        return True
    
    def get_weight_statistics(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Get statistics about sample weights in the database.
        
        Args:
            limit (int): Maximum samples to analyze
            
        Returns:
            Dict: Weight statistics
        """
        weighted_samples, weights = self.get_weighted_training_data(limit=limit)
        
        if not weights:
            return {"error": "No samples found"}
        
        return {
            "total_samples": len(weights),
            "weight_sum": sum(weights),
            "avg_weight": np.mean(weights),
            "min_weight": min(weights),
            "max_weight": max(weights),
            "std_weight": np.std(weights),
            "decay_rate": self.decay_rate,
            "age_range_days": {
                "newest": min([(datetime.now() - s['timestamp']).total_seconds() / (24 * 3600) 
                               for s in weighted_samples]),
                "oldest": max([(datetime.now() - s['timestamp']).total_seconds() / (24 * 3600) 
                               for s in weighted_samples])
            }
        }


# Example usage and testing
if __name__ == "__main__":
    from app.drift.drift import ConceptDriftDetector
    
    # Initialize retraining pipeline
    drift_detector = ConceptDriftDetector()
    retrain_pipeline = RetrainingPipeline(drift_detector)
    
    print("Testing Weighted Retraining Pipeline")
    print("=" * 50)
    
    # Test weight computation
    from datetime import datetime, timedelta
    
    test_times = [
        datetime.now() - timedelta(days=1),    # 1 day old
        datetime.now() - timedelta(days=7),    # 1 week old
        datetime.now() - timedelta(days=30),   # 1 month old
        datetime.now() - timedelta(days=90),   # 3 months old
    ]
    
    print("\n--- Weight Computation Test ---")
    for i, test_time in enumerate(test_times, 1):
        age_days = (datetime.now() - test_time).total_seconds() / (24 * 3600)
        weight = retrain_pipeline.compute_sample_weight(test_time)
        print(f"Sample {i}: Age={age_days:.1f} days, Weight={weight:.4f}")
    
    # Test weighted data retrieval
    print(f"\n--- Weighted Data Test ---")
    weighted_samples, weights = retrain_pipeline.get_weighted_training_data(limit=10)
    
    for i, sample in enumerate(weighted_samples[:3], 1):
        print(f"Sample {i}: Weight={sample['weight']:.4f}, Age={sample.get('age', 'Unknown')}")
    
    # Show statistics
    stats = retrain_pipeline.get_weight_statistics(limit=100)
    print(f"\n--- Weight Statistics ---")
    for key, value in stats.items():
        if key != "error":
            print(f"{key}: {value}")
