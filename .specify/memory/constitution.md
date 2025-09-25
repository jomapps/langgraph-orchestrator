<!--
Sync Impact Report:
Version change: 1.0.0 (initial constitution)
Modified principles: None (initial creation)
Added sections: Core Principles (5), Performance Standards, Service Integration, Governance
Removed sections: None (from template)
Templates requiring updates: All templates reference constitution checks - validated
Follow-up TODOs: None
-->

# LangGraph Agent Orchestrator Constitution

## Core Principles

### I. Library-First Architecture
Every core capability MUST be implemented as a standalone, reusable library before integration. Libraries MUST be self-contained, independently testable, and documented with clear purpose. Orchestration logic, state management, and agent communication patterns are implemented as modular libraries under `src/lib/` and `src/services/`. No organizational-only libraries without functional purpose are permitted.

### II. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory: Contract tests written → Integration tests written → Tests MUST fail → Then implement. Red-Green-Refactor cycle is strictly enforced. All API endpoints require contract tests before implementation. All workflow scenarios require integration tests before orchestration logic. Test coverage MUST exceed 90% for core orchestration components.

### III. Service Boundary Isolation
Clean separation MUST be maintained between orchestrator, agents, and external services. All inter-service communication occurs through well-defined contracts (OpenAPI specs). Direct service-to-service coupling is forbidden - all communication flows through the orchestrator hub. External service integrations MUST implement circuit breaker patterns for fault tolerance.

### IV. Observability and Monitoring
Structured JSON logging is required for all components. Every workflow execution MUST have correlation IDs for distributed tracing. Real-time metrics collection is mandatory for workflow progress, agent performance, and system health. Performance targets (100+ concurrent workflows, <2hr production time, 99.9% completion rate) MUST be continuously monitored and validated.

### V. State Management Consistency
Workflow state MUST persist across service restarts using Redis with structured schemas. State transitions MUST be atomic and logged to Redis Streams for auditability. Concurrent workflow execution MUST NOT interfere with each other's state. All state mutations MUST be validated against defined state machine rules before persistence.

## Performance Standards

All implementations MUST meet these non-negotiable performance requirements:
- Support 100+ concurrent movie production workflows
- Process 1000+ agent task executions per minute  
- Respond to workflow status queries in <1 second
- Complete full movie production in <2 hours
- Maintain 99.9% workflow completion rate
- Provide real-time progress updates with <5 second latency

Performance regression testing is required for all core path changes.

## Service Integration Requirements

External service integration MUST follow these patterns:
- Auto-Movie App: REST API with retry logic and timeout handling
- Brain Service: WebSocket MCP protocol with connection pooling
- Task Service: HTTP with async polling and circuit breakers
- All external calls MUST implement exponential backoff with jitter
- Service health checks MUST be automated and continuous
- Failed service calls MUST degrade gracefully without blocking workflows

## Governance

This constitution supersedes all other development practices and coding standards. All pull requests MUST include constitutional compliance verification in the review checklist. Architectural decisions that violate principles MUST be documented in the Complexity Tracking section with explicit justification for why simpler alternatives are insufficient.

Constitution amendments require:
1. Documentation of rationale and impact analysis
2. Approval from system architects
3. Migration plan for existing code
4. Update to all dependent templates and documentation

All constitution checks in planning documents MUST validate against current version. Use CLAUDE.md and other agent guidance files for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-09-25