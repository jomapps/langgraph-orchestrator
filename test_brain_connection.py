#!/usr/bin/env python3
"""
Test script to verify brain service connection and integration.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.clients.brain_client import BrainServiceClient
from src.workflows.base_workflow import create_workflow
from src.models.workflow import Workflow, WorkflowType, WorkflowStatus, WorkflowState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_brain_client_connection():
    """Test basic brain client connection"""
    print("Testing brain service client connection...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
    print(f"Connecting to brain service at: {brain_service_url}")

    try:
        async with BrainServiceClient(brain_service_url) as client:
            print("✅ Successfully connected to brain service")

            # Test storing an embedding
            embedding_id = await client.store_embedding(
                "Test content for orchestrator integration",
                {"test": True, "component": "orchestrator"}
            )
            print(f"✅ Successfully stored embedding: {embedding_id}")

            # Test searching embeddings
            results = await client.search_embeddings("test content", limit=3)
            print(f"✅ Successfully searched embeddings, found {len(results)} results")

            # Test storing knowledge
            knowledge_id = await client.store_knowledge(
                "test_knowledge",
                {"message": "Brain service integration test", "timestamp": "2024-01-01"}
            )
            print(f"✅ Successfully stored knowledge: {knowledge_id}")

            # Test retrieving knowledge
            knowledge_results = await client.get_knowledge("test_knowledge")
            print(f"✅ Successfully retrieved knowledge, found {len(knowledge_results)} items")

            return True

    except Exception as e:
        print(f"❌ Brain service connection failed: {str(e)}")
        return False


async def test_workflow_creation():
    """Test workflow creation with brain service"""
    print("\nTesting workflow creation with brain service...")

    brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')

    try:
        # Test video creation workflow
        video_workflow = await create_workflow("video_creation", brain_service_url)
        print("✅ Successfully created video creation workflow")

        # Test content optimization workflow
        content_workflow = await create_workflow("content_optimization", brain_service_url)
        print("✅ Successfully created content optimization workflow")

        return True

    except Exception as e:
        print(f"❌ Workflow creation failed: {str(e)}")
        return False


async def test_workflow_execution():
    """Test workflow execution (mock)"""
    print("\nTesting workflow execution...")

    try:
        # Create a mock workflow
        workflow = Workflow(
            project_id="test-project-123",
            workflow_type=WorkflowType.MOVIE_CREATION,
            title="Test Movie",
            description="Test movie creation workflow",
            genre="educational",
            target_duration=60
        )

        print(f"Created mock workflow: {workflow.workflow_id}")

        # Create workflow handler
        brain_service_url = os.getenv('BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
        workflow_handler = await create_workflow("video_creation", brain_service_url)

        # Execute workflow (this will actually try to connect and store data)
        result = await workflow_handler.execute(workflow)
        print(f"✅ Successfully executed workflow, result keys: {list(result.keys())}")

        return True

    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🧠 Brain Service Integration Test Suite")
    print("=" * 50)

    tests = [
        ("Brain Client Connection", test_brain_client_connection),
        ("Workflow Creation", test_workflow_creation),
        ("Workflow Execution", test_workflow_execution)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Brain service integration is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Check brain service configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)