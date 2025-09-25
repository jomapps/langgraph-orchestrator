import pytest
import httpx
from typing import Dict, Any
import uuid


class TestWorkflowsControlContract:
    """Contract tests for workflow control endpoints (pause, resume, cancel)."""
    
    @pytest.mark.asyncio
    async def test_pause_workflow_success(self):
        """Test successful workflow pause."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Test Workflow to Pause",
                "description": "Test description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Test pause
                response = await client.post(f"/api/v1/workflows/{workflow_id}/pause")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                assert response_data["status"] == "paused"
                assert response_data["workflow_id"] == workflow_id
    
    @pytest.mark.asyncio
    async def test_pause_workflow_not_found(self):
        """Test workflow pause with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(f"/api/v1/workflows/{non_existent_id}/pause")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_pause_already_paused_workflow(self):
        """Test pausing an already paused workflow."""
        # First create and pause a workflow
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
                
                # Pause it first
                await client.post(f"/api/v1/workflows/{workflow_id}/pause")
                
                # Try to pause again
                response = await client.post(f"/api/v1/workflows/{workflow_id}/pause")
                
                # Expected: 409 Conflict or 400 Bad Request
                assert response.status_code in [409, 400]
                
                response_data = response.json()
                assert "error" in response_data
                assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_resume_workflow_success(self):
        """Test successful workflow resume."""
        # First create and pause a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Test Workflow to Resume",
                "description": "Test description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Pause it first
                await client.post(f"/api/v1/workflows/{workflow_id}/pause")
                
                # Test resume
                response = await client.post(f"/api/v1/workflows/{workflow_id}/resume")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                assert response_data["status"] == "running"
                assert response_data["workflow_id"] == workflow_id
    
    @pytest.mark.asyncio
    async def test_resume_workflow_not_found(self):
        """Test workflow resume with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(f"/api/v1/workflows/{non_existent_id}/resume")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_resume_already_running_workflow(self):
        """Test resuming an already running workflow."""
        # First create a workflow (should be running by default)
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
                
                # Try to resume without pausing first
                response = await client.post(f"/api/v1/workflows/{workflow_id}/resume")
                
                # Expected: 409 Conflict or 400 Bad Request
                assert response.status_code in [409, 400]
                
                response_data = response.json()
                assert "error" in response_data
                assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_success(self):
        """Test successful workflow cancellation."""
        # First create a workflow
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            create_response = await client.post("/api/v1/workflows", json={
                "project_id": str(uuid.uuid4()),
                "workflow_type": "movie_creation",
                "title": "Test Workflow to Cancel",
                "description": "Test description",
                "genre": "action",
                "target_duration": 120,
                "priority": 5
            })
            
            if create_response.status_code == 201:
                created_workflow = create_response.json()
                workflow_id = created_workflow["workflow_id"]
                
                # Test cancel
                response = await client.post(f"/api/v1/workflows/{workflow_id}/cancel")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                assert response_data["status"] == "cancelled"
                assert response_data["workflow_id"] == workflow_id
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_not_found(self):
        """Test workflow cancellation with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(f"/api/v1/workflows/{non_existent_id}/cancel")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_cancel_already_completed_workflow(self):
        """Test cancelling an already completed workflow."""
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
                
                # Cancel it first
                await client.post(f"/api/v1/workflows/{workflow_id}/cancel")
                
                # Try to cancel again
                response = await client.post(f"/api/v1/workflows/{workflow_id}/cancel")
                
                # Expected: 409 Conflict or 400 Bad Request
                assert response.status_code in [409, 400]
                
                response_data = response.json()
                assert "error" in response_data
                assert "message" in response_data