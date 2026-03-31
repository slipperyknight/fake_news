"""
drift_detector.py
Concept drift detection for fake news models.
- Tracks rolling confidence scores
- Monitors prediction distribution changes
- Computes drift signals and flags when threshold exceeded
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
import json
import os
from datetime import datetime, timedelta


class ConceptDriftDetector:
    """
    Detects concept drift in fake news model predictions.
    Tracks rolling statistics and flags when drift is detected.
    """
    
    def __init__(self, 
                 window_size: int = 1000,
                 confidence_threshold: float = 0.05,
                 distribution_threshold: float = 0.15,
                 drift_threshold: float = 0.3):
        """
        Initialize drift detector.
        
        Args:
            window_size (int): Size of rolling window for statistics
            confidence_threshold (float): Minimum confidence change to consider
            distribution_threshold (float): Distribution change threshold
            drift_threshold (float): Overall drift signal threshold
        """
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.distribution_threshold = distribution_threshold
        self.drift_threshold = drift_threshold
        
        # Rolling windows for tracking
        self.confidence_window = deque(maxlen=window_size)
        self.prediction_window = deque(maxlen=window_size)
        
        # Statistics tracking
        self.initial_confidence_mean = None
        self.initial_distribution = None
        self.total_predictions = 0
        self.drift_history = []
        
        # Drift state
        self.drift_flagged = False
        self.last_drift_time = None
        
        print(f"ConceptDriftDetector initialized:")
        print(f"  Window size: {window_size}")
        print(f"  Drift threshold: {drift_threshold}")
    
    def update(self, prediction: Dict[str, any]) -> float:
        """
        Update drift detector with new prediction.
        
        Args:
            prediction (Dict): Prediction result with confidence and label
            
        Returns:
            float: Current drift signal
        """
        confidence = prediction.get('confidence', 0.0)
        label = prediction.get('label', 0)
        
        # Update rolling windows
        self.confidence_window.append(confidence)
        self.prediction_window.append(label)
        self.total_predictions += 1
        
        # Initialize baseline after first window
        if len(self.confidence_window) == self.window_size and self.initial_confidence_mean is None:
            self.initial_confidence_mean = np.mean(self.confidence_window)
            self.initial_distribution = self._compute_distribution()
            print(f"Baseline established with {self.window_size} predictions")
            print(f"  Initial confidence mean: {self.initial_confidence_mean:.4f}")
        
        return self._compute_drift_signal()
    
    def _compute_drift_signal(self) -> float:
        """
        Compute drift signal based on current vs baseline statistics.
        
        Returns:
            float: Drift signal (0-1)
        """
        if len(self.confidence_window) < self.window_size:
            return 0.0  # Not enough data
        
        current_confidence_mean = np.mean(self.confidence_window)
        current_distribution = self._compute_distribution()
        
        # Confidence drift component
        confidence_drift = 0.0
        if self.initial_confidence_mean is not None:
            confidence_change = abs(current_confidence_mean - self.initial_confidence_mean)
            confidence_drift = min(confidence_change / self.initial_confidence_mean, 1.0)
        
        # Distribution drift component
        distribution_drift = 0.0
        if self.initial_distribution is not None:
            distribution_change = self._distribution_distance(current_distribution, self.initial_distribution)
            distribution_drift = min(distribution_change, 1.0)
        
        # Combined drift signal (weighted average)
        drift_signal = 0.7 * confidence_drift + 0.3 * distribution_drift
        
        return drift_signal
    
    def _compute_distribution(self) -> Dict[str, float]:
        """
        Compute prediction distribution statistics.
        
        Returns:
            Dict: Distribution metrics
        """
        if not self.prediction_window:
            return {"fake_ratio": 0.5, "real_ratio": 0.5, "entropy": 1.0}
        
        predictions = list(self.prediction_window)
        fake_count = predictions.count(0)
        real_count = predictions.count(1)
        total = len(predictions)
        
        fake_ratio = fake_count / total
        real_ratio = real_count / total
        
        # Compute entropy
        entropy = 0.0
        for ratio in [fake_ratio, real_ratio]:
            if ratio > 0:
                entropy -= ratio * np.log2(ratio)
        
        return {
            "fake_ratio": fake_ratio,
            "real_ratio": real_ratio,
            "entropy": entropy
        }
    
    def _distribution_distance(self, dist1: Dict[str, float], dist2: Dict[str, float]) -> float:
        """
        Compute distance between two distributions.
        
        Args:
            dist1 (Dict): First distribution
            dist2 (Dict): Second distribution
            
        Returns:
            float: Distance metric (0-1)
        """
        # Jensen-Shannon divergence for distribution comparison
        distance = 0.0
        for key in ["fake_ratio", "real_ratio"]:
            p = dist1.get(key, 0.5)
            q = dist2.get(key, 0.5)
            if p > 0 and q > 0:
                distance += p * np.log2(p / q)
        
        return min(abs(distance), 1.0)
    
    def get_drift_status(self) -> Dict[str, any]:
        """
        Get current drift status and statistics.
        
        Returns:
            Dict: Current drift information
        """
        drift_signal = self._compute_drift_signal()
        
        # Check if drift should be flagged
        should_flag = drift_signal > self.drift_threshold
        newly_flagged = should_flag and not self.drift_flagged
        
        if newly_flagged:
            self.drift_flagged = True
            self.last_drift_time = datetime.now()
            self.drift_history.append({
                "timestamp": self.last_drift_time.isoformat(),
                "drift_signal": drift_signal,
                "confidence_mean": np.mean(self.confidence_window) if self.confidence_window else 0.0,
                "total_predictions": self.total_predictions
            })
        
        return {
            "drift_signal": drift_signal,
            "drift_flagged": self.drift_flagged,
            "newly_flagged": newly_flagged,
            "threshold": self.drift_threshold,
            "window_size": len(self.confidence_window),
            "total_predictions": self.total_predictions,
            "last_drift_time": self.last_drift_time.isoformat() if self.last_drift_time else None,
            "statistics": {
                "current_confidence_mean": np.mean(self.confidence_window) if self.confidence_window else 0.0,
                "initial_confidence_mean": self.initial_confidence_mean,
                "confidence_drift": abs(np.mean(self.confidence_window) - self.initial_confidence_mean) if self.initial_confidence_mean else 0.0,
                "current_distribution": self._compute_distribution(),
                "initial_distribution": self.initial_distribution
            }
        }
    
    def reset_baseline(self):
        """
        Reset baseline with current statistics.
        Useful after model retraining.
        """
        if len(self.confidence_window) >= self.window_size:
            self.initial_confidence_mean = np.mean(self.confidence_window)
            self.initial_distribution = self._compute_distribution()
            self.drift_flagged = False
            print(f"Baseline reset with new confidence mean: {self.initial_confidence_mean:.4f}")
    
    def save_state(self, filepath: str):
        """
        Save drift detector state to file.
        
        Args:
            filepath (str): Path to save state
        """
        state = {
            "window_size": self.window_size,
            "drift_threshold": self.drift_threshold,
            "confidence_window": list(self.confidence_window),
            "prediction_window": list(self.prediction_window),
            "initial_confidence_mean": self.initial_confidence_mean,
            "initial_distribution": self.initial_distribution,
            "total_predictions": self.total_predictions,
            "drift_history": self.drift_history,
            "drift_flagged": self.drift_flagged,
            "last_drift_time": self.last_drift_time.isoformat() if self.last_drift_time else None
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"Drift detector state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """
        Load drift detector state from file.
        
        Args:
            filepath (str): Path to load state from
        """
        if not os.path.exists(filepath):
            print(f"State file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.confidence_window = deque(state["confidence_window"], maxlen=self.window_size)
            self.prediction_window = deque(state["prediction_window"], maxlen=self.window_size)
            self.initial_confidence_mean = state["initial_confidence_mean"]
            self.initial_distribution = state["initial_distribution"]
            self.total_predictions = state["total_predictions"]
            self.drift_history = state["drift_history"]
            self.drift_flagged = state["drift_flagged"]
            
            if state["last_drift_time"]:
                self.last_drift_time = datetime.fromisoformat(state["last_drift_time"])
            
            print(f"Drift detector state loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return False


# Global drift detector instance
_drift_detector = None


def get_drift_detector() -> ConceptDriftDetector:
    """
    Get or create global drift detector instance.
    
    Returns:
        ConceptDriftDetector: Global drift detector
    """
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = ConceptDriftDetector()
    return _drift_detector


def update_drift_detector(prediction: Dict[str, any]) -> float:
    """
    Update drift detector with new prediction.
    
    Args:
        prediction (Dict): Prediction result
        
    Returns:
        float: Current drift signal
    """
    detector = get_drift_detector()
    return detector.update(prediction)


def get_drift_status() -> Dict[str, any]:
    """
    Get current drift status.
    
    Returns:
        Dict: Current drift information
    """
    detector = get_drift_detector()
    return detector.get_drift_status()


# Example usage
if __name__ == "__main__":
    # Test drift detector
    detector = ConceptDriftDetector(window_size=10, drift_threshold=0.3)
    
    # Simulate predictions
    test_predictions = [
        {"label": 1, "confidence": 0.8},
        {"label": 0, "confidence": 0.6},
        {"label": 1, "confidence": 0.9},
        {"label": 0, "confidence": 0.4},
        {"label": 1, "confidence": 0.7},
        {"label": 0, "confidence": 0.5},
        {"label": 1, "confidence": 0.85},
        {"label": 0, "confidence": 0.3},
        {"label": 1, "confidence": 0.95},
    ]
    
    print("Testing drift detector with simulated predictions...")
    
    for i, pred in enumerate(test_predictions):
        drift_signal = detector.update(pred)
        status = detector.get_drift_status()
        
        print(f"Prediction {i+1}: Label={pred['label']}, Conf={pred['confidence']:.2f}, Drift={drift_signal:.3f}")
        print(f"  Status: Flagged={status['drift_flagged']}, Threshold={status['threshold']}")
        
        if status['newly_flagged']:
            print(f"  🚨 DRIFT DETECTED at prediction {i+1}!")
    
    print(f"\nFinal drift status:")
    final_status = detector.get_drift_status()
    for key, value in final_status.items():
        print(f"  {key}: {value}")
