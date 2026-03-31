"""
meta_features.py
Extract metadata features from news articles for fake news detection.
- URL domain extraction
- Text statistics
- Linguistic features
"""

import re
import string
from urllib.parse import urlparse
from typing import Dict, Any, Optional


def extract_domain(url: Optional[str]) -> str:
    """
    Extract domain from URL.
    
    Args:
        url (Optional[str]): URL string
        
    Returns:
        str: Domain name or 'unknown' if invalid
    """
    if not url or not isinstance(url, str):
        return "unknown"
    
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain if domain else "unknown"
    except Exception:
        return "unknown"


def extract_text_features(text: str) -> Dict[str, Any]:
    """
    Extract text-based features.
    
    Args:
        text (str): Input text
        
    Returns:
        Dict: Text statistics
    """
    if not text or not isinstance(text, str):
        return {
            "text_length": 0,
            "word_count": 0,
            "uppercase_word_count": 0
        }
    
    # Basic counts
    text_length = len(text.strip())
    words = text.split()
    word_count = len(words)
    
    # Uppercase words (excluding first word of sentences)
    uppercase_words = [word for word in words if word.isupper() and len(word) > 1]
    uppercase_word_count = len(uppercase_words)
    
    return {
        "text_length": text_length,
        "word_count": word_count,
        "uppercase_word_count": uppercase_word_count
    }


def extract_meta_features(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts domain, text length, word count, and uppercase words from a sample.
    Returns a dict of numeric features.
    
    Args:
        sample (Dict): Dictionary containing 'text' and 'url'
        
    Returns:
        Dict: Extracted features
    """
    url = sample.get("url")
    text = sample.get("text", "")
    
    # Extract text features
    text_features = extract_text_features(text)
    
    # Extract domain
    domain = extract_domain(url)
    
    # Combine all features
    return {
        "domain": domain,
        **text_features
    }


# Example usage and testing
if __name__ == "__main__":
    # Test examples
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
    
    print("Metadata Feature Extraction Test")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Text: {case['text'][:50]}...")
        print(f"URL: {case['url']}")
        
        features = extract_meta_features(case)
        
        print(f"Domain: {features['domain']}")
        print(f"Text length: {features['text_length']}")
        print(f"Word count: {features['word_count']}")
        print(f"Uppercase words: {features['uppercase_word_count']}")
        print("-" * 30)
