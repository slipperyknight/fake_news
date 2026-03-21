# app/main.py
"""
Entry point for FastAPI application.
"""

from fastapi import FastAPI

app = FastAPI(title="Multimodal Fake News Detection API")

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
