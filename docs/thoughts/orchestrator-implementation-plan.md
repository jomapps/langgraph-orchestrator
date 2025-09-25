# Agent Orchestrator Service - Implementation Plan

## Overview
Implementation planning document for the LangGraph Agent Orchestrator that coordinates all 50+ AI movie production agents. This service runs at `agents.ft.tc` and manages intelligent workflows from story creation through final video assembly.

## Architecture Overview

### Core Components
- **LangGraph Workflow Engine**: Manages complex state-driven workflows with conditional branching
- **Agent Registry**: Dynamic discovery and routing for 50+ specialized agents  
- **Service Integration Layer**: Connects to Auto-Movie, Brain Service, and Task Service
- **State Management**: Redis-backed persistent workflow state
- **REST API**: HTTP endpoints for workflow management and monitoring

### Key Design Principles
- **Stateful Workflows**: Persistent state across long-running movie production processes
- **Fault Tolerance**: Automatic retry, error recovery, and graceful degradation
- **Scalability**: Handle multiple concurrent movie projects
- **Flexibility**: Dynamic agent registration and workflow modification
- **Observability**: Comprehensive monitoring and logging

## Project Structure

```
agent-orchestrator-service/
├── src/
│   ├── orchestrator/          # Core orchestration engine
│   │   ├── engine.py         # LangGraph workflow execution
│   │   ├── state.py          # Workflow state management
│   │   └── routing.py        # Agent request routing
│   ├── agents/               # Agent implementations
│   │   ├── base/             # Base agent classes
│   │   ├── story/            # Story-related agents
│   │   ├── character/        # Character agents
│   │   ├── visual/           # Visual production agents
│   │   └── production/       # Final production agents
│   ├── workflows/            # Workflow definitions
│   │   ├── movie_creation.py # End-to-end movie workflows
│   │   ├── episode_production.py
│   │   └── character_development.py
│   ├── services/             # External service clients
│   │   ├── auto_movie_client.py
│   │   ├── brain_client.py
│   │   └── task_client.py
│   ├── models/               # Data models
│   └── config/               # Configuration
├── tests/
└── docker/
```

## Core Technology Stack

### Primary Framework: LangGraph
- **Why**: Built for complex, stateful AI workflows with conditional logic
- **Usage**: Define movie production workflows as state graphs
- **Benefits**: Built-in state persistence, error recovery, human-in-the-loop

### State Management: Redis
- **Purpose**: Persist workflow state, agent status, and intermediate results
- **Schema**: Workflow states, agent registry, task queues
- **Benefits**: Fast access, pub/sub for real-time updates

### API Framework: FastAPI
- **Endpoints**: Workflow management, agent status, monitoring
- **Features**: Async support, automatic OpenAPI docs, WebSocket support

## Workflow Architecture

### State-Driven Workflow Design

**Concept**: Each movie production workflow is a state machine where agents process specific states and transition to new states based on results.

```python
# Example workflow states
MovieProductionStates = {
    "concept_development": ["story_architect", "world_builder"],
    "character_creation": ["character_creator", "character_designer"],  
    "scene_planning": ["scene_director", "storyboard_artist"],
    "media_generation": ["image_generation", "video_generation"],
    "post_production": ["video_editor", "audio_mixer"],
    "final_assembly": ["final_qc", "distribution"]
}
```

### Workflow Types

#### 1. Linear Workflows
Sequential agent execution with dependencies
- Story development → Character creation → Scene planning

#### 2. Parallel Workflows  
Multiple agents working simultaneously
- Multiple episode production, character voice generation

#### 3. Conditional Workflows
Branch based on results or user input
- If story approved → proceed to characters, else → revise story

#### 4. Interactive Workflows
Human-in-the-loop decision points
- Present 4 choices to user, await selection

## Agent System Design

### Base Agent Architecture

**Concept**: All agents inherit from BaseAgent with standardized interface for orchestrator communication.

```python
# Conceptual agent structure
class BaseAgent:
    def __init__(self, agent_id, capabilities, resource_requirements)
    async def execute(self, task_data, context)
    async def validate_input(self, task_data) 
    async def handle_error(self, error, retry_count)
    def get_status(self) -> AgentStatus
```

### Agent Categories

#### Story Agents
- **Series Creator**: Initial concept development
- **Story Architect**: Overall narrative structure  
- **Episode Breakdown**: Individual episode planning
- **Dialogue Writer**: Character dialogue generation

#### Character Agents  
- **Character Creator**: Personality and background
- **Character Designer**: Visual appearance
- **Voice Creator**: Voice profile generation
- **Character Arc Manager**: Development tracking

#### Visual Agents
- **Concept Artist**: Style guides and mood boards
- **Environment Designer**: Location and set design
- **Image Generation**: Visual asset creation
- **Video Generation**: Scene video production

#### Production Agents
- **Video Editor**: Scene assembly
- **Audio Mixer**: Sound and music integration
- **Quality Control**: Final review and validation
- **Distribution**: Format and delivery

### Agent Communication Pattern

**Concept**: Agents communicate through the orchestrator, never directly with each other. This enables monitoring, logging, and error handling.

```python
# Agent execution flow
workflow_state = orchestrator.get_current_state(project_id)
task_data = orchestrator.prepare_task(agent_id, workflow_state)
result = await agent.execute(task_data, context)
new_state = orchestrator.process_result(result, workflow_state)
```

## Service Integration Architecture

### Auto-Movie App Integration
- **Purpose**: Get project data, user preferences, store results
- **Pattern**: REST API calls for CRUD operations
- **Data Flow**: Project setup → workflow triggering → progress updates

### Brain Service Integration  
- **Purpose**: Knowledge consistency, semantic search, character relationships
- **Pattern**: WebSocket MCP protocol for real-time queries
- **Data Flow**: Query existing knowledge → validate consistency → store new knowledge

### Task Service Integration
- **Purpose**: GPU-intensive media generation (images, videos, audio)
- **Pattern**: HTTP task submission with async result polling
- **Data Flow**: Submit task → monitor progress → retrieve results

## Workflow Implementation Strategy

### Phase 1: Basic Orchestration
**Goal**: Simple linear workflows with manual transitions

**Implementation**:
- Basic LangGraph setup with state management
- Simple agent registry with 5-10 core agents
- Linear movie creation workflow (story → characters → scenes)
- Redis state persistence

**Success Criteria**: Complete end-to-end movie creation with manual steps

### Phase 2: Intelligent Routing
**Goal**: Automatic agent selection and parallel execution

**Implementation**:
- Dynamic agent discovery and capability matching
- Parallel workflow execution for independent tasks
- Conditional branching based on agent results
- Error handling and retry mechanisms

**Success Criteria**: Multiple projects running simultaneously with smart routing

### Phase 3: Advanced Workflows
**Goal**: Complex conditional workflows with user interaction

**Implementation**:
- Human-in-the-loop decision points
- Conditional workflows based on quality checks
- Advanced error recovery and workflow repair
- Performance optimization and resource management

**Success Criteria**: Production-ready system handling complex creative workflows

## State Management Design

### Workflow State Schema
```python
# Conceptual state structure
WorkflowState = {
    "workflow_id": "uuid",
    "project_id": "project_123", 
    "current_step": "character_creation",
    "completed_steps": ["concept_development", "story_architecture"],
    "pending_tasks": [{"agent": "character_creator", "data": {...}}],
    "results": {"story": {...}, "characters": [...]},
    "user_decisions": [{"step": "story_approval", "choice": "approved"}],
    "error_history": [],
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### State Persistence Strategy
- **Redis Streams**: Workflow event log for audit and replay
- **Redis Hashes**: Current workflow states for fast access  
- **Redis Sets**: Agent availability and resource tracking
- **TTL Policy**: Cleanup completed workflows after 30 days

## API Design

### RESTful Endpoints

#### Workflow Management
- `POST /api/v1/workflows` - Start new workflow
- `GET /api/v1/workflows/{id}` - Get workflow status
- `PUT /api/v1/workflows/{id}/pause` - Pause workflow
- `PUT /api/v1/workflows/{id}/resume` - Resume workflow
- `DELETE /api/v1/workflows/{id}` - Cancel workflow

#### Agent Management  
- `GET /api/v1/agents` - List available agents
- `GET /api/v1/agents/{id}/status` - Agent status
- `POST /api/v1/agents/{id}/reset` - Reset agent state

#### Project Operations
- `GET /api/v1/projects/{id}/workflows` - Project workflows
- `POST /api/v1/projects/{id}/workflows/{type}` - Start project workflow

### WebSocket Endpoints
- `/ws/workflows/{id}` - Real-time workflow updates
- `/ws/agents` - Agent status broadcasts

## Error Handling Strategy

### Error Categories
1. **Agent Errors**: Individual agent failures, retry with exponential backoff
2. **Service Errors**: External service unavailable, circuit breaker pattern
3. **Workflow Errors**: Invalid state transitions, workflow repair mechanisms
4. **System Errors**: Resource exhaustion, graceful degradation

### Recovery Patterns
- **Automatic Retry**: Transient failures with configurable backoff
- **Circuit Breaker**: Prevent cascading failures from external services
- **Workflow Checkpoints**: Resume from last successful state
- **Manual Intervention**: Human oversight for complex failures

## Monitoring and Observability

### Metrics Collection
- **Workflow Metrics**: Completion rates, execution times, error rates
- **Agent Metrics**: Utilization, success rates, response times  
- **System Metrics**: Resource usage, queue depths, throughput
- **Business Metrics**: Movies produced, user satisfaction, cost per production

### Logging Strategy
- **Structured Logging**: JSON format for automated analysis
- **Correlation IDs**: Track requests across service boundaries
- **Workflow Traces**: Complete execution history for debugging
- **Performance Profiling**: Identify bottlenecks and optimization opportunities

## Deployment Architecture

### Development Environment
- **Local Setup**: Docker Compose with all dependencies
- **Mock Services**: Stub implementations for independent development
- **Test Data**: Sample projects and workflows for validation

### Production Deployment
- **Container Strategy**: Docker containers with health checks
- **Load Balancing**: Multiple orchestrator instances behind load balancer
- **State Replication**: Redis cluster for high availability
- **Monitoring Stack**: Prometheus + Grafana for observability

## Testing Strategy

### Unit Testing
- **Agent Testing**: Mock orchestrator interactions
- **Workflow Testing**: State transition validation
- **Service Integration**: Mock external service responses

### Integration Testing  
- **End-to-End Workflows**: Complete movie production scenarios
- **Service Integration**: Real interactions with Auto-Movie, Brain, Task services
- **Performance Testing**: Load testing with multiple concurrent workflows

### Chaos Testing
- **Service Failures**: Test resilience to external service outages
- **Network Partitions**: Validate behavior during network issues
- **Resource Constraints**: Behavior under memory/CPU pressure

## Security Considerations

### Authentication & Authorization
- **API Key Authentication**: Service-to-service authentication
- **Workflow Signing**: Cryptographic verification of workflow integrity
- **Project Isolation**: Ensure users only access their projects

### Data Protection
- **Encryption**: TLS for all external communications
- **Sensitive Data**: Secure handling of user content and credentials
- **Audit Logging**: Complete audit trail for compliance

## Performance Considerations

### Scalability Targets
- **Concurrent Workflows**: Support 100+ simultaneous movie productions
- **Agent Throughput**: Handle 1000+ agent executions per minute
- **Response Times**: Sub-second response for workflow status queries
- **State Updates**: Real-time workflow progress updates

### Optimization Strategies
- **Connection Pooling**: Efficient external service connections
- **Caching**: Aggressive caching of agent results and project data
- **Resource Management**: Smart agent scheduling based on resource availability
- **Batch Operations**: Group related operations for efficiency

## Success Metrics

### Development Milestones
1. **Basic Orchestration**: Linear workflows with 5 agents (Week 1-2)
2. **Service Integration**: Connect to all external services (Week 3-4)
3. **Complex Workflows**: Conditional and parallel workflows (Week 5-6)
4. **Production Ready**: Full agent set with monitoring (Week 7-8)

### Production KPIs
- **Reliability**: 99.9% workflow completion rate
- **Performance**: Average movie production time < 2 hours
- **Scalability**: Handle 10x traffic growth
- **User Satisfaction**: 95%+ approval rate for generated content

This implementation plan provides the architectural foundation for building a sophisticated AI movie production orchestrator that can grow from simple linear workflows to complex, intelligent movie production pipelines.