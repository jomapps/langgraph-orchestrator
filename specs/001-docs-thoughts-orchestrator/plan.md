
# Implementation Plan: LangGraph Agent Orchestrator Service

**Branch**: `001-docs-thoughts-orchestrator` | **Date**: 2025-09-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-docs-thoughts-orchestrator/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build an intelligent orchestrator service that coordinates 50+ specialized AI agents to automate complete movie production workflows. The system manages stateful, long-running processes from initial concept through final video delivery, with support for parallel execution, fault tolerance, and human-in-the-loop decision points. Core capabilities include workflow state persistence, intelligent agent routing, external service integration (Auto-Movie, Brain Service, Task Service), and real-time progress monitoring.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: LangGraph, FastAPI, Redis, asyncio  
**Storage**: Redis for workflow state persistence, external service APIs for data  
**Testing**: pytest for unit/integration tests, contract testing for service boundaries  
**Target Platform**: Linux server deployment (agents.ft.tc)
**Project Type**: single - backend service with REST API  
**Performance Goals**: Support 100+ concurrent workflows, 1000+ agent executions/min, sub-second status queries  
**Constraints**: <2 hour movie production time, 99.9% workflow completion rate, real-time progress updates  
**Scale/Scope**: 50+ agents, multiple concurrent projects, stateful long-running processes

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check**:
- **Library-First Principle**: ✅ PASS - Core orchestration logic implemented as reusable libraries
- **Testing Requirements**: ✅ PASS - TDD approach with contract tests for service boundaries
- **Simplicity Principle**: ⚠️  REVIEW - Complex state management required; justified by domain complexity
- **Observability**: ✅ PASS - Structured logging, workflow traces, metrics collection planned
- **Service Boundaries**: ✅ PASS - Clear separation between orchestrator, agents, and external services

**Post-Design Re-evaluation**:
- **Library-First Principle**: ✅ PASS - Design maintains modular libraries (workflow engine, agent registry, state management)
- **Testing Requirements**: ✅ PASS - Contract tests defined in API specs, integration scenarios in quickstart
- **Simplicity Principle**: ✅ PASS - Complexity justified and well-structured with clear data models and API boundaries
- **Observability**: ✅ PASS - Comprehensive monitoring and tracing designed into architecture
- **Service Boundaries**: ✅ PASS - Clean API contracts define all service interactions

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- API contract tests for workflow and agent endpoints [P]
- Data model implementation tasks for core entities [P]
- LangGraph workflow engine implementation
- Redis state management layer
- Agent registry and communication system
- External service integration clients
- Error handling and fault tolerance mechanisms
- Integration test scenarios from quickstart guide
- Performance and scalability optimizations

**Ordering Strategy**:
- TDD order: Contract tests → Models → Services → Workflows → Integration
- Dependency order: Core libraries → State management → Workflow engine → API layer
- Parallel execution: Independent components marked [P]
- Critical path: Workflow engine → Agent coordination → External integrations

**Key Task Categories**:
1. **Foundation** [P]: Data models, Redis schemas, base classes
2. **Core Services**: Workflow engine, agent registry, state management
3. **Integration**: External service clients, communication protocols  
4. **API Layer**: REST endpoints, WebSocket handlers, authentication
5. **Testing**: Contract tests, integration scenarios, performance tests
6. **Deployment**: Configuration, monitoring, health checks

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md covering complete orchestrator implementation

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
