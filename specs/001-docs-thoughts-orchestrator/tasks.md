# Tasks: LangGraph Agent Orchestrator Service

**Input**: Design documents from `/specs/001-docs-thoughts-orchestrator/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, LangGraph, FastAPI, Redis, asyncio
   → Structure: Single project - backend service with REST API
2. Load design documents:
   → data-model.md: 5 core entities (Workflow, Agent, Project, Task, ExecutionContext)
   → contracts/: 2 API files (workflow-api.yaml, agent-api.yaml)
   → quickstart.md: Integration scenarios and test cases
3. Generate tasks by category following TDD approach
4. Apply parallel execution rules for independent components
5. Number tasks sequentially (T001, T002...)
6. SUCCESS: 38 tasks ready for orchestrator implementation
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Single project structure as per plan.md:
- **Source**: `src/` at repository root
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`

## Phase 3.1: Project Setup

- [ ] T001 Create project structure with src/{models,services,orchestrator,agents,workflows,config}/ directories
- [ ] T002 Initialize Python project with requirements.txt (LangGraph, FastAPI, Redis, pytest, asyncio)
- [ ] T003 [P] Configure linting (ruff, black) and pre-commit hooks in pyproject.toml
- [ ] T004 [P] Create Docker compose for Redis development environment in docker-compose.dev.yml
- [ ] T005 [P] Setup environment configuration in src/config/settings.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [ ] T006 [P] Contract test POST /api/v1/workflows in tests/contract/test_workflows_post.py
- [ ] T007 [P] Contract test GET /api/v1/workflows/{id} in tests/contract/test_workflows_get.py
- [ ] T008 [P] Contract test PUT /api/v1/workflows/{id}/pause in tests/contract/test_workflows_pause.py
- [ ] T009 [P] Contract test PUT /api/v1/workflows/{id}/resume in tests/contract/test_workflows_resume.py
- [ ] T010 [P] Contract test POST /api/v1/workflows/{id}/decisions in tests/contract/test_workflows_decisions.py
- [ ] T011 [P] Contract test POST /api/v1/agents in tests/contract/test_agents_post.py
- [ ] T012 [P] Contract test GET /api/v1/agents in tests/contract/test_agents_get.py
- [ ] T013 [P] Contract test GET /api/v1/agents/{id}/health in tests/contract/test_agents_health.py

### Integration Tests (from quickstart scenarios)
- [ ] T014 [P] Integration test complete movie creation workflow in tests/integration/test_movie_creation.py
- [ ] T015 [P] Integration test agent registration and health checks in tests/integration/test_agent_management.py
- [ ] T016 [P] Integration test workflow pause/resume functionality in tests/integration/test_workflow_control.py
- [ ] T017 [P] Integration test error recovery and retry mechanisms in tests/integration/test_error_recovery.py
- [ ] T018 [P] Integration test concurrent workflow execution in tests/integration/test_concurrent_workflows.py
- [ ] T019 [P] Integration test user decision handling in tests/integration/test_user_decisions.py

## Phase 3.3: Core Data Models (ONLY after tests are failing)

- [ ] T020 [P] Workflow model with state transitions in src/models/workflow.py
- [ ] T021 [P] Agent model with capability matching in src/models/agent.py
- [ ] T022 [P] Project model with metadata validation in src/models/project.py
- [ ] T023 [P] Task model with dependency management in src/models/task.py
- [ ] T024 [P] ExecutionContext model with runtime state in src/models/execution_context.py
- [ ] T025 [P] Base model classes and validation utilities in src/models/base.py

## Phase 3.4: Redis State Management

- [ ] T026 [P] Redis connection and configuration in src/services/redis_client.py
- [ ] T027 [P] Workflow state persistence service in src/services/workflow_state_service.py
- [ ] T028 [P] Agent registry service with Redis backend in src/services/agent_registry_service.py
- [ ] T029 [P] Task queue management service in src/services/task_queue_service.py
- [ ] T030 [P] Real-time event streaming with Redis Streams in src/services/event_stream_service.py

## Phase 3.5: Core Orchestration Engine

- [ ] T031 LangGraph workflow engine implementation in src/orchestrator/engine.py
- [ ] T032 Workflow state management and transitions in src/orchestrator/state.py
- [ ] T033 Agent request routing and load balancing in src/orchestrator/routing.py
- [ ] T034 Error handling and fault tolerance mechanisms in src/orchestrator/error_handler.py

## Phase 3.6: External Service Integration

- [ ] T035 [P] Auto-Movie App REST client in src/services/auto_movie_client.py
- [ ] T036 [P] Brain Service WebSocket MCP client in src/services/brain_client.py
- [ ] T037 [P] Task Service HTTP client with async polling in src/services/task_client.py

## Phase 3.7: FastAPI REST Endpoints

- [ ] T038 Workflow management endpoints (/api/v1/workflows) in src/api/workflow_endpoints.py
- [ ] T039 Agent management endpoints (/api/v1/agents) in src/api/agent_endpoints.py
- [ ] T040 Authentication and API key validation middleware in src/api/auth_middleware.py
- [ ] T041 Error handling and response formatting in src/api/error_handlers.py
- [ ] T042 WebSocket endpoints for real-time updates in src/api/websocket_handlers.py

## Phase 3.8: Agent Implementations

- [ ] T043 [P] Base agent class with standard interface in src/agents/base/base_agent.py
- [ ] T044 [P] Story agent implementations in src/agents/story/
- [ ] T045 [P] Character agent implementations in src/agents/character/
- [ ] T046 [P] Visual agent implementations in src/agents/visual/
- [ ] T047 [P] Production agent implementations in src/agents/production/

## Phase 3.9: Workflow Definitions

- [ ] T048 Movie creation workflow definition in src/workflows/movie_creation.py
- [ ] T049 Episode production workflow definition in src/workflows/episode_production.py
- [ ] T050 Character development workflow definition in src/workflows/character_development.py

## Phase 3.10: Application Bootstrap

- [ ] T051 FastAPI application factory and startup in src/main.py
- [ ] T052 Health check endpoints and service monitoring in src/api/health.py
- [ ] T053 Logging configuration and structured output in src/config/logging.py

## Phase 3.11: Polish and Optimization

- [ ] T054 [P] Unit tests for models validation in tests/unit/test_models.py
- [ ] T055 [P] Unit tests for state management in tests/unit/test_state_management.py
- [ ] T056 [P] Performance tests for concurrent workflows in tests/performance/test_concurrency.py
- [ ] T057 [P] Load testing with 100+ workflows in tests/performance/test_load.py
- [ ] T058 [P] API documentation generation and OpenAPI spec validation in docs/api/
- [ ] T059 [P] Deployment configuration and Docker production image in Dockerfile
- [ ] T060 Production monitoring and alerting configuration in monitoring/

## Dependencies

**Critical Path**:
- Setup (T001-T005) → Tests (T006-T019) → Models (T020-T025) → Services (T026-T030) → Engine (T031-T034) → Endpoints (T038-T042) → Bootstrap (T051-T053)

**Blocking Dependencies**:
- T020-T025 (models) must complete before T026-T030 (services)
- T026-T030 (services) must complete before T031-T034 (orchestration)
- T031-T034 (orchestration) must complete before T038-T042 (API endpoints)
- T038-T042 (endpoints) must complete before T051 (application bootstrap)

**Parallel Groups**:
- Tests T006-T019 can all run together
- Models T020-T025 can all run together
- Services T026-T030 can run together (except T031+ depend on them)
- Agent implementations T043-T047 can run together
- Workflow definitions T048-T050 can run together
- Polish tasks T054-T060 can all run together

## Parallel Execution Examples

### Contract Tests Phase
```bash
# Launch T006-T013 together:
Task: "Contract test POST /api/v1/workflows in tests/contract/test_workflows_post.py"
Task: "Contract test GET /api/v1/workflows/{id} in tests/contract/test_workflows_get.py"  
Task: "Contract test PUT /api/v1/workflows/{id}/pause in tests/contract/test_workflows_pause.py"
Task: "Contract test POST /api/v1/agents in tests/contract/test_agents_post.py"
```

### Integration Tests Phase  
```bash
# Launch T014-T019 together:
Task: "Integration test complete movie creation workflow in tests/integration/test_movie_creation.py"
Task: "Integration test agent registration in tests/integration/test_agent_management.py"
Task: "Integration test workflow control in tests/integration/test_workflow_control.py"
```

### Core Models Phase
```bash
# Launch T020-T025 together:
Task: "Workflow model with state transitions in src/models/workflow.py"
Task: "Agent model with capability matching in src/models/agent.py"
Task: "Project model with metadata validation in src/models/project.py"
Task: "Task model with dependency management in src/models/task.py"
```

### Services Phase
```bash
# Launch T026-T030 together after models complete:
Task: "Redis connection and configuration in src/services/redis_client.py"
Task: "Workflow state persistence service in src/services/workflow_state_service.py"
Task: "Agent registry service in src/services/agent_registry_service.py"
```

## Notes
- **[P] tasks**: Different files, no dependencies - can run in parallel
- **TDD Critical**: ALL tests (T006-T019) must be written and failing before any implementation
- **Redis Dependency**: Ensure Redis is running for service and integration tests
- **External Services**: Mock Auto-Movie, Brain, and Task services for testing
- **Performance Targets**: Validate 100+ concurrent workflows, sub-second queries
- **Error Recovery**: Test all failure scenarios from quickstart guide

## Validation Checklist
*GATE: Checked before implementation begins*

- [x] All API contracts have corresponding contract tests (T006-T013)
- [x] All data model entities have implementation tasks (T020-T025) 
- [x] All integration scenarios from quickstart covered (T014-T019)
- [x] Tests scheduled before implementation (Phase 3.2 before 3.3+)
- [x] Parallel tasks are truly independent (different files/components)
- [x] Each task specifies exact file path
- [x] Critical dependencies identified and sequenced
- [x] Performance and scale requirements addressed (T056-T057)