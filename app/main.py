# app/main.py
"""
Entry point for FastAPI application.
Production-ready with optimized model loading and CORS support.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import predict

# Initialize FastAPI with production configuration
app = FastAPI(
    title="Multimodal Fake News Detection API",
    description="Production-ready multimodal fake news detection with text, metadata, and image analysis",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include prediction router
app.include_router(predict.router)

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Returns basic API status and configuration.
    """
    return {
        "status": "ok",
        "api_version": "1.0.0",
        "models_loaded": True,
        "endpoints": {
            "predict": "POST /predict/",
            "health": "GET /health",
            "info": "GET /predict/info",
            "drift_status": "GET /predict/drift-status"
        }
    }
