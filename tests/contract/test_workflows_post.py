import pytest
import httpx
from typing import Dict, Any
import uuid


class TestWorkflowsPostContract:
    """Contract tests for POST /api/v1/workflows endpoint."""
    
    @pytest.fixture
    def valid_workflow_request(self) -> Dict[str, Any]:
        return {
            "project_id": str(uuid.uuid4()),
            "workflow_type": "movie_creation",
            "title": "Test Movie Production",
            "description": "A test movie production workflow",
            "genre": "action",
            "target_duration": 120,
            "style_preferences": {
                "visual_style": "cinematic",
                "narrative_tone": "dramatic"
            },
            "priority": 5
        }
    
    @pytest.fixture
    def expected_workflow_response(self) -> Dict[str, Any]:
        return {
            "workflow_id": str(uuid.uuid4()),
            "project_id": str(uuid.uuid4()),
            "workflow_type": "movie_creation",
            "current_state": "concept_development",
            "status": "running",
            "title": "Test Movie Production",
            "description": "A test movie production workflow",
            "genre": "action",
            "target_duration": 120,
            "style_preferences": {
                "visual_style": "cinematic",
                "narrative_tone": "dramatic"
            },
            "priority": 5,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "estimated_completion": "2024-01-01T02:00:00Z",
            "progress_percentage": 0
        }
    
    @pytest.mark.asyncio
    async def test_create_workflow_success(self, valid_workflow_request, expected_workflow_response):
        """Test successful workflow creation."""
        # This test should FAIL until implementation is complete
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/workflows", json=valid_workflow_request)
            
            # Expected: 201 Created
            assert response.status_code == 201
            
            response_data = response.json()
            
            # Validate response schema
            assert "workflow_id" in response_data
            assert response_data["project_id"] == valid_workflow_request["project_id"]
            assert response_data["workflow_type"] == valid_workflow_request["workflow_type"]
            assert response_data["status"] == "running"
            assert response_data["current_state"] == "concept_development"
            assert response_data["title"] == valid_workflow_request["title"]
            assert response_data["priority"] == valid_workflow_request["priority"]
            
            # Validate timestamps
            assert "created_at" in response_data
            assert "updated_at" in response_data
            assert "estimated_completion" in response_data
            
            # Validate progress
            assert response_data["progress_percentage"] == 0
    
    @pytest.mark.asyncio
    async def test_create_workflow_invalid_request(self):
        """Test workflow creation with invalid request."""
        invalid_request = {
            "project_id": "invalid-uuid",
            "workflow_type": "invalid_type"
        }
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/workflows", json=invalid_request)
            
            # Expected: 400 Bad Request
            assert response.status_code == 400
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_create_workflow_duplicate_project(self, valid_workflow_request):
        """Test workflow creation when project already has active workflow."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response1 = await client.post("/api/v1/workflows", json=valid_workflow_request)
            assert response1.status_code == 201
            
            # Try to create another workflow for the same project
            response2 = await client.post("/api/v1/workflows", json=valid_workflow_request)
            
            # Expected: 409 Conflict
            assert response2.status_code == 409
            
            response_data = response2.json()
            assert "error" in response_data
            assert "message" in response_data