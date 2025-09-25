# LangGraph Orchestrator - Comprehensive Test Suite

This document provides comprehensive information about the test suite for the LangGraph Orchestrator project, including test categories, execution strategies, and best practices.

## Test Suite Overview

The test suite is organized into five distinct categories, each serving a specific purpose in ensuring the reliability and performance of the LangGraph Orchestrator system.

### Test Categories

#### 1. Contract Tests (`tests/contract/`)
**Purpose**: Verify API contracts and endpoint behavior
**Scope**: 
- API endpoint validation (request/response formats)
- HTTP status codes and error handling
- Input validation and sanitization
- API versioning compatibility

**Key Test Files**:
- `test_workflows_crud.py` - Workflow CRUD operations
- `test_workflows_put_delete.py` - Workflow update/delete operations
- `test_workflows_control.py` - Workflow control endpoints (pause/resume/cancel)
- `test_agents_get_register.py` - Agent registration and retrieval
- `test_agents_update_deregister.py` - Agent update and deregistration
- `test_agents_health_reset_tasks.py` - Agent health and task management

**Execution Strategy**: Sequential execution to avoid API conflicts
**Dependencies**: Running API server

#### 2. Integration Tests (`tests/integration/`)
**Purpose**: Test system integration and end-to-end workflows
**Scope**:
- Complete workflow orchestration scenarios
- Agent coordination and task assignment
- Redis state management integration
- Error handling and recovery mechanisms

**Key Test Files**:
- `test_integration.py` - Comprehensive integration scenarios

**Execution Strategy**: Sequential execution to maintain test isolation
**Dependencies**: Redis server, API server

#### 3. Performance Tests (`tests/performance/`)
**Purpose**: Validate system performance under load
**Scope**:
- Concurrent workflow execution
- Large dataset handling
- Response time validation
- Resource usage monitoring

**Key Test Files**:
- `test_performance.py` - Performance benchmarks and load tests

**Execution Strategy**: Sequential execution to avoid resource conflicts
**Dependencies**: Redis server, API server

#### 4. Unit Tests (`tests/unit/`)
**Purpose**: Test individual components in isolation
**Scope**:
- Data model validation
- Service layer functionality
- Business logic correctness
- Utility function behavior

**Key Test Files**:
- `test_unit.py` - Comprehensive unit test suite

**Execution Strategy**: Parallel execution supported
**Dependencies**: None (mocked dependencies)

#### 5. Redis Tests (`tests/redis/`)
**Purpose**: Test Redis-specific functionality
**Scope**:
- Connection management
- Data persistence and retrieval
- Distributed locking mechanisms
- Cleanup operations

**Key Test Files**:
- `test_redis.py` - Redis functionality tests

**Execution Strategy**: Sequential execution to avoid data conflicts
**Dependencies**: Redis server

## Test Execution

### Using the Test Runner

The project includes a comprehensive test runner (`test_runner.py`) that provides a unified interface for executing all test categories.

#### Basic Usage

```bash
# Run all tests
python test_runner.py

# Run specific categories
python test_runner.py --categories unit contract integration

# Run with coverage reporting
python test_runner.py --coverage

# Run with parallel execution (for supported categories)
python test_runner.py --parallel

# Quick test run (skip performance tests)
python test_runner.py --categories unit contract integration
```

#### Advanced Options

```bash
# Skip dependency checks
python test_runner.py --no-deps-check

# Skip Redis connection check
python test_runner.py --no-redis-check

# Custom project root
python test_runner.py --project-root /path/to/project

# Combine multiple options
python test_runner.py --categories unit integration --coverage --parallel
```

### Direct pytest Execution

You can also run tests directly using pytest:

```bash
# Run all tests
pytest

# Run specific categories
pytest -m contract
pytest -m integration
pytest -m performance
pytest -m unit
pytest -m redis

# Run specific test files
pytest tests/contract/test_workflows_crud.py
pytest tests/integration/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run with verbose output
pytest -v

# Run with specific markers
pytest -m "not performance"  # Skip performance tests
pytest -m "contract or integration"  # Run contract and integration tests
```

## Test Configuration

### pytest Configuration

The project uses `pytest.ini` for configuration:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    contract: API contract tests
    integration: Integration tests
    performance: Performance tests
    unit: Unit tests
    redis: Redis-specific tests
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### Environment Variables

Key environment variables for testing:

```bash
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API server configuration
API_HOST=localhost
API_PORT=8000

# Test configuration
TEST_TIMEOUT=300
TEST_PARALLEL_WORKERS=4
```

## Test Data and Fixtures

### Test Fixtures (`tests/conftest.py`)

The test suite includes comprehensive fixtures for:

#### Core Fixtures
- `event_loop`: Async event loop for tests
- `redis_client`: Redis client instance
- `api_client`: HTTP client for API tests
- `cleanup_redis_data`: Redis data cleanup

#### ID Generation Fixtures
- `project_id`: Unique project identifier
- `workflow_id`: Unique workflow identifier
- `agent_id`: Unique agent identifier
- `task_id`: Unique task identifier

#### Sample Data Fixtures
- `project`: Sample project data
- `workflow`: Sample workflow data
- `agent`: Sample agent data
- `task`: Sample task data

#### Model Fixtures
- `sample_project_data`: Project model data
- `sample_workflow_data`: Workflow model data
- `sample_agent_data`: Agent model data
- `sample_task_data`: Task model data

### Test Data Management

Tests use isolated data to prevent conflicts:
- Unique IDs generated for each test run
- Automatic cleanup after test completion
- Isolated test environments
- Mock data for unit tests

## Best Practices

### Test Writing Guidelines

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Clarity**: Test names should clearly indicate what is being tested
3. **Simplicity**: Tests should be simple and focused on a single behavior
4. **Reliability**: Tests should be deterministic and not flaky
5. **Performance**: Tests should execute quickly and not have unnecessary delays

### Test Organization

1. **Categorization**: Place tests in appropriate category directories
2. **Naming**: Use descriptive test function names
3. **Documentation**: Include docstrings explaining test purpose
4. **Fixtures**: Use fixtures for common setup and teardown
5. **Markers**: Use appropriate markers for test categorization

### Error Handling

1. **Expected Errors**: Test both success and failure scenarios
2. **Error Messages**: Verify error messages are informative
3. **Edge Cases**: Test boundary conditions and edge cases
4. **Recovery**: Test error recovery mechanisms

## Continuous Integration

### Pre-commit Checks

Run these commands before committing:

```bash
# Run unit tests (fast feedback)
python test_runner.py --categories unit

# Run contract tests (API validation)
python test_runner.py --categories contract

# Run integration tests (system validation)
python test_runner.py --categories integration

# Full test suite (comprehensive validation)
python test_runner.py --coverage
```

### CI/CD Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions configuration
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start Redis
        run: redis-server --daemonize yes
      - name: Run tests
        run: python test_runner.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

#### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Start Redis server
redis-server --daemonize yes

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

#### API Server Issues
```bash
# Start API server
python src/main.py

# Check server logs
tail -f logs/api.log

# Test API health
curl http://localhost:8000/health
```

#### Test Execution Issues
```bash
# Check Python environment
python --version
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear pytest cache
pytest --cache-clear
```

### Performance Optimization

1. **Parallel Execution**: Use `--parallel` flag for unit tests
2. **Selective Testing**: Run only relevant test categories during development
3. **Mock External Services**: Use mocks for external dependencies
4. **Optimize Test Data**: Minimize test data size and complexity
5. **Use Fixtures**: Leverage fixtures for expensive setup operations

## Test Coverage

### Coverage Goals

- **Unit Tests**: >90% code coverage
- **Integration Tests**: >80% functional coverage
- **Contract Tests**: 100% API endpoint coverage
- **Performance Tests**: Critical path coverage

### Coverage Analysis

```bash
# Generate coverage report
python test_runner.py --coverage

# View HTML coverage report
open coverage/unit/index.html

# Check specific module coverage
pytest --cov=src.models --cov-report=term-missing
```

## Test Maintenance

### Regular Tasks

1. **Update Tests**: Keep tests in sync with code changes
2. **Remove Flaky Tests**: Fix or remove unreliable tests
3. **Optimize Performance**: Improve slow test execution
4. **Add New Tests**: Cover new features and edge cases
5. **Review Coverage**: Ensure adequate test coverage

### Test Review Process

1. **Code Review**: Include tests in code review process
2. **Test Review**: Regular review of test quality and effectiveness
3. **Metrics Monitoring**: Track test execution time and success rates
4. **Feedback Integration**: Incorporate feedback from test failures

## Conclusion

This comprehensive test suite ensures the reliability, performance, and maintainability of the LangGraph Orchestrator system. Regular execution of all test categories, combined with proper test maintenance and continuous improvement, provides confidence in the system's behavior and helps catch issues early in the development process.

For questions or issues with the test suite, please refer to the project's issue tracker or contact the development team.