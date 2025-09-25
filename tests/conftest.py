import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, List
import httpx
import redis.asyncio as redis
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create a Redis client for testing."""
    client = redis.from_url(settings.redis_url)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture(scope="session")
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an HTTP client for API testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture(autouse=True)
async def cleanup_redis(redis_client: redis.Redis):
    """Clean up Redis data before each test."""
    # Clear all test data
    await redis_client.flushdb()
    yield
    # Clean up after test
    await redis_client.flushdb()


@pytest.fixture
def test_project_id() -> str:
    """Generate a test project ID."""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def test_workflow_id() -> str:
    """Generate a test workflow ID."""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def test_agent_id() -> str:
    """Generate a test agent ID."""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def test_task_id() -> str:
    """Generate a test task ID."""
    import uuid
    return str(uuid.uuid4())


# Custom markers for different test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "contract: mark test as contract test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as Redis-dependent"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )


# Skip contract tests if API server is not running
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on conditions."""
    
    # Check if API server is running
    api_server_running = False
    try:
        import httpx
        client = httpx.Client(base_url="http://localhost:8000")
        response = client.get("/health")
        api_server_running = response.status_code == 200
        client.close()
    except:
        api_server_running = False
    
    # Skip contract tests if API server is not running
    if not api_server_running:
        skip_contract = pytest.mark.skip(reason="API server not running")
        for item in items:
            if "contract" in item.keywords:
                item.add_marker(skip_contract)


# Test data fixtures
@pytest.fixture
def sample_workflow_data() -> Dict[str, Any]:
    """Sample workflow data for testing."""
    import uuid
    from datetime import datetime, timezone
    
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "estimated_completion": datetime.now(timezone.utc).isoformat(),
        "progress_percentage": 0
    }


@pytest.fixture
def sample_agent_data() -> Dict[str, Any]:
    """Sample agent data for testing."""
    import uuid
    from datetime import datetime, timezone
    
    return {
        "agent_id": str(uuid.uuid4()),
        "name": "TestAgent",
        "category": "content_creation",
        "description": "Test agent for unit testing",
        "capabilities": ["test_capability"],
        "status": "active",
        "version": "1.0.0",
        "last_health_check": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "test_config": "test_value"
        },
        "health_status": "healthy",
        "task_count": 0
    }


@pytest.fixture
def sample_task_data() -> Dict[str, Any]:
    """Sample task data for testing."""
    import uuid
    from datetime import datetime, timezone
    
    return {
        "task_id": str(uuid.uuid4()),
        "agent_id": str(uuid.uuid4()),
        "workflow_id": str(uuid.uuid4()),
        "task_type": "script_writing",
        "status": "pending",
        "priority": 5,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
        "input_data": {"test_input": "test_value"},
        "output_data": None,
        "error_message": None,
        "retry_count": 0,
        "max_retries": 3
    }