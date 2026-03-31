"""
image_dataset.py
PyTorch Dataset for image data in fake news detection.
- Loads images and labels
- Applies transforms (resize, normalize)
- Returns tensors
"""

import os
import json
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as T

class FakeNewsImageDataset(Dataset):
    def __init__(self, split: str = "train", data_dir: str = "data/processed/", img_dir: str = "data/images/", transform=None):
        self.samples = []
        self.img_dir = img_dir
        path = os.path.join(data_dir, f"{split}.json")
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                sample = json.loads(line)
                url = sample.get("url", "")
                label = sample.get("label", 0)
                if not url:
                    continue
                fname = self.url_to_filename(url)
                img_path = os.path.join(img_dir, fname)
                if os.path.exists(img_path):
                    self.samples.append({"img_path": img_path, "label": label})
        self.transform = transform or T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        img = Image.open(sample["img_path"]).convert("RGB")
        img = self.transform(img)
        label = sample["label"]
        return {"image": img, "label": label}

    @staticmethod
    def url_to_filename(url):
        import hashlib
        return hashlib.md5(url.encode("utf-8")).hexdigest() + ".jpg"
