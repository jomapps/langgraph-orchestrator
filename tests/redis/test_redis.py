import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import time

from src.models import Workflow, Agent, Task, Project, ExecutionContext
from src.models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from src.models.agent import AgentStatus, AgentCategory
from src.models.task import TaskStatus, TaskPriority
from src.services import RedisStateManager
from src.orchestrator import WorkflowOrchestrator


class TestRedisConnection:
    """Tests for Redis connection and basic operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_ping(self, redis_client):
        """Test Redis ping operation."""
        result = await redis_client.ping()
        assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_basic_operations(self, redis_client):
        """Test basic Redis operations."""
        # Test set and get
        key = "test:basic:string"
        value = "test_value"
        
        await redis_client.set(key, value)
        retrieved = await redis_client.get(key)
        assert retrieved.decode() == value
        
        # Test delete
        await redis_client.delete(key)
        deleted = await redis_client.get(key)
        assert deleted is None
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_hash_operations(self, redis_client):
        """Test Redis hash operations."""
        hash_key = "test:basic:hash"
        field1, value1 = "field1", "value1"
        field2, value2 = "field2", "value2"
        
        # Test hset and hget
        await redis_client.hset(hash_key, field1, value1)
        await redis_client.hset(hash_key, field2, value2)
        
        retrieved1 = await redis_client.hget(hash_key, field1)
        retrieved2 = await redis_client.hget(hash_key, field2)
        
        assert retrieved1.decode() == value1
        assert retrieved2.decode() == value2
        
        # Test hgetall
        all_fields = await redis_client.hgetall(hash_key)
        assert len(all_fields) == 2
        assert all_fields[field1.encode()].decode() == value1
        assert all_fields[field2.encode()].decode() == value2
        
        # Cleanup
        await redis_client.delete(hash_key)
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_list_operations(self, redis_client):
        """Test Redis list operations."""
        list_key = "test:basic:list"
        items = ["item1", "item2", "item3"]
        
        # Test lpush and lrange
        for item in items:
            await redis_client.lpush(list_key, item)
        
        retrieved = await redis_client.lrange(list_key, 0, -1)
        retrieved_items = [item.decode() for item in retrieved]
        
        # Items are in reverse order due to lpush
        assert retrieved_items == list(reversed(items))
        
        # Cleanup
        await redis_client.delete(list_key)
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_set_operations(self, redis_client):
        """Test Redis set operations."""
        set_key = "test:basic:set"
        members = ["member1", "member2", "member3"]
        
        # Test sadd and smembers
        for member in members:
            await redis_client.sadd(set_key, member)
        
        retrieved = await redis_client.smembers(set_key)
        retrieved_members = [member.decode() for member in retrieved]
        
        assert set(retrieved_members) == set(members)
        
        # Test sismember
        assert await redis_client.sismember(set_key, "member1") == 1
        assert await redis_client.sismember(set_key, "nonexistent") == 0
        
        # Cleanup
        await redis_client.delete(set_key)
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_expiration(self, redis_client):
        """Test Redis key expiration."""
        key = "test:basic:expire"
        value = "expiring_value"
        
        await redis_client.set(key, value)
        await redis_client.expire(key, 1)  # Expire in 1 second
        
        # Should exist immediately
        assert await redis_client.exists(key) == 1
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired
        assert await redis_client.exists(key) == 0


class TestRedisStateManagerOperations:
    """Tests for Redis state manager operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_state_manager_connection(self, redis_client):
        """Test Redis state manager connection."""
        state_manager = RedisStateManager(redis_client)
        
        # Test connection
        assert await state_manager.connect() is True
        assert await state_manager.ping() is True
        
        # Test disconnection
        await state_manager.disconnect()
        # Note: Redis client doesn't have a direct way to test disconnection
        # The connection pool will handle reconnection automatically
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_workflow_indexing(self, redis_client, sample_workflow_data):
        """Test workflow indexing operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create multiple workflows
        workflows = []
        for i in range(5):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"index_test_workflow_{i}",
                "metadata": {"title": f"Index Test {i}"},
                "status": WorkflowStatus.PENDING if i % 2 == 0 else WorkflowStatus.RUNNING
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
            workflows.append(workflow)
        
        # Test workflow retrieval by status
        pending_workflows = await state_manager.get_workflows(status=WorkflowStatus.PENDING)
        running_workflows = await state_manager.get_workflows(status=WorkflowStatus.RUNNING)
        
        assert len(pending_workflows) >= 2  # At least the even-indexed workflows
        assert len(running_workflows) >= 2  # At least the odd-indexed workflows
        
        # Test workflow retrieval by project ID (if available)
        if workflows[0].project_id:
            project_workflows = await state_manager.get_workflows(project_id=workflows[0].project_id)
            assert len(project_workflows) >= 5
        
        # Cleanup
        for workflow in workflows:
            await state_manager.delete_workflow(workflow.id)
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_agent_indexing(self, redis_client, sample_agent_data):
        """Test agent indexing operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create multiple agents
        agents = []
        capabilities = ["script_generation", "scene_planning", "voice_generation"]
        
        for i in range(6):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"index_test_agent_{i}",
                "name": f"Index Test Agent {i}",
                "capabilities": [capabilities[i % len(capabilities)]],
                "status": AgentStatus.AVAILABLE if i % 2 == 0 else AgentStatus.BUSY
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
            agents.append(agent)
        
        # Test agent retrieval by capability
        script_agents = await state_manager.get_agents_by_capability("script_generation")
        scene_agents = await state_manager.get_agents_by_capability("scene_planning")
        
        assert len(script_agents) >= 2  # At least agents 0, 3
        assert len(scene_agents) >= 2  # At least agents 1, 4
        
        # Test agent retrieval by status
        available_agents = await state_manager.get_agents_by_status(AgentStatus.AVAILABLE)
        busy_agents = await state_manager.get_agents_by_status(AgentStatus.BUSY)
        
        assert len(available_agents) >= 3  # At least the even-indexed agents
        assert len(busy_agents) >= 3  # At least the odd-indexed agents
        
        # Cleanup
        for agent in agents:
            await state_manager.delete_agent(agent.id)
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_task_indexing(self, redis_client, project, workflow, sample_task_data):
        """Test task indexing operations."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        workflow_obj = Workflow(**workflow)
        await state_manager.save_project(project_obj)
        await state_manager.save_workflow(workflow_obj)
        
        # Create multiple tasks
        tasks = []
        statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
        
        for i in range(9):
            task_data = sample_task_data.copy()
            task_data.update({
                "id": f"index_test_task_{i}",
                "workflow_id": workflow_obj.id,
                "project_id": project_obj.id,
                "name": f"Index Test Task {i}",
                "status": statuses[i % len(statuses)],
                "agent_id": f"test_agent_{i % 3}"
            })
            task = Task(**task_data)
            await state_manager.save_task(task)
            tasks.append(task)
        
        # Test task retrieval by workflow
        workflow_tasks = await state_manager.get_tasks_by_workflow(workflow_obj.id)
        assert len(workflow_tasks) >= 9
        
        # Test task retrieval by agent
        agent_tasks = await state_manager.get_tasks_by_agent("test_agent_0")
        assert len(agent_tasks) >= 3  # Tasks 0, 3, 6
        
        # Test task retrieval by status
        pending_tasks = await state_manager.get_tasks_by_status(TaskStatus.PENDING)
        completed_tasks = await state_manager.get_tasks_by_status(TaskStatus.COMPLETED)
        
        assert len(pending_tasks) >= 3  # At least tasks 0, 3, 6
        assert len(completed_tasks) >= 3  # At least tasks 2, 5, 8
        
        # Cleanup
        for task in tasks:
            await state_manager.delete_task(task.id)


class TestRedisDistributedLocking:
    """Tests for Redis distributed locking mechanisms."""
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_distributed_lock_acquisition(self, redis_client):
        """Test distributed lock acquisition and release."""
        state_manager = RedisStateManager(redis_client)
        
        lock_key = "test:lock:workflow_123"
        lock_value = "test_lock_value"
        
        # Acquire lock
        lock_acquired = await state_manager._acquire_lock(lock_key, lock_value, timeout=10)
        assert lock_acquired is True
        
        # Try to acquire the same lock again (should fail)
        lock_acquired_again = await state_manager._acquire_lock(lock_key, "different_value", timeout=10)
        assert lock_acquired_again is False
        
        # Release lock
        lock_released = await state_manager._release_lock(lock_key, lock_value)
        assert lock_released is True
        
        # Now try to acquire the lock again (should succeed)
        lock_acquired_after_release = await state_manager._acquire_lock(lock_key, "new_value", timeout=10)
        assert lock_acquired_after_release is True
        
        # Cleanup
        await state_manager._release_lock(lock_key, "new_value")
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_distributed_lock_timeout(self, redis_client):
        """Test distributed lock timeout."""
        state_manager = RedisStateManager(redis_client)
        
        lock_key = "test:lock:timeout_test"
        lock_value = "timeout_test_value"
        
        # Acquire lock with short timeout
        lock_acquired = await state_manager._acquire_lock(lock_key, lock_value, timeout=1)
        assert lock_acquired is True
        
        # Wait for lock to expire
        await asyncio.sleep(2)
        
        # Try to acquire the lock again (should succeed after timeout)
        lock_acquired_after_timeout = await state_manager._acquire_lock(lock_key, "new_value", timeout=10)
        assert lock_acquired_after_timeout is True
        
        # Cleanup
        await state_manager._release_lock(lock_key, "new_value")
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_concurrent_lock_access(self, redis_client):
        """Test concurrent lock access."""
        state_manager = RedisStateManager(redis_client)
        
        lock_key = "test:lock:concurrent"
        
        async def try_acquire_lock(lock_value, results, index):
            """Helper function to try acquiring lock."""
            result = await state_manager._acquire_lock(lock_key, lock_value, timeout=10)
            results[index] = result
            if result:
                # Hold the lock briefly
                await asyncio.sleep(0.1)
                await state_manager._release_lock(lock_key, lock_value)
        
        # Test concurrent lock acquisition
        results = [None] * 5
        tasks = []
        
        for i in range(5):
            task = try_acquire_lock(f"concurrent_value_{i}", results, i)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Only one should have acquired the lock
        successful_acquisitions = sum(1 for result in results if result)
        assert successful_acquisitions == 1


class TestRedisCleanupOperations:
    """Tests for Redis cleanup operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_expired_data_cleanup(self, redis_client, sample_workflow_data):
        """Test cleanup of expired data."""
        state_manager = RedisStateManager(redis_client)
        
        # Create old and new workflows
        from datetime import datetime, timedelta
        
        old_date = datetime.utcnow() - timedelta(days=31)  # 31 days old
        recent_date = datetime.utcnow() - timedelta(days=1)  # 1 day old
        
        # Create old workflow
        old_workflow_data = sample_workflow_data.copy()
        old_workflow_data.update({
            "id": "old_workflow_for_cleanup",
            "created_at": old_date,
            "updated_at": old_date
        })
        old_workflow = Workflow(**old_workflow_data)
        await state_manager.save_workflow(old_workflow)
        
        # Create recent workflow
        recent_workflow_data = sample_workflow_data.copy()
        recent_workflow_data.update({
            "id": "recent_workflow_no_cleanup",
            "created_at": recent_date,
            "updated_at": recent_date
        })
        recent_workflow = Workflow(**recent_workflow_data)
        await state_manager.save_workflow(recent_workflow)
        
        # Run cleanup (max_age_days=30)
        deleted_count = await state_manager.cleanup_expired_data(max_age_days=30)
        
        # Verify old workflow was deleted
        old_workflow_after = await state_manager.get_workflow("old_workflow_for_cleanup")
        assert old_workflow_after is None
        
        # Verify recent workflow was not deleted
        recent_workflow_after = await state_manager.get_workflow("recent_workflow_no_cleanup")
        assert recent_workflow_after is not None
        
        # Cleanup remaining data
        await state_manager.delete_workflow("recent_workflow_no_cleanup")
    
    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_cleanup_performance(self, redis_client, sample_workflow_data):
        """Test cleanup performance with large dataset."""
        state_manager = RedisStateManager(redis_client)
        
        from datetime import datetime, timedelta
        
        # Create multiple old workflows
        num_old_workflows = 20
        old_date = datetime.utcnow() - timedelta(days=32)
        
        for i in range(num_old_workflows):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"cleanup_perf_workflow_{i}",
                "created_at": old_date,
                "updated_at": old_date
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
        
        # Measure cleanup performance
        start_time = datetime.utcnow()
        deleted_count = await state_manager.cleanup_expired_data(max_age_days=30)
        cleanup_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify performance
        assert deleted_count >= num_old_workflows
        assert cleanup_time < 5.0  # Should complete within 5 seconds
        
        print(f"Cleaned up {deleted_count} workflows in {cleanup_time:.2f} seconds")
        print(f"Average cleanup time: {cleanup_time/deleted_count:.3f} seconds per workflow")