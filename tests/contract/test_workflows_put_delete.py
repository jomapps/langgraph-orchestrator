import pytest
import httpx
from typing import Dict, Any
import uuid


class TestWorkflowsPutContract:
    """Contract tests for PUT /api/v1/workflows/{workflow_id} endpoint."""
    
    @pytest.fixture
    def valid_update_request(self) -> Dict[str, Any]:
        return {
            "title": "Updated Movie Production",
            "description": "Updated description",
            "priority": 8,
            "style_preferences": {
                "visual_style": "noir",
                "narrative_tone": "suspenseful"
            }
        }
    
    @pytest.mark.asyncio
    async def test_update_workflow_success(self, valid_update_request):
        """Test successful workflow update."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Original Title",
                "description": "Original description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Now test update
                response = await client.put(f"/api/v1/workflows/{workflow_id}", json=valid_update_request)
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                updated_workflow = response.json()
                
                # Validate updated fields
                assert updated_workflow["title"] == valid_update_request["title"]
                assert updated_workflow["description"] == valid_update_request["description"]
                assert updated_workflow["priority"] == valid_update_request["priority"]
                assert updated_workflow["style_preferences"] == valid_update_request["style_preferences"]
                
                # Validate unchanged fields
                assert updated_workflow["workflow_id"] == workflow_id
                assert "created_at" in updated_workflow
                assert "updated_at" in updated_workflow
    
    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, valid_update_request):
        """Test workflow update with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.put(f"/api/v1/workflows/{non_existent_id}", json=valid_update_request)
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_update_workflow_invalid_request(self):
        """Test workflow update with invalid request."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Test Workflow",
                "description": "Test description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Invalid update request
                invalid_request = {
                    "priority": "invalid_priority",  # Should be integer
                    "style_preferences": "invalid_preferences"  # Should be object
                }
                
                response = await client.put(f"/api/v1/workflows/{workflow_id}", json=invalid_request)
                
                # Expected: 400 Bad Request
                assert response.status_code == 400
                
                response_data = response.json()
                assert "error" in response_data
                assert "message" in response_data


class TestWorkflowsDeleteContract:
    """Contract tests for DELETE /api/v1/workflows/{workflow_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_workflow_success(self):
        """Test successful workflow deletion."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Test Workflow to Delete",
                "description": "Test description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Now test deletion
                response = await client.delete(f"/api/v1/workflows/{workflow_id}")
                
                # Expected: 204 No Content
                assert response.status_code == 204
                
                # Verify workflow is deleted
                get_response = await client.get(f"/api/v1/workflows/{workflow_id}")
                assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self):
        """Test workflow deletion with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.delete(f"/api/v1/workflows/{non_existent_id}")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data