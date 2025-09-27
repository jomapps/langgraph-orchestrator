from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import logging
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt

from ..models import Workflow, Agent, Task, ExecutionContext
from ..models.workflow import WorkflowStatus, WorkflowState
from ..models.task import TaskStatus
from ..services import RedisStateManager
from ..config import settings
from ..clients.brain_client import BrainServiceClient
from ..workflows.base_workflow import create_workflow

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """
    Core workflow orchestrator using LangGraph for managing video creation workflows.
    Handles workflow state management, agent coordination, and task execution.
    """
    
    def __init__(self, state_manager: RedisStateManager):
        self.state_manager = state_manager
        self.workflows: Dict[str, StateGraph] = {}
        self.memory_saver = MemorySaver()
        self._running_workflows: Dict[str, asyncio.Task] = {}
        self.brain_client = None
        self._brain_workflows: Dict[str, object] = {}  # Store brain service workflows

    async def initialize_brain_client(self):
        """Initialize brain service client"""
        if self.brain_client is None:
            brain_service_url = getattr(settings, 'BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
            self.brain_client = BrainServiceClient(brain_service_url)
            await self.brain_client.connect()
            logger.info("Brain service client initialized and connected")

    async def initialize_workflow(self, workflow: Workflow) -> StateGraph:
        """
        Initialize a new workflow graph based on workflow configuration.
        Now supports both LangGraph and brain service workflows.
        """
        logger.info(f"Initializing workflow {workflow.workflow_id} of type {workflow.workflow_type}")

        # Initialize brain client if needed
        await self.initialize_brain_client()

        # Try to create brain service workflow first
        try:
            brain_workflow = await create_workflow(
                workflow.workflow_type.value,
                getattr(settings, 'BRAIN_SERVICE_BASE_URL', 'https://brain.ft.tc')
            )
            self._brain_workflows[workflow.workflow_id] = brain_workflow
            logger.info(f"Created brain service workflow for {workflow.workflow_id}")
        except Exception as e:
            logger.warning(f"Failed to create brain service workflow, falling back to LangGraph: {str(e)}")

        # Create traditional LangGraph workflow as fallback
        workflow_graph = StateGraph(ExecutionContext)

        # Add nodes based on workflow type
        if workflow.workflow_type.value == "movie_creation":
            await self._build_video_creation_workflow(workflow_graph, workflow)
        elif workflow.workflow_type.value == "content_generation":
            await self._build_content_optimization_workflow(workflow_graph, workflow)
        else:
            raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")

        # Compile the graph
        compiled_graph = workflow_graph.compile(checkpointer=self.memory_saver)
        self.workflows[workflow.workflow_id] = compiled_graph

        return compiled_graph
    
    async def _build_video_creation_workflow(self, graph: StateGraph, workflow: Workflow):
        """
        Build a video creation workflow graph with sequential and parallel processing nodes.
        """
        # Define workflow nodes
        nodes = {
            "script_generation": self._create_script_generation_node(),
            "scene_planning": self._create_scene_planning_node(),
            "visual_generation": self._create_visual_generation_node(),
            "voice_generation": self._create_voice_generation_node(),
            "video_assembly": self._create_video_assembly_node(),
            "quality_review": self._create_quality_review_node(),
            "finalize": self._create_finalize_node()
        }
        
        # Add nodes to graph
        for node_name, node_func in nodes.items():
            graph.add_node(node_name, node_func)
        
        # Define edges for sequential execution with parallel branches
        graph.add_edge("script_generation", "scene_planning")
        graph.add_edge("scene_planning", "visual_generation")
        graph.add_edge("scene_planning", "voice_generation")
        graph.add_edge("visual_generation", "video_assembly")
        graph.add_edge("voice_generation", "video_assembly")
        graph.add_edge("video_assembly", "quality_review")
        graph.add_edge("quality_review", "finalize")
        graph.add_edge("finalize", END)
        
        # Set entry point
        graph.set_entry_point("script_generation")
    
    async def _build_content_optimization_workflow(self, graph: StateGraph, workflow: Workflow):
        """
        Build a content optimization workflow graph.
        """
        nodes = {
            "content_analysis": self._create_content_analysis_node(),
            "optimization_suggestions": self._create_optimization_suggestions_node(),
            "apply_optimizations": self._create_apply_optimizations_node(),
            "validate_results": self._create_validate_results_node()
        }
        
        for node_name, node_func in nodes.items():
            graph.add_node(node_name, node_func)
        
        graph.add_edge("content_analysis", "optimization_suggestions")
        graph.add_edge("optimization_suggestions", "apply_optimizations")
        graph.add_edge("apply_optimizations", "validate_results")
        graph.add_edge("validate_results", END)
        
        graph.set_entry_point("content_analysis")
    
    def _create_script_generation_node(self):
        """Create script generation node."""
        async def script_generation_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing script generation for workflow {state.workflow_id}")
            
            # Get available script generation agents
            agents = await self.state_manager.get_agents_by_capability("script_generation")
            if not agents:
                raise ValueError("No script generation agents available")
            
            # Select best agent based on workflow requirements
            agent = self._select_best_agent(agents, state)
            
            # Create task for script generation
            task = Task(
                id=f"script_gen_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Script Generation",
                description="Generate video script based on requirements",
                type="script_generation",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "genre": state.metadata.get("genre", "educational"),
                    "duration": state.metadata.get("duration", 300),
                    "style": state.metadata.get("style_preferences", {})
                }
            )
            
            # Save task and update state
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started script generation task: {task.id}")
            
            return state
        
        return script_generation_node
    
    def _create_scene_planning_node(self):
        """Create scene planning node."""
        async def scene_planning_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing scene planning for workflow {state.workflow_id}")
            
            # Get script generation task result
            script_task = await self._get_previous_task_result(state, "script_generation")
            if not script_task or script_task.status != TaskStatus.COMPLETED:
                raise NodeInterrupt("Script generation must complete before scene planning")
            
            # Create scene planning task
            agents = await self.state_manager.get_agents_by_capability("scene_planning")
            if not agents:
                raise ValueError("No scene planning agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"scene_plan_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Scene Planning",
                description="Plan video scenes based on script",
                type="scene_planning",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "script": script_task.result,
                    "style": state.metadata.get("style_preferences", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started scene planning task: {task.id}")
            
            return state
        
        return scene_planning_node
    
    def _create_visual_generation_node(self):
        """Create visual generation node."""
        async def visual_generation_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing visual generation for workflow {state.workflow_id}")
            
            # This node can run in parallel with voice generation
            agents = await self.state_manager.get_agents_by_capability("visual_generation")
            if not agents:
                raise ValueError("No visual generation agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"visual_gen_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Visual Generation",
                description="Generate visual content for video",
                type="visual_generation",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "style": state.metadata.get("style_preferences", {}),
                    "scene_data": state.shared_data.get("scene_planning", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started visual generation task: {task.id}")
            
            return state
        
        return visual_generation_node
    
    def _create_voice_generation_node(self):
        """Create voice generation node."""
        async def voice_generation_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing voice generation for workflow {state.workflow_id}")
            
        # This node can run in parallel with visual generation
            agents = await self.state_manager.get_agents_by_capability("voice_generation")
            if not agents:
                raise ValueError("No voice generation agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"voice_gen_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Voice Generation",
                description="Generate voice content for video",
                type="voice_generation",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "script": state.shared_data.get("script", ""),
                    "voice_style": state.metadata.get("voice_preferences", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started voice generation task: {task.id}")
            
            return state
        
        return voice_generation_node
    
    def _create_video_assembly_node(self):
        """Create video assembly node."""
        async def video_assembly_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing video assembly for workflow {state.workflow_id}")
            
            # Wait for both visual and voice generation to complete
            visual_task = await self._get_previous_task_result(state, "visual_generation")
            voice_task = await self._get_previous_task_result(state, "voice_generation")
            
            if not visual_task or not voice_task:
                raise NodeInterrupt("Both visual and voice generation must complete before assembly")
            
            agents = await self.state_manager.get_agents_by_capability("video_assembly")
            if not agents:
                raise ValueError("No video assembly agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"video_assembly_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Video Assembly",
                description="Assemble final video from components",
                type="video_assembly",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "visual_data": visual_task.result,
                    "voice_data": voice_task.result,
                    "scene_data": state.shared_data.get("scene_planning", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started video assembly task: {task.id}")
            
            return state
        
        return video_assembly_node
    
    def _create_quality_review_node(self):
        """Create quality review node."""
        async def quality_review_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing quality review for workflow {state.workflow_id}")
            
            video_task = await self._get_previous_task_result(state, "video_assembly")
            if not video_task:
                raise NodeInterrupt("Video assembly must complete before quality review")
            
            agents = await self.state_manager.get_agents_by_capability("quality_review")
            if not agents:
                logger.warning("No quality review agents available, skipping review")
                return state
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"quality_review_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Quality Review",
                description="Review video quality and suggest improvements",
                type="quality_review",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "video_data": video_task.result,
                    "quality_standards": state.metadata.get("quality_standards", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started quality review task: {task.id}")
            
            return state
        
        return quality_review_node
    
    def _create_finalize_node(self):
        """Create finalize node."""
        async def finalize_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Finalizing workflow {state.workflow_id}")
            
            # Collect all task results
            final_results = {}
            for task_type in ["script_generation", "scene_planning", "visual_generation", 
                            "voice_generation", "video_assembly", "quality_review"]:
                task = await self._get_previous_task_result(state, task_type)
                if task and task.status == TaskStatus.COMPLETED:
                    final_results[task_type] = task.result
            
            # Update workflow state
            state.shared_data["final_results"] = final_results
            state.current_state = "completed"
            state.execution_history.append("Workflow completed successfully")
            
            return state
        
        return finalize_node
    
    # Content optimization workflow nodes
    def _create_content_analysis_node(self):
        """Create content analysis node."""
        async def content_analysis_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Executing content analysis for workflow {state.workflow_id}")
            
            agents = await self.state_manager.get_agents_by_capability("content_analysis")
            if not agents:
                raise ValueError("No content analysis agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"content_analysis_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Content Analysis",
                description="Analyze existing content for optimization opportunities",
                type="content_analysis",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters=state.metadata.get("analysis_parameters", {})
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started content analysis task: {task.id}")
            
            return state
        
        return content_analysis_node
    
    def _create_optimization_suggestions_node(self):
        """Create optimization suggestions node."""
        async def optimization_suggestions_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Creating optimization suggestions for workflow {state.workflow_id}")
            
            analysis_task = await self._get_previous_task_result(state, "content_analysis")
            if not analysis_task or analysis_task.status != TaskStatus.COMPLETED:
                raise NodeInterrupt("Content analysis must complete before optimization suggestions")
            
            agents = await self.state_manager.get_agents_by_capability("optimization_suggestions")
            if not agents:
                raise ValueError("No optimization suggestion agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"optimization_suggestions_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Optimization Suggestions",
                description="Generate optimization suggestions based on analysis",
                type="optimization_suggestions",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "analysis_results": analysis_task.result,
                    "optimization_goals": state.metadata.get("optimization_goals", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started optimization suggestions task: {task.id}")
            
            return state
        
        return optimization_suggestions_node
    
    def _create_apply_optimizations_node(self):
        """Create apply optimizations node."""
        async def apply_optimizations_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Applying optimizations for workflow {state.workflow_id}")
            
            suggestions_task = await self._get_previous_task_result(state, "optimization_suggestions")
            if not suggestions_task or suggestions_task.status != TaskStatus.COMPLETED:
                raise NodeInterrupt("Optimization suggestions must complete before applying optimizations")
            
            agents = await self.state_manager.get_agents_by_capability("apply_optimizations")
            if not agents:
                raise ValueError("No apply optimization agents available")
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"apply_optimizations_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Apply Optimizations",
                description="Apply optimization suggestions to content",
                type="apply_optimizations",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "suggestions": suggestions_task.result,
                    "optimization_settings": state.metadata.get("optimization_settings", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started apply optimizations task: {task.id}")
            
            return state
        
        return apply_optimizations_node
    
    def _create_validate_results_node(self):
        """Create validate results node."""
        async def validate_results_node(state: ExecutionContext) -> ExecutionContext:
            logger.info(f"Validating optimization results for workflow {state.workflow_id}")
            
            optimization_task = await self._get_previous_task_result(state, "apply_optimizations")
            if not optimization_task or optimization_task.status != TaskStatus.COMPLETED:
                raise NodeInterrupt("Apply optimizations must complete before validation")
            
            agents = await self.state_manager.get_agents_by_capability("validate_results")
            if not agents:
                logger.warning("No validation agents available, skipping validation")
                return state
            
            agent = self._select_best_agent(agents, state)
            
            task = Task(
                id=f"validate_results_{state.workflow_id}_{datetime.utcnow().isoformat()}",
                workflow_id=state.workflow_id,
                project_id=state.project_id,
                agent_id=agent.id,
                name="Validate Results",
                description="Validate optimization results",
                type="validate_results",
                status=TaskStatus.PENDING,
                priority=state.metadata.get("priority", "medium"),
                parameters={
                    "optimized_content": optimization_task.result,
                    "validation_criteria": state.metadata.get("validation_criteria", {})
                }
            )
            
            await self.state_manager.save_task(task)
            state.current_task_id = task.id
            state.task_states[task.id] = task.status.value
            state.execution_history.append(f"Started validation task: {task.id}")
            
            return state
        
        return validate_results_node
    
    async def start_workflow(self, workflow: Workflow) -> str:
        """
        Start a workflow execution with brain service integration.
        """
        logger.info(f"Starting workflow {workflow.workflow_id}")

        # Initialize workflow graph
        workflow_graph = await self.initialize_workflow(workflow)

        # Check if we have a brain service workflow
        if workflow.workflow_id in self._brain_workflows:
            logger.info(f"Using brain service workflow for {workflow.workflow_id}")
            # Start brain service workflow execution in background
            task = asyncio.create_task(self._execute_brain_workflow(workflow))
            self._running_workflows[workflow.workflow_id] = task
            return workflow.workflow_id

        # Fallback to traditional LangGraph execution
        # Create execution context
        execution_context = ExecutionContext(
            workflow_id=workflow.workflow_id,
            project_id=workflow.project_id,
            current_state="initializing",
            previous_state="",
            runtime_variables={},
            shared_data={},
            execution_history=[],
            task_states={},
            agent_states={},
            metadata=workflow.metadata,
            checkpoints=[],
            error_count=0,
            retry_attempts=0,
            performance_metrics={"start_time": datetime.utcnow().isoformat()}
        )
        
        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING
        workflow.current_state = WorkflowState.CONCEPT_DEVELOPMENT
        await self.state_manager.save_workflow(workflow)

        # Start workflow execution in background
        task = asyncio.create_task(self._execute_workflow(workflow_graph, execution_context))
        self._running_workflows[workflow.workflow_id] = task

        return workflow.workflow_id

    async def _execute_brain_workflow(self, workflow: Workflow):
        """
        Execute workflow using brain service.
        """
        try:
            logger.info(f"Executing brain service workflow {workflow.workflow_id}")

            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.current_state = WorkflowState.CONCEPT_DEVELOPMENT
            await self.state_manager.save_workflow(workflow)

            # Get brain service workflow
            brain_workflow = self._brain_workflows[workflow.workflow_id]

            # Execute the brain workflow
            result = await brain_workflow.execute(workflow)

            # Update workflow completion
            await self._complete_brain_workflow(workflow.workflow_id, result)

        except Exception as e:
            logger.error(f"Brain workflow execution failed: {e}")
            await self._fail_workflow(workflow.workflow_id, str(e))

    async def _complete_brain_workflow(self, workflow_id: str, final_result: Dict[str, Any]):
        """
        Handle brain workflow completion.
        """
        logger.info(f"Brain workflow {workflow_id} completed successfully")

        # Update workflow status
        workflow = await self.state_manager.get_workflow(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.current_state = WorkflowState.FINALIZATION
            workflow.progress_percentage = 100.0
            workflow.updated_at = datetime.utcnow()
            await self.state_manager.save_workflow(workflow)

        # Clean up running workflows
        if workflow_id in self._running_workflows:
            del self._running_workflows[workflow_id]
        if workflow_id in self._brain_workflows:
            del self._brain_workflows[workflow_id]
    
    async def _execute_workflow(self, workflow_graph: StateGraph, execution_context: ExecutionContext):
        """
        Execute workflow graph with error handling and state management.
        """
        try:
            logger.info(f"Executing workflow {execution_context.workflow_id}")
            
            # Execute the graph
            result = await workflow_graph.ainvoke(execution_context)
            
            # Update workflow completion
            await self._complete_workflow(execution_context.workflow_id, result)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            await self._fail_workflow(execution_context.workflow_id, str(e))
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pause a running workflow.
        """
        logger.info(f"Pausing workflow {workflow_id}")
        
        if workflow_id in self._running_workflows:
            task = self._running_workflows[workflow_id]
            if not task.done():
                # In a real implementation, you might use cancellation tokens
                # or cooperative cancellation patterns
                task.cancel()
                
                # Update workflow status
                workflow = await self.state_manager.get_workflow(workflow_id)
                if workflow:
                    workflow.status = WorkflowStatus.PAUSED
                    await self.state_manager.save_workflow(workflow)
                
                return True
        
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a paused workflow.
        """
        logger.info(f"Resuming workflow {workflow_id}")
        
        # Get workflow and execution context
        workflow = await self.state_manager.get_workflow(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False
        
        # Rebuild workflow graph
        workflow_graph = await self.initialize_workflow(workflow)
        
        # Get last execution context
        execution_context = await self.state_manager.get_execution_context(workflow_id)
        if not execution_context:
            return False
        
        # Resume execution
        task = asyncio.create_task(self._execute_workflow(workflow_graph, execution_context))
        self._running_workflows[workflow_id] = task
        
        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING
        await self.state_manager.save_workflow(workflow)
        
        return True
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        """
        logger.info(f"Canceling workflow {workflow_id}")
        
        # Cancel running task
        if workflow_id in self._running_workflows:
            task = self._running_workflows[workflow_id]
            if not task.done():
                task.cancel()
        
        # Update workflow status
        workflow = await self.state_manager.get_workflow(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.CANCELLED
            await self.state_manager.save_workflow(workflow)
        
        # Clean up running workflows
        if workflow_id in self._running_workflows:
            del self._running_workflows[workflow_id]
        
        return True
    
    async def _complete_workflow(self, workflow_id: str, final_state: ExecutionContext):
        """
        Handle workflow completion.
        """
        logger.info(f"Workflow {workflow_id} completed successfully")
        
        # Update workflow status
        workflow = await self.state_manager.get_workflow(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.state = WorkflowState.FINISHED
            workflow.progress = 100.0
            workflow.completed_at = datetime.utcnow()
            await self.state_manager.save_workflow(workflow)
        
        # Clean up running workflows
        if workflow_id in self._running_workflows:
            del self._running_workflows[workflow_id]
    
    async def _fail_workflow(self, workflow_id: str, error_message: str):
        """
        Handle workflow failure.
        """
        logger.error(f"Workflow {workflow_id} failed: {error_message}")
        
        # Update workflow status
        workflow = await self.state_manager.get_workflow(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.FAILED
            workflow.state = WorkflowState.ERROR
            workflow.error_message = error_message
            await self.state_manager.save_workflow(workflow)
        
        # Clean up running workflows
        if workflow_id in self._running_workflows:
            del self._running_workflows[workflow_id]
    
    def _select_best_agent(self, agents: List[Agent], state: ExecutionContext) -> Agent:
        """
        Select the best agent based on capabilities, performance, and availability.
        """
        # Simple selection logic - in a real implementation, this would be more sophisticated
        # considering agent load, performance metrics, specializations, etc.
        
        # Filter available agents
        available_agents = [agent for agent in agents if agent.status.value == "available"]
        
        if not available_agents:
            # If no available agents, select the one with best performance metrics
            return min(agents, key=lambda a: a.performance_metrics.get("error_rate", 1.0))
        
        # Select agent with best performance metrics
        return min(available_agents, key=lambda a: a.performance_metrics.get("error_rate", 1.0))
    
    async def _get_previous_task_result(self, state: ExecutionContext, task_type: str) -> Optional[Task]:
        """
        Get the result of a previous task by type.
        """
        # Get all tasks for this workflow
        tasks = await self.state_manager.get_tasks_by_workflow(state.workflow_id)
        
        # Find the most recent task of the specified type
        for task in sorted(tasks, key=lambda t: t.created_at, reverse=True):
            if task.type == task_type:
                return task
        
        return None
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a workflow.
        """
        workflow = await self.state_manager.get_workflow(workflow_id)
        if not workflow:
            return None
        
        execution_context = await self.state_manager.get_execution_context(workflow_id)
        
        return {
            "workflow": workflow,
            "execution_context": execution_context,
            "is_running": workflow_id in self._running_workflows and not self._running_workflows[workflow_id].done()
        }
    
    async def cleanup_completed_workflows(self):
        """
        Clean up completed workflows from memory.
        """
        completed_workflows = []
        
        for workflow_id, task in self._running_workflows.items():
            if task.done():
                completed_workflows.append(workflow_id)
        
        for workflow_id in completed_workflows:
            del self._running_workflows[workflow_id]
        
        logger.info(f"Cleaned up {len(completed_workflows)} completed workflows")

    async def cleanup_brain_service(self):
        """Clean up brain service connections"""
        if self.brain_client:
            await self.brain_client.disconnect()
            self.brain_client = None
            logger.info("Brain service connections cleaned up")

# Global orchestrator instance
orchestrator = None

async def get_orchestrator() -> WorkflowOrchestrator:
    """
    Get the global orchestrator instance.
    """
    global orchestrator
    if orchestrator is None:
        state_manager = await RedisStateManager.create()
        orchestrator = WorkflowOrchestrator(state_manager)
    
    return orchestrator