# Data Model: LangGraph Agent Orchestrator Service

## Core Entities

### Workflow
Represents a complete movie production process with defined states and transitions.

**Fields**:
- `workflow_id`: Unique identifier (UUID)
- `project_id`: Reference to associated project 
- `workflow_type`: Type of workflow (movie_creation, episode_production, character_development)
- `current_state`: Current workflow state (concept_development, character_creation, scene_planning, etc.)
- `completed_states`: List of successfully completed states
- `pending_tasks`: Queue of tasks awaiting execution
- `results`: Dictionary of intermediate and final results by state
- `user_decisions`: History of human-in-the-loop decisions
- `error_history`: Log of errors and recovery actions
- `status`: Overall workflow status (running, paused, completed, failed, cancelled)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp
- `estimated_completion`: Projected completion time
- `priority`: Workflow execution priority (1-10)

**State Transitions**:
- Linear: concept_development → character_creation → scene_planning → media_generation → post_production → final_assembly
- Conditional: Based on quality checks, user approval, or error conditions
- Parallel: Multiple sub-workflows can execute simultaneously

**Validation Rules**:
- workflow_id must be unique
- project_id must reference existing project
- current_state must be valid for workflow_type
- completed_states must be chronologically consistent

### Agent
Specialized AI service with specific capabilities and resource requirements.

**Fields**:
- `agent_id`: Unique identifier
- `agent_type`: Category (story, character, visual, production)
- `capabilities`: List of specific functions (story_architect, character_creator, etc.)
- `resource_requirements`: CPU, memory, GPU requirements
- `status`: Current status (available, busy, maintenance, offline)
- `max_concurrent_tasks`: Maximum parallel task capacity
- `current_tasks`: List of currently executing tasks
- `success_rate`: Historical success percentage
- `average_execution_time`: Average task completion time
- `last_heartbeat`: Last health check timestamp
- `version`: Agent implementation version
- `endpoint_url`: Service endpoint for communication
- `health_check_url`: Health monitoring endpoint

**Agent Categories**:
- Story Agents: series_creator, story_architect, episode_breakdown, dialogue_writer
- Character Agents: character_creator, character_designer, voice_creator, character_arc_manager
- Visual Agents: concept_artist, environment_designer, image_generation, video_generation  
- Production Agents: video_editor, audio_mixer, quality_control, distribution

**Validation Rules**:
- agent_id must be unique
- capabilities must match agent_type
- resource_requirements must be positive values
- endpoint_url must be valid and accessible

### Project
User-initiated movie concept with metadata and preferences.

**Fields**:
- `project_id`: Unique identifier
- `user_id`: Owner of the project
- `title`: Project name/title
- `description`: Project concept description
- `genre`: Movie genre (action, comedy, drama, etc.)
- `target_duration`: Desired final video length
- `style_preferences`: Visual and narrative style choices
- `characters`: List of main characters with descriptions
- `settings`: List of locations/environments
- `themes`: List of narrative themes
- `content_rating`: Target audience rating (G, PG, R, etc.)
- `status`: Project status (draft, in_production, completed, cancelled)
- `created_at`: Creation timestamp
- `deadline`: Target completion date
- `budget_constraints`: Resource limitations if any
- `custom_requirements`: Special instructions or constraints

**Validation Rules**:
- project_id must be unique
- user_id must reference valid user
- target_duration must be positive
- deadline must be in the future (if specified)

### Task
Individual work unit assigned to agents with execution parameters.

**Fields**:
- `task_id`: Unique identifier
- `workflow_id`: Parent workflow reference
- `agent_id`: Assigned agent identifier
- `task_type`: Specific task category
- `input_data`: Task input parameters and context
- `output_data`: Task results (populated on completion)
- `dependencies`: List of prerequisite task IDs
- `status`: Execution status (pending, running, completed, failed, cancelled)
- `priority`: Task priority within workflow
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum allowed retries
- `timeout`: Maximum execution time allowed
- `started_at`: Execution start timestamp
- `completed_at`: Completion timestamp
- `error_message`: Error details if failed
- `resource_usage`: Actual CPU/memory/GPU consumption
- `quality_score`: Result quality assessment (if applicable)

**Status Flow**:
- pending → running → (completed | failed)
- failed → pending (on retry)
- Any status → cancelled

**Validation Rules**:
- task_id must be unique
- workflow_id must reference existing workflow
- agent_id must reference available agent
- dependencies must form acyclic graph
- timeout must be positive

### ExecutionContext
Runtime state and metadata for workflow execution.

**Fields**:
- `context_id`: Unique identifier
- `workflow_id`: Associated workflow reference
- `current_step`: Detailed current execution step
- `step_history`: Chronological log of execution steps
- `active_tasks`: Currently executing task references
- `completed_tasks`: Successfully finished tasks
- `failed_tasks`: Failed task references with error details
- `resource_allocation`: Current resource usage by category
- `performance_metrics`: Execution performance data
- `user_interaction_points`: Points requiring human decisions
- `external_service_calls`: Log of external API interactions
- `checkpoint_data`: State snapshot for recovery
- `environment_variables`: Runtime configuration
- `debug_information`: Debugging and troubleshooting data

**Relationships**:
- One-to-one with Workflow
- One-to-many with Task
- Contains references to Agent interactions

## Data Relationships

### Primary Relationships
- Project → Workflow (one-to-many): A project can have multiple workflows
- Workflow → Task (one-to-many): A workflow contains multiple tasks
- Workflow → ExecutionContext (one-to-one): Each workflow has one execution context
- Agent → Task (one-to-many): An agent can handle multiple tasks
- Task → Task (many-to-many): Tasks can have dependencies on other tasks

### State Consistency Rules
- Workflow state must be consistent with completed tasks
- Agent availability must match current task assignments
- Task dependencies must not create circular references
- Execution context must reflect current workflow state
- Project status must align with associated workflow states

## Storage Schema

### Redis Data Structures

**Workflow State** (Hash):
```
workflow:{workflow_id} -> {
    project_id: string,
    type: string,
    current_state: string,
    status: string,
    created_at: timestamp,
    updated_at: timestamp,
    ...
}
```

**Agent Registry** (Hash + Set):
```
agent:{agent_id} -> {agent_data}
agents:available -> set of available agent_ids
agents:busy -> set of busy agent_ids
```

**Task Queue** (List + Hash):
```
tasks:pending -> list of pending task_ids
tasks:running -> set of running task_ids
task:{task_id} -> {task_data}
```

**Workflow Events** (Stream):
```
workflow_events:{workflow_id} -> stream of state change events
```

### Data Persistence Strategy
- **Hot Data**: Current workflow states, active tasks, agent status (Redis memory)
- **Warm Data**: Recent workflow history, performance metrics (Redis with TTL)
- **Cold Data**: Completed workflows, audit logs (External storage via Task Service)
- **Backup Strategy**: Periodic snapshots to external storage
- **Recovery Strategy**: Replay from checkpoints and event streams