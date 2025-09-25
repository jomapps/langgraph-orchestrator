import pytest
import httpx
from typing import Dict, Any, List
import uuid


class TestAgentsGetContract:
    """Contract tests for GET /api/v1/agents endpoints."""
    
    @pytest.fixture
    def sample_agent(self) -> Dict[str, Any]:
        return {
            "agent_id": str(uuid.uuid4()),
            "name": "ScriptWriterAgent",
            "category": "content_creation",
            "description": "AI agent specialized in writing movie scripts",
            "capabilities": ["script_writing", "dialogue_generation", "story_structure"],
            "status": "active",
            "version": "1.0.0",
            "last_health_check": "2024-01-01T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "configuration": {
                "max_script_length": 120,
                "genre_preferences": ["action", "drama", "thriller"],
                "tone_options": ["serious", "humorous", "dramatic"]
            },
            "health_status": "healthy",
            "task_count": 0
        }
    
    @pytest.mark.asyncio
    async def test_list_agents_success(self):
        """Test successful agent listing."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/api/v1/agents")
            
            # Expected: 200 OK
            assert response.status_code == 200
            
            response_data = response.json()
            
            # Validate response is a list
            assert isinstance(response_data, list)
            
            # If there are agents, validate schema
            if response_data:
                agent = response_data[0]
                required_fields = [
                    "agent_id", "name", "category", "description",
                    "capabilities", "status", "version", "health_status"
                ]
                for field in required_fields:
                    assert field in agent
    
    @pytest.mark.asyncio
    async def test_list_agents_with_filters(self):
        """Test agent listing with filters."""
        params = {
            "category": "content_creation",
            "status": "active"
        }
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/api/v1/agents", params=params)
            
            # Expected: 200 OK
            assert response.status_code == 200
            
            response_data = response.json()
            assert isinstance(response_data, list)
            
            # All returned agents should match the filters
            for agent in response_data:
                assert agent["category"] == params["category"]
                assert agent["status"] == params["status"]
    
    @pytest.mark.asyncio
    async def test_get_agent_by_id_success(self, sample_agent):
        """Test successful agent retrieval by ID."""
        # First register an agent to test retrieval
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            register_response = await client.post("/api/v1/agents/register", json={
                "name": sample_agent["name"],
                "category": sample_agent["category"],
                "description": sample_agent["description"],
                "capabilities": sample_agent["capabilities"],
                "version": sample_agent["version"],
                "configuration": sample_agent["configuration"]
            })
            
            if register_response.status_code == 201:
                registered_agent = register_response.json()
                agent_id = registered_agent["agent_id"]
                
                # Now test retrieval
                response = await client.get(f"/api/v1/agents/{agent_id}")
                
                # Expected: 200 OK
                assert response.status_code == 200
                
                agent_data = response.json()
                
                # Validate complete schema
                required_fields = [
                    "agent_id", "name", "category", "description", "capabilities",
                    "status", "version", "last_health_check", "created_at",
                    "updated_at", "configuration", "health_status", "task_count"
                ]
                for field in required_fields:
                    assert field in agent_data
                
                # Validate specific values
                assert agent_data["agent_id"] == agent_id
                assert agent_data["name"] == sample_agent["name"]
    
    @pytest.mark.asyncio
    async def test_get_agent_by_id_not_found(self):
        """Test agent retrieval with non-existent ID."""
        non_existent_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/api/v1/agents/{non_existent_id}")
            
            # Expected: 404 Not Found
            assert response.status_code == 404
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data


class TestAgentsRegisterContract:
    """Contract tests for POST /api/v1/agents/register endpoint."""
    
    @pytest.fixture
    def valid_agent_registration(self) -> Dict[str, Any]:
        return {
            "name": "StoryboardArtistAgent",
            "category": "visual_design",
            "description": "AI agent specialized in creating storyboards",
            "capabilities": ["storyboard_creation", "visual_composition", "scene_planning"],
            "version": "1.0.0",
            "configuration": {
                "max_storyboards": 50,
                "style_preferences": ["realistic", "stylized"],
                "color_palette": "vibrant"
            }
        }
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, valid_agent_registration):
        """Test successful agent registration."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/agents/register", json=valid_agent_registration)
            
            # Expected: 201 Created
            assert response.status_code == 201
            
            response_data = response.json()
            
            # Validate response schema
            assert "agent_id" in response_data
            assert response_data["name"] == valid_agent_registration["name"]
            assert response_data["category"] == valid_agent_registration["category"]
            assert response_data["description"] == valid_agent_registration["description"]
            assert response_data["capabilities"] == valid_agent_registration["capabilities"]
            assert response_data["version"] == valid_agent_registration["version"]
            assert response_data["status"] == "active"
            assert response_data["health_status"] == "healthy"
            
            # Validate timestamps
            assert "created_at" in response_data
            assert "updated_at" in response_data
            assert "last_health_check" in response_data
            
            # Validate configuration
            assert response_data["configuration"] == valid_agent_registration["configuration"]
            assert response_data["task_count"] == 0
    
    @pytest.mark.asyncio
    async def test_register_agent_invalid_request(self):
        """Test agent registration with invalid request."""
        invalid_request = {
            "name": "",  # Empty name
            "category": "invalid_category",
            "capabilities": "invalid_capabilities",  # Should be array
            "version": "invalid_version"
        }
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/api/v1/agents/register", json=invalid_request)
            
            # Expected: 400 Bad Request
            assert response.status_code == 400
            
            response_data = response.json()
            assert "error" in response_data
            assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_agent(self, valid_agent_registration):
        """Test registering an agent with duplicate name."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # First registration should succeed
            response1 = await client.post("/api/v1/agents/register", json=valid_agent_registration)
            assert response1.status_code == 201
            
            # Second registration with same name should fail
            response2 = await client.post("/api/v1/agents/register", json=valid_agent_registration)
            
            # Expected: 409 Conflict
            assert response2.status_code == 409
            
            response_data = response2.json()
            assert "error" in response_data
            assert "message" in response_data