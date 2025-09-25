import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from src.models import Workflow, Agent, Task, Project
from src.models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from src.models.agent import AgentStatus, AgentCategory
from src.models.task import TaskStatus, TaskPriority
from src.services import RedisStateManager
from src.orchestrator import WorkflowOrchestrator


class TestWorkflowIntegration:
    """Integration tests for workflow orchestration."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_video_creation_workflow(self, redis_client, api_client, project, sample_workflow_data):
        """Test complete video creation workflow execution."""
        # Create project
        project_obj = Project(**project)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project_obj)
        
        # Create workflow
        workflow_data = sample_workflow_data.copy()
        workflow_data["project_id"] = project_obj.id
        workflow_data["type"] = WorkflowType.VIDEO_CREATION
        workflow = Workflow(**workflow_data)
        await state_manager.save_workflow(workflow)
        
        # Register required agents
        agents = [
            Agent(
                id=f"script_gen_agent_{i}",
                name=f"Script Generator {i}",
                category=AgentCategory.CONTENT_GENERATION,
                status=AgentStatus.AVAILABLE,
                capabilities=["script_generation"],
                specializations=["educational_content", "entertainment"],
                version="1.0.0",
                description="Script generation agent",
                author="TestAuthor",
                resource_limits={"cpu": 2, "memory": "4GB"},
                performance_metrics={"error_rate": 0.1, "avg_response_time": 2.0},
                health_status={"status": "healthy", "message": "Ready"},
                configuration={"model": "gpt-4", "temperature": 0.7}
            )
            for i in range(2)
        ]
        
        for agent in agents:
            await state_manager.save_agent(agent)
        
        # Start workflow
        orchestrator = WorkflowOrchestrator(state_manager)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Wait for workflow to complete (with timeout)
        timeout = 30  # seconds
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).seconds < timeout:
            workflow_status = await orchestrator.get_workflow_status(workflow_id)
            if workflow_status and workflow_status["workflow"].status == WorkflowStatus.COMPLETED:
                break
            await asyncio.sleep(1)
        
        # Verify workflow completed
        final_workflow = await state_manager.get_workflow(workflow_id)
        assert final_workflow.status == WorkflowStatus.COMPLETED
        assert final_workflow.progress == 100.0
        assert final_workflow.state == WorkflowState.FINISHED
        
        # Verify tasks were created
        tasks = await state_manager.get_tasks_by_workflow(workflow_id)
        assert len(tasks) > 0
        
        # Verify at least one task was completed
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        assert len(completed_tasks) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_pause_resume(self, redis_client, api_client, project, sample_workflow_data):
        """Test workflow pause and resume functionality."""
        # Create project and workflow
        project_obj = Project(**project)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project_obj)
        
        workflow_data = sample_workflow_data.copy()
        workflow_data["project_id"] = project_obj.id
        workflow = Workflow(**workflow_data)
        await state_manager.save_workflow(workflow)
        
        # Register agents
        agent = Agent(
            id="test_agent_pause",
            name="Test Agent Pause",
            category=AgentCategory.CONTENT_GENERATION,
            status=AgentStatus.AVAILABLE,
            capabilities=["script_generation"],
            specializations=["educational_content"],
            version="1.0.0",
            description="Test agent for pause/resume",
            author="TestAuthor",
            resource_limits={"cpu": 1, "memory": "2GB"},
            performance_metrics={"error_rate": 0.0, "avg_response_time": 1.0},
            health_status={"status": "healthy", "message": "Ready"},
            configuration={}
        )
        await state_manager.save_agent(agent)
        
        # Start workflow
        orchestrator = WorkflowOrchestrator(state_manager)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Wait a bit for workflow to start
        await asyncio.sleep(2)
        
        # Pause workflow
        pause_result = await orchestrator.pause_workflow(workflow_id)
        assert pause_result is True
        
        # Verify workflow is paused
        workflow_status = await orchestrator.get_workflow_status(workflow_id)
        assert workflow_status["workflow"].status == WorkflowStatus.PAUSED
        
        # Resume workflow
        resume_result = await orchestrator.resume_workflow(workflow_id)
        assert resume_result is True
        
        # Verify workflow is running again
        workflow_status = await orchestrator.get_workflow_status(workflow_id)
        assert workflow_status["workflow"].status == WorkflowStatus.RUNNING
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_cancel(self, redis_client, api_client, project, sample_workflow_data):
        """Test workflow cancellation."""
        # Create project and workflow
        project_obj = Project(**project)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project_obj)
        
        workflow_data = sample_workflow_data.copy()
        workflow_data["project_id"] = project_obj.id
        workflow = Workflow(**workflow_data)
        await state_manager.save_workflow(workflow)
        
        # Register agents
        agent = Agent(
            id="test_agent_cancel",
            name="Test Agent Cancel",
            category=AgentCategory.CONTENT_GENERATION,
            status=AgentStatus.AVAILABLE,
            capabilities=["script_generation"],
            specializations=["educational_content"],
            version="1.0.0",
            description="Test agent for cancellation",
            author="TestAuthor",
            resource_limits={"cpu": 1, "memory": "2GB"},
            performance_metrics={"error_rate": 0.0, "avg_response_time": 1.0},
            health_status={"status": "healthy", "message": "Ready"},
            configuration={}
        )
        await state_manager.save_agent(agent)
        
        # Start workflow
        orchestrator = WorkflowOrchestrator(state_manager)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Wait a bit for workflow to start
        await asyncio.sleep(2)
        
        # Cancel workflow
        cancel_result = await orchestrator.cancel_workflow(workflow_id)
        assert cancel_result is True
        
        # Verify workflow is cancelled
        workflow_status = await orchestrator.get_workflow_status(workflow_id)
        assert workflow_status["workflow"].status == WorkflowStatus.CANCELLED


class TestAgentIntegration:
    """Integration tests for agent management."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_registration_and_health(self, redis_client, api_client, sample_agent_data):
        """Test agent registration and health monitoring."""
        state_manager = RedisStateManager(redis_client)
        
        # Register agent
        agent_data = sample_agent_data.copy()
        agent = Agent(**agent_data)
        await state_manager.save_agent(agent)
        
        # Verify agent was registered
        retrieved_agent = await state_manager.get_agent(agent.id)
        assert retrieved_agent is not None
        assert retrieved_agent.name == agent_data["name"]
        assert retrieved_agent.status == AgentStatus.AVAILABLE
        
        # Update agent health
        retrieved_agent.health_status = {"status": "degraded", "message": "High memory usage"}
        retrieved_agent.performance_metrics["error_rate"] = 0.15
        await state_manager.save_agent(retrieved_agent)
        
        # Verify health update
        updated_agent = await state_manager.get_agent(agent.id)
        assert updated_agent.health_status["status"] == "degraded"
        assert updated_agent.performance_metrics["error_rate"] == 0.15
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_task_assignment(self, redis_client, api_client, project, sample_workflow_data, sample_task_data):
        """Test agent task assignment and execution."""
        # Create project and workflow
        project_obj = Project(**project)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project_obj)
        
        workflow_data = sample_workflow_data.copy()
        workflow_data["project_id"] = project_obj.id
        workflow = Workflow(**workflow_data)
        await state_manager.save_workflow(workflow)
        
        # Register agent
        agent = Agent(
            id="task_assignment_agent",
            name="Task Assignment Agent",
            category=AgentCategory.CONTENT_GENERATION,
            status=AgentStatus.AVAILABLE,
            capabilities=["script_generation", "scene_planning"],
            specializations=["educational_content"],
            version="1.0.0",
            description="Agent for task assignment testing",
            author="TestAuthor",
            resource_limits={"cpu": 2, "memory": "4GB"},
            performance_metrics={"error_rate": 0.05, "avg_response_time": 1.5},
            health_status={"status": "healthy", "message": "Ready"},
            configuration={"max_concurrent_tasks": 3}
        )
        await state_manager.save_agent(agent)
        
        # Create and assign task
        task_data = sample_task_data.copy()
        task_data.update({
            "workflow_id": workflow.id,
            "project_id": project_obj.id,
            "agent_id": agent.id,
            "type": "script_generation"
        })
        task = Task(**task_data)
        await state_manager.save_task(task)
        
        # Assign task to agent
        task.assign_to_agent(agent.id)
        task.start()
        await state_manager.save_task(task)
        
        # Verify task assignment
        agent_tasks = await state_manager.get_tasks_by_agent(agent.id)
        assert len(agent_tasks) == 1
        assert agent_tasks[0].id == task.id
        assert agent_tasks[0].status == TaskStatus.IN_PROGRESS
        
        # Complete task
        task.complete({"script": "Generated script content", "word_count": 250})
        await state_manager.save_task(task)
        
        # Verify task completion
        completed_tasks = await state_manager.get_tasks_by_agent(agent.id, status="completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0].status == TaskStatus.COMPLETED
        assert completed_tasks[0].result["script"] == "Generated script content"


class TestProjectIntegration:
    """Integration tests for project management."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_project_workflow_association(self, redis_client, api_client, sample_project_data):
        """Test project and workflow association."""
        state_manager = RedisStateManager(redis_client)
        
        # Create project
        project = Project(**sample_project_data)
        await state_manager.save_project(project)
        
        # Create multiple workflows for the project
        workflows = []
        for i in range(3):
            workflow = Workflow(
                id=f"test_workflow_{i}",
                project_id=project.id,
                type=WorkflowType.VIDEO_CREATION,
                state="pending",
                status=WorkflowStatus.PENDING,
                metadata={"title": f"Test Workflow {i}", "description": f"Test workflow {i}"},
                progress=0.0,
                assigned_agents=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await state_manager.save_workflow(workflow)
            workflows.append(workflow)
        
        # Verify workflows are associated with project
        project_workflows = await state_manager.get_workflows(project_id=project.id)
        assert len(project_workflows) == 3
        
        # Verify all workflows have correct project ID
        for workflow in project_workflows:
            assert workflow.project_id == project.id
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_project_resource_limits(self, redis_client, api_client, sample_project_data):
        """Test project resource limit enforcement."""
        # Create project with resource limits
        project_data = sample_project_data.copy()
        project_data["resource_limits"] = {
            "max_workflows": 2,
            "max_agents": 5,
            "max_concurrent_tasks": 10
        }
        
        project = Project(**project_data)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project)
        
        # Create workflows up to the limit
        for i in range(2):  # max_workflows = 2
            workflow = Workflow(
                id=f"resource_test_workflow_{i}",
                project_id=project.id,
                type=WorkflowType.VIDEO_CREATION,
                state="pending",
                status=WorkflowStatus.PENDING,
                metadata={"title": f"Resource Test {i}"},
                progress=0.0,
                assigned_agents=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await state_manager.save_workflow(workflow)
        
        # Verify resource limits are respected
        project_workflows = await state_manager.get_workflows(project_id=project.id)
        assert len(project_workflows) <= project.resource_limits["max_workflows"]


class TestErrorHandlingIntegration:
    """Integration tests for error handling and recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_failure_recovery(self, redis_client, api_client, project, sample_workflow_data):
        """Test workflow failure and recovery."""
        # Create project and workflow
        project_obj = Project(**project)
        state_manager = RedisStateManager(redis_client)
        await state_manager.save_project(project_obj)
        
        workflow_data = sample_workflow_data.copy()
        workflow_data["project_id"] = project_obj.id
        workflow = Workflow(**workflow_data)
        await state_manager.save_workflow(workflow)
        
        # Create agent that will fail
        failing_agent = Agent(
            id="failing_agent",
            name="Failing Agent",
            category=AgentCategory.CONTENT_GENERATION,
            status=AgentStatus.AVAILABLE,
            capabilities=["script_generation"],
            specializations=["educational_content"],
            version="1.0.0",
            description="Agent that will fail for testing",
            author="TestAuthor",
            resource_limits={"cpu": 1, "memory": "2GB"},
            performance_metrics={"error_rate": 0.8, "avg_response_time": 5.0},  # High error rate
            health_status={"status": "unhealthy", "message": "Simulated failure"},
            configuration={}
        )
        await state_manager.save_agent(failing_agent)
        
        # Start workflow (it should handle agent failure gracefully)
        orchestrator = WorkflowOrchestrator(state_manager)
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Wait and check if workflow handles failure appropriately
        await asyncio.sleep(5)
        
        # Verify workflow status is not failed (should handle errors gracefully)
        workflow_status = await orchestrator.get_workflow_status(workflow_id)
        assert workflow_status["workflow"].status != WorkflowStatus.FAILED
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_redis_connection_recovery(self, redis_client, api_client):
        """Test Redis connection recovery."""
        state_manager = RedisStateManager(redis_client)
        
        # Test normal operation
        test_project = Project(
            id="redis_test_project",
            name="Redis Test Project",
            description="Testing Redis connection recovery",
            type="test",
            domain="testing",
            configuration={},
            resource_limits={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        await state_manager.save_project(test_project)
        retrieved_project = await state_manager.get_project(test_project.id)
        assert retrieved_project is not None
        assert retrieved_project.name == test_project.name
        
        # Test reconnection after simulated disconnection
        await state_manager.disconnect()
        await state_manager.connect()
        
        # Verify operations still work after reconnection
        retrieved_project_after = await state_manager.get_project(test_project.id)
        assert retrieved_project_after is not None
        assert retrieved_project_after.name == test_project.name