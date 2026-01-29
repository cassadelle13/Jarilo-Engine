#!/usr/bin/env python3
"""
Main FastAPI application entry point for Jarilo Brain.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the FastAPI app from app.py
from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)