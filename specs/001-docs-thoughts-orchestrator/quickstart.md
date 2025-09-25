# Quickstart: LangGraph Agent Orchestrator Service

## Overview
This guide walks through setting up and running your first movie production workflow using the LangGraph Agent Orchestrator Service.

## Prerequisites
- Python 3.11+
- Redis server
- Docker (optional, for containerized agents)
- Access to external services (Auto-Movie App, Brain Service, Task Service)

## Quick Setup

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd langgraph-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_URL="redis://localhost:6379"
export AUTO_MOVIE_API_URL="https://auto-movie.ft.tc/api"
export BRAIN_SERVICE_URL="wss://brain.ft.tc/mcp"
export TASK_SERVICE_URL="https://tasks.ft.tc/api"
export API_KEY="your-api-key-here"
```

### 2. Start Redis
```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:latest

# Or install locally (Ubuntu/Debian)
sudo apt update && sudo apt install redis-server
sudo systemctl start redis
```

### 3. Start the Orchestrator Service
```bash
# Development mode
python -m src.main --dev

# Or using uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Basic Usage

### Create Your First Movie Project
```bash
# Create a project via Auto-Movie App API
curl -X POST https://auto-movie.ft.tc/api/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "title": "My First AI Movie",
    "description": "A sci-fi adventure about AI consciousness",
    "genre": "science_fiction",
    "target_duration": 600,
    "style_preferences": {
      "visual_style": "cyberpunk",
      "tone": "dramatic"
    },
    "characters": [
      {
        "name": "Alex",
        "description": "A curious AI researcher"
      },
      {
        "name": "ARIA",
        "description": "An emerging AI consciousness"
      }
    ]
  }'
```

### Start a Movie Production Workflow
```bash
# Start a complete movie creation workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "project_id": "project-123",
    "workflow_type": "movie_creation",
    "priority": 5
  }'

# Response:
# {
#   "workflow_id": "wf-uuid-123",
#   "status": "running",
#   "current_state": "concept_development",
#   "estimated_completion": "2025-09-25T14:30:00Z"
# }
```

### Monitor Workflow Progress
```bash
# Check workflow status
curl http://localhost:8000/api/v1/workflows/wf-uuid-123 \
  -H "X-API-Key: your-api-key"

# List all workflows
curl http://localhost:8000/api/v1/workflows \
  -H "X-API-Key: your-api-key"

# Get real-time updates via WebSocket
wscat -c ws://localhost:8000/ws/workflows/wf-uuid-123
```

### Handle User Decisions
```bash
# When workflow pauses for user input, submit decision
curl -X POST http://localhost:8000/api/v1/workflows/wf-uuid-123/decisions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "decision_id": "story_approval_001",
    "choice": "approved",
    "feedback": "Great concept, proceed with character development"
  }'
```

## Agent Management

### Register a New Agent
```bash
# Register a story architect agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "agent_id": "story-architect-01",
    "agent_type": "story",
    "capabilities": ["story_architecture", "plot_development", "narrative_structure"],
    "endpoint_url": "http://story-agent:8001",
    "health_check_url": "http://story-agent:8001/health",
    "resource_requirements": {
      "cpu_cores": 2,
      "memory_gb": 4,
      "gpu_memory_gb": 0,
      "storage_gb": 1
    },
    "max_concurrent_tasks": 3,
    "version": "1.0.0"
  }'
```

### Check Agent Status
```bash
# List all agents
curl http://localhost:8000/api/v1/agents \
  -H "X-API-Key: your-api-key"

# Get specific agent details
curl http://localhost:8000/api/v1/agents/story-architect-01 \
  -H "X-API-Key: your-api-key"

# Check agent health
curl http://localhost:8000/api/v1/agents/story-architect-01/health \
  -H "X-API-Key: your-api-key"
```

## Workflow Control

### Pause and Resume Workflows
```bash
# Pause a running workflow
curl -X PUT http://localhost:8000/api/v1/workflows/wf-uuid-123/pause \
  -H "X-API-Key: your-api-key"

# Resume a paused workflow
curl -X PUT http://localhost:8000/api/v1/workflows/wf-uuid-123/resume \
  -H "X-API-Key: your-api-key"

# Cancel a workflow
curl -X DELETE http://localhost:8000/api/v1/workflows/wf-uuid-123 \
  -H "X-API-Key: your-api-key"
```

## Testing the Integration

### Validate Workflow Execution
1. **Start a simple workflow** and verify it progresses through states
2. **Check agent assignments** to ensure proper routing
3. **Test error recovery** by simulating agent failures
4. **Verify external integrations** with Auto-Movie, Brain, and Task services
5. **Test user decision points** with different choices

### Test Scenarios

#### Scenario 1: Complete Movie Creation
```bash
# This should take the workflow through all states:
# concept_development → character_creation → scene_planning → 
# media_generation → post_production → final_assembly

# Monitor each state transition
watch -n 5 'curl -s http://localhost:8000/api/v1/workflows/wf-uuid-123 | jq .current_state'
```

#### Scenario 2: Error Recovery
```bash
# Simulate agent failure by stopping an agent
docker stop story-agent-container

# Verify workflow automatically retries and recovers
curl http://localhost:8000/api/v1/workflows/wf-uuid-123 | jq .error_details

# Restart agent and verify recovery
docker start story-agent-container
```

#### Scenario 3: Concurrent Workflows
```bash
# Start multiple workflows simultaneously
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/workflows \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-api-key" \
    -d "{\"project_id\": \"project-$i\", \"workflow_type\": \"movie_creation\"}" &
done

# Monitor resource usage and scheduling
curl http://localhost:8000/api/v1/agents | jq '[.agents[] | {agent_id, status, current_tasks}]'
```

## Expected Results

### Successful Workflow Completion
After running through the quickstart, you should see:

1. **Workflow Creation**: Successfully created workflow with unique ID
2. **State Progression**: Workflow advances through all production states
3. **Agent Coordination**: Multiple agents work on different aspects simultaneously
4. **External Integration**: Successful calls to Auto-Movie, Brain, and Task services
5. **Final Output**: Complete movie production with all deliverables

### Performance Metrics
- **Workflow Creation Time**: < 1 second
- **State Transition Time**: < 30 seconds per state
- **Complete Movie Production**: < 2 hours for standard project
- **Agent Response Time**: < 5 seconds average
- **API Response Time**: < 200ms for status queries

### Key Indicators of Success
- [ ] Workflow starts and progresses through all states
- [ ] Agents are properly assigned and execute tasks
- [ ] External services integrate successfully
- [ ] User decision points function correctly
- [ ] Error recovery mechanisms activate when needed
- [ ] Final deliverables are produced and accessible
- [ ] Performance meets expected benchmarks

## Troubleshooting

### Common Issues
1. **Redis Connection Error**: Verify Redis is running and accessible
2. **Agent Registration Failed**: Check agent endpoint URLs and health
3. **Workflow Stuck**: Verify all dependencies are available
4. **External Service Error**: Check API keys and service endpoints
5. **Resource Exhaustion**: Monitor CPU/memory usage of agents

### Debug Commands
```bash
# Check orchestrator logs
tail -f logs/orchestrator.log

# Monitor Redis activity
redis-cli monitor

# Health check all services
curl http://localhost:8000/health

# Get detailed workflow execution trace
curl http://localhost:8000/api/v1/workflows/wf-uuid-123?include_trace=true
```

## Next Steps
1. **Explore Advanced Features**: Conditional workflows, parallel execution, custom agents
2. **Performance Tuning**: Optimize for your specific workload and infrastructure
3. **Monitoring Setup**: Implement comprehensive observability and alerting
4. **Production Deployment**: Scale to production with load balancing and high availability
5. **Custom Integrations**: Add new external services and specialized agents