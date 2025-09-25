import pytest
import httpx
from typing import Dict, Any
import uuid


class TestAgentsHealthContract:
    """Contract tests for agent health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_check_agent_health_success(self):
        """Test successful agent health check."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "HealthCheckAgent",
                "category": "content_creation",
                "description": "Agent for health check testing",
                "capabilities": ["capability1"],
                "version": "1.0.0",
                "configuration": {}
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Test health check
                response = await client.get(f"/api/v1/agents/{agent_id}/health")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                
                # Validate health check response
                assert "agent_id" in response_data
                assert "health_status" in response_data
                assert "last_health_check" in response_data
                assert "message" in response_data
                
                assert response_data["agent_id"] == agent_id
                assert response_data["health_status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_check_agent_health_not_found(self):
        """Test agent health check with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/api/v1/agents/{non_existent_id}/health")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data


class TestAgentsResetContract:
    """Contract tests for POST /api/v1/agents/{agent_id}/reset endpoint."""
    
    @pytest.mark.asyncio
    async def test_reset_agent_success(self):
        """Test successful agent reset."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "ResetAgent",
                "category": "content_creation",
                "description": "Agent for reset testing",
                "capabilities": ["capability1"],
                "version": "1.0.0",
                "configuration": {}
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Test reset
                response = await client.post(f"/api/v1/agents/{agent_id}/reset")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                
                # Validate reset response
                assert response_data["agent_id"] == agent_id
                assert response_data["status"] == "active"
                assert response_data["task_count"] == 0
                assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_reset_agent_not_found(self):
        """Test agent reset with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(f"/api/v1/agents/{non_existent_id}/reset")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data


class TestAgentsTasksContract:
    """Contract tests for GET /api/v1/agents/{agent_id}/tasks endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_agent_tasks_success(self):
        """Test successful retrieval of agent tasks."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "TaskAgent",
                "category": "content_creation",
                "description": "Agent for task testing",
                "capabilities": ["capability1"],
                "version": "1.0.0",
                "configuration": {}
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Test task retrieval
                response = await client.get(f"/api/v1/agents/{agent_id}/tasks")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                response_data = response.json()
                
                # Validate response structure
                assert isinstance(response_data, list)
                
                # If there are tasks, validate schema
                if response_data:
                    task = response_data[0]
                    required_fields = [
                        "task_id", "agent_id", "workflow_id", "task_type",
                        "status", "priority", "created_at", "updated_at"
                    ]
                    for field in required_fields:
                        assert field in task
    
    @pytest.mark.asyncio
    async def test_get_agent_tasks_not_found(self):
        """Test agent tasks retrieval with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/api/v1/agents/{non_existent_id}/tasks")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data