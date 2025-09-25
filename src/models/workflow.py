from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(str, Enum):
    """Workflow type enumeration."""
    MOVIE_CREATION = "movie_creation"
    CONTENT_GENERATION = "content_generation"
    DATA_PROCESSING = "data_processing"


class WorkflowState(str, Enum):
    """Workflow state enumeration for movie creation workflow."""
    CONCEPT_DEVELOPMENT = "concept_development"
    SCRIPT_WRITING = "script_writing"
    STORYBOARD_CREATION = "storyboard_creation"
    CASTING = "casting"
    LOCATION_SCOUTING = "location_scouting"
    BUDGET_PLANNING = "budget_planning"
    SCHEDULING = "scheduling"
    PRODUCTION = "production"
    POST_PRODUCTION = "post_production"
    REVIEW = "review"
    FINALIZATION = "finalization"


class Workflow(BaseModel):
    """Workflow data model representing an AI agent orchestration workflow."""
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = Field(..., description="Project ID this workflow belongs to")
    workflow_type: WorkflowType = Field(..., description="Type of workflow")
    current_state: WorkflowState = Field(default=WorkflowState.CONCEPT_DEVELOPMENT, description="Current state of the workflow")
    status: WorkflowStatus = Field(default=WorkflowStatus.RUNNING, description="Current status of the workflow")
    
    # Metadata
    title: str = Field(..., description="Workflow title")
    description: str = Field(default="", description="Workflow description")
    genre: Optional[str] = Field(default=None, description="Genre for movie creation workflows")
    target_duration: Optional[int] = Field(default=None, ge=1, description="Target duration in minutes")
    style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Style preferences and configuration")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1-10)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    
    # Agent assignments
    assigned_agents: List[str] = Field(default_factory=list, description="List of assigned agent IDs")
    
    # Validation
    @validator('project_id')
    def validate_project_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid project_id format")
        return v
    
    @validator('style_preferences')
    def validate_style_preferences(cls, v):
        if not isinstance(v, dict):
            raise ValueError("style_preferences must be a dictionary")
        return v
    
    def update_progress(self, percentage: float) -> None:
        """Update workflow progress percentage."""
        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        self.progress_percentage = percentage
        self.updated_at = datetime.utcnow()
    
    def update_state(self, new_state: WorkflowState) -> None:
        """Update workflow state."""
        self.current_state = new_state
        self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: WorkflowStatus) -> None:
        """Update workflow status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def assign_agent(self, agent_id: str) -> None:
        """Assign an agent to this workflow."""
        if agent_id not in self.assigned_agents:
            self.assigned_agents.append(agent_id)
            self.updated_at = datetime.utcnow()
    
    def unassign_agent(self, agent_id: str) -> None:
        """Unassign an agent from this workflow."""
        if agent_id in self.assigned_agents:
            self.assigned_agents.remove(agent_id)
            self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True