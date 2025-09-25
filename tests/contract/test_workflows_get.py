import pytest
import httpx
from typing import Dict, Any, List
import uuid


class TestWorkflowsGetContract:
    """Contract tests for GET /api/v1/workflows endpoints."""
    
    @pytest.fixture
    def sample_workflow(self) -> Dict[str, Any]:
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
            "progress_percentage": 25
        }
    
    @pytest.mark.asyncio
    async def test_list_workflows_success(self):
        """Test successful workflow listing."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/api/v1/workflows")
            
            # Expected: 200 OK
            assert response.status_code == 200
            
            response_data = response.json()
            
            # Validate response is a list
            assert isinstance(response_data, list)
            
            # Validate pagination metadata
            assert "total" in response_data
            assert "page" in response_data
            assert "page_size" in response_data
            assert "items" in response_data
            
            # Validate items is a list
            assert isinstance(response_data["items"], list)
            
            # If there are workflows, validate schema
            if response_data["items"]:
                workflow = response_data["items"][0]
                required_fields = [
                    "workflow_id", "project_id", "workflow_type", "status",
                    "title", "created_at", "updated_at", "progress_percentage"
                ]
                for field in required_fields:
                    assert field in workflow
    
    @pytest.mark.asyncio
    async def test_list_workflows_with_filters(self):
        """Test workflow listing with filters."""
        params = {
            "project_id": str(uuid.uuid4()),
            "workflow_type": "movie_creation",
            "status": "running"
        }
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/api/v1/workflows", params=params)
            
            # Expected: 200 OK
            assert response.status_code == 200
            
            response_data = response.json()
            assert isinstance(response_data, dict)
            assert "items" in response_data
            
            # All returned workflows should match the filters
            for workflow in response_data["items"]:
                assert workflow["project_id"] == params["project_id"]
                assert workflow["workflow_type"] == params["workflow_type"]
                assert workflow["status"] == params["status"]
    
    @pytest.mark.asyncio
    async def test_get_workflow_by_id_success(self, sample_workflow):
        """Test successful workflow retrieval by ID."""
        # First create a workflow to test retrieval
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": sample_workflow["project_id"],
                "workflow_type": sample_workflow["workflow_type"],
                "title": sample_workflow["title"],
                "description": sample_workflow["description"],
                "genre": sample_workflow["genre"],
                "target_duration": sample_workflow["target_duration"],
                "priority": sample_workflow["priority"]
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Now test retrieval
                response = await client.get(f"/api/v1/workflows/{workflow_id}")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                workflow_data = response.json()
                
                # Validate complete schema
                required_fields = [
                    "workflow_id", "project_id", "workflow_type", "current_state",
                    "status", "title", "description", "genre", "target_duration",
                    "style_preferences", "priority", "created_at", "updated_at",
                    "estimated_completion", "progress_percentage"
                ]
                for field in required_fields:
                    assert field in workflow_data
                
                # Validate specific values
                assert workflow_data["workflow_id"] == workflow_id
                assert workflow_data["title"] == sample_workflow["title"]
    
    @pytest.mark.asyncio
    async def test_get_workflow_by_id_not_found(self):
        """Test workflow retrieval with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/api/v1/workflows/{non_existent_id}")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_list_workflows_pagination(self):
        """Test workflow listing with pagination."""
        params = {
            "page": 2,
            "page_size": 10
        }
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/api/v1/workflows", params=params)
            
            # Expected: 200 OK
            assert response.status_code == 200
            
            response_data = response.json()
            
            # Validate pagination fields
            assert response_data["page"] == params["page"]
            assert response_data["page_size"] == params["page_size"]
            assert "total" in response_data
            assert "items" in response_data
            
            # Items should not exceed page_size
            assert len(response_data["items"]) <= params["page_size"]