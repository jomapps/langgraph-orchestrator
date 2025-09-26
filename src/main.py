from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from .models import Workflow, Agent, Task, Project, ExecutionContext
from .models.workflow import WorkflowStatus, WorkflowType, WorkflowState
from .models.agent import AgentStatus, AgentCategory
from .models.task import TaskStatus, TaskPriority
from .services import RedisStateManager, redis_state_manager
from .orchestrator import WorkflowOrchestrator, get_orchestrator
from .config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangGraph Orchestrator Service",
    description="Orchestration service for AI video creation workflows",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get state manager
async def get_state_manager() -> RedisStateManager:
    return redis_state_manager

# Dependency to get orchestrator
async def get_orchestrator_service() -> WorkflowOrchestrator:
    return await get_orchestrator()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        await redis_state_manager.redis_client.ping()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Workflow endpoints
@app.post("/api/v1/workflows", response_model=Dict[str, Any])
async def create_workflow(
    workflow: Workflow,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Create a new workflow."""
    try:
        # Check if project exists
        project = await state_manager.get_project(workflow.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Save workflow
        await state_manager.save_workflow(workflow)
        
        return {
            "id": workflow.id,
            "message": "Workflow created successfully",
            "created_at": workflow.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """List workflows with optional filtering."""
    try:
        workflows = await state_manager.list_workflows(
            project_id=project_id,
            status=status,
            limit=limit
        )
        
        return [
            {
                "id": w.workflow_id,
                "project_id": w.project_id,
                "type": w.workflow_type.value if hasattr(w.workflow_type, 'value') else str(w.workflow_type),
                "status": w.status.value if hasattr(w.status, 'value') else str(w.status),
                "state": w.current_state.value if hasattr(w.current_state, 'value') else str(w.current_state),
                "progress": w.progress_percentage,
                "title": w.title,
                "description": w.description,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat()
            }
            for w in workflows
        ]
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager),
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Get workflow by ID."""
    try:
        workflow = await state_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get execution status if workflow is running
        execution_status = await orchestrator.get_workflow_status(workflow_id)
        
        return {
            "workflow": {
                "id": workflow.id,
                "project_id": workflow.project_id,
                "type": workflow.type.value,
                "status": workflow.status.value,
                "state": workflow.state.value,
                "progress": workflow.progress,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "metadata": workflow.metadata,
                "error_message": workflow.error_message
            },
            "execution_status": execution_status,
            "is_running": execution_status.get("is_running", False) if execution_status else False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: str,
    workflow_update: Dict[str, Any],
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Update workflow configuration."""
    try:
        workflow = await state_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update allowed fields
        if "metadata" in workflow_update:
            workflow.metadata.update(workflow_update["metadata"])
        
        if "assigned_agents" in workflow_update:
            workflow.assigned_agents = workflow_update["assigned_agents"]
        
        workflow.updated_at = datetime.utcnow()
        await state_manager.save_workflow(workflow)
        
        return {
            "id": workflow.id,
            "message": "Workflow updated successfully",
            "updated_at": workflow.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager),
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Delete workflow."""
    try:
        workflow = await state_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Cancel workflow if running
        if workflow.status.value == "running":
            await orchestrator.cancel_workflow(workflow_id)
        
        # Delete workflow
        await state_manager.delete_workflow(workflow_id)
        
        return {"message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Workflow control endpoints
@app.post("/api/v1/workflows/{workflow_id}/start", response_model=Dict[str, Any])
async def start_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    state_manager: RedisStateManager = Depends(get_state_manager),
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Start workflow execution."""
    try:
        workflow = await state_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status.value not in ["pending", "paused", "failed"]:
            raise HTTPException(status_code=400, detail=f"Cannot start workflow in {workflow.status.value} state")
        
        # Start workflow in background
        workflow_id = await orchestrator.start_workflow(workflow)
        
        # Schedule cleanup task
        background_tasks.add_task(_cleanup_completed_workflows, orchestrator)
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow started successfully",
            "started_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/workflows/{workflow_id}/pause", response_model=Dict[str, Any])
async def pause_workflow(
    workflow_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Pause running workflow."""
    try:
        success = await orchestrator.pause_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=400, detail="Workflow not running or already paused")
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow paused successfully",
            "paused_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/workflows/{workflow_id}/resume", response_model=Dict[str, Any])
async def resume_workflow(
    workflow_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Resume paused workflow."""
    try:
        success = await orchestrator.resume_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=400, detail="Workflow not paused or not found")
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow resumed successfully",
            "resumed_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/workflows/{workflow_id}/cancel", response_model=Dict[str, Any])
async def cancel_workflow(
    workflow_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator_service)
):
    """Cancel running workflow."""
    try:
        success = await orchestrator.cancel_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=400, detail="Workflow not found")
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow cancelled successfully",
            "cancelled_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Agent endpoints
@app.get("/api/v1/agents", response_model=List[Dict[str, Any]])
async def list_agents(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """List registered agents."""
    try:
        agents = await state_manager.list_agents(
            category=category,
            status=status,
            limit=limit
        )
        
        return [
            {
                "id": a.agent_id,
                "name": a.name,
                "category": a.category.value if hasattr(a.category, 'value') else str(a.category),
                "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                "capabilities": a.capabilities,
                "specializations": a.specializations,
                "version": a.version,
                "description": a.description,
                "performance_score": a.performance_score,
                "reliability_score": a.reliability_score,
                "max_concurrent_tasks": a.max_concurrent_tasks,
                "current_task_count": a.current_task_count,
                "health_status": a.health_status,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat()
            }
            for a in agents
        ]
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/agents/register", response_model=Dict[str, Any])
async def register_agent(
    agent: Agent,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Register a new agent."""
    try:
        await state_manager.save_agent(agent)
        
        return {
            "id": agent.id,
            "message": "Agent registered successfully",
            "registered_at": agent.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/agents/{agent_id}", response_model=Dict[str, Any])
async def update_agent(
    agent_id: str,
    agent_update: Dict[str, Any],
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Update agent configuration."""
    try:
        agent = await state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update allowed fields
        updatable_fields = ["capabilities", "specializations", "description", 
                          "resource_limits", "health_status", "configuration"]
        
        for field in updatable_fields:
            if field in agent_update:
                setattr(agent, field, agent_update[field])
        
        agent.updated_at = datetime.utcnow()
        await state_manager.save_agent(agent)
        
        return {
            "id": agent.id,
            "message": "Agent updated successfully",
            "updated_at": agent.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/agents/{agent_id}")
async def deregister_agent(
    agent_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Deregister an agent."""
    try:
        agent = await state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        await state_manager.delete_agent(agent_id)
        
        return {"message": "Agent deregistered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deregister agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/agents/{agent_id}/health", response_model=Dict[str, Any])
async def get_agent_health(
    agent_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Get agent health status."""
    try:
        agent = await state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_id": agent_id,
            "status": agent.status.value,
            "health_status": agent.health_status,
            "last_health_check": agent.last_health_check.isoformat() if agent.last_health_check else None,
            "performance_metrics": agent.performance_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/agents/{agent_id}/reset", response_model=Dict[str, Any])
async def reset_agent(
    agent_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Reset agent state."""
    try:
        agent = await state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Reset agent state
        agent.status = AgentStatus.AVAILABLE
        agent.health_status = {"status": "healthy", "message": "Agent reset"}
        agent.performance_metrics = {"error_rate": 0.0, "avg_response_time": 0.0, "tasks_completed": 0}
        agent.updated_at = datetime.utcnow()
        
        await state_manager.save_agent(agent)
        
        return {
            "agent_id": agent_id,
            "message": "Agent reset successfully",
            "reset_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/agents/{agent_id}/tasks", response_model=List[Dict[str, Any]])
async def get_agent_tasks(
    agent_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Get tasks assigned to an agent."""
    try:
        agent = await state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        tasks = await state_manager.list_tasks(
            agent_id=agent_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "id": t.id,
                "workflow_id": t.workflow_id,
                "project_id": t.project_id,
                "agent_id": t.agent_id,
                "name": t.name,
                "description": t.description,
                "type": t.type,
                "status": t.status.value,
                "priority": t.priority.value,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "result": t.result
            }
            for t in tasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility functions
async def _cleanup_completed_workflows(orchestrator: WorkflowOrchestrator):
    """Background task to clean up completed workflows."""
    try:
        await orchestrator.cleanup_completed_workflows()
    except Exception as e:
        logger.error(f"Failed to cleanup workflows: {e}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting LangGraph Orchestrator Service")
    
    # Initialize Redis connection
    await redis_state_manager.connect()
    
    # Initialize orchestrator
    await get_orchestrator()
    
    logger.info("Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down LangGraph Orchestrator Service")
    
    # Disconnect Redis
    await redis_state_manager.disconnect()
    
    logger.info("Service shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
        log_level="info"
    )