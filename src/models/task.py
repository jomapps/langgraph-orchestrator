from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """Task data model representing a unit of work in the orchestrator."""
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = Field(..., description="Workflow ID this task belongs to")
    project_id: str = Field(..., description="Project ID this task belongs to")
    agent_id: Optional[str] = Field(default=None, description="Assigned agent ID")
    
    # Task details
    name: str = Field(..., description="Task name")
    description: str = Field(default="", description="Task description")
    task_type: str = Field(..., description="Type of task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    
    # Task configuration
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Task constraints")
    
    # Execution details
    execution_context: Optional[Dict[str, Any]] = Field(default=None, description="Execution context")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="List of dependent task IDs")
    
    # Results and output
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task result")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    output: Optional[str] = Field(default=None, description="Task output")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    started_at: Optional[datetime] = Field(default=None, description="Task start time")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion time")
    estimated_duration: Optional[float] = Field(default=None, ge=0, description="Estimated duration in seconds")
    actual_duration: Optional[float] = Field(default=None, ge=0, description="Actual duration in seconds")
    
    # Validation
    @validator('workflow_id', 'project_id')
    def validate_id_format(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid ID format")
        return v
    
    @validator('parameters', 'constraints', 'execution_context', 'result')
    def validate_dict_fields(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Must be a dictionary or None")
        return v
    
    @validator('dependencies')
    def validate_dependencies(cls, v):
        if not isinstance(v, list):
            raise ValueError("Dependencies must be a list")
        if not all(isinstance(item, str) for item in v):
            raise ValueError("All dependencies must be strings")
        return v
    
    def assign_to_agent(self, agent_id: str) -> None:
        """Assign task to an agent."""
        self.agent_id = agent_id
        self.updated_at = datetime.utcnow()
    
    def start_execution(self) -> None:
        """Mark task as running."""
        if self.status != TaskStatus.PENDING:
            raise ValueError("Task must be pending to start execution")
        
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_execution(self, result: Optional[Dict[str, Any]] = None, output: Optional[str] = None) -> None:
        """Mark task as completed."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError("Task must be running to complete execution")
        
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.output = output
        self.completed_at = datetime.utcnow()
        
        # Calculate actual duration
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
        
        self.updated_at = datetime.utcnow()
    
    def fail_execution(self, error_message: str) -> None:
        """Mark task as failed."""
        if self.status not in [TaskStatus.RUNNING, TaskStatus.RETRYING]:
            raise ValueError("Task must be running or retrying to fail execution")
        
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        
        # Calculate actual duration
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
        
        self.updated_at = datetime.utcnow()
    
    def retry_execution(self) -> None:
        """Mark task for retry."""
        if self.status != TaskStatus.FAILED:
            raise ValueError("Task must be failed to retry execution")
        
        if self.retry_count >= self.max_retries:
            raise ValueError("Maximum retry count reached")
        
        self.status = TaskStatus.RETRYING
        self.retry_count += 1
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.actual_duration = None
        self.updated_at = datetime.utcnow()
    
    def cancel_execution(self) -> None:
        """Cancel task execution."""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError("Task cannot be cancelled in current status")
        
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        # Calculate actual duration
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
        
        self.updated_at = datetime.utcnow()
    
    def add_dependency(self, task_id: str) -> None:
        """Add a task dependency."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.utcnow()
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove a task dependency."""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.utcnow()
    
    def is_ready_to_execute(self) -> bool:
        """Check if task is ready to execute (pending and no dependencies)."""
        return self.status == TaskStatus.PENDING and len(self.dependencies) == 0
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True