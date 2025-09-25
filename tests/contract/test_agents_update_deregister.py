import pytest
import httpx
from typing import Dict, Any
import uuid


class TestAgentsUpdateContract:
    """Contract tests for PUT /api/v1/agents/{agent_id} endpoint."""
    
    @pytest.fixture
    def valid_update_request(self) -> Dict[str, Any]:
        return {
            "description": "Updated agent description",
            "capabilities": ["script_writing", "dialogue_generation", "story_structure", "character_development"],
            "configuration": {
                "max_script_length": 150,
                "genre_preferences": ["action", "drama", "thriller", "comedy"],
                "tone_options": ["serious", "humorous", "dramatic", "sarcastic"]
            }
        }
    
    @pytest.mark.asyncio
    async def test_update_agent_success(self, valid_update_request):
        """Test successful agent update."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "ScriptWriterAgent",
                "category": "content_creation",
                "description": "Original description",
                "capabilities": ["script_writing", "dialogue_generation"],
                "version": "1.0.0",
                "configuration": {
                    "max_script_length": 100,
                    "genre_preferences": ["action"]
                }
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Now test update
                response = await client.put(f"/api/v1/agents/{agent_id}", json=valid_update_request)
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                updated_agent = response.json()
                
                # Validate updated fields
                assert updated_agent["description"] == valid_update_request["description"]
                assert updated_agent["capabilities"] == valid_update_request["capabilities"]
                assert updated_agent["configuration"] == valid_update_request["configuration"]
                
                # Validate unchanged fields
                assert updated_agent["agent_id"] == agent_id
                assert updated_agent["name"] == registered_agent["name"]  # Name should not change
                assert "created_at" in updated_agent
                assert "updated_at" in updated_agent
    
    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, valid_update_request):
        """Test agent update with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.put(f"/api/v1/agents/{non_existent_id}", json=valid_update_request)
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_update_agent_invalid_request(self):
        """Test agent update with invalid request."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "TestAgent",
                "category": "content_creation",
                "description": "Test description",
                "capabilities": ["capability1"],
                "version": "1.0.0",
                "configuration": {}
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Invalid update request
                invalid_request = {
                    "capabilities": "invalid_capabilities",  # Should be array
                    "configuration": "invalid_config"  # Should be object
                }
                
                response = await client.put(f"/api/v1/agents/{agent_id}", json=invalid_request)
                
                # Expected: 400 Bad Request
                assert response.status_code == 400
                
                response_data = response.json()
                assert "error" in response_data
                assert "message" in response_data


class TestAgentsDeregisterContract:
    """Contract tests for DELETE /api/v1/agents/{agent_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_deregister_agent_success(self):
        """Test successful agent deregistration."""
        # First register an agent
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": "AgentToDeregister",
                "category": "content_creation",
                "description": "Agent to be deregistered",
                "capabilities": ["capability1"],
                "version": "1.0.0",
                "configuration": {}
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Now test deregistration
                response = await client.delete(f"/api/v1/agents/{agent_id}")
                
                # Expected: 204 No Content
                assert response.status_code == 204
                
                # Verify agent is deleted
                get_response = await client.get(f"/api/v1/agents/{agent_id}")
                assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_deregister_agent_not_found(self):
        """Test agent deregistration with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.delete(f"/api/v1/agents/{non_existent_id}")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data