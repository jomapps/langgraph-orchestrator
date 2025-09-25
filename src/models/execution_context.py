from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class ExecutionContext(BaseModel):
    """ExecutionContext data model representing the runtime state of workflow execution."""
    
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = Field(..., description="Workflow ID this context belongs to")
    project_id: str = Field(..., description="Project ID this context belongs to")
    
    # Execution state
    current_state: str = Field(..., description="Current execution state")
    previous_state: Optional[str] = Field(default=None, description="Previous execution state")
    
    # Runtime data
    variables: Dict[str, Any] = Field(default_factory=dict, description="Runtime variables")
    shared_data: Dict[str, Any] = Field(default_factory=dict, description="Shared data between agents")
    execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="Execution history")
    
    # Agent state tracking
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent states")
    active_agents: List[str] = Field(default_factory=list, description="Currently active agent IDs")
    completed_agents: List[str] = Field(default_factory=list, description="Completed agent IDs")
    
    # Task state tracking
    task_queue: List[str] = Field(default_factory=list, description="Task queue")
    completed_tasks: List[str] = Field(default_factory=list, description="Completed task IDs")
    failed_tasks: List[str] = Field(default_factory=list, description="Failed task IDs")
    
    # Execution metadata
    execution_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Execution checkpoints")
    
    # Error handling
    error_state: Optional[Dict[str, Any]] = Field(default=None, description="Error state information")
    retry_attempts: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_checkpoint: Optional[datetime] = Field(default=None, description="Last checkpoint time")
    
    # Validation
    @validator('workflow_id', 'project_id')
    def validate_id_format(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid ID format")
        return v
    
    @validator('variables', 'shared_data', 'execution_metadata', 'performance_metrics')
    def validate_dict_fields(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Must be a dictionary")
        return v
    
    @validator('execution_history', 'active_agents', 'completed_agents', 'task_queue', 'completed_tasks', 'failed_tasks', 'checkpoints')
    def validate_list_fields(cls, v):
        if not isinstance(v, list):
            raise ValueError("Must be a list")
        return v
    
    def update_state(self, new_state: str) -> None:
        """Update execution state."""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.updated_at = datetime.utcnow()
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a runtime variable."""
        self.variables[name] = value
        self.updated_at = datetime.utcnow()
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a runtime variable."""
        return self.variables.get(name, default)
    
    def add_shared_data(self, key: str, value: Any) -> None:
        """Add shared data."""
        self.shared_data[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data."""
        return self.shared_data.get(key, default)
    
    def add_execution_history_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history."""
        self.execution_history.append(entry)
        self.updated_at = datetime.utcnow()
    
    def update_agent_state(self, agent_id: str, state_data: Dict[str, Any]) -> None:
        """Update agent state."""
        self.agent_states[agent_id] = state_data
        self.updated_at = datetime.utcnow()
    
    def get_agent_state(self, agent_id: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get agent state."""
        return self.agent_states.get(agent_id, default)
    
    def activate_agent(self, agent_id: str) -> None:
        """Activate an agent."""
        if agent_id not in self.active_agents:
            self.active_agents.append(agent_id)
            self.updated_at = datetime.utcnow()
    
    def deactivate_agent(self, agent_id: str) -> None:
        """Deactivate an agent."""
        if agent_id in self.active_agents:
            self.active_agents.remove(agent_id)
            self.updated_at = datetime.utcnow()
    
    def mark_agent_completed(self, agent_id: str) -> None:
        """Mark an agent as completed."""
        self.deactivate_agent(agent_id)
        if agent_id not in self.completed_agents:
            self.completed_agents.append(agent_id)
            self.updated_at = datetime.utcnow()
    
    def add_task_to_queue(self, task_id: str) -> None:
        """Add a task to the queue."""
        if task_id not in self.task_queue:
            self.task_queue.append(task_id)
            self.updated_at = datetime.utcnow()
    
    def remove_task_from_queue(self, task_id: str) -> None:
        """Remove a task from the queue."""
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
            self.updated_at = datetime.utcnow()
    
    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        self.remove_task_from_queue(task_id)
        if task_id not in self.completed_tasks:
            self.completed_tasks.append(task_id)
            self.updated_at = datetime.utcnow()
    
    def mark_task_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self.remove_task_from_queue(task_id)
        if task_id not in self.failed_tasks:
            self.failed_tasks.append(task_id)
            self.updated_at = datetime.utcnow()
    
    def create_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """Create an execution checkpoint."""
        checkpoint = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": checkpoint_data
        }
        self.checkpoints.append(checkpoint)
        self.last_checkpoint = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_error_state(self, error_info: Dict[str, Any]) -> None:
        """Set error state."""
        self.error_state = error_info
        self.updated_at = datetime.utcnow()
    
    def clear_error_state(self) -> None:
        """Clear error state."""
        self.error_state = None
        self.updated_at = datetime.utcnow()
    
    def increment_retry_attempts(self) -> None:
        """Increment retry attempts."""
        self.retry_attempts += 1
        self.updated_at = datetime.utcnow()
    
    def update_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update performance metrics."""
        self.performance_metrics.update(metrics)
        self.updated_at = datetime.utcnow()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "current_state": self.current_state,
            "previous_state": self.previous_state,
            "active_agents": len(self.active_agents),
            "completed_agents": len(self.completed_agents),
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "retry_attempts": self.retry_attempts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_checkpoint": self.last_checkpoint.isoformat() if self.last_checkpoint else None
        }
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }