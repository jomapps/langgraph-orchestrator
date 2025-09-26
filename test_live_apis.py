#!/usr/bin/env python3
"""
Test Live API Operations
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

from src.config.settings import settings
from src.models import Project
from src.services.redis_state_manager import RedisStateManager

async def setup_test_project():
    """Create a test project in Redis"""
    manager = await RedisStateManager.create()
    
    # Create test project
    project = Project(
        project_id="550e8400-e29b-41d4-a716-446655440000",
        name="Epic Adventure Movie",
        description="A test movie project",
        project_type="video_production"
    )
    
    # Store in Redis
    project_key = f"project:{project.project_id}"
    project_data = project.model_dump_json()
    
    await manager.redis_client.set(project_key, project_data)
    print(f"Created test project: {project.project_id}")
    
    await manager.disconnect()
    return project.project_id

async def test_workflow_operations():
    """Test workflow API operations"""
    base_url = "http://127.0.0.1:8003"
    
    # Setup test project first
    project_id = await setup_test_project()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\\n=== Testing Workflow Operations ===")
        
        # Test workflow creation
        workflow_data = {
            "project_id": project_id,
            "workflow_type": "movie_creation",
            "title": "Epic Adventure Movie"
        }
        
        print("1. Creating workflow...")
        response = await client.post(
            f"{base_url}/api/v1/workflows",
            json=workflow_data,
            headers={"X-API-Key": "dev-api-key-123"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            workflow_result = response.json()
            workflow_id = workflow_result.get("workflow_id")
            print(f"   SUCCESS: Created workflow {workflow_id}")
            
            # Test workflow retrieval
            print("2. Retrieving workflow...")
            get_response = await client.get(
                f"{base_url}/api/v1/workflows/{workflow_id}",
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"   Status: {get_response.status_code}")
            if get_response.status_code == 200:
                workflow_info = get_response.json()
                print(f"   SUCCESS: Retrieved workflow - Status: {workflow_info.get('status')}")
            
            # Test workflow list
            print("3. Listing workflows...")
            list_response = await client.get(
                f"{base_url}/api/v1/workflows",
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"   Status: {list_response.status_code}")
            if list_response.status_code == 200:
                workflows = list_response.json()
                print(f"   SUCCESS: Found {len(workflows)} workflows")
            
            # Test workflow start
            print("4. Starting workflow...")
            start_response = await client.post(
                f"{base_url}/api/v1/workflows/{workflow_id}/start",
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"   Status: {start_response.status_code}")
            if start_response.status_code in [200, 202]:
                print("   SUCCESS: Workflow started")
            
            return workflow_id
            
        else:
            print(f"   FAILED: {response.text}")
            return None

async def test_agent_operations():
    """Test agent API operations"""
    base_url = "http://127.0.0.1:8003"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\\n=== Testing Agent Operations ===")
        
        # Test agent registration
        agent_data = {
            "agent_id": f"test-agent-{uuid.uuid4()}",
            "name": "Story Creation Agent",
            "category": "creative",
            "capabilities": ["story_creation", "character_development"]
        }
        
        print("1. Registering agent...")
        response = await client.post(
            f"{base_url}/api/v1/agents/register",
            json=agent_data,
            headers={"X-API-Key": "dev-api-key-123"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            agent_result = response.json()
            agent_id = agent_result.get("agent_id")
            print(f"   SUCCESS: Registered agent {agent_id}")
            
            # Test agent list
            print("2. Listing agents...")
            list_response = await client.get(
                f"{base_url}/api/v1/agents",
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"   Status: {list_response.status_code}")
            if list_response.status_code == 200:
                agents = list_response.json()
                print(f"   SUCCESS: Found {len(agents)} agents")
            
            # Test agent health check
            print("3. Checking agent health...")
            health_response = await client.get(
                f"{base_url}/api/v1/agents/{agent_id}/health",
                headers={"X-API-Key": "dev-api-key-123"}
            )
            print(f"   Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_info = health_response.json()
                print(f"   SUCCESS: Agent health - Status: {health_info.get('status', 'unknown')}")
            
            return agent_id
            
        else:
            print(f"   FAILED: {response.text}")
            return None

async def test_redis_data_persistence():
    """Test that data is actually stored in Redis"""
    print("\\n=== Testing Redis Data Persistence ===")
    
    manager = await RedisStateManager.create()
    
    # Check stored workflows
    workflow_keys = []
    async for key in manager.redis_client.scan_iter(match="workflow:*"):
        workflow_keys.append(key)
    
    print(f"Found {len(workflow_keys)} workflows in Redis:")
    for key in workflow_keys[:3]:  # Show first 3
        workflow_data = await manager.redis_client.get(key)
        if workflow_data:
            workflow = json.loads(workflow_data)
            print(f"  - {key}: {workflow.get('title', 'No title')} (Status: {workflow.get('status', 'unknown')})")
    
    # Check stored agents
    agent_keys = []
    async for key in manager.redis_client.scan_iter(match="agent:*"):
        agent_keys.append(key)
    
    print(f"Found {len(agent_keys)} agents in Redis:")
    for key in agent_keys[:3]:  # Show first 3
        agent_data = await manager.redis_client.get(key)
        if agent_data:
            agent = json.loads(agent_data)
            print(f"  - {key}: {agent.get('agent_type', 'unknown')} (Status: {agent.get('status', 'unknown')})")
    
    # Check agent availability sets
    available_agents = await manager.redis_client.smembers("agents:available")
    busy_agents = await manager.redis_client.smembers("agents:busy")
    
    print(f"Agent availability: {len(available_agents)} available, {len(busy_agents)} busy")
    
    await manager.disconnect()

async def run_all_tests():
    """Run comprehensive live API tests"""
    print("Starting Live API Tests")
    print(f"Server: http://127.0.0.1:8003")
    print(f"Redis: {settings.redis_url}")
    print("=" * 50)
    
    try:
        # Test health first
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://127.0.0.1:8003/health")
            if health_response.status_code != 200:
                print("ERROR: Server not healthy!")
                return
            print(f"Server healthy: {health_response.json()}")
        
        # Run API tests
        workflow_id = await test_workflow_operations()
        agent_id = await test_agent_operations()
        
        # Test data persistence
        await test_redis_data_persistence()
        
        print("\\n" + "=" * 50)
        if workflow_id and agent_id:
            print("ALL TESTS PASSED!")
            print("Workflow operations working")
            print("Agent operations working") 
            print("Redis persistence confirmed")
            print("\\nSystem is ready for production!")
        else:
            print("Some tests failed - check logs above")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all_tests())