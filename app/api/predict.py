"""
predict.py
FastAPI endpoint for fake news prediction.
- POST /predict endpoint
- Input validation and error handling
- Integration with FakeNewsDetector
- Database storage of predictions
"""

from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict
import sys
import os
from datetime import datetime
import shutil
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.model_wrapper import FakeNewsDetector
from app.db.database import get_db
from app.drift.drift_detector import update_drift_detector, get_drift_status

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Pydantic models for request/response
class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="News text content")
    url: Optional[str] = Field(None, max_length=500, description="News URL (optional)")
    image: Optional[str] = Field(None, max_length=500, description="Image path (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Breaking: Scientists discover cure for cancer in common household ingredient",
                "url": "https://example.com/news/article",
                "image": "/path/to/image.jpg"
            }
        }


class PredictionResponse(BaseModel):
    label: int = Field(..., description="Prediction label (0=Fake, 1=Real)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    modal_contributions: Optional[Dict[str, float]] = Field(None, description="Modality contributions")
    drift_signal: Optional[float] = Field(None, description="Concept drift signal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": 0,
                "confidence": 0.9470,
                "modal_contributions": {"text": 0.8, "image": 0.2},
                "drift_signal": 0.05
            }
        }


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# Initialize router and detector (load once at startup)
router = APIRouter(prefix="/predict", tags=["prediction"])

# Global detector instance for drift detection
from app.drift.drift_detector import get_drift_detector, update_drift_detector

# Global model instance (load once at startup)
_detector = None

def get_detector():
    """Get or create global detector instance."""
    global _detector
    if _detector is None:
        from app.models.model_wrapper import FakeNewsDetector
        _detector = FakeNewsDetector()
        print("FakeNewsDetector loaded once at startup")
    return _detector


@router.post("/", response_model=PredictionResponse, responses={
    200: {"model": PredictionResponse, "description": "Successful prediction"},
    400: {"model": ErrorResponse, "description": "Invalid input"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def predict_news(request: PredictionRequest):
    """
    Predict if news text is fake or real using multimodal fusion.
    
    - **text**: News content (required, 1-10000 characters)
    - **url**: News URL (optional, max 500 characters)
    - **image**: Image path (optional, max 500 characters)
    
    Returns:
    - **label**: 0 (Fake) or 1 (Real)
    - **confidence**: Confidence score (0.0-1.0)
    - **modal_contributions**: Individual modality contributions
    - **drift_signal**: Concept drift indicator
    """
    try:
        # Get global detector instance (loaded once at startup)
        detector = get_detector()
        
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and cannot be empty"
            )
        
        # Call detector with all available modalities
        result = detector.predict(
            text=request.text.strip(),
            url=request.url,
            image=request.image
        )
        
        # Extract prediction and fusion details
        prediction = result["prediction"]
        fusion = result["fusion"]
        
        # Calculate drift signal using drift detector
        drift_status = get_drift_status()
        drift_signal = drift_status["drift_signal"]
        
        # Update drift detector with this prediction
        from app.drift.drift_detector import update_drift_detector
        update_drift_detector({
            "label": prediction["label"],
            "confidence": prediction["confidence"]
        })
        
        # Store prediction in database
        try:
            db = get_db()
            is_high_confidence = prediction["confidence"] > 0.85
            
            db.insert_prediction(
                text=request.text.strip(),
                predicted_label=prediction["label"],
                confidence=prediction["confidence"],
                url=request.url,
                text_score=fusion.get("text_prob", 0.0),
                meta_score=fusion.get("meta_prob", 0.0),
                is_high_confidence=is_high_confidence,
                is_used_for_training=False
            )
        except Exception as db_error:
            print(f"Database storage failed: {db_error}")
        
        return PredictionResponse(
            label=prediction["label"],
            confidence=prediction["confidence"],
            modal_contributions={
                "text": fusion.get("text_prob", 0.0),
                "metadata": fusion.get("meta_prob", 0.0),
                "image": fusion.get("image_prob", 0.0)
            },
            drift_signal=drift_signal
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/drift-status", responses={
    200: {"description": "Current drift status"},
    500: {"description": "Internal server error"}
})
async def drift_status():
    """
    Get current concept drift status.
    
    Returns:
        Dict: Current drift information including signal, threshold, and statistics
    """
    try:
        from app.drift.drift_detector import get_drift_status
        drift_info = get_drift_status()
        
        return {
            "status": "available",
            "drift_signal": drift_info["drift_signal"],
            "drift_flagged": drift_info["drift_flagged"],
            "threshold": drift_info["threshold"],
            "window_size": drift_info["window_size"],
            "total_predictions": drift_info["total_predictions"],
            "statistics": drift_info["statistics"],
            "last_drift_time": drift_info["last_drift_time"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get drift status: {str(e)}"
        )


@router.get("/health", responses={
    200: {"description": "Service is healthy"}
})
async def health_check():
    """
    Health check endpoint for the prediction service.
    """
    return {"status": "healthy", "model": "FakeNewsDetector"}


@router.get("/info", responses={
    200: {"description": "Model information"}
})
async def model_info():
    """
    Get information about available models.
    """
    try:
        # Get global detector instance
        detector = get_detector()
        info = detector.get_model_info()
        return {
            "status": "available",
            "models": info["available_models"],
            "capabilities": info["capabilities"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/multimodal", responses={
    200: {"description": "Successful prediction with image"},
    400: {"description": "Invalid input"},
    500: {"description": "Internal server error"}
})
async def predict_multimodal(
    text: str = Form(..., description="News text content"),
    url: Optional[str] = Form(None, description="News URL (optional)"),
    image: Optional[UploadFile] = File(None, description="Image file (optional)")
):
    """
    Predict fake news with multimodal input including image upload.
    
    - **text**: News content (required)
    - **url**: News URL (optional)
    - **image**: Image file upload (optional, jpg/png/jpeg)
    
    Returns prediction with all modality contributions.
    """
    image_path = None
    
    try:
        # Validate text input
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and cannot be empty"
            )
        
        # Handle image upload if provided
        if image:
            # Validate file type
            allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            file_ext = os.path.splitext(image.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image format. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Save uploaded file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{image.filename}"
            image_path = UPLOAD_DIR / safe_filename
            
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            print(f"Image uploaded: {image_path}")
        
        # Get detector and make prediction
        detector = get_detector()
        result = detector.predict(
            text=text.strip(),
            url=url,
            image=str(image_path) if image_path else None
        )
        
        # Extract prediction and fusion details
        prediction = result["prediction"]
        fusion = result["fusion"]
        
        # Get drift status
        drift_status = get_drift_status()
        drift_signal = drift_status["drift_signal"]
        
        # Update drift detector
        update_drift_detector({
            "label": prediction["label"],
            "confidence": prediction["confidence"]
        })
        
        # Store prediction in database
        try:
            db = get_db()
            is_high_confidence = prediction["confidence"] > 0.85
            
            db.insert_prediction(
                text=text.strip(),
                predicted_label=prediction["label"],
                confidence=prediction["confidence"],
                url=url,
                text_score=fusion.get("text_prob", 0.0),
                meta_score=fusion.get("meta_prob", 0.0),
                is_high_confidence=is_high_confidence,
                is_used_for_training=False
            )
        except Exception as db_error:
            print(f"Database storage failed: {db_error}")
        
        # Clean up uploaded image after processing
        if image_path and image_path.exists():
            try:
                os.remove(image_path)
                print(f"Cleaned up uploaded image: {image_path}")
            except Exception as e:
                print(f"Failed to clean up image: {e}")
        
        return {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "modal_contributions": {
                "text": fusion.get("text_prob", 0.0),
                "metadata": fusion.get("meta_prob", 0.0),
                "image": fusion.get("image_prob", 0.0)
            },
            "drift_signal": drift_signal,
            "modalities_used": {
                "text": result["modalities"]["text"]["used"],
                "metadata": result["modalities"]["metadata"]["used"],
                "image": result["modalities"]["image"]["used"]
            }
        }
        
    except HTTPException:
        # Clean up on error
        if image_path and image_path.exists():
            os.remove(image_path)
        raise
        
    except Exception as e:
        # Clean up on error
        if image_path and image_path.exists():
            os.remove(image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
