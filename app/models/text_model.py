"""
text_model.py
DistilBERT model wrapper for fake news detection.
- Loads trained model and tokenizer
- Provides fast inference interface
- Returns predictions with confidence scores
"""

import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer, DistilBertModel
import os


class TextModel:
    """
    Trained DistilBERT model for fake news classification.
    Loads fine-tuned model and provides inference interface.
    """
    def __init__(self, model_dir: str = "models/text_model/"):
        """
        Load trained DistilBERT model and tokenizer.
        
        Args:
            model_dir (str): Path to saved model directory
        """
        self.device = torch.device("cpu")  # CPU compatibility
        self.model_dir = model_dir
        
        # Load model and tokenizer
        self.model = DistilBertForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_dir)
        
        print(f"TextModel loaded from {model_dir}")
    
    def predict(self, text: str) -> dict:
        """
        Predict fake/real news classification.
        
        Args:
            text (str): Input text to classify
            
        Returns:
            dict: {"label": int, "confidence": float}
                 label: 0 (fake) or 1 (real)
                 confidence: probability score (0-1)
        """
        # Tokenize input text
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=64,
            return_tensors="pt"
        )
        
        # Move to device
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            # Apply softmax to get probabilities
            probabilities = torch.softmax(logits, dim=1)
            confidence, predicted_class = torch.max(probabilities, dim=1)
            
            # Convert to Python types
            label = predicted_class.cpu().item()
            confidence_score = confidence.cpu().item()
            
        return {
            "label": label,
            "confidence": confidence_score
        }


class DistilBERTTextEncoder:
    """
    Encapsulates DistilBERT loading, tokenization, and embedding extraction.
    For feature extraction purposes (not classification).
    """
    def __init__(self, model_name: str = "distilbert-base-uncased", device: torch.device = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        self.model = DistilBertModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def tokenize(self, texts, max_length: int = 256):
        """
        Tokenize input text(s) for DistilBERT.
        """
        return self.tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )

    @torch.no_grad()
    def encode(self, texts, max_length: int = 256) -> torch.Tensor:
        """
        Extract [CLS] embeddings for input text(s).
        Returns: Tensor of shape (batch_size, hidden_size)
        """
        tokens = self.tokenize(texts, max_length)
        tokens = {k: v.to(self.device) for k, v in tokens.items()}
        outputs = self.model(**tokens)
        # Use the first token ([CLS]) as sentence embedding
        return outputs.last_hidden_state[:, 0, :]
