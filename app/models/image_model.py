"""
image_model.py
EfficientNet-B0 model for fake news image classification.
- Loads trained EfficientNet-B0 model
- Handles image preprocessing and inference
- Returns predictions with confidence scores
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import os
from typing import Union, List, Dict, Any


class ImageModel:
    """
    EfficientNet-B0 model for fake news image classification.
    Handles loading, preprocessing, and inference.
    """
    
    def __init__(self, model_path: str = "models/image_model/efficientnet_b0_model.pth"):
        """
        Initialize ImageModel with EfficientNet-B0.
        
        Args:
            model_path (str): Path to trained model file
        """
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.preprocess = None
        
        # Initialize preprocessing
        self._setup_preprocessing()
        
        print(f"ImageModel initialized:")
        print(f"  Model path: {model_path}")
        print(f"  Device: {self.device}")
    
    def _setup_preprocessing(self):
        """Setup image preprocessing for EfficientNet-B0."""
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        print("Image preprocessing setup complete (224x224, ImageNet normalization)")
    
    def load(self):
        """
        Load the trained EfficientNet-B0 model.
        """
        try:
            if os.path.exists(self.model_path):
                # Load with weights_only=False to handle PyTorch compatibility
                self.model = torch.load(self.model_path, map_location=self.device, weights_only=False)
                self.model.to(self.device)
                self.model.eval()
                
                print(f"✅ Model loaded successfully from {self.model_path}")
                print(f"   Model type: {type(self.model)}")
                print(f"   Device: {next(self.model.parameters()).device}")
            else:
                print(f"❌ Model file not found: {self.model_path}")
                print("   Please train the model first using scripts/train_image_model.py")
                return False
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            # Try alternative loading method
            try:
                print("Attempting alternative loading method...")
                self.model = torch.load(self.model_path, map_location=self.device)
                self.model.to(self.device)
                self.model.eval()
                print(f"✅ Model loaded successfully with alternative method")
                return True
            except Exception as e2:
                print(f"❌ Alternative loading also failed: {e2}")
                return False
        
        return True
    
    def load_image(self, image_path: str) -> Image.Image:
        """
        Load and validate image from file path.
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            PIL.Image: Loaded RGB image
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            image = Image.open(image_path).convert("RGB")
            return image
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            # Return a dummy black image if loading fails
            return Image.new('RGB', (224, 224), (0, 0, 0))
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess a PIL image for EfficientNet-B0.
        
        Args:
            image (PIL.Image): Input image
            
        Returns:
            torch.Tensor: Preprocessed tensor
        """
        return self.preprocess(image)
    
    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Predict fake/real news from image.
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            Dict: Prediction results with label and confidence
        """
        if self.model is None:
            return {
                "error": "Model not loaded. Call load() first.",
                "label": -1,
                "confidence": 0.0
            }
        
        try:
            # Load and preprocess image
            image = self.load_image(image_path)
            image_tensor = self.preprocess_image(image)
            image_tensor = image_tensor.unsqueeze(0).to(self.device)  # Add batch dimension
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, dim=1)
                
                # Convert to numpy for easier handling
                confidence_score = confidence.item()
                predicted_label = predicted.item()
                
                # Create result dictionary
                result = {
                    "label": int(predicted_label),
                    "confidence": float(confidence_score),
                    "probabilities": {
                        "fake": float(probabilities[0][0]),
                        "real": float(probabilities[0][1])
                    },
                    "image_path": image_path,
                    "prediction": "real" if predicted_label == 1 else "fake"
                }
                
                return result
                
        except Exception as e:
            return {
                "error": f"Prediction failed: {str(e)}",
                "label": -1,
                "confidence": 0.0
            }
    
    def predict_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Predict fake/real news from multiple images.
        
        Args:
            image_paths (List[str]): List of image file paths
            
        Returns:
            List[Dict]: List of prediction results
        """
        results = []
        
        for image_path in image_paths:
            result = self.predict(image_path)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dict: Model information
        """
        if self.model is None:
            return {
                "loaded": False,
                "model_path": self.model_path,
                "device": str(self.device)
            }
        
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            "loaded": True,
            "model_path": self.model_path,
            "device": str(self.device),
            "model_type": "EfficientNet-B0",
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "input_size": (224, 224),
            "num_classes": 2,
            "class_names": ["fake", "real"]
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize model
    image_model = ImageModel("models/image_model/efficientnet_b0_model.pth")
    
    # Load model
    if image_model.load():
        print("\n✅ Model loaded successfully!")
        
        # Get model info
        info = image_model.get_model_info()
        print(f"\n📋 Model Information:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # Test prediction on sample image
        test_image_path = "data/images/dove-cameron-shield.png.jpg"
        
        if os.path.exists(test_image_path):
            print(f"\n🔍 Testing prediction on: {test_image_path}")
            result = image_model.predict(test_image_path)
            
            print(f"📊 Prediction Results:")
            print(f"   Label: {result['label']} ({result['prediction']})")
            print(f"   Confidence: {result['confidence']:.4f}")
            print(f"   Probabilities: Fake={result['probabilities']['fake']:.4f}, Real={result['probabilities']['real']:.4f}")
        else:
            print(f"\n❌ Test image not found: {test_image_path}")
            print("   Available images in data/images/:")
            if os.path.exists("data/images/"):
                images = os.listdir("data/images/")[:5]  # Show first 5
                for img in images:
                    print(f"   - {img}")
    else:
        print(f"\n❌ Failed to load model!")
