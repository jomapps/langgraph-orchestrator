#!/usr/bin/env python3
"""
Test FastAPI Application with Live Redis
"""

import asyncio
import sys
import json
import uuid
from pathlib import Path
import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

async def test_api_endpoints():
    """Test API endpoints with live server"""
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        print("Testing API endpoints...")
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"Health data: {health_data}")
            else:
                print("Health check failed")
                return False
        except Exception as e:
            print(f"Cannot connect to API server: {e}")
            print("Make sure to start the server with: uvicorn src.main:app --reload")
            return False
            
        # Test workflow creation
        workflow_data = {
            "project_id": str(uuid.uuid4()),
            "workflow_type": "movie_creation", 
            "title": "Test Movie",
            "description": "A test movie workflow"
        }
        
        try:
            response = await client.post(
                f"{base_url}/api/v1/workflows",
                json=workflow_data,
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"Create workflow: {response.status_code}")
            if response.status_code in [200, 201]:
                workflow_result = response.json()
                print(f"Created workflow ID: {workflow_result.get('workflow_id')}")
                return True
            else:
                print(f"Workflow creation failed: {response.text}")
                return False
        except Exception as e:
            print(f"Workflow creation error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_api_endpoints())