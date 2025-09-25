from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class Project(BaseModel):
    """Project data model representing a collection of workflows and tasks."""
    
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Project name")
    description: str = Field(default="", description="Project description")
    
    # Project metadata
    project_type: str = Field(..., description="Type of project")
    domain: Optional[str] = Field(default=None, description="Project domain")
    
    # Project configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Project configuration")
    
    # Resource management
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    # Status tracking
    is_active: bool = Field(default=True, description="Whether the project is active")
    
    # Validation
    @validator('config', 'resource_limits')
    def validate_dict_fields(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Must be a dictionary")
        return v
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update project configuration."""
        self.config.update(config_updates)
        self.updated_at = datetime.utcnow()
    
    def update_resource_limits(self, limits: Dict[str, Any]) -> None:
        """Update resource limits."""
        self.resource_limits.update(limits)
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the project."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the project."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }