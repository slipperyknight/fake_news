"""
data_collector.py
Collects and prepares high-confidence predictions for model retraining.
- Queries database for qualified samples
- Applies auto-labeling and time-based weighting
- Marks samples as used for training
"""

import os
import sys
from typing import List, Dict, Any, Tuple
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.db.database import get_db
from app.retrain.auto_label import AutoLabeler


class DataCollector:
    """
    Collects and prepares training data from high-confidence predictions.
    Integrates auto-labeling and time-based weighting.
    """
    
    def __init__(self):
        """Initialize data collector with auto-labeler."""
        self.auto_labeler = AutoLabeler()
        print("DataCollector initialized for training data collection")
    
    def collect_training_data(self, limit: int = None) -> Tuple[List[Dict], List[float]]:
        """
        Collect high-confidence predictions for training.
        
        Args:
            limit (int): Maximum number of samples to collect
            
        Returns:
            Tuple[List[Dict], List[float]]: (weighted_samples, weights)
        """
        print(f"Collecting training data (limit={limit})...")
        
        # Get high-confidence, unused predictions from database
        db = get_db()
        predictions = db.get_predictions(
            limit=limit,
            high_confidence_only=True,
            unused_for_training_only=True
        )
        
        if not predictions:
            print("No high-confidence predictions available for training")
            return [], []
        
        print(f"Found {len(predictions)} high-confidence predictions")
        
        # Apply auto-labeling filter
        filtered_samples = []
        for pred in predictions:
            # Apply auto-labeling logic
            eval_result = self.auto_labeler.evaluate_prediction(
                prediction=pred['predicted_label'],
                confidence=pred['confidence'],
                url=pred['url']
            )
            
            # Only accept samples that pass auto-labeling
            if eval_result['accepted']:
                # Merge evaluation result with prediction data
                sample = {
                    **pred,
                    'auto_label_result': eval_result,
                    'accepted_by_auto_label': True
                }
                filtered_samples.append(sample)
            else:
                print(f"Rejected by auto-label: {eval_result['reason']}")
        
        print(f"Auto-labeler accepted {len(filtered_samples)}/{len(predictions)} samples")
        
        if not filtered_samples:
            return [], []
        
        # Apply time-based weighting
        weighted_samples = []
        weights = []
        
        for sample in filtered_samples:
            # Parse timestamp
            if isinstance(sample['timestamp'], str):
                from datetime import datetime
                timestamp = datetime.fromisoformat(sample['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = sample['timestamp']
            
            # Compute time-based weight
            weight = self.auto_labeler.compute_sample_weight(timestamp)
            
            # Add weight to sample
            weighted_sample = {
                **sample,
                'time_weight': weight,
                'final_weight': weight  # Could combine with other weights here
            }
            
            weighted_samples.append(weighted_sample)
            weights.append(weight)
        
        print(f"Applied time-based weights to {len(weighted_samples)} samples")
        if weights:
            print(f"Weight range: {min(weights):.4f} to {max(weights):.4f}")
            print(f"Average weight: {np.mean(weights):.4f}")
        
        return weighted_samples, weights
    
    def prepare_training_dataset(self, limit: int = None) -> Dict[str, Any]:
        """
        Prepare complete training dataset for model retraining.
        
        Args:
            limit (int): Maximum number of samples to collect
            
        Returns:
            Dict: Complete training dataset information
        """
        print("Preparing training dataset...")
        
        # Collect weighted training data
        weighted_samples, weights = self.collect_training_data(limit=limit)
        
        if not weighted_samples:
            return {
                "status": "no_data",
                "message": "No suitable training data found",
                "samples": [],
                "weights": []
            }
        
        # Prepare training data in standard format
        X_texts = [sample['text'] for sample in weighted_samples]
        y_labels = [sample['predicted_label'] for sample in weighted_samples]
        sample_weights = [sample['final_weight'] for sample in weighted_samples]
        
        # Extract metadata for multimodal training
        metadata = []
        for sample in weighted_samples:
            meta = {
                'url': sample['url'],
                'confidence': sample['confidence'],
                'text_score': sample.get('text_score'),
                'meta_score': sample.get('meta_score'),
                'timestamp': sample['timestamp'],
                'time_weight': sample['time_weight'],
                'auto_label_accepted': sample['accepted_by_auto_label']
            }
            metadata.append(meta)
        
        # Mark samples as used for training
        self.mark_samples_as_used(weighted_samples)
        
        # Prepare dataset summary
        dataset_info = {
            "status": "ready",
            "total_samples": len(weighted_samples),
            "X_texts": X_texts,
            "y_labels": y_labels,
            "sample_weights": sample_weights,
            "metadata": metadata,
            "weight_statistics": {
                "min_weight": min(weights) if weights else 0,
                "max_weight": max(weights) if weights else 0,
                "avg_weight": np.mean(weights) if weights else 0,
                "std_weight": np.std(weights) if weights else 0
            },
            "quality_metrics": {
                "high_confidence_count": sum(1 for s in weighted_samples if s.get('confidence', 0) > 0.9),
                "trusted_source_count": sum(1 for s in weighted_samples 
                                         if s.get('auto_label_result', {}).get('is_trusted_source', False)),
                "avg_confidence": np.mean([s.get('confidence', 0) for s in weighted_samples])
            }
        }
        
        print(f"Training dataset prepared: {len(weighted_samples)} samples")
        print(f"Average confidence: {dataset_info['quality_metrics']['avg_confidence']:.4f}")
        print(f"High confidence samples: {dataset_info['quality_metrics']['high_confidence_count']}")
        
        return dataset_info
    
    def mark_samples_as_used(self, samples: List[Dict]):
        """
        Mark collected samples as used for training.
        
        Args:
            samples (List[Dict]): List of samples to mark as used
        """
        if not samples:
            return
        
        # Extract sample IDs
        sample_ids = [sample.get('id') for sample in samples if 'id' in sample]
        
        if sample_ids:
            db = get_db()
            db.mark_as_used_for_training(sample_ids)
            print(f"Marked {len(sample_ids)} samples as used for training")
        else:
            print("No sample IDs to mark as used")
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about training data collection.
        
        Returns:
            Dict: Collection statistics
        """
        db = get_db()
        
        # Get all predictions for analysis
        all_predictions = db.get_predictions(limit=10000)
        high_conf_predictions = db.get_predictions(
            limit=10000, 
            high_confidence_only=True
        )
        unused_predictions = db.get_predictions(
            limit=10000,
            unused_for_training_only=True
        )
        unused_high_conf = [p for p in high_conf_predictions if not p.get('is_used_for_training', False)]
        
        return {
            "total_predictions": len(all_predictions),
            "high_confidence_predictions": len(high_conf_predictions),
            "unused_predictions": len(unused_predictions),
            "unused_high_confidence": len(unused_high_conf),
            "collection_ready": len(unused_high_conf),
            "collection_rate": len(unused_high_conf) / len(high_conf_predictions) if high_conf_predictions else 0,
            "database_stats": db.get_statistics()
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize data collector
    collector = DataCollector()
    
    print("Training Data Collection Test")
    print("=" * 50)
    
    # Show collection statistics
    stats = collector.get_collection_statistics()
    print("\n--- Collection Statistics ---")
    for key, value in stats.items():
        if key != "database_stats":
            print(f"{key}: {value}")
    
    # Prepare training dataset
    dataset = collector.prepare_training_dataset(limit=100)
    
    if dataset['status'] == 'ready':
        print(f"\n--- Training Dataset Summary ---")
        print(f"Status: {dataset['status']}")
        print(f"Total samples: {dataset['total_samples']}")
        print(f"Weight stats: min={dataset['weight_statistics']['min_weight']:.4f}, "
              f"max={dataset['weight_statistics']['max_weight']:.4f}, "
              f"avg={dataset['weight_statistics']['avg_weight']:.4f}")
        print(f"Quality metrics:")
        for key, value in dataset['quality_metrics'].items():
            print(f"  {key}: {value}")
    else:
        print(f"\n--- Dataset Status ---")
        print(f"Status: {dataset['status']}")
        print(f"Message: {dataset['message']}")
    
    print("\n✅ Data collection test completed!")
