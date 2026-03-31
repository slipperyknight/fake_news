"""
drift.py
Concept drift detection module.
- Monitors feature or prediction distributions
- Triggers retraining if drift is detected
"""

import numpy as np
from scipy.stats import ks_2samp

class ConceptDriftDetector:
    """
    Detects concept drift using statistical tests (e.g., KS test).
    """
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold  # p-value threshold
        self.reference = None  # Reference distribution

    def update_reference(self, data: np.ndarray):
        """
        Set the reference distribution (e.g., from training data).
        """
        self.reference = data.copy()

    def check_drift(self, new_data: np.ndarray) -> bool:
        """
        Returns True if drift is detected (p < threshold).
        """
        if self.reference is None:
            raise ValueError("Reference distribution not set.")
        stat, p = ks_2samp(self.reference.flatten(), new_data.flatten())
        return p < self.threshold
