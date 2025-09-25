from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class AgentCategory(str, Enum):
    """Agent category enumeration."""
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    TECHNICAL = "technical"
    COORDINATION = "coordination"
    RESEARCH = "research"
    CONTENT = "content"


class Agent(BaseModel):
    """Agent data model representing an AI agent in the orchestrator."""
    
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Agent name")
    category: AgentCategory = Field(..., description="Agent category")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current agent status")
    
    # Agent capabilities and configuration
    capabilities: List[str] = Field(..., description="List of agent capabilities")
    specializations: List[str] = Field(default_factory=list, description="Agent specializations")
    version: str = Field(default="1.0.0", description="Agent version")
    
    # Agent metadata
    description: str = Field(default="", description="Agent description")
    author: Optional[str] = Field(default=None, description="Agent author/creator")
    
    # Resource limits and performance
    max_concurrent_tasks: int = Field(default=1, ge=1, description="Maximum concurrent tasks")
    current_task_count: int = Field(default=0, ge=0, description="Current task count")
    performance_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Performance score")
    reliability_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Reliability score")
    
    # Health and monitoring
    last_heartbeat: Optional[datetime] = Field(default=None, description="Last heartbeat timestamp")
    health_status: Dict[str, Any] = Field(default_factory=dict, description="Health status details")
    error_count: int = Field(default=0, ge=0, description="Error count")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    
    # Validation
    @validator('capabilities', 'specializations')
    def validate_string_lists(cls, v):
        if not isinstance(v, list):
            raise ValueError("Must be a list")
        if not all(isinstance(item, str) for item in v):
            raise ValueError("All items must be strings")
        return v
    
    @validator('health_status', 'config')
    def validate_dict_fields(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Must be a dictionary")
        return v
    
    def can_accept_task(self) -> bool:
        """Check if agent can accept a new task."""
        return (self.status == AgentStatus.IDLE and 
                self.current_task_count < self.max_concurrent_tasks)
    
    def assign_task(self) -> None:
        """Assign a task to this agent."""
        if not self.can_accept_task():
            raise ValueError("Agent cannot accept more tasks")
        
        self.current_task_count += 1
        self.status = AgentStatus.BUSY if self.current_task_count >= self.max_concurrent_tasks else AgentStatus.IDLE
        self.updated_at = datetime.utcnow()
    
    def complete_task(self) -> None:
        """Mark a task as completed by this agent."""
        if self.current_task_count <= 0:
            raise ValueError("No tasks to complete")
        
        self.current_task_count -= 1
        self.status = AgentStatus.IDLE if self.current_task_count == 0 else AgentStatus.BUSY
        self.updated_at = datetime.utcnow()
    
    def update_health_status(self, health_data: Dict[str, Any]) -> None:
        """Update agent health status."""
        self.health_status.update(health_data)
        self.last_heartbeat = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_error_count(self) -> None:
        """Increment error count and update status if needed."""
        self.error_count += 1
        if self.error_count > 5:  # Threshold for error status
            self.status = AgentStatus.ERROR
        self.updated_at = datetime.utcnow()
    
    def reset_error_count(self) -> None:
        """Reset error count."""
        self.error_count = 0
        if self.status == AgentStatus.ERROR:
            self.status = AgentStatus.IDLE
        self.updated_at = datetime.utcnow()
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities
    
    def is_specialized_in(self, specialization: str) -> bool:
        """Check if agent is specialized in a specific area."""
        return specialization in self.specializations
    
    def update_performance_score(self, score: float) -> None:
        """Update performance score with moving average."""
        if not 0 <= score <= 100:
            raise ValueError("Performance score must be between 0 and 100")
        
        # Simple moving average
        if self.performance_score == 0:
            self.performance_score = score
        else:
            self.performance_score = (self.performance_score * 0.8 + score * 0.2)
        
        self.updated_at = datetime.utcnow()
    
    def update_reliability_score(self, score: float) -> None:
        """Update reliability score with moving average."""
        if not 0 <= score <= 100:
            raise ValueError("Reliability score must be between 0 and 100")
        
        # Simple moving average
        if self.reliability_score == 0:
            self.reliability_score = score
        else:
            self.reliability_score = (self.reliability_score * 0.8 + score * 0.2)
        
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True