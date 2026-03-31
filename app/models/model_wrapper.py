"""
model_wrapper.py
Unified wrapper for fake news detection models.
- Integrates text, metadata, and image models
- Provides single API for multimodal predictions
- Designed for extensibility
"""

import sys
import os
from typing import Optional, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.models.text_model import TextModel
from app.models.meta_model import CatBoostMetaModel
from app.models.image_model import ImageModel


class FakeNewsDetector:
    """
    Unified fake news detection system.
    Integrates text and metadata models with weighted fusion.
    """
    
    def __init__(self):
        """Initialize all available models."""
        # Load text model
        self.text_model = TextModel()
        
        # Load metadata model
        try:
            self.metadata_model = CatBoostMetaModel()
            metadata_available = True
        except Exception as e:
            print(f"Metadata model not available: {e}")
            self.metadata_model = None
            metadata_available = False
        
        # Load image model
        try:
            self.image_model = ImageModel()
            image_available = self.image_model.load()
        except Exception as e:
            print(f"Image model not available: {e}")
            self.image_model = None
            image_available = False
        
        print("FakeNewsDetector initialized:")
        print(f"  Text model: ✅ Available")
        print(f"  Metadata model: {'✅' if metadata_available else '❌'} Available")
        print(f"  Image model: {'✅' if image_available else '❌'} Available")
    
    def predict(self, text: str, url: Optional[str] = None, image: Optional[Any] = None) -> Dict[str, Any]:
        """
        Predict fake news using available modalities with weighted fusion.
        
        Args:
            text (str): News text content (required)
            url (Optional[str]): News URL for metadata extraction
            image (Optional[Any]): Image data (path, PIL Image, etc.)
            
        Returns:
            Dict containing prediction results and metadata
        """
        if not text or not text.strip():
            raise ValueError("Text content is required for prediction")
        
        # Text prediction (always available)
        text_result = self.text_model.predict(text)
        text_prob = text_result["confidence"] if text_result["label"] == 1 else (1 - text_result["confidence"])
        
        # Metadata prediction (if available)
        meta_prob = 0.5  # Default neutral probability
        meta_result = None
        if url and self.metadata_model:
            try:
                meta_result = self.metadata_model.predict(text, url)
                meta_prob = meta_result["confidence"] if meta_result["label"] == 1 else (1 - meta_result["confidence"])
            except Exception as e:
                print(f"Metadata prediction failed: {e}")
        
        # Image prediction (if available)
        image_prob = 0.5  # Default neutral probability
        image_result = None
        if image and self.image_model:
            try:
                if isinstance(image, str):
                    image_result = self.image_model.predict(image)
                else:
                    # Handle PIL Image or other formats
                    import tempfile
                    import os
                    # Save PIL Image to temp file
                    if hasattr(image, 'save'):
                        temp_path = tempfile.mktemp(suffix='.jpg')
                        image.save(temp_path)
                        image_result = self.image_model.predict(temp_path)
                        os.unlink(temp_path)
                    else:
                        image_result = {"error": "Unsupported image format", "label": -1, "confidence": 0.0}
                
                if "error" not in image_result:
                    image_prob = image_result["confidence"] if image_result["label"] == 1 else (1 - image_result["confidence"])
            except Exception as e:
                print(f"Image prediction failed: {e}")
        
        # Weighted fusion with updated weights
        if image_result and "error" not in image_result:
            # All modalities available: 80% text, 15% metadata, 5% image
            final_prob = 0.8 * text_prob + 0.15 * meta_prob + 0.05 * image_prob
        else:
            # Text and metadata only: 75% text, 25% metadata
            final_prob = 0.75 * text_prob + 0.25 * meta_prob
        
        final_label = int(final_prob >= 0.5)
        final_confidence = max(final_prob, 1 - final_prob)  # Distance from decision boundary
        
        # Build result structure
        result = {
            "prediction": {
                "label": final_label,
                "confidence": final_confidence,
                "label_name": "Real" if final_label == 1 else "Fake"
            },
            "fusion": {
                "text_weight": 0.8 if image_result else 0.75,
                "meta_weight": 0.15 if image_result else 0.25,
                "image_weight": 0.05 if image_result else 0.0,
                "text_prob": text_prob,
                "meta_prob": meta_prob,
                "image_prob": image_prob,
                "final_prob": final_prob
            },
            "modalities": {
                "text": {
                    "used": True,
                    "result": text_result
                },
                "metadata": {
                    "used": bool(meta_result),
                    "result": meta_result,
                    "message": None if meta_result else "Metadata model not available"
                },
                "image": {
                    "used": bool(image_result and "error" not in image_result),
                    "result": image_result,
                    "message": None if (image_result and "error" not in image_result) else "Image model not available or failed"
                }
            },
            "input_info": {
                "has_text": bool(text and text.strip()),
                "has_url": bool(url),
                "has_image": bool(image),
                "text_length": len(text) if text else 0
            }
        }
        
        return result
    
    def _predict_image(self, image: Any) -> Dict[str, Any]:
        """
        Placeholder for image prediction.
        
        Args:
            image: Image data (path, PIL Image, etc.)
            
        Returns:
            Dict: Image-based prediction
        """
        # TODO: Implement image model integration
        return {
            "label": 0,
            "confidence": 0.5,
            "features": {}
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available models.
        
        Returns:
            Dict: Model status and capabilities
        """
        image_available = self.image_model is not None
        
        return {
            "available_models": {
                "text": True,
                "metadata": self.metadata_model is not None,
                "image": image_available
            },
            "model_details": {
                "text": {
                    "type": "DistilBERT",
                    "trained": True,
                    "accuracy": 0.87
                },
                "metadata": {
                    "type": "CatBoost",
                    "trained": self.metadata_model is not None,
                    "features": ["text_length", "word_count", "uppercase_word_count", "domain_encoded"]
                },
                "image": {
                    "type": "EfficientNet-B0",
                    "trained": image_available,
                    "accuracy": 1.00 if image_available else None
                }
            },
            "fusion_weights": {
                "text": 0.8,
                "metadata": 0.15,
                "image": 0.05
            },
            "capabilities": [
                "Text-based fake news detection",
                "Metadata-based fake news detection", 
                "Image-based fake news detection",
                "Weighted multimodal fusion",
                "Confidence scoring",
                "Extensible architecture"
            ]
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize detector
    detector = FakeNewsDetector()
    
    # Test predictions
    test_cases = [
        {
            "text": "Breaking: Scientists discover cure for cancer in common household ingredient",
            "url": "https://fake-news.example.com/cure-found",
            "image": None
        },
        {
            "text": "Study shows regular exercise reduces risk of heart disease by 30%",
            "url": None,
            "image": None
        },
        {
            "text": "Celebrity spotted at local grocery store buying vegetables",
            "url": "https://gossip.example.com/celebrity-grocery",
            "image": None
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        result = detector.predict(
            text=case["text"],
            url=case.get("url"),
            image=case.get("image")
        )
        
        print(f"Prediction: {result['prediction']['label_name']} "
              f"(Confidence: {result['prediction']['confidence']:.4f})")
        print(f"Fusion: Text={result['fusion']['text_prob']:.3f}, "
              f"Meta={result['fusion']['meta_prob']:.3f}, "
              f"Final={result['fusion']['final_prob']:.3f}")
        print(f"Modalities used: {[k for k, v in result['modalities'].items() if v['used']]}")
        print(f"Text length: {result['input_info']['text_length']} chars")
    
    # Show model info
    print("\n--- Model Information ---")
    info = detector.get_model_info()
    print(f"Available models: {list(info['available_models'].keys())}")
    print(f"Fusion weights: {info['fusion_weights']}")
    print(f"Capabilities: {', '.join(info['capabilities'])}")
