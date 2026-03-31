"""
meta_model.py
CatBoost model wrapper for metadata-based fake news detection.
- Loads trained CatBoost model
- Provides inference interface
- Handles preprocessing and encoding
"""

import os
import sys
import pickle
import numpy as np
from catboost import CatBoostClassifier
from typing import Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.preprocessing.meta_features import extract_meta_features


class CatBoostMetaModel:
    """
    Trained CatBoost model for metadata-based fake news classification.
    Loads fine-tuned model and provides inference interface.
    """
    
    def __init__(self, model_dir: str = "models/meta_model/"):
        """
        Load trained CatBoost model and preprocessing artifacts.
        
        Args:
            model_dir (str): Path to saved model directory
        """
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "catboost_meta_model.cbm")
        self.encoder_path = os.path.join(model_dir, "domain_encoder.pkl")
        self.feature_names_path = os.path.join(model_dir, "feature_names.pkl")
        
        # Load model and artifacts
        self.model = CatBoostClassifier()
        self.model.load_model(self.model_path)
        
        with open(self.encoder_path, "rb") as f:
            self.domain_encoder = pickle.load(f)
            
        with open(self.feature_names_path, "rb") as f:
            self.feature_names = pickle.load(f)
        
        print(f"CatBoostMetaModel loaded from {model_dir}")
        print(f"Features: {self.feature_names}")
    
    def predict(self, text: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Predict fake/real news classification using metadata features.
        
        Args:
            text (str): Input text to classify
            url (Optional[str]): URL for metadata extraction
            
        Returns:
            Dict: {"label": int, "confidence": float}
                 label: 0 (fake) or 1 (real)
                 confidence: probability score (0-1)
        """
        # Extract metadata features
        sample = {"text": text, "url": url}
        meta_features = extract_meta_features(sample)
        
        # Prepare feature vector
        feature_dict = {k: v for k, v in meta_features.items() if k != "domain"}
        
        # Encode domain
        domain = meta_features["domain"]
        if domain in self.domain_encoder.classes_:
            domain_encoded = self.domain_encoder.transform([domain])[0]
        else:
            # Handle unseen domains
            domain_encoded = -1
        
        feature_dict["domain_encoded"] = domain_encoded
        
        # Create feature vector in correct order
        feature_vector = np.array([[feature_dict[name] for name in self.feature_names]])
        
        # Run inference
        probabilities = self.model.predict_proba(feature_vector)
        confidence = float(probabilities[0, 1])  # Probability of class 1 (real)
        label = int(confidence >= 0.5)
        
        return {
            "label": label,
            "confidence": confidence
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize model
    model = CatBoostMetaModel()
    
    # Test predictions
    test_cases = [
        {
            "text": "BREAKING: Scientists discover CURE for cancer in household ingredient!",
            "url": "https://suspicious-site.xyz/breaking-news"
        },
        {
            "text": "Study shows regular exercise reduces risk of heart disease by 30%.",
            "url": "https://www.medicaljournal.org/research/exercise-benefits"
        },
        {
            "text": "Short news",
            "url": None
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = model.predict(case["text"], case["url"])
        label_name = "Real" if result["label"] == 1 else "Fake"
        print(f"Test {i}: {label_name} (Confidence: {result['confidence']:.4f})")
        print(f"  Text: {case['text'][:50]}...")
        print(f"  URL: {case['url']}")
        print("-" * 50)
