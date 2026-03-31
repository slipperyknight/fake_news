"""
dataset.py
PyTorch Dataset for multimodal fake news detection.
- Loads JSON lines from data/processed/
- Tokenizes text using DistilBERT tokenizer
- Returns input_ids, attention_mask, label
- Supports train/val/test modes
"""

import os
import json
import torch
from torch.utils.data import Dataset
from transformers import DistilBertTokenizer

class FakeNewsTextDataset(Dataset):
    def __init__(self, split: str = "train", data_dir: str = "data/processed/", max_length: int = 64):
        assert split in {"train", "val", "test"}, "split must be 'train', 'val', or 'test'"
        self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased", use_fast=True)
        self.data_path = os.path.join(data_dir, f"{split}.json")
        self.max_length = max_length
        
        # Load file paths and cache sample count
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.num_samples = sum(1 for _ in f)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Read only the specific line needed
        with open(self.data_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == idx:
                    sample = json.loads(line)
                    break
        
        text = sample["text"]
        label = sample["label"]
        encoding = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long)
        }
