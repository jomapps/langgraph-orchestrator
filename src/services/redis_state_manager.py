import json
import redis.asyncio as redis
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from ..config.settings import settings
from ..models import Workflow, Agent, Project, Task, ExecutionContext

logger = logging.getLogger(__name__)


class RedisStateManager:
    """Redis-based state management service for the orchestrator."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
    
    def _ensure_connected(self) -> redis.Redis:
        """Ensure Redis client is connected and return it."""
        if not self.is_connected or self.redis_client is None:
            raise RuntimeError("Redis not connected")
        return self.redis_client
    
    @classmethod
    async def create(cls) -> 'RedisStateManager':
        """Create and initialize RedisStateManager"""
        manager = cls()
        await manager.connect()
        return manager
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis")
    
    async def save_workflow(self, workflow: Workflow) -> bool:
        """Save workflow to Redis."""
        try:
            client = self._ensure_connected()
            key = f"workflow:{workflow.workflow_id}"
            workflow_data = workflow.model_dump_json()
            
            # Save workflow data
            await client.set(key, workflow_data)
            
            # Add to project index
            project_key = f"project:{workflow.project_id}:workflows"
            await client.sadd(project_key, workflow.workflow_id)
            
            # Add to status index
            status_key = f"workflows:status:{workflow.status}"
            await client.sadd(status_key, workflow.workflow_id)
            
            # Add to type index
            type_key = f"workflows:type:{workflow.workflow_type}"
            await client.sadd(type_key, workflow.workflow_id)
            
            # Set expiration for status indices (24 hours)
            await client.expire(status_key, 86400)
            await client.expire(type_key, 86400)
            
            logger.debug(f"Saved workflow {workflow.workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow {workflow.workflow_id}: {e}")
            return False
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow from Redis."""
        try:
            client = self._ensure_connected()
            key = f"workflow:{workflow_id}"
            workflow_data = await client.get(key)
            
            if not workflow_data:
                return None
            
            return Workflow.model_validate_json(workflow_data)
            
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            return None
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow from Redis."""
        try:
            client = self._ensure_connected()
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                return False
            
            key = f"workflow:{workflow_id}"
            await client.delete(key)
            
            # Remove from project index
            project_key = f"project:{workflow.project_id}:workflows"
            await client.srem(project_key, workflow_id)
            
            # Remove from status index
            status_key = f"workflows:status:{workflow.status}"
            await client.srem(status_key, workflow_id)
            
            # Remove from type index
            type_key = f"workflows:type:{workflow.workflow_type}"
            await client.srem(type_key, workflow_id)
            
            logger.debug(f"Deleted workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False
    
    async def list_workflows(self, project_id: Optional[str] = None, 
                           status: Optional[str] = None,
                           workflow_type: Optional[str] = None,
                           limit: int = 100) -> List[Workflow]:
        """List workflows with optional filters."""
        try:
            client = self._ensure_connected()
            workflow_ids = set()
            
            # Get workflow IDs based on filters
            if project_id:
                project_key = f"project:{project_id}:workflows"
                project_workflows = await client.smembers(project_key)
                workflow_ids.update(project_workflows)
            
            if status:
                status_key = f"workflows:status:{status}"
                status_workflows = await client.smembers(status_key)
                if workflow_ids:
                    workflow_ids.intersection_update(status_workflows)
                else:
                    workflow_ids.update(status_workflows)
            
            if workflow_type:
                type_key = f"workflows:type:{workflow_type}"
                type_workflows = await client.smembers(type_key)
                if workflow_ids:
                    workflow_ids.intersection_update(type_workflows)
                else:
                    workflow_ids.update(type_workflows)
            
            # If no filters, get all workflows (scan approach)
            if not workflow_ids:
                cursor = 0
                while True:
                    cursor, keys = await client.scan(cursor, match="workflow:*", count=100)
                    for key in keys:
                        workflow_id = key.replace("workflow:", "")
                        workflow_ids.add(workflow_id)
                    
                    if cursor == 0:
                        break
            
            # Fetch workflow data
            workflows = []
            for workflow_id in list(workflow_ids)[:limit]:
                workflow = await self.get_workflow(workflow_id)
                if workflow:
                    workflows.append(workflow)
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    async def save_agent(self, agent: Agent) -> bool:
        """Save agent to Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"agent:{agent.agent_id}"
            agent_data = agent.model_dump_json()
            
            await self.redis_client.set(key, agent_data)
            
            # Add to category index
            category_key = f"agents:category:{agent.category}"
            await self.redis_client.sadd(category_key, agent.agent_id)
            
            # Add to status index
            status_key = f"agents:status:{agent.status}"
            await self.redis_client.sadd(status_key, agent.agent_id)
            
            # Set expiration for status indices (24 hours)
            await self.redis_client.expire(category_key, 86400)
            await self.redis_client.expire(status_key, 86400)
            
            logger.debug(f"Saved agent {agent.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent {agent.agent_id}: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"agent:{agent_id}"
            agent_data = await self.redis_client.get(key)
            
            if not agent_data:
                return None
            
            return Agent.model_validate_json(agent_data)
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            agent = await self.get_agent(agent_id)
            if not agent:
                return False
            
            key = f"agent:{agent_id}"
            await self.redis_client.delete(key)
            
            # Remove from category index
            category_key = f"agents:category:{agent.category}"
            await self.redis_client.srem(category_key, agent_id)
            
            # Remove from status index
            status_key = f"agents:status:{agent.status}"
            await self.redis_client.srem(status_key, agent_id)
            
            logger.debug(f"Deleted agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False
    
    async def list_agents(self, category: Optional[str] = None,
                         status: Optional[str] = None,
                         limit: int = 100) -> List[Agent]:
        """List agents with optional filters."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            agent_ids = set()
            
            if category:
                category_key = f"agents:category:{category}"
                category_agents = await self.redis_client.smembers(category_key)
                agent_ids.update(category_agents)
            
            if status:
                status_key = f"agents:status:{status}"
                status_agents = await self.redis_client.smembers(status_key)
                if agent_ids:
                    agent_ids.intersection_update(status_agents)
                else:
                    agent_ids.update(status_agents)
            
            # If no filters, get all agents
            if not agent_ids:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match="agent:*", count=100)
                    for key in keys:
                        agent_id = key.replace("agent:", "")
                        agent_ids.add(agent_id)
                    
                    if cursor == 0:
                        break
            
            # Fetch agent data
            agents = []
            for agent_id in list(agent_ids)[:limit]:
                agent = await self.get_agent(agent_id)
                if agent:
                    agents.append(agent)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def save_project(self, project: Project) -> bool:
        """Save project to Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"project:{project.project_id}"
            project_data = project.model_dump_json()
            
            await self.redis_client.set(key, project_data)
            
            # Add to active projects index if active
            if project.is_active:
                await self.redis_client.sadd("projects:active", project.project_id)
            else:
                await self.redis_client.srem("projects:active", project.project_id)
            
            logger.debug(f"Saved project {project.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project {project.project_id}: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"project:{project_id}"
            project_data = await self.redis_client.get(key)
            
            if not project_data:
                return None
            
            return Project.model_validate_json(project_data)
            
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"project:{project_id}"
            result = await self.redis_client.delete(key)
            
            # Remove from active projects index
            await self.redis_client.srem("projects:active", project_id)
            
            # Delete all workflows for this project
            project_workflows_key = f"project:{project_id}:workflows"
            workflow_ids = await self.redis_client.smembers(project_workflows_key)
            
            for workflow_id in workflow_ids:
                await self.delete_workflow(workflow_id)
            
            await self.redis_client.delete(project_workflows_key)
            
            logger.debug(f"Deleted project {project_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    async def list_projects(self, active_only: bool = False, limit: int = 100) -> List[Project]:
        """List projects with optional filters."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            project_ids = set()
            
            if active_only:
                active_ids = await self.redis_client.smembers("projects:active")
                project_ids.update(active_ids)
            else:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match="project:*", count=100)
                    for key in keys:
                        project_id = key.replace("project:", "")
                        project_ids.add(project_id)
                    
                    if cursor == 0:
                        break
            
            # Fetch project data
            projects = []
            for project_id in list(project_ids)[:limit]:
                project = await self.get_project(project_id)
                if project:
                    projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
    
    async def save_task(self, task: Task) -> bool:
        """Save task to Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"task:{task.task_id}"
            task_data = task.model_dump_json()
            
            await self.redis_client.set(key, task_data)
            
            # Add to workflow index
            workflow_key = f"workflow:{task.workflow_id}:tasks"
            await self.redis_client.sadd(workflow_key, task.task_id)
            
            # Add to project index
            project_key = f"project:{task.project_id}:tasks"
            await self.redis_client.sadd(project_key, task.task_id)
            
            # Add to agent index if assigned
            if task.agent_id:
                agent_key = f"agent:{task.agent_id}:tasks"
                await self.redis_client.sadd(agent_key, task.task_id)
            
            # Add to status index
            status_key = f"tasks:status:{task.status}"
            await self.redis_client.sadd(status_key, task.task_id)
            
            # Set expiration for status indices (24 hours)
            await self.redis_client.expire(status_key, 86400)
            
            logger.debug(f"Saved task {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id}: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"task:{task_id}"
            task_data = await self.redis_client.get(key)
            
            if not task_data:
                return None
            
            return Task.model_validate_json(task_data)
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            task = await self.get_task(task_id)
            if not task:
                return False
            
            key = f"task:{task_id}"
            await self.redis_client.delete(key)
            
            # Remove from workflow index
            workflow_key = f"workflow:{task.workflow_id}:tasks"
            await self.redis_client.srem(workflow_key, task_id)
            
            # Remove from project index
            project_key = f"project:{task.project_id}:tasks"
            await self.redis_client.srem(project_key, task_id)
            
            # Remove from agent index if assigned
            if task.agent_id:
                agent_key = f"agent:{task.agent_id}:tasks"
                await self.redis_client.srem(agent_key, task_id)
            
            # Remove from status index
            status_key = f"tasks:status:{task.status}"
            await self.redis_client.srem(status_key, task_id)
            
            logger.debug(f"Deleted task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    async def list_tasks(self, workflow_id: Optional[str] = None,
                        project_id: Optional[str] = None,
                        agent_id: Optional[str] = None,
                        status: Optional[str] = None,
                        limit: int = 100) -> List[Task]:
        """List tasks with optional filters."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            task_ids = set()
            
            if workflow_id:
                workflow_key = f"workflow:{workflow_id}:tasks"
                workflow_tasks = await self.redis_client.smembers(workflow_key)
                task_ids.update(workflow_tasks)
            
            if project_id:
                project_key = f"project:{project_id}:tasks"
                project_tasks = await self.redis_client.smembers(project_key)
                if task_ids:
                    task_ids.intersection_update(project_tasks)
                else:
                    task_ids.update(project_tasks)
            
            if agent_id:
                agent_key = f"agent:{agent_id}:tasks"
                agent_tasks = await self.redis_client.smembers(agent_key)
                if task_ids:
                    task_ids.intersection_update(agent_tasks)
                else:
                    task_ids.update(agent_tasks)
            
            if status:
                status_key = f"tasks:status:{status}"
                status_tasks = await self.redis_client.smembers(status_key)
                if task_ids:
                    task_ids.intersection_update(status_tasks)
                else:
                    task_ids.update(status_tasks)
            
            # If no filters, get all tasks
            if not task_ids:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match="task:*", count=100)
                    for key in keys:
                        task_id = key.replace("task:", "")
                        task_ids.add(task_id)
                    
                    if cursor == 0:
                        break
            
            # Fetch task data
            tasks = []
            for task_id in list(task_ids)[:limit]:
                task = await self.get_task(task_id)
                if task:
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
    
    async def save_execution_context(self, context: ExecutionContext) -> bool:
        """Save execution context to Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"execution_context:{context.context_id}"
            context_data = context.model_dump_json()
            
            await self.redis_client.set(key, context_data)
            
            # Add to workflow index
            workflow_key = f"workflow:{context.workflow_id}:execution_contexts"
            await self.redis_client.sadd(workflow_key, context.context_id)
            
            # Add to project index
            project_key = f"project:{context.project_id}:execution_contexts"
            await self.redis_client.sadd(project_key, context.context_id)
            
            logger.debug(f"Saved execution context {context.context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save execution context {context.context_id}: {e}")
            return False
    
    async def get_execution_context(self, context_id: str) -> Optional[ExecutionContext]:
        """Get execution context from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            key = f"execution_context:{context_id}"
            context_data = await self.redis_client.get(key)
            
            if not context_data:
                return None
            
            return ExecutionContext.model_validate_json(context_data)
            
        except Exception as e:
            logger.error(f"Failed to get execution context {context_id}: {e}")
            return None
    
    async def delete_execution_context(self, context_id: str) -> bool:
        """Delete execution context from Redis."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            context = await self.get_execution_context(context_id)
            if not context:
                return False
            
            key = f"execution_context:{context_id}"
            await self.redis_client.delete(key)
            
            # Remove from workflow index
            workflow_key = f"workflow:{context.workflow_id}:execution_contexts"
            await self.redis_client.srem(workflow_key, context_id)
            
            # Remove from project index
            project_key = f"project:{context.project_id}:execution_contexts"
            await self.redis_client.srem(project_key, context_id)
            
            logger.debug(f"Deleted execution context {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete execution context {context_id}: {e}")
            return False
    
    async def acquire_lock(self, resource_name: str, timeout: int = 30) -> Optional[str]:
        """Acquire a distributed lock."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            lock_id = f"lock:{resource_name}:{datetime.utcnow().timestamp()}"
            lock_key = f"lock:{resource_name}"
            
            # Try to acquire lock with NX (only set if not exists)
            result = await self.redis_client.set(
                lock_key, lock_id, nx=True, ex=timeout
            )
            
            if result:
                return lock_id
            return None
            
        except Exception as e:
            logger.error(f"Failed to acquire lock {resource_name}: {e}")
            return None
    
    async def release_lock(self, resource_name: str, lock_id: str) -> bool:
        """Release a distributed lock."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            lock_key = f"lock:{resource_name}"
            
            # Use Lua script to ensure atomic check and delete
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = await self.redis_client.eval(lua_script, 1, lock_key, lock_id)
            return result == 1
            
        except Exception as e:
            logger.error(f"Failed to release lock {resource_name}: {e}")
            return False
    
    async def cleanup_expired_data(self, max_age_days: int = 30) -> int:
        """Clean up expired data older than max_age_days."""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
            cleaned_count = 0
            
            # Clean up old completed workflows
            completed_workflows = await self.list_workflows(status="completed")
            for workflow in completed_workflows:
                if workflow.updated_at < cutoff_time:
                    if await self.delete_workflow(workflow.workflow_id):
                        cleaned_count += 1
            
            # Clean up old completed tasks
            completed_tasks = await self.list_tasks(status="completed")
            for task in completed_tasks:
                if task.updated_at < cutoff_time:
                    if await self.delete_task(task.task_id):
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired items")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return 0


# Global instance
redis_state_manager = RedisStateManager()