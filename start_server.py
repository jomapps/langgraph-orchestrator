#!/usr/bin/env python3
"""
Start the FastAPI server with local configuration
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

import uvicorn
from src.main import app
from src.config.settings import settings

if __name__ == "__main__":
    print("Starting LangGraph Orchestrator...")
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"API Host: {settings.api.host}")
    print(f"API Port: {settings.api.port}")
    print("-" * 50)
    
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8003,
        reload=True,
        log_level="info"
    )