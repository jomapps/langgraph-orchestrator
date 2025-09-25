from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import time
import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApplicationMetricsExporter:
    """
    Custom Prometheus metrics exporter for LangGraph Orchestrator application.
    Provides business-specific metrics beyond standard system metrics.
    """
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.metrics = {}
        self._initialize_metrics()
        
    def _initialize_metrics(self):
        """Initialize all custom metrics."""
        
        # Workflow metrics
        self.workflow_created = Counter(
            'workflow_created_total',
            'Total number of workflows created',
            ['project_id', 'workflow_type', 'priority']
        )
        
        self.workflow_completed = Counter(
            'workflow_completed_total',
            'Total number of workflows completed',
            ['project_id', 'workflow_type', 'status']
        )
        
        self.workflow_duration = Histogram(
            'workflow_duration_seconds',
            'Workflow execution duration in seconds',
            ['project_id', 'workflow_type']
        )
        
        self.workflows_active = Gauge(
            'workflows_active',
            'Number of currently active workflows',
            ['project_id', 'workflow_type']
        )
        
        self.workflow_errors = Counter(
            'workflow_errors_total',
            'Total number of workflow errors',
            ['project_id', 'workflow_type', 'error_type']
        )
        
        # Agent metrics
        self.agent_registered = Counter(
            'agent_registered_total',
            'Total number of agents registered',
            ['agent_category', 'agent_version']
        )
        
        self.agent_tasks_assigned = Counter(
            'agent_tasks_assigned_total',
            'Total number of tasks assigned to agents',
            ['agent_id', 'task_type']
        )
        
        self.agent_tasks_completed = Counter(
            'agent_tasks_completed_total',
            'Total number of tasks completed by agents',
            ['agent_id', 'status']
        )
        
        self.agent_task_duration = Histogram(
            'agent_task_duration_seconds',
            'Agent task execution duration in seconds',
            ['agent_id', 'task_type']
        )
        
        self.agent_health_status = Gauge(
            'agent_health_status',
            'Agent health status (1=healthy, 0=unhealthy)',
            ['agent_id']
        )
        
        self.agent_errors = Counter(
            'agent_errors_total',
            'Total number of agent errors',
            ['agent_id', 'error_type']
        )
        
        # Task metrics
        self.task_created = Counter(
            'task_created_total',
            'Total number of tasks created',
            ['workflow_id', 'task_type', 'priority']
        )
        
        self.task_completed = Counter(
            'task_completed_total',
            'Total number of tasks completed',
            ['workflow_id', 'task_type', 'status']
        )
        
        self.task_duration = Histogram(
            'task_duration_seconds',
            'Task execution duration in seconds',
            ['workflow_id', 'task_type']
        )
        
        self.task_retries = Counter(
            'task_retries_total',
            'Total number of task retries',
            ['workflow_id', 'task_type']
        )
        
        self.tasks_active = Gauge(
            'tasks_active',
            'Number of currently active tasks',
            ['workflow_id', 'task_type']
        )
        
        # Project metrics
        self.project_created = Counter(
            'project_created_total',
            'Total number of projects created',
            ['project_type']
        )
        
        self.project_workflows = Gauge(
            'project_workflows',
            'Number of workflows in project',
            ['project_id']
        )
        
        # System health metrics
        self.app_info = Info(
            'app_info',
            'Application information'
        )
        
        self.app_uptime = Gauge(
            'app_uptime_seconds',
            'Application uptime in seconds'
        )
        
        # Business metrics
        self.video_processing_duration = Histogram(
            'video_processing_duration_seconds',
            'Video processing duration in seconds',
            ['video_type', 'resolution']
        )
        
        self.content_optimization_duration = Histogram(
            'content_optimization_duration_seconds',
            'Content optimization duration in seconds',
            ['content_type', 'optimization_type']
        )
        
        self.api_rate_limit_hits = Counter(
            'api_rate_limit_hits_total',
            'Total number of API rate limit hits',
            ['endpoint', 'client_id']
        )
        
        # Initialize app info
        self.app_info.info({
            'version': '1.0.0',
            'build_date': datetime.now().isoformat(),
            'environment': 'production'
        })
        
        logger.info("Application metrics exporter initialized")
    
    def start_server(self):
        """Start the metrics HTTP server."""
        try:
            start_http_server(self.port)
            logger.info(f"Application metrics exporter started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise
    
    # Workflow metrics methods
    def record_workflow_created(self, project_id: str, workflow_type: str, priority: str):
        """Record workflow creation."""
        self.workflow_created.labels(
            project_id=project_id,
            workflow_type=workflow_type,
            priority=priority
        ).inc()
        
        # Increment active workflows
        self.workflows_active.labels(
            project_id=project_id,
            workflow_type=workflow_type
        ).inc()
    
    def record_workflow_completed(self, project_id: str, workflow_type: str, status: str, duration: float):
        """Record workflow completion."""
        self.workflow_completed.labels(
            project_id=project_id,
            workflow_type=workflow_type,
            status=status
        ).inc()
        
        # Record duration
        self.workflow_duration.labels(
            project_id=project_id,
            workflow_type=workflow_type
        ).observe(duration)
        
        # Decrement active workflows
        self.workflows_active.labels(
            project_id=project_id,
            workflow_type=workflow_type
        ).dec()
    
    def record_workflow_error(self, project_id: str, workflow_type: str, error_type: str):
        """Record workflow error."""
        self.workflow_errors.labels(
            project_id=project_id,
            workflow_type=workflow_type,
            error_type=error_type
        ).inc()
    
    # Agent metrics methods
    def record_agent_registered(self, agent_category: str, agent_version: str):
        """Record agent registration."""
        self.agent_registered.labels(
            agent_category=agent_category,
            agent_version=agent_version
        ).inc()
    
    def record_agent_task_assigned(self, agent_id: str, task_type: str):
        """Record task assignment to agent."""
        self.agent_tasks_assigned.labels(
            agent_id=agent_id,
            task_type=task_type
        ).inc()
    
    def record_agent_task_completed(self, agent_id: str, status: str, duration: float, task_type: str):
        """Record agent task completion."""
        self.agent_tasks_completed.labels(
            agent_id=agent_id,
            status=status
        ).inc()
        
        # Record duration
        self.agent_task_duration.labels(
            agent_id=agent_id,
            task_type=task_type
        ).observe(duration)
    
    def set_agent_health_status(self, agent_id: str, is_healthy: bool):
        """Set agent health status."""
        self.agent_health_status.labels(
            agent_id=agent_id
        ).set(1 if is_healthy else 0)
    
    def record_agent_error(self, agent_id: str, error_type: str):
        """Record agent error."""
        self.agent_errors.labels(
            agent_id=agent_id,
            error_type=error_type
        ).inc()
    
    # Task metrics methods
    def record_task_created(self, workflow_id: str, task_type: str, priority: str):
        """Record task creation."""
        self.task_created.labels(
            workflow_id=workflow_id,
            task_type=task_type,
            priority=priority
        ).inc()
        
        # Increment active tasks
        self.tasks_active.labels(
            workflow_id=workflow_id,
            task_type=task_type
        ).inc()
    
    def record_task_completed(self, workflow_id: str, task_type: str, status: str, duration: float):
        """Record task completion."""
        self.task_completed.labels(
            workflow_id=workflow_id,
            task_type=task_type,
            status=status
        ).inc()
        
        # Record duration
        self.task_duration.labels(
            workflow_id=workflow_id,
            task_type=task_type
        ).observe(duration)
        
        # Decrement active tasks
        self.tasks_active.labels(
            workflow_id=workflow_id,
            task_type=task_type
        ).dec()
    
    def record_task_retry(self, workflow_id: str, task_type: str):
        """Record task retry."""
        self.task_retries.labels(
            workflow_id=workflow_id,
            task_type=task_type
        ).inc()
    
    # Project metrics methods
    def record_project_created(self, project_type: str):
        """Record project creation."""
        self.project_created.labels(
            project_type=project_type
        ).inc()
    
    def set_project_workflows(self, project_id: str, count: int):
        """Set number of workflows in project."""
        self.project_workflows.labels(
            project_id=project_id
        ).set(count)
    
    # Business metrics methods
    def record_video_processing_duration(self, video_type: str, resolution: str, duration: float):
        """Record video processing duration."""
        self.video_processing_duration.labels(
            video_type=video_type,
            resolution=resolution
        ).observe(duration)
    
    def record_content_optimization_duration(self, content_type: str, optimization_type: str, duration: float):
        """Record content optimization duration."""
        self.content_optimization_duration.labels(
            content_type=content_type,
            optimization_type=optimization_type
        ).observe(duration)
    
    def record_api_rate_limit_hit(self, endpoint: str, client_id: str):
        """Record API rate limit hit."""
        self.api_rate_limit_hits.labels(
            endpoint=endpoint,
            client_id=client_id
        ).inc()
    
    # System metrics methods
    def set_uptime(self, uptime_seconds: float):
        """Set application uptime."""
        self.app_uptime.set(uptime_seconds)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "workflows": {
                "created": self.workflow_created._value._value,
                "active": sum(g._value for g in self.workflows_active._metrics.values()),
                "errors": self.workflow_errors._value._value
            },
            "agents": {
                "registered": self.agent_registered._value._value,
                "tasks_assigned": self.agent_tasks_assigned._value._value,
                "health_issues": sum(1 for g in self.agent_health_status._metrics.values() if g._value == 0)
            },
            "tasks": {
                "created": self.task_created._value._value,
                "active": sum(g._value for g in self.tasks_active._metrics.values()),
                "retries": self.task_retries._value._value
            }
        }

# Global exporter instance
metrics_exporter = ApplicationMetricsExporter()

def start_metrics_server():
    """Start the metrics server."""
    metrics_exporter.start_server()

# Convenience functions for common operations
def record_workflow_start(project_id: str, workflow_type: str, priority: str):
    """Record workflow start."""
    metrics_exporter.record_workflow_created(project_id, workflow_type, priority)

def record_workflow_end(project_id: str, workflow_type: str, status: str, duration: float):
    """Record workflow end."""
    metrics_exporter.record_workflow_completed(project_id, workflow_type, status, duration)

def record_agent_task(agent_id: str, task_type: str, status: str, duration: float):
    """Record agent task completion."""
    metrics_exporter.record_agent_task_completed(agent_id, status, duration, task_type)

def set_agent_health(agent_id: str, is_healthy: bool):
    """Set agent health status."""
    metrics_exporter.set_agent_health_status(agent_id, is_healthy)

if __name__ == "__main__":
    # Start the metrics server
    start_metrics_server()
    
    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Metrics server stopped")