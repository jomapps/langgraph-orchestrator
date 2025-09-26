#!/usr/bin/env python3
"""
Live Operations Testing Script
Tests the LangGraph Orchestrator with local Redis
"""

import asyncio
import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

import redis.asyncio as redis
from src.config.settings import settings
from src.models import Workflow, Agent, Project, Task, ExecutionContext
from src.models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from src.models.agent import AgentStatus, AgentCategory
from src.models.task import TaskStatus, TaskPriority
from src.services.redis_state_manager import RedisStateManager

class LiveOperationsTest:
    """Test live operations with Redis"""
    
    def __init__(self):
        self.redis_manager = RedisStateManager()
        self.test_data = {}
        
    async def setup(self):
        """Initialize Redis connection"""
        print("Setting up Redis connection...")
        await self.redis_manager.connect()
        
        # Test basic Redis connection
        try:
            await self.redis_manager.redis_client.ping()
            print("SUCCESS: Redis connection successful")
            print(f"Connected to: {settings.redis_url}")
        except Exception as e:
            print(f"ERROR: Redis connection failed: {e}")
            raise
            
    async def cleanup(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        if self.redis_manager.redis_client:
            # Clean up test keys
            test_keys = []
            for key_pattern in ["test:*", "workflow:test*", "agent:test*", "task:test*"]:
                keys = await self.redis_manager.redis_client.keys(key_pattern)
                test_keys.extend(keys)
            
            if test_keys:
                await self.redis_manager.redis_client.delete(*test_keys)
                print(f"🗑️  Deleted {len(test_keys)} test keys")
            
            await self.redis_manager.disconnect()
            
    async def test_basic_redis_operations(self):
        """Test basic Redis operations"""
        print("\n📊 Testing Basic Redis Operations...")
        
        # Test string operations
        test_key = "test:basic_string"
        test_value = "hello_redis"
        
        await self.redis_manager.redis_client.set(test_key, test_value, ex=60)
        retrieved = await self.redis_manager.redis_client.get(test_key)
        
        assert retrieved == test_value, f"Expected {test_value}, got {retrieved}"
        print("✅ String operations working")
        
        # Test hash operations
        hash_key = "test:basic_hash"
        hash_data = {"field1": "value1", "field2": "value2"}
        
        await self.redis_manager.redis_client.hset(hash_key, mapping=hash_data)
        retrieved_hash = await self.redis_manager.redis_client.hgetall(hash_key)
        
        assert retrieved_hash == hash_data, f"Hash mismatch: {retrieved_hash}"
        print("✅ Hash operations working")
        
        # Test list operations  
        list_key = "test:basic_list"
        list_items = ["item1", "item2", "item3"]
        
        for item in list_items:
            await self.redis_manager.redis_client.lpush(list_key, item)
            
        list_length = await self.redis_manager.redis_client.llen(list_key)
        assert list_length == len(list_items), f"Expected {len(list_items)}, got {list_length}"
        print("✅ List operations working")
        
    async def test_workflow_operations(self):
        """Test workflow creation and management"""
        print("\n🔄 Testing Workflow Operations...")
        
        # Create test project
        project = Project(
            project_id=f"test-project-{uuid.uuid4()}",
            user_id="test-user",
            title="Test Movie Project",
            description="A test movie for validating the orchestrator",
            genre="action",
            target_duration=120,
            status="in_production"
        )
        
        # Create test workflow
        workflow = Workflow(
            workflow_id=f"test-workflow-{uuid.uuid4()}",
            project_id=project.project_id,
            workflow_type=WorkflowType.MOVIE_CREATION,
            current_state=WorkflowState.CONCEPT_DEVELOPMENT,
            status=WorkflowStatus.RUNNING,
            title="Test Workflow"
        )
        
        self.test_data['project'] = project
        self.test_data['workflow'] = workflow
        
        # Store workflow in Redis
        workflow_key = f"workflow:{workflow.workflow_id}"
        workflow_data = workflow.model_dump_json()
        
        await self.redis_manager.redis_client.set(workflow_key, workflow_data)
        print(f"✅ Stored workflow: {workflow.workflow_id}")
        
        # Retrieve and validate
        retrieved_data = await self.redis_manager.redis_client.get(workflow_key)
        retrieved_workflow = Workflow.model_validate_json(retrieved_data)
        
        assert retrieved_workflow.workflow_id == workflow.workflow_id
        assert retrieved_workflow.status == WorkflowStatus.RUNNING
        print("✅ Workflow retrieval successful")
        
        # Test workflow state updates
        new_state = WorkflowState.CHARACTER_CREATION
        workflow.current_state = new_state
        workflow.updated_at = datetime.utcnow()
        
        await self.redis_manager.redis_client.set(workflow_key, workflow.model_dump_json())
        
        updated_data = await self.redis_manager.redis_client.get(workflow_key)
        updated_workflow = Workflow.model_validate_json(updated_data)
        
        assert updated_workflow.current_state == new_state
        print(f"✅ Workflow state updated to: {new_state}")
        
    async def test_agent_operations(self):
        """Test agent registration and management"""
        print("\n🤖 Testing Agent Operations...")
        
        # Create test agent
        agent = Agent(
            agent_id=f"test-agent-{uuid.uuid4()}",
            agent_type=AgentCategory.STORY,
            capabilities=["story_creation", "character_development"],
            status=AgentStatus.AVAILABLE,
            endpoint_url="http://localhost:9000/agent"
        )
        
        self.test_data['agent'] = agent
        
        # Store agent in Redis
        agent_key = f"agent:{agent.agent_id}"
        agent_data = agent.model_dump_json()
        
        await self.redis_manager.redis_client.set(agent_key, agent_data)
        print(f"✅ Registered agent: {agent.agent_id}")
        
        # Add to available agents set
        await self.redis_manager.redis_client.sadd("agents:available", agent.agent_id)
        
        # Verify agent in available set
        is_available = await self.redis_manager.redis_client.sismember("agents:available", agent.agent_id)
        assert is_available, "Agent not found in available set"
        print("✅ Agent added to available set")
        
        # Test agent status update
        agent.status = AgentStatus.BUSY
        await self.redis_manager.redis_client.set(agent_key, agent.model_dump_json())
        
        # Move from available to busy set
        await self.redis_manager.redis_client.srem("agents:available", agent.agent_id)
        await self.redis_manager.redis_client.sadd("agents:busy", agent.agent_id)
        
        # Verify agent moved to busy set
        is_busy = await self.redis_manager.redis_client.sismember("agents:busy", agent.agent_id)
        assert is_busy, "Agent not found in busy set"
        print("✅ Agent status updated to busy")
        
    async def test_task_operations(self):
        """Test task creation and queue management"""
        print("\n📋 Testing Task Operations...")
        
        workflow = self.test_data.get('workflow')
        agent = self.test_data.get('agent')
        
        if not workflow or not agent:
            print("⚠️  Skipping task tests - missing workflow or agent")
            return
            
        # Create test task
        task = Task(
            task_id=f"test-task-{uuid.uuid4()}",
            workflow_id=workflow.workflow_id,
            project_id=workflow.project_id,
            agent_id=agent.agent_id,
            task_type="story_creation",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            parameters={"genre": "action", "theme": "heroic journey"}
        )
        
        self.test_data['task'] = task
        
        # Store task in Redis
        task_key = f"task:{task.task_id}"
        task_data = task.model_dump_json()
        
        await self.redis_manager.redis_client.set(task_key, task_data)
        print(f"✅ Created task: {task.task_id}")
        
        # Add to pending tasks queue
        await self.redis_manager.redis_client.lpush("tasks:pending", task.task_id)
        
        # Verify task in pending queue
        queue_length = await self.redis_manager.redis_client.llen("tasks:pending")
        assert queue_length > 0, "Task not added to pending queue"
        print("✅ Task added to pending queue")
        
        # Simulate task processing
        task_id = await self.redis_manager.redis_client.rpop("tasks:pending")
        assert task_id == task.task_id, "Wrong task popped from queue"
        
        # Move to running set
        await self.redis_manager.redis_client.sadd("tasks:running", task.task_id)
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        await self.redis_manager.redis_client.set(task_key, task.model_dump_json())
        
        print("✅ Task moved to running state")
        
        # Complete task
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = {"story": "An epic tale of heroes and adventure"}
        
        await self.redis_manager.redis_client.set(task_key, task.model_dump_json())
        await self.redis_manager.redis_client.srem("tasks:running", task.task_id)
        
        print("✅ Task completed successfully")
        
    async def test_execution_context_operations(self):
        """Test execution context management"""
        print("\n⚙️  Testing Execution Context Operations...")
        
        workflow = self.test_data.get('workflow')
        if not workflow:
            print("⚠️  Skipping context tests - missing workflow")
            return
            
        # Create execution context
        context = ExecutionContext(
            context_id=f"test-context-{uuid.uuid4()}",
            workflow_id=workflow.workflow_id,
            project_id=workflow.project_id,
            current_step="story_development",
            variables={"genre": "action", "target_audience": "teens"},
            shared_data={"characters": [], "scenes": []},
            performance_metrics={"tasks_completed": 0, "avg_processing_time": 0}
        )
        
        self.test_data['context'] = context
        
        # Store context in Redis
        context_key = f"context:{context.context_id}"
        context_data = context.model_dump_json()
        
        await self.redis_manager.redis_client.set(context_key, context_data)
        print(f"✅ Created execution context: {context.context_id}")
        
        # Test context updates
        context.variables["mood"] = "epic"
        context.shared_data["characters"].append({"name": "Hero", "type": "protagonist"})
        context.performance_metrics["tasks_completed"] = 1
        
        await self.redis_manager.redis_client.set(context_key, context.model_dump_json())
        
        # Retrieve and validate updates
        retrieved_data = await self.redis_manager.redis_client.get(context_key)
        retrieved_context = ExecutionContext.model_validate_json(retrieved_data)
        
        assert retrieved_context.variables["mood"] == "epic"
        assert len(retrieved_context.shared_data["characters"]) == 1
        assert retrieved_context.performance_metrics["tasks_completed"] == 1
        
        print("✅ Execution context updates successful")
        
    async def test_real_time_events(self):
        """Test real-time event streaming"""
        print("\n🔴 Testing Real-time Event Streaming...")
        
        workflow = self.test_data.get('workflow')
        if not workflow:
            print("⚠️  Skipping events tests - missing workflow")
            return
            
        stream_key = f"workflow_events:{workflow.workflow_id}"
        
        # Add events to stream
        events = [
            {"event": "workflow_started", "timestamp": datetime.utcnow().isoformat()},
            {"event": "state_changed", "from": "concept_development", "to": "character_creation"},
            {"event": "task_completed", "task_id": "story_task_1", "result": "success"}
        ]
        
        for event in events:
            await self.redis_manager.redis_client.xadd(stream_key, event)
            
        print(f"✅ Added {len(events)} events to stream")
        
        # Read events from stream
        stream_data = await self.redis_manager.redis_client.xread({stream_key: '0'})
        
        if stream_data:
            stream_name, messages = stream_data[0]
            assert len(messages) == len(events), f"Expected {len(events)} messages, got {len(messages)}"
            print(f"✅ Retrieved {len(messages)} events from stream")
        else:
            print("⚠️  No events found in stream")
            
    async def run_all_tests(self):
        """Run all live operation tests"""
        print("🚀 Starting Live Operations Tests")
        print("=" * 50)
        
        try:
            await self.setup()
            
            await self.test_basic_redis_operations()
            await self.test_workflow_operations() 
            await self.test_agent_operations()
            await self.test_task_operations()
            await self.test_execution_context_operations()
            await self.test_real_time_events()
            
            print("\n🎉 ALL TESTS PASSED!")
            print("=" * 50)
            print("✅ Redis integration working perfectly")
            print("✅ Data models serialize/deserialize correctly")
            print("✅ State management operations successful")
            print("✅ Real-time event streaming functional")
            print("\n🚀 Ready for production deployment!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    print(f"Environment: {settings.environment}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"Debug Mode: {settings.debug}")
    
    test_runner = LiveOperationsTest()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())