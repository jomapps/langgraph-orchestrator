import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import json
import time

from src.models import Workflow, Agent, Task, Project
from src.models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from src.models.agent import AgentStatus, AgentCategory
from src.models.task import TaskStatus, TaskPriority
from src.services import RedisStateManager
from src.orchestrator import WorkflowOrchestrator


class TestRedisStateManager:
    """Unit tests for Redis state manager."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_redis_connection(self, redis_client):
        """Test Redis connection and basic operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Test connection
        assert await state_manager.connect() is True
        assert await state_manager.ping() is True
        
        # Test basic set/get operations
        test_key = "test:connection:ping"
        test_value = "pong"
        
        await redis_client.set(test_key, test_value)
        result = await redis_client.get(test_key)
        assert result.decode() == test_value
        
        # Cleanup
        await redis_client.delete(test_key)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_crud_operations(self, redis_client, sample_workflow_data):
        """Test workflow CRUD operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create workflow
        workflow = Workflow(**sample_workflow_data)
        result = await state_manager.save_workflow(workflow)
        assert result is True
        
        # Read workflow
        retrieved_workflow = await state_manager.get_workflow(workflow.id)
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == workflow.id
        assert retrieved_workflow.metadata["title"] == sample_workflow_data["metadata"]["title"]
        
        # Update workflow
        retrieved_workflow.status = WorkflowStatus.RUNNING
        retrieved_workflow.progress = 50.0
        update_result = await state_manager.save_workflow(retrieved_workflow)
        assert update_result is True
        
        # Verify update
        updated_workflow = await state_manager.get_workflow(workflow.id)
        assert updated_workflow.status == WorkflowStatus.RUNNING
        assert updated_workflow.progress == 50.0
        
        # Delete workflow
        delete_result = await state_manager.delete_workflow(workflow.id)
        assert delete_result is True
        
        # Verify deletion
        deleted_workflow = await state_manager.get_workflow(workflow.id)
        assert deleted_workflow is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_crud_operations(self, redis_client, sample_agent_data):
        """Test agent CRUD operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create agent
        agent = Agent(**sample_agent_data)
        result = await state_manager.save_agent(agent)
        assert result is True
        
        # Read agent
        retrieved_agent = await state_manager.get_agent(agent.id)
        assert retrieved_agent is not None
        assert retrieved_agent.id == agent.id
        assert retrieved_agent.name == sample_agent_data["name"]
        
        # Update agent
        retrieved_agent.status = AgentStatus.BUSY
        retrieved_agent.health_status = {"status": "degraded", "message": "High CPU usage"}
        update_result = await state_manager.save_agent(retrieved_agent)
        assert update_result is True
        
        # Verify update
        updated_agent = await state_manager.get_agent(agent.id)
        assert updated_agent.status == AgentStatus.BUSY
        assert updated_agent.health_status["status"] == "degraded"
        
        # Delete agent
        delete_result = await state_manager.delete_agent(agent.id)
        assert delete_result is True
        
        # Verify deletion
        deleted_agent = await state_manager.get_agent(agent.id)
        assert deleted_agent is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_task_crud_operations(self, redis_client, sample_task_data):
        """Test task CRUD operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create task
        task = Task(**sample_task_data)
        result = await state_manager.save_task(task)
        assert result is True
        
        # Read task
        retrieved_task = await state_manager.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.name == sample_task_data["name"]
        
        # Update task
        retrieved_task.status = TaskStatus.IN_PROGRESS
        retrieved_task.retry_count = 1
        update_result = await state_manager.save_task(retrieved_task)
        assert update_result is True
        
        # Verify update
        updated_task = await state_manager.get_task(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.retry_count == 1
        
        # Delete task
        delete_result = await state_manager.delete_task(task.id)
        assert delete_result is True
        
        # Verify deletion
        deleted_task = await state_manager.get_task(task.id)
        assert deleted_task is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_project_crud_operations(self, redis_client, sample_project_data):
        """Test project CRUD operations."""
        state_manager = RedisStateManager(redis_client)
        
        # Create project
        project = Project(**sample_project_data)
        result = await state_manager.save_project(project)
        assert result is True
        
        # Read project
        retrieved_project = await state_manager.get_project(project.id)
        assert retrieved_project is not None
        assert retrieved_project.id == project.id
        assert retrieved_project.name == sample_project_data["name"]
        
        # Update project
        retrieved_project.configuration = {"new_setting": "value"}
        retrieved_project.resource_limits = {"max_workflows": 10}
        update_result = await state_manager.save_project(retrieved_project)
        assert update_result is True
        
        # Verify update
        updated_project = await state_manager.get_project(project.id)
        assert updated_project.configuration["new_setting"] == "value"
        assert updated_project.resource_limits["max_workflows"] == 10
        
        # Delete project
        delete_result = await state_manager.delete_project(project.id)
        assert delete_result is True
        
        # Verify deletion
        deleted_project = await state_manager.get_project(project.id)
        assert deleted_project is None


class TestWorkflowOrchestratorUnit:
    """Unit tests for workflow orchestrator."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_initialization(self, redis_client, sample_workflow_data):
        """Test workflow initialization."""
        state_manager = RedisStateManager(redis_client)
        orchestrator = WorkflowOrchestrator(state_manager)
        
        workflow = Workflow(**sample_workflow_data)
        
        # Test workflow initialization
        workflow_id = await orchestrator.start_workflow(workflow)
        assert workflow_id == workflow.id
        
        # Verify workflow was saved to Redis
        saved_workflow = await state_manager.get_workflow(workflow_id)
        assert saved_workflow is not None
        assert saved_workflow.status == WorkflowStatus.RUNNING
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_state_transitions(self, redis_client, sample_workflow_data):
        """Test workflow state transitions."""
        state_manager = RedisStateManager(redis_client)
        orchestrator = WorkflowOrchestrator(state_manager)
        
        workflow = Workflow(**sample_workflow_data)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Test pause transition
        pause_result = await orchestrator.pause_workflow(workflow_id)
        assert pause_result is True
        
        paused_workflow = await state_manager.get_workflow(workflow_id)
        assert paused_workflow.status == WorkflowStatus.PAUSED
        
        # Test resume transition
        resume_result = await orchestrator.resume_workflow(workflow_id)
        assert resume_result is True
        
        resumed_workflow = await state_manager.get_workflow(workflow_id)
        assert resumed_workflow.status == WorkflowStatus.RUNNING
        
        # Test cancel transition
        cancel_result = await orchestrator.cancel_workflow(workflow_id)
        assert cancel_result is True
        
        cancelled_workflow = await state_manager.get_workflow(workflow_id)
        assert cancelled_workflow.status == WorkflowStatus.CANCELLED
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_status_retrieval(self, redis_client, sample_workflow_data):
        """Test workflow status retrieval."""
        state_manager = RedisStateManager(redis_client)
        orchestrator = WorkflowOrchestrator(state_manager)
        
        workflow = Workflow(**sample_workflow_data)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Get workflow status
        status = await orchestrator.get_workflow_status(workflow_id)
        assert status is not None
        assert "workflow" in status
        assert "tasks" in status
        assert "agents" in status
        assert status["workflow"].id == workflow_id
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_selection(self, redis_client, sample_workflow_data, sample_agent_data):
        """Test agent selection logic."""
        state_manager = RedisStateManager(redis_client)
        orchestrator = WorkflowOrchestrator(state_manager)
        
        # Create test agents
        agents = []
        for i in range(3):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"test_agent_{i}",
                "name": f"Test Agent {i}",
                "status": AgentStatus.AVAILABLE if i < 2 else AgentStatus.BUSY,
                "capabilities": ["script_generation"],
                "performance_metrics": {"error_rate": 0.1 * i, "avg_response_time": 1.0 + i}
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
            agents.append(agent)
        
        # Test agent selection
        selected_agent = await orchestrator._select_agent("script_generation")
        assert selected_agent is not None
        assert selected_agent.status == AgentStatus.AVAILABLE
        assert "script_generation" in selected_agent.capabilities


class TestTaskManagementUnit:
    """Unit tests for task management."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_task_lifecycle(self, redis_client, sample_task_data):
        """Test complete task lifecycle."""
        state_manager = RedisStateManager(redis_client)
        
        # Create task
        task = Task(**sample_task_data)
        
        # Test task assignment
        task.assign_to_agent("test_agent_123")
        assert task.agent_id == "test_agent_123"
        assert task.status == TaskStatus.PENDING
        
        # Test task start
        task.start()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        
        # Test task completion
        result = {"output": "Task completed successfully", "metrics": {"duration": 10.5}}
        task.complete(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.completed_at is not None
        
        # Test task failure
        failed_task = Task(**sample_task_data)
        failed_task.start()
        failed_task.fail("Task failed due to timeout")
        assert failed_task.status == TaskStatus.FAILED
        assert failed_task.error_message == "Task failed due to timeout"
        assert failed_task.completed_at is not None
        
        # Test task retry
        failed_task.retry()
        assert failed_task.status == TaskStatus.PENDING
        assert failed_task.retry_count == 1
        assert failed_task.error_message is None
        assert failed_task.completed_at is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_task_dependency_management(self, redis_client, sample_task_data):
        """Test task dependency management."""
        state_manager = RedisStateManager(redis_client)
        
        # Create tasks with dependencies
        task1 = Task(**sample_task_data)
        task1.id = "task_1"
        
        task2_data = sample_task_data.copy()
        task2_data["id"] = "task_2"
        task2_data["dependencies"] = ["task_1"]
        task2 = Task(**task2_data)
        
        # Test dependency checking
        assert task2.has_dependencies() is True
        assert task2.dependencies == ["task_1"]
        
        # Test dependency resolution (mock)
        # In a real scenario, this would check if task_1 is completed
        task1.status = TaskStatus.COMPLETED
        await state_manager.save_task(task1)
        
        # Test that task2 can start when dependencies are met
        # (This would be handled by the orchestrator in practice)
        assert task1.status == TaskStatus.COMPLETED


class TestAgentManagementUnit:
    """Unit tests for agent management."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_health_monitoring(self, redis_client, sample_agent_data):
        """Test agent health monitoring."""
        state_manager = RedisStateManager(redis_client)
        
        # Create agent
        agent = Agent(**sample_agent_data)
        
        # Test initial health status
        assert agent.health_status["status"] == "healthy"
        assert agent.health_status["message"] == "Ready"
        
        # Test health update
        agent.update_health("degraded", "High memory usage detected")
        assert agent.health_status["status"] == "degraded"
        assert agent.health_status["message"] == "High memory usage detected"
        
        # Test performance metrics update
        agent.update_performance_metrics(error_rate=0.15, avg_response_time=3.5)
        assert agent.performance_metrics["error_rate"] == 0.15
        assert agent.performance_metrics["avg_response_time"] == 3.5
        
        # Test reliability calculation
        reliability = agent.get_reliability_score()
        assert 0 <= reliability <= 1
        assert reliability < 0.9  # Due to high error rate
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_capability_matching(self, redis_client, sample_agent_data):
        """Test agent capability matching."""
        state_manager = RedisStateManager(redis_client)
        
        # Create agent with specific capabilities
        agent_data = sample_agent_data.copy()
        agent_data["capabilities"] = ["script_generation", "scene_planning", "voice_generation"]
        agent_data["specializations"] = ["educational_content", "entertainment"]
        agent = Agent(**agent_data)
        
        # Test capability matching
        assert agent.has_capability("script_generation") is True
        assert agent.has_capability("scene_planning") is True
        assert agent.has_capability("video_editing") is False
        
        # Test specialization matching
        assert agent.has_specialization("educational_content") is True
        assert agent.has_specialization("entertainment") is True
        assert agent.has_specialization("marketing") is False
        
        # Test capability score calculation
        required_capabilities = ["script_generation", "scene_planning"]
        score = agent.get_capability_score(required_capabilities)
        assert score == 1.0  # All required capabilities present
        
        required_capabilities = ["script_generation", "video_editing"]
        score = agent.get_capability_score(required_capabilities)
        assert score == 0.5  # Only half of required capabilities present


class TestProjectManagementUnit:
    """Unit tests for project management."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_project_lifecycle(self, redis_client, sample_project_data):
        """Test complete project lifecycle."""
        state_manager = RedisStateManager(redis_client)
        
        # Create project
        project = Project(**sample_project_data)
        
        # Test project activation/deactivation
        assert project.is_active is True
        
        project.deactivate()
        assert project.is_active is False
        
        project.activate()
        assert project.is_active is True
        
        # Test configuration updates
        new_config = {"new_setting": "value", "timeout": 300}
        project.update_configuration(new_config)
        assert project.configuration == new_config
        
        # Test resource limit updates
        new_limits = {"max_workflows": 10, "max_agents": 5}
        project.update_resource_limits(new_limits)
        assert project.resource_limits == new_limits
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_project_workflow_association(self, redis_client, sample_project_data, sample_workflow_data):
        """Test project-workflow association."""
        state_manager = RedisStateManager(redis_client)
        
        # Create project
        project = Project(**sample_project_data)
        await state_manager.save_project(project)
        
        # Create workflows associated with project
        workflows = []
        for i in range(3):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"project_workflow_{i}",
                "project_id": project.id,
                "metadata": {"title": f"Project Workflow {i}"}
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
            workflows.append(workflow)
        
        # Retrieve workflows by project
        project_workflows = await state_manager.get_workflows(project_id=project.id)
        assert len(project_workflows) == 3
        
        # Verify all workflows belong to the project
        for workflow in project_workflows:
            assert workflow.project_id == project.id


class TestExecutionContextUnit:
    """Unit tests for execution context."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execution_context_lifecycle(self, redis_client):
        """Test execution context lifecycle."""
        state_manager = RedisStateManager(redis_client)
        
        # Create execution context
        context = ExecutionContext(
            workflow_id="test_workflow_123",
            project_id="test_project_456",
            current_state="script_generation",
            previous_state="initialization",
            runtime_variables={"script_length": 500, "tone": "educational"},
            shared_data={"common_assets": ["asset1", "asset2"]},
            execution_history=["initialized", "script_generation_started"],
            agent_states={"agent_1": "working", "agent_2": "idle"},
            task_states={"task_1": "completed", "task_2": "in_progress"},
            metadata={"version": "1.0", "environment": "test"},
            checkpoints={"checkpoint_1": {"data": "state_at_checkpoint_1"}},
            error_count=0,
            retry_attempts={},
            performance_metrics={"execution_time": 0, "memory_usage": 0},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test state transitions
        context.update_state("scene_planning", "script_generation")
        assert context.current_state == "scene_planning"
        assert context.previous_state == "script_generation"
        assert "scene_planning" in context.execution_history
        
        # Test variable management
        context.set_variable("scene_count", 5)
        assert context.get_variable("scene_count") == 5
        assert context.get_variable("non_existent") is None
        
        # Test error handling
        context.record_error("Scene planning failed", "agent_1")
        assert context.error_count == 1
        assert "agent_1" in context.retry_attempts
        
        # Test performance tracking
        context.update_performance_metrics(execution_time=15.5, memory_usage=1024)
        assert context.performance_metrics["execution_time"] == 15.5
        assert context.performance_metrics["memory_usage"] == 1024
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_checkpoint_management(self, redis_client):
        """Test checkpoint management."""
        state_manager = RedisStateManager(redis_client)
        
        context = ExecutionContext(
            workflow_id="test_workflow_123",
            project_id="test_project_456",
            current_state="script_generation",
            previous_state="initialization",
            runtime_variables={},
            shared_data={},
            execution_history=[],
            agent_states={},
            task_states={},
            metadata={},
            checkpoints={},
            error_count=0,
            retry_attempts={},
            performance_metrics={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test checkpoint creation
        checkpoint_data = {
            "current_state": "scene_planning",
            "variables": {"scene_count": 3, "current_scene": 1},
            "agent_states": {"agent_1": "working"}
        }
        
        context.create_checkpoint("checkpoint_1", checkpoint_data)
        assert "checkpoint_1" in context.checkpoints
        assert context.checkpoints["checkpoint_1"] == checkpoint_data
        
        # Test checkpoint retrieval
        retrieved_checkpoint = context.get_checkpoint("checkpoint_1")
        assert retrieved_checkpoint == checkpoint_data
        
        # Test checkpoint restoration (mock)
        # In practice, this would restore the context state
        assert retrieved_checkpoint["current_state"] == "scene_planning"


class TestErrorHandlingUnit:
    """Unit tests for error handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_redis_connection_error_handling(self, redis_client):
        """Test Redis connection error handling."""
        # Test with invalid Redis client (simulated)
        # This would normally test connection errors, timeouts, etc.
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_error_handling(self, redis_client, sample_workflow_data):
        """Test workflow error handling."""
        state_manager = RedisStateManager(redis_client)
        orchestrator = WorkflowOrchestrator(state_manager)
        
        # Test handling of non-existent workflow
        non_existent_workflow_id = "non_existent_workflow_123"
        
        result = await orchestrator.pause_workflow(non_existent_workflow_id)
        assert result is False
        
        result = await orchestrator.resume_workflow(non_existent_workflow_id)
        assert result is False
        
        result = await orchestrator.cancel_workflow(non_existent_workflow_id)
        assert result is False
        
        status = await orchestrator.get_workflow_status(non_existent_workflow_id)
        assert status is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_error_handling(self, redis_client, sample_agent_data):
        """Test agent error handling."""
        state_manager = RedisStateManager(redis_client)
        
        # Test handling of non-existent agent
        non_existent_agent_id = "non_existent_agent_123"
        
        agent = await state_manager.get_agent(non_existent_agent_id)
        assert agent is None
        
        result = await state_manager.delete_agent(non_existent_agent_id)
        assert result is False
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_task_error_handling(self, redis_client, sample_task_data):
        """Test task error handling."""
        state_manager = RedisStateManager(redis_client)
        
        # Test handling of non-existent task
        non_existent_task_id = "non_existent_task_123"
        
        task = await state_manager.get_task(non_existent_task_id)
        assert task is None
        
        result = await state_manager.delete_task(non_existent_task_id)
        assert result is False