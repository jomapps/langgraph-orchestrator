import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from src.models import Workflow, Agent, Task, Project, ExecutionContext
from src.models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from src.models.agent import AgentStatus, AgentCategory
from src.models.task import TaskStatus, TaskPriority
from src.services import RedisStateManager
from src.orchestrator import WorkflowOrchestrator


class TestWorkflowPerformance:
    """Performance tests for workflow orchestration."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_workflow_creation_performance(self, redis_client, project, sample_workflow_data):
        """Test performance of creating multiple workflows."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        await state_manager.save_project(project_obj)
        
        # Create multiple workflows
        num_workflows = 50
        start_time = datetime.utcnow()
        
        workflows = []
        for i in range(num_workflows):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"perf_workflow_{i}",
                "project_id": project_obj.id,
                "metadata": {"title": f"Performance Test {i}"}
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
            workflows.append(workflow)
        
        creation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify all workflows were created
        assert len(workflows) == num_workflows
        assert creation_time < 10.0  # Should complete within 10 seconds
        
        print(f"Created {num_workflows} workflows in {creation_time:.2f} seconds")
        print(f"Average creation time: {creation_time/num_workflows:.3f} seconds per workflow")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_workflow_query_performance(self, redis_client, project, sample_workflow_data):
        """Test performance of querying workflows."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        await state_manager.save_project(project_obj)
        
        # Create test workflows with different statuses
        statuses = [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED]
        num_workflows_per_status = 20
        
        for i in range(num_workflows_per_status * len(statuses)):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"query_perf_workflow_{i}",
                "project_id": project_obj.id,
                "status": statuses[i % len(statuses)],
                "metadata": {"title": f"Query Performance Test {i}"}
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
        
        # Test query performance
        num_queries = 100
        start_time = datetime.utcnow()
        
        for _ in range(num_queries):
            workflows = await state_manager.get_workflows(
                project_id=project_obj.id,
                status=WorkflowStatus.RUNNING
            )
        
        query_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert query_time < 5.0  # Should complete within 5 seconds
        print(f"Executed {num_queries} queries in {query_time:.2f} seconds")
        print(f"Average query time: {query_time/num_queries:.3f} seconds per query")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_workflow_execution(self, redis_client, project, sample_workflow_data, sample_agent_data):
        """Test performance of concurrent workflow execution."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        await state_manager.save_project(project_obj)
        
        # Register multiple agents
        num_agents = 10
        agents = []
        for i in range(num_agents):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"concurrent_agent_{i}",
                "name": f"Concurrent Agent {i}",
                "capabilities": ["script_generation", "scene_planning", "voice_generation"]
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
            agents.append(agent)
        
        # Create multiple workflows
        num_workflows = 20
        workflows = []
        for i in range(num_workflows):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"concurrent_workflow_{i}",
                "project_id": project_obj.id,
                "type": WorkflowType.VIDEO_CREATION,
                "metadata": {"title": f"Concurrent Test {i}"}
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
            workflows.append(workflow)
        
        # Start all workflows concurrently
        orchestrator = WorkflowOrchestrator(state_manager)
        start_time = datetime.utcnow()
        
        # Start workflows with slight delays to avoid overwhelming the system
        start_tasks = []
        for i, workflow in enumerate(workflows):
            task = asyncio.create_task(
                self._start_workflow_with_delay(orchestrator, workflow, i * 0.1)
            )
            start_tasks.append(task)
        
        # Wait for all workflows to start
        workflow_ids = await asyncio.gather(*start_tasks)
        
        # Wait for workflows to complete (with timeout)
        timeout = 60  # 60 seconds
        completed_workflows = 0
        start_wait = datetime.utcnow()
        
        while (datetime.utcnow() - start_wait).seconds < timeout:
            completed_count = 0
            for workflow_id in workflow_ids:
                workflow = await state_manager.get_workflow(workflow_id)
                if workflow and workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                    completed_count += 1
            
            if completed_count == len(workflow_ids):
                completed_workflows = completed_count
                break
            
            await asyncio.sleep(1)
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify results
        assert completed_workflows == len(workflow_ids)
        assert total_time < timeout
        
        print(f"Executed {num_workflows} concurrent workflows in {total_time:.2f} seconds")
        print(f"Average execution time: {total_time/num_workflows:.3f} seconds per workflow")
    
    async def _start_workflow_with_delay(self, orchestrator, workflow, delay):
        """Helper method to start workflow with delay."""
        await asyncio.sleep(delay)
        return await orchestrator.start_workflow(workflow)


class TestAgentPerformance:
    """Performance tests for agent management."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_agent_registration_performance(self, redis_client, sample_agent_data):
        """Test performance of registering multiple agents."""
        state_manager = RedisStateManager(redis_client)
        
        # Register multiple agents
        num_agents = 100
        start_time = datetime.utcnow()
        
        agents = []
        for i in range(num_agents):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"perf_agent_{i}",
                "name": f"Performance Agent {i}",
                "capabilities": [f"capability_{j}" for j in range(5)]
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
            agents.append(agent)
        
        registration_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify all agents were registered
        assert len(agents) == num_agents
        assert registration_time < 15.0  # Should complete within 15 seconds
        
        print(f"Registered {num_agents} agents in {registration_time:.2f} seconds")
        print(f"Average registration time: {registration_time/num_agents:.3f} seconds per agent")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_agent_query_performance(self, redis_client, sample_agent_data):
        """Test performance of querying agents by capabilities."""
        state_manager = RedisStateManager(redis_client)
        
        # Register agents with different capabilities
        capabilities = ["script_generation", "scene_planning", "voice_generation", "video_editing"]
        num_agents_per_capability = 25
        
        for i in range(num_agents_per_capability * len(capabilities)):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"query_perf_agent_{i}",
                "name": f"Query Performance Agent {i}",
                "capabilities": [capabilities[i % len(capabilities)]],
                "status": AgentStatus.AVAILABLE if i % 3 != 0 else AgentStatus.BUSY
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
        
        # Test query performance
        num_queries = 50
        start_time = datetime.utcnow()
        
        for _ in range(num_queries):
            agents = await state_manager.get_agents_by_capability("script_generation", status="available")
        
        query_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert query_time < 3.0  # Should complete within 3 seconds
        print(f"Executed {num_queries} capability queries in {query_time:.2f} seconds")
        print(f"Average query time: {query_time/num_queries:.3f} seconds per query")


class TestTaskPerformance:
    """Performance tests for task management."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_task_creation_performance(self, redis_client, project, workflow, sample_task_data):
        """Test performance of creating multiple tasks."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        workflow_obj = Workflow(**workflow)
        await state_manager.save_project(project_obj)
        await state_manager.save_workflow(workflow_obj)
        
        # Create multiple tasks
        num_tasks = 200
        start_time = datetime.utcnow()
        
        tasks = []
        for i in range(num_tasks):
            task_data = sample_task_data.copy()
            task_data.update({
                "id": f"perf_task_{i}",
                "workflow_id": workflow_obj.id,
                "project_id": project_obj.id,
                "name": f"Performance Task {i}",
                "status": TaskStatus.PENDING
            })
            task = Task(**task_data)
            await state_manager.save_task(task)
            tasks.append(task)
        
        creation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify all tasks were created
        assert len(tasks) == num_tasks
        assert creation_time < 20.0  # Should complete within 20 seconds
        
        print(f"Created {num_tasks} tasks in {creation_time:.2f} seconds")
        print(f"Average creation time: {creation_time/num_tasks:.3f} seconds per task")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_task_status_update_performance(self, redis_client, project, workflow, sample_task_data):
        """Test performance of updating task statuses."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        workflow_obj = Workflow(**workflow)
        await state_manager.save_project(project_obj)
        await state_manager.save_workflow(workflow_obj)
        
        # Create tasks
        num_tasks = 100
        tasks = []
        for i in range(num_tasks):
            task_data = sample_task_data.copy()
            task_data.update({
                "id": f"status_task_{i}",
                "workflow_id": workflow_obj.id,
                "project_id": project_obj.id,
                "name": f"Status Update Task {i}",
                "status": TaskStatus.PENDING
            })
            task = Task(**task_data)
            await state_manager.save_task(task)
            tasks.append(task)
        
        # Test status update performance
        num_updates = 50
        start_time = datetime.utcnow()
        
        for i in range(num_updates):
            task = tasks[i % num_tasks]
            task.status = TaskStatus.IN_PROGRESS if i % 2 == 0 else TaskStatus.COMPLETED
            await state_manager.save_task(task)
        
        update_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert update_time < 5.0  # Should complete within 5 seconds
        print(f"Updated {num_updates} task statuses in {update_time:.2f} seconds")
        print(f"Average update time: {update_time/num_updates:.3f} seconds per update")


class TestMemoryAndResourceUsage:
    """Tests for memory usage and resource management."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_dataset_handling(self, redis_client, project, sample_workflow_data, sample_agent_data):
        """Test handling of large datasets."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        await state_manager.save_project(project_obj)
        
        # Create large dataset
        num_workflows = 100
        num_agents = 50
        num_tasks_per_workflow = 10
        
        print(f"Creating large dataset: {num_workflows} workflows, {num_agents} agents, {num_workflows * num_tasks_per_workflow} tasks")
        
        # Create agents
        for i in range(num_agents):
            agent_data = sample_agent_data.copy()
            agent_data.update({
                "id": f"large_dataset_agent_{i}",
                "name": f"Large Dataset Agent {i}",
                "capabilities": ["script_generation", "scene_planning", "voice_generation"]
            })
            agent = Agent(**agent_data)
            await state_manager.save_agent(agent)
        
        # Create workflows and tasks
        for i in range(num_workflows):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"large_workflow_{i}",
                "project_id": project_obj.id,
                "metadata": {"title": f"Large Dataset Workflow {i}", "description": "x" * 1000}  # Large metadata
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
            
            # Create tasks for each workflow
            for j in range(num_tasks_per_workflow):
                task = Task(
                    id=f"large_task_{i}_{j}",
                    workflow_id=workflow.id,
                    project_id=project_obj.id,
                    name=f"Large Dataset Task {i}_{j}",
                    description="x" * 500,  # Large description
                    type="script_generation",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                    parameters={"param1": "x" * 200, "param2": "y" * 200},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await state_manager.save_task(task)
        
        # Test query performance on large dataset
        start_time = datetime.utcnow()
        
        # Query workflows by status
        workflows = await state_manager.get_workflows(project_id=project_obj.id)
        
        query_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify results
        assert len(workflows) == num_workflows
        assert query_time < 10.0  # Should complete within 10 seconds
        
        print(f"Queried {len(workflows)} workflows in {query_time:.2f} seconds")
        print(f"Dataset creation completed successfully")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cleanup_performance(self, redis_client, project, sample_workflow_data):
        """Test performance of cleanup operations."""
        state_manager = RedisStateManager(redis_client)
        project_obj = Project(**project)
        await state_manager.save_project(project_obj)
        
        # Create old workflows to be cleaned up
        num_old_workflows = 50
        old_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(num_old_workflows):
            workflow_data = sample_workflow_data.copy()
            workflow_data.update({
                "id": f"cleanup_workflow_{i}",
                "project_id": project_obj.id,
                "metadata": {"title": f"Cleanup Test {i}"},
                "created_at": old_date,
                "updated_at": old_date
            })
            workflow = Workflow(**workflow_data)
            await state_manager.save_workflow(workflow)
        
        # Test cleanup performance
        start_time = datetime.utcnow()
        
        deleted_count = await state_manager.cleanup_expired_data(max_age_days=29)
        
        cleanup_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify cleanup results
        assert deleted_count >= num_old_workflows
        assert cleanup_time < 5.0  # Should complete within 5 seconds
        
        print(f"Cleaned up {deleted_count} expired items in {cleanup_time:.2f} seconds")
        print(f"Average cleanup time: {cleanup_time/deleted_count:.3f} seconds per item")