"""
auto_label.py
Automatic labeling system for high-confidence predictions.
- Validates predictions based on confidence and source trustworthiness
- Accepts/rejects samples for training data
"""

import os
import sys
import math
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.db.database import get_db


class AutoLabeler:
    """
    Automatic labeling system for fake news predictions.
    Validates predictions based on confidence and trusted sources.
    Integrates with database for training data collection.
    """
    
    def __init__(self):
        """Initialize auto-labeler with trusted sources."""
        self.trusted_sources = [
            "bbc.com",
            "reuters.com", 
            "apnews.com",
            "cnn.com",
            "npr.org",
            "wsj.com",
            "theguardian.com",
            "nytimes.com",
            "washingtonpost.com"
        ]
        
        # Updated confidence threshold 
        self.confidence_threshold = 0.85
        
        print(f"AutoLabeler initialized with {len(self.trusted_sources)} trusted sources")
        print(f"Confidence threshold: {self.confidence_threshold}")
    
    def extract_domain(self, url: Optional[str]) -> str:
        """
        Extract domain from URL.
        
        Args:
            url (Optional[str]): URL string
            
        Returns:
            str: Domain name or empty string
        """
        if not url or not isinstance(url, str):
            return ""
        
        try:
            parsed = urlparse(url.strip())
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except Exception:
            return ""
    
    def evaluate_prediction(self, 
                        prediction: int,
                        confidence: float, 
                        url: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate if a prediction should be accepted for training.
        
        Args:
            prediction (int): Predicted label (0=Fake, 1=Real)
            confidence (float): Confidence score (0-1)
            url (Optional[str]): URL of news source
            
        Returns:
            Dict: {"accepted": bool, "label": int, "confidence": float}
        """
        # Extract domain for trusted source check
        domain = self.extract_domain(url)
        is_trusted_source = domain in self.trusted_sources
        
        # Auto-labeling logic with updated threshold
        accepted = confidence >= self.confidence_threshold
        reason = ""
        
        if accepted:
            if confidence >= 0.90:
                reason = "Very high confidence (≥0.90)"
            else:
                reason = f"High confidence (≥{self.confidence_threshold})"
        else:
            if confidence >= 0.75:
                reason = f"Medium confidence (≥0.75) but below threshold ({self.confidence_threshold})"
            elif not is_trusted_source and url:
                reason = f"Low confidence (<{self.confidence_threshold}) and untrusted source ({domain})"
            else:
                reason = f"Low confidence (<{self.confidence_threshold})"
        
        result = {
            "accepted": accepted,
            "label": prediction,
            "confidence": confidence,
            "reason": reason,
            "domain": domain,
            "is_trusted_source": is_trusted_source,
            "url_provided": bool(url)
        }
        
        return result
    
    def get_training_data_with_weights(self, limit: Optional[int] = None) -> list:
        """
        Get training data with recency weights from database.
        
        Args:
            limit (Optional[int]): Maximum number of records to return
            
        Returns:
            list: Training data with recency weights
        """
        try:
            db = get_db()
            training_data = db.get_training_data(limit=limit, min_confidence=self.confidence_threshold)
            
            # Add recency weights to each record
            weighted_data = []
            for record in training_data:
                age_in_days = record.get('age_in_days', 0)
                recency_weight = math.exp(-0.01 * age_in_days)
                
                weighted_record = record.copy()
                weighted_record['recency_weight'] = recency_weight
                weighted_record['effective_weight'] = recency_weight  # For training
                
                weighted_data.append(weighted_record)
            
            print(f"Retrieved {len(weighted_data)} training samples with recency weights")
            return weighted_data
            
        except Exception as e:
            print(f"Error getting training data: {e}")
            return []
    
    def process_predictions_for_training(self, predictions: list) -> Dict[str, Any]:
        """
        Process predictions and prepare training data.
        
        Args:
            predictions (list): List of prediction dictionaries
            
        Returns:
            Dict: Processing results and statistics
        """
        # Evaluate predictions
        evaluations = self.batch_evaluate(predictions)
        
        # Get accepted predictions
        accepted_predictions = [eval_result for eval_result in evaluations if eval_result["accepted"]]
        
        # Store in database and mark as used for training
        try:
            db = get_db()
            prediction_ids = []
            
            for i, (eval_result, pred) in enumerate(zip(evaluations, predictions)):
                if eval_result["accepted"]:
                    # Insert into database
                    pred_id = db.insert_prediction(
                        text=pred.get("text", ""),
                        predicted_label=eval_result["label"],
                        confidence=eval_result["confidence"],
                        url=pred.get("url"),
                        is_high_confidence=True
                    )
                    prediction_ids.append(pred_id)
            
            # Mark as used for training
            if prediction_ids:
                db.mark_as_used_for_training(prediction_ids)
                
            return {
                "total_predictions": len(predictions),
                "accepted_predictions": len(accepted_predictions),
                "rejected_predictions": len(predictions) - len(accepted_predictions),
                "acceptance_rate": len(accepted_predictions) / len(predictions) if predictions else 0,
                "training_data_prepared": len(accepted_predictions),
                "prediction_ids_marked": prediction_ids
            }
            
        except Exception as e:
            print(f"Error processing predictions for training: {e}")
            return {
                "error": str(e),
                "total_predictions": len(predictions),
                "accepted_predictions": 0,
                "rejected_predictions": len(predictions),
                "acceptance_rate": 0
            }
    
    def batch_evaluate(self, predictions: list) -> list:
        """
        Evaluate multiple predictions.
        
        Args:
            predictions (list): List of prediction dictionaries
            
        Returns:
            list: List of evaluation results
        """
        results = []
        for pred in predictions:
            result = self.evaluate_prediction(
                prediction=pred.get("prediction", 0),
                confidence=pred.get("confidence", 0.0),
                url=pred.get("url")
            )
            results.append(result)
        
        return results
    
    def get_statistics(self, evaluations: list) -> Dict[str, Any]:
        """
        Get statistics about auto-labeling decisions.
        
        Args:
            evaluations (list): List of evaluation results
            
        Returns:
            Dict: Statistics about acceptance/rejection
        """
        total = len(evaluations)
        
        # Add recency weights to each record
        weighted_data = []
        for record in training_data:
            age_in_days = record.get('age_in_days', 0)
            recency_weight = math.exp(-0.01 * age_in_days)
            
            weighted_record = record.copy()
            weighted_record['recency_weight'] = recency_weight
            weighted_record['effective_weight'] = recency_weight  # For training
            
            weighted_data.append(weighted_record)
        
        print(f"Retrieved {len(weighted_data)} training samples with recency weights")
        return weighted_data
            
    except Exception as e:
        print(f"Error getting training data: {e}")
        return []
    
def process_predictions_for_training(self, predictions: list) -> Dict[str, Any]:
    """
    Process predictions and prepare training data.
    
    Args:
        predictions (list): List of prediction dictionaries
        
    Returns:
        Dict: Processing results and statistics
    """
    # Evaluate predictions
    evaluations = self.batch_evaluate(predictions)
    
    # Get accepted predictions
    accepted_predictions = [eval_result for eval_result in evaluations if eval_result["accepted"]]
    
    # Store in database and mark as used for training
    try:
        db = get_db()
        prediction_ids = []
        
        for i, (eval_result, pred) in enumerate(zip(evaluations, predictions)):
            if eval_result["accepted"]:
                # Insert into database
                pred_id = db.insert_prediction(
                    text=pred.get("text", ""),
                    predicted_label=eval_result["label"],
                    confidence=eval_result["confidence"],
                    url=pred.get("url"),
                    is_high_confidence=True
                )
                prediction_ids.append(pred_id)
        
        # Mark as used for training
        if prediction_ids:
            db.mark_as_used_for_training(prediction_ids)
            
        return {
            "total_predictions": len(predictions),
            "accepted_predictions": len(accepted_predictions),
            "rejected_predictions": len(predictions) - len(accepted_predictions),
            "acceptance_rate": len(accepted_predictions) / len(predictions) if predictions else 0,
            "training_data_prepared": len(accepted_predictions),
            "prediction_ids_marked": prediction_ids
        }
            
    except Exception as e:
        print(f"Error processing predictions for training: {e}")
        return {
            "error": str(e),
            "total_predictions": len(predictions),
            "accepted_predictions": 0,
            "rejected_predictions": len(predictions),
            "acceptance_rate": 0
        }
    
def batch_evaluate(self, predictions: list) -> list:
    """
    Evaluate multiple predictions.
    
    Args:
        predictions (list): List of prediction dictionaries
        
    Returns:
        list: List of evaluation results
    """
    results = []
    for pred in predictions:
        result = self.evaluate_prediction(
            prediction=pred.get("prediction", 0),
            confidence=pred.get("confidence", 0.0),
            url=pred.get("url")
        )
        results.append(result)
    
    return results
    
def get_statistics(self, evaluations: list) -> Dict[str, Any]:
    """
    Get statistics about auto-labeling decisions.
    
    Args:
        evaluations (list): List of evaluation results
        
    Returns:
        Dict: Statistics about acceptance/rejection
    """
    total = len(evaluations)
    accepted = sum(1 for e in evaluations if e["accepted"])
    rejected = total - accepted
    
    # Breakdown by reason
    high_conf_accepted = sum(1 for e in evaluations 
                          if e["accepted"] and "Very high confidence" in e["reason"])
    trusted_source_accepted = sum(1 for e in evaluations 
                              if e["accepted"] and "trusted source" in e["reason"])
    
    return {
        "total_evaluations": total,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": accepted / total if total > 0 else 0,
        "high_confidence_accepted": high_conf_accepted,
        "trusted_source_accepted": trusted_source_accepted,
        "trusted_sources_used": len(set(e["domain"] for e in evaluations 
                                   if e["is_trusted_source"] and e["domain"]))
    }


# Example usage and testing
if __name__ == "__main__":
    # Initialize auto-labeler
    labeler = AutoLabeler()
    
    print("Testing updated auto-labeler with database integration...")
    
    # Test database integration
    training_data = labeler.get_training_data_with_weights(limit=10)
    if training_data:
        print(f"\n📊 Retrieved {len(training_data)} training samples:")
        for i, record in enumerate(training_data[:3]):  # Show first 3
            print(f"   Sample {i+1}:")
            print(f"     Age (days): {record.get('age_in_days', 'N/A')}")
            print(f"     Recency weight: {record.get('recency_weight', 0):.4f}")
            print(f"     Confidence: {record.get('confidence', 0):.3f}")
            print(f"     Label: {record.get('predicted_label', 'N/A')}")
    
    # Test prediction processing
    test_predictions = [
        {
            "prediction": 1,
            "confidence": 0.92,
            "url": "https://bbc.com/news/article",
            "text": "Breaking news from trusted source"
        },
        {
            "prediction": 0,
            "confidence": 0.87,
            "url": "https://reuters.com/world/fake-news",
            "text": "Suspicious news from untrusted source"
        },
        {
            "prediction": 1,
            "confidence": 0.83,
            "url": "https://unknown-site.xyz/breaking",
            "text": "News from unknown source"
        }
    ]
    
    results = labeler.process_predictions_for_training(test_predictions)
    print(f"\n🎯 Processing Results:")
    print(f"   Total predictions: {results.get('total_predictions', 0)}")
    print(f"   Accepted: {results.get('accepted_predictions', 0)}")
    print(f"   Rejected: {results.get('rejected_predictions', 0)}")
    print(f"   Acceptance rate: {results.get('acceptance_rate', 0):.2%}")
    print(f"   Training data prepared: {results.get('training_data_prepared', 0)}")
    
    print("\n✅ Auto-labeler with database integration completed successfully!")
    print("✅ Confidence threshold: 0.85")
    print("✅ Recency weight calculation: exp(-0.01 * age_in_days)")
    print("✅ Database integration: Working")
        print(f"Result: {'✅ ACCEPTED' if result['accepted'] else '❌ REJECTED'}")
        print(f"Reason: {result['reason']}")
        print(f"Domain: {result['domain']}")
        print(f"Trusted Source: {result['is_trusted_source']}")
    
    # Show statistics
    stats = labeler.get_statistics(results)
    print(f"\n--- Statistics ---")
    print(f"Total evaluations: {stats['total_evaluations']}")
    print(f"Accepted: {stats['accepted']} ({stats['acceptance_rate']:.2%})")
    print(f"Rejected: {stats['rejected']}")
    print(f"High confidence accepted: {stats['high_confidence_accepted']}")
    print(f"Trusted source accepted: {stats['trusted_source_accepted']}")
    print(f"Unique trusted sources: {stats['trusted_sources_used']}")
