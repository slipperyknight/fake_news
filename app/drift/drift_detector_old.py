"""
drift_detector.py
Concept drift detection for fake news models.
- Tracks rolling average confidence over time
- Monitors fake vs real prediction distribution
- Detects significant shifts in model performance
"""

import os
import sys
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.db.database import get_db


class ConceptDriftDetector:
    """
    Detects concept drift in fake news model predictions.
    Tracks confidence trends and prediction distribution shifts.
    """
    
    def __init__(self, 
                 window_size: int = 1000,
                 confidence_threshold: float = 0.05,
                 distribution_threshold: float = 0.1):
        """
        Initialize drift detector.
        
        Args:
            window_size (int): Number of recent predictions to analyze
            confidence_threshold (float): Confidence drop threshold (5% = 0.05)
            distribution_threshold (float): Distribution shift threshold (10% = 0.1)
        """
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.distribution_threshold = distribution_threshold
        
        # Rolling window for recent predictions
        self.confidence_window = deque(maxlen=window_size)
        self.label_window = deque(maxlen=window_size)
        
        # Baseline metrics (established after warmup)
        self.baseline_confidence = None
        self.baseline_fake_ratio = None
        self.baseline_real_ratio = None
        
        # Warmup period
        self.warmup_period = window_size
        self.prediction_count = 0
        
        print(f"ConceptDriftDetector initialized:")
        print(f"  Window size: {window_size}")
        print(f"  Confidence threshold: {confidence_threshold * 100:.1f}%")
        print(f"  Distribution threshold: {distribution_threshold * 100:.1f}%")
    
    def add_prediction(self, confidence: float, predicted_label: int):
        """
        Add a new prediction to the drift detection window.
        
        Args:
            confidence (float): Model confidence score (0-1)
            predicted_label (int): Predicted label (0=Fake, 1=Real)
        """
        self.confidence_window.append(confidence)
        self.label_window.append(predicted_label)
        self.prediction_count += 1
        
        # Update baseline after warmup period
        if (self.prediction_count >= self.warmup_period and 
            self.baseline_confidence is None):
            self._establish_baseline()
    
    def _establish_baseline(self):
        """Establish baseline metrics from current window."""
        if len(self.confidence_window) < 10:
            return
        
        # Calculate baseline confidence
        self.baseline_confidence = np.mean(list(self.confidence_window))
        
        # Calculate baseline label distribution
        labels = list(self.label_window)
        fake_count = labels.count(0)
        real_count = labels.count(1)
        total = len(labels)
        
        self.baseline_fake_ratio = fake_count / total
        self.baseline_real_ratio = real_count / total
        
        print(f"Baseline established:")
        print(f"  Confidence: {self.baseline_confidence:.4f}")
        print(f"  Fake ratio: {self.baseline_fake_ratio:.3f}")
        print(f"  Real ratio: {self.baseline_real_ratio:.3f}")
    
    def check_confidence_drift(self) -> bool:
        """
        Check if average confidence has dropped significantly.
        
        Returns:
            bool: True if confidence drop > threshold
        """
        if len(self.confidence_window) < 10 or self.baseline_confidence is None:
            return False
        
        current_avg_confidence = np.mean(list(self.confidence_window))
        
        # Calculate relative drop
        confidence_drop = (self.baseline_confidence - current_avg_confidence) / self.baseline_confidence
        
        drift_detected = confidence_drop > self.confidence_threshold
        
        if drift_detected:
            print(f"Confidence drift detected:")
            print(f"  Baseline: {self.baseline_confidence:.4f}")
            print(f"  Current: {current_avg_confidence:.4f}")
            print(f"  Drop: {confidence_drop:.3f} ({confidence_drop*100:.1f}%)")
        
        return drift_detected
    
    def check_distribution_drift(self) -> bool:
        """
        Check if prediction distribution has shifted significantly.
        
        Returns:
            bool: True if distribution shift > threshold
        """
        if len(self.label_window) < 10 or self.baseline_fake_ratio is None:
            return False
        
        # Calculate current distribution
        labels = list(self.label_window)
        fake_count = labels.count(0)
        real_count = labels.count(1)
        total = len(labels)
        
        current_fake_ratio = fake_count / total
        current_real_ratio = real_count / total
        
        # Calculate distribution shift
        fake_shift = abs(current_fake_ratio - self.baseline_fake_ratio)
        real_shift = abs(current_real_ratio - self.baseline_real_ratio)
        max_shift = max(fake_shift, real_shift)
        
        drift_detected = max_shift > self.distribution_threshold
        
        if drift_detected:
            print(f"Distribution drift detected:")
            print(f"  Baseline - Fake: {self.baseline_fake_ratio:.3f}, Real: {self.baseline_real_ratio:.3f}")
            print(f"  Current - Fake: {current_fake_ratio:.3f}, Real: {current_real_ratio:.3f}")
            print(f"  Max shift: {max_shift:.3f} ({max_shift*100:.1f}%)")
        
        return drift_detected
    
    def check_drift(self) -> Dict[str, Any]:
        """
        Check for both confidence and distribution drift.
        
        Returns:
            Dict: Drift detection results
        """
        if self.prediction_count < self.warmup_period:
            return {
                "drift_detected": False,
                "status": "warmup",
                "predictions_count": self.prediction_count,
                "warmup_remaining": self.warmup_period - self.prediction_count
            }
        
        # Check both types of drift
        confidence_drift = self.check_confidence_drift()
        distribution_drift = self.check_distribution_drift()
        
        drift_detected = confidence_drift or distribution_drift
        
        result = {
            "drift_detected": drift_detected,
            "confidence_drift": confidence_drift,
            "distribution_drift": distribution_drift,
            "predictions_analyzed": len(self.confidence_window),
            "current_metrics": self._get_current_metrics(),
            "baseline_metrics": self._get_baseline_metrics(),
            "timestamp": datetime.now().isoformat()
        }
        
        if drift_detected:
            print(f"🚨 CONCEPT DRIFT DETECTED!")
        else:
            print(f"✅ No drift detected")
        
        return result
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        if len(self.confidence_window) == 0:
            return {"avg_confidence": 0.0, "fake_ratio": 0.0, "real_ratio": 0.0}
        
        avg_confidence = np.mean(list(self.confidence_window))
        labels = list(self.label_window)
        fake_count = labels.count(0)
        real_count = labels.count(1)
        total = len(labels)
        
        return {
            "avg_confidence": avg_confidence,
            "fake_ratio": fake_count / total if total > 0 else 0.0,
            "real_ratio": real_count / total if total > 0 else 0.0
        }
    
    def _get_baseline_metrics(self) -> Dict[str, float]:
        """Get baseline performance metrics."""
        if self.baseline_confidence is None:
            return {"avg_confidence": 0.0, "fake_ratio": 0.0, "real_ratio": 0.0}
        
        return {
            "avg_confidence": self.baseline_confidence,
            "fake_ratio": self.baseline_fake_ratio,
            "real_ratio": self.baseline_real_ratio
        }
    
    def reset_baseline(self):
        """Reset baseline metrics (useful after model updates)."""
        self.baseline_confidence = None
        self.baseline_fake_ratio = None
        self.baseline_real_ratio = None
        print("Baseline reset - will re-establish after warmup period")
    
    def get_drift_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive drift detection statistics.
        
        Returns:
            Dict: Drift detection statistics
        """
        current = self._get_current_metrics()
        baseline = self._get_baseline_metrics()
        
        return {
            "predictions_processed": self.prediction_count,
            "window_size": len(self.confidence_window),
            "window_full": len(self.confidence_window) >= self.window_size,
            "current_metrics": current,
            "baseline_metrics": baseline,
            "drift_thresholds": {
                "confidence_threshold": self.confidence_threshold,
                "distribution_threshold": self.distribution_threshold
            },
            "status": "active" if self.prediction_count >= self.warmup_period else "warmup"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize drift detector
    drift_detector = ConceptDriftDetector(
        window_size=100,
        confidence_threshold=0.05,  # 5% confidence drop
        distribution_threshold=0.1   # 10% distribution shift
    )
    
    print("Concept Drift Detection Test")
    print("=" * 50)
    
    # Simulate prediction stream
    import random
    
    # Phase 1: Normal predictions (establish baseline)
    print("\n--- Phase 1: Establishing Baseline ---")
    for i in range(150):
        confidence = random.uniform(0.8, 0.95)  # High confidence
        label = random.choice([0, 1])
        drift_detector.add_prediction(confidence, label)
    
    # Check for drift
    result = drift_detector.check_drift()
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Drift detected: {result.get('drift_detected', False)}")
    
    # Phase 2: Confidence drop (simulate drift)
    print("\n--- Phase 2: Simulating Confidence Drop ---")
    for i in range(50):
        confidence = random.uniform(0.6, 0.75)  # Lower confidence
        label = random.choice([0, 1])
        drift_detector.add_prediction(confidence, label)
    
    # Check for drift
    result = drift_detector.check_drift()
    print(f"Drift detected: {result['drift_detected']}")
    
    # Phase 3: Distribution shift (simulate drift)
    print("\n--- Phase 3: Simulating Distribution Shift ---")
    for i in range(50):
        confidence = random.uniform(0.8, 0.95)  # Normal confidence
        label = 0 if random.random() < 0.8 else 1  # Skewed towards fake
        drift_detector.add_prediction(confidence, label)
    
    # Check for drift
    result = drift_detector.check_drift()
    print(f"Drift detected: {result['drift_detected']}")
    
    # Show final statistics
    stats = drift_detector.get_drift_statistics()
    print(f"\n--- Final Statistics ---")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✅ Drift detection test completed!")
