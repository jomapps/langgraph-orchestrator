# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Server Management
```bash
# Start development server
python src/main.py
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Start production server (as configured)
uvicorn src.main:app --host 0.0.0.0 --port 8003 --workers 4

# Run with specific configuration
python start_server.py
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python test_simple.py
python test_api.py
python test_live_operations.py

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code
black src/ tests/ --line-length 120

# Lint code
ruff src/ tests/ --fix

# Run pre-commit hooks
pre-commit run --all-files
```

### Docker Operations
```bash
# Build Docker image
docker build -t langgraph-orchestrator .

# Run with Docker Compose (development)
docker-compose -f docker-compose.dev.yml up

# Run with Docker Compose (production)
docker-compose -f docker-compose.prod.yml up
```

### Deployment
```bash
# Deploy to Coolify
./deploy-coolify.sh

# Test API endpoints after deployment
curl https://agents.ft.tc/health
curl https://agents.ft.tc/api/v1/agents
curl https://agents.ft.tc/api/v1/workflows
```

## Architecture Overview

### High-Level Architecture
The LangGraph Orchestrator is a **FastAPI-based workflow orchestration system** that manages AI video creation workflows using the LangGraph framework. It operates as a microservice that coordinates between multiple AI agents to execute complex, multi-stage workflows.

### Core Components

#### 1. **FastAPI Application** (`src/main.py`)
- RESTful API server with comprehensive endpoints
- CORS middleware for cross-origin requests
- Health monitoring and background task management
- Serves at `/api/v1/` with OpenAPI documentation at `/api/docs`

#### 2. **Workflow Orchestrator** (`src/orchestrator/workflow_orchestrator.py`)
- **LangGraph-based workflow engine** using StateGraph
- Manages complex workflows with sequential and parallel execution
- Supports two main workflow types:
  - **Movie Creation**: Multi-stage video production (script → scene planning → visual/voice generation → assembly → review)
  - **Content Optimization**: Analysis → suggestions → optimization → validation
- Built-in error handling, pause/resume capabilities, and agent selection logic

#### 3. **State Management** (`src/services/redis_state_manager.py`)
- **Redis-based persistence** for workflows, agents, tasks, and execution contexts
- Handles workflow lifecycle state transitions
- Manages agent availability and task assignments

#### 4. **Data Models** (`src/models/`)
- **Pydantic models** with validation and enum support
- Key entities: `Workflow`, `Agent`, `Task`, `Project`, `ExecutionContext`
- Enum-based status management for consistent state tracking

#### 5. **Configuration Management** (`src/config/settings.py`)
- Environment-based configuration using pydantic-settings
- Supports Redis, Neo4j, and external service connections

### Workflow Execution Flow

1. **Workflow Creation**: API receives workflow request → validates project → stores in Redis
2. **Workflow Initialization**: Orchestrator builds LangGraph StateGraph based on workflow type
3. **Agent Selection**: Dynamic agent assignment based on capabilities and performance metrics
4. **Task Execution**: Sequential/parallel task execution with state checkpointing
5. **Progress Tracking**: Real-time status updates stored in Redis
6. **Completion**: Results aggregation and cleanup

### Key External Dependencies

- **LangGraph**: Core workflow orchestration framework
- **Redis**: State management and caching layer  
- **Neo4j**: Graph database (production deployment)
- **External Services**: Auto-movie service, brain service, task service

## Project-Specific Guidelines

### Byterover MCP Integration
This project integrates with **Byterover MCP Server Tools** for advanced memory and planning capabilities. When working with this codebase:

#### Memory Management
- **Always use** `byterover-retrieve-knowledge` before implementing new features to gather context
- **Store important insights** using `byterover-store-knowledge` after significant changes
- Reference Byterover sources explicitly in code comments: *"According to Byterover memory layer"*

#### Planning Workflows  
- For multi-step implementation tasks, use `byterover-save-implementation-plan` to persist plans
- Update progress with `byterover-update-plan-progress` as tasks complete
- Use `byterover-reflect-context` and `byterover-assess-context` during implementation

### API Development Patterns

#### Model Field Mapping
When working with API endpoints, be aware of field name inconsistencies:
- Agent model: Use `agent.agent_id` not `agent.id`
- Workflow model: Use `workflow.workflow_id`, `workflow.workflow_type`, `workflow.current_state`, `workflow.progress_percentage`
- Always check enum handling: `obj.value if hasattr(obj, 'value') else str(obj)`

#### State Manager Methods
- Use `list_agents()` and `list_workflows()` (not `get_agents()` or `get_workflows()`)  
- The `offset` parameter is not supported in list methods
- **Type Safety**: All Redis operations use `_ensure_connected()` pattern (null-safe)
- Always handle Redis connection failures gracefully
- **Reliability**: 70+ type safety fixes applied (September 2025)

### Environment Configuration

#### Development Setup
```bash
# Required environment variables
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true
REDIS_HOST=redis://localhost:6379/0
LOG_LEVEL=INFO
```

#### Production Configuration  
- Port 8003 (exposed via Coolify)
- Worker processes: 4
- Health checks enabled at `/health`
- CORS configured for production domains

### Testing Strategy

#### API Testing
- Use `test_api.py` for basic API functionality
- `test_live_operations.py` for integration testing with external services
- `test_live_apis.py` for production API validation

#### Workflow Testing
- Mock Redis and external services for unit tests
- Use real Redis instance for integration testing
- Test workflow pause/resume and cancellation scenarios

### Deployment Notes

#### Production Environment
- **URL**: https://agents.ft.tc
- **Platform**: Coolify with Docker containerization
- **Database**: Neo4j cluster + Redis state management
- **Monitoring**: Health checks, structured logging (configurable)

#### Common Deployment Issues
1. **Dockerfile**: Ensure only existing files are copied (no setup.py, pytest.ini, README.md)
2. **Field Mappings**: Verify model field names match between API and data layers
3. **Redis Connection**: Handle Redis connectivity failures gracefully
4. **Agent Performance**: Monitor agent selection algorithms under load

### External API Integration
The orchestrator integrates with multiple external services. When adding new integrations:
- Follow the existing service URL pattern in environment variables
- Implement proper error handling and retry logic  
- Use structured logging for external API calls
- Consider rate limiting and circuit breaker patterns

This architecture supports complex, stateful workflows while maintaining scalability and reliability through proper state management and error recovery mechanisms.