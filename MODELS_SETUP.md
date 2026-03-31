# Model Files Setup Guide

## Overview

The trained model files are too large for GitHub (265MB+). You have two options:

## Option 1: Download Pre-trained Models (Recommended)

The model files should be placed in the following structure:

```
models/
├── text_model/
│   ├── config.json
│   ├── model.safetensors  (LARGE - not in git)
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── image_model/
│   ├── best_model.pth  (LARGE - not in git)
│   └── efficientnet_b0_model.pth  (LARGE - not in git)
└── meta_model/
    ├── catboost_meta_model.cbm  (LARGE - not in git)
    ├── domain_encoder.pkl  (LARGE - not in git)
    └── feature_names.pkl  (LARGE - not in git)
```

### Download Links

**Option A: From Google Drive / Dropbox**
1. Upload your model files to Google Drive or Dropbox
2. Share the link
3. Download and place in the `models/` directory

**Option B: From Hugging Face Hub**
1. Create account at [huggingface.co](https://huggingface.co)
2. Upload models to your repository
3. Download using:
   ```bash
   pip install huggingface_hub
   python download_models.py
   ```

**Option C: Use Git LFS (Large File Storage)**
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.pth"
git lfs track "*.cbm"
git lfs track "*.pkl"
git lfs track "*.safetensors"

# Add and commit
git add .gitattributes
git add models/
git commit -m "Add model files with LFS"
git push origin main
```

## Option 2: Train Models from Scratch

If you want to train the models yourself:

### Text Model (DistilBERT)
```bash
python scripts/train_text_model.py
```

### Image Model (EfficientNet-B0)
```bash
python scripts/train_image_model.py
```

### Metadata Model (CatBoost)
```bash
python scripts/train_meta_model.py
```

### All Models
```bash
python scripts/train_pipeline.py
```

## Verification

After setting up models, verify they load correctly:

```bash
python -c "from app.models.model_wrapper import FakeNewsDetector; detector = FakeNewsDetector(); print('Models loaded successfully!')"
```

## For Deployment

### Docker Deployment
- Models should be in the `models/` directory before building
- Docker will copy them into the container

### Cloud Deployment (Railway/Render)
- Upload models to cloud storage (S3, Google Cloud Storage)
- Download during deployment using a setup script
- Or include in Docker image

### Vercel (Frontend Only)
- Frontend doesn't need models
- Backend with models should be deployed separately

## Model File Sizes

- **text_model/model.safetensors**: ~250MB
- **image_model/efficientnet_b0_model.pth**: ~15MB
- **meta_model/catboost_meta_model.cbm**: ~1MB
- **Total**: ~266MB

## Alternative: Model Hosting Services

Consider using:
- **Hugging Face Hub**: Free model hosting
- **AWS S3**: Pay-as-you-go storage
- **Google Cloud Storage**: Free tier available
- **Azure Blob Storage**: Enterprise option

## Support

If you need help with model setup:
1. Check model file paths in code
2. Verify file permissions
3. Ensure sufficient disk space
4. Review error logs

---

**Note**: For production deployment, always use a reliable model hosting solution rather than including large files in your git repository.
