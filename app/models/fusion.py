"""
fusion.py
Cross-modal attention fusion module.
- Fuses text, image, and metadata embeddings
- Implements cross-modal attention
- Modular and reusable

Tensor shape conventions:
    text_emb:    (batch_size, text_dim)
    image_emb:   (batch_size, image_dim)
    meta_emb:    (batch_size, meta_dim)
    All are projected to fusion_dim before attention.

Attention flow:
    1. Project all modalities to fusion_dim
    2. Stack: (batch_size, 3, fusion_dim)
    3. Apply multi-head self-attention across modalities (dim=3)
    4. Output: fused embedding (batch_size, fusion_dim)
"""

import torch
import torch.nn as nn
from typing import Tuple


# Weighted probability fusion for text, metadata, and image models
def weighted_fusion(text_prob: float, meta_prob: float, image_prob: float) -> float:
    """
    Combine text, metadata, and image model probabilities using weighted sum.
    final = 0.6 * text + 0.2 * meta + 0.2 * image
    Returns final probability (float).
    """
    return 0.6 * text_prob + 0.2 * meta_prob + 0.2 * image_prob
