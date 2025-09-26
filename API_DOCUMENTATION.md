# LangGraph Orchestrator - API Documentation

## Overview

The LangGraph Orchestrator is a comprehensive workflow management system designed for video creation and content optimization. It provides a RESTful API for managing workflows, agents, projects, and tasks with real-time orchestration capabilities.

## Base URLs

**Production**: `https://agents.ft.tc`  
**Local Development**: `http://localhost:8000`  
**API Documentation**: `https://agents.ft.tc/api/docs`

## Authentication

Currently, the API does not require authentication. In production environments, implement appropriate authentication mechanisms.

## Content Type

All requests and responses use `application/json` unless otherwise specified.

## API Endpoints

### Health Check

#### GET /health

Check the health status of the API server and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "redis": "connected",
    "database": "connected"
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

---

### Workflow Management

#### GET /api/v1/workflows

Retrieve all workflows with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by workflow status (`running`, `paused`, `completed`, `failed`, `cancelled`)
- `project_id` (optional): Filter by project ID
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "f156b7e6-770e-4484-a7bc-dbccbac0a252",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "movie_creation",
    "status": "running",
    "state": "concept_development",
    "progress": 0.0,
    "title": "Epic Adventure Movie",
    "description": "",
    "created_at": "2025-09-25T23:58:34.355415",
    "updated_at": "2025-09-25T23:58:34.355415"
  }
]
```

#### GET /workflows/{workflow_id}

Retrieve a specific workflow by ID.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "id": "workflow-123",
  "project_id": "project-456",
  "type": "video_creation",
  "status": "running",
  "state": {
    "current_step": "script_generation",
    "completed_steps": ["research", "outline"],
    "total_steps": 8
  },
  "title": "Product Demo Video",
  "description": "Create a promotional video for new product launch",
  "genre": "promotional",
  "duration": 120,
  "style_preferences": {
    "tone": "professional",
    "visual_style": "modern"
  },
  "priority": "high",
  "progress": 65.5,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:30:00Z",
  "assigned_agents": ["agent-1", "agent-2"]
}
```

#### POST /workflows

Create a new workflow.

**Request Body:**
```json
{
  "project_id": "project-456",
  "type": "video_creation",
  "title": "Product Demo Video",
  "description": "Create a promotional video for new product launch",
  "genre": "promotional",
  "duration": 120,
  "style_preferences": {
    "tone": "professional",
    "visual_style": "modern"
  },
  "priority": "high"
}
```

**Response:**
```json
{
  "id": "workflow-123",
  "status": "pending",
  "message": "Workflow created successfully",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### PUT /workflows/{workflow_id}

Update an existing workflow.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Request Body:**
```json
{
  "title": "Updated Product Demo Video",
  "description": "Updated description",
  "priority": "urgent"
}
```

**Response:**
```json
{
  "id": "workflow-123",
  "message": "Workflow updated successfully",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

#### DELETE /workflows/{workflow_id}

Delete a workflow.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "message": "Workflow deleted successfully"
}
```

#### POST /workflows/{workflow_id}/start

Start a workflow execution.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "message": "Workflow started successfully",
  "status": "running",
  "started_at": "2024-01-01T12:00:00Z"
}
```

#### POST /workflows/{workflow_id}/pause

Pause a running workflow.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "message": "Workflow paused successfully",
  "status": "paused",
  "paused_at": "2024-01-01T12:30:00Z"
}
```

#### POST /workflows/{workflow_id}/resume

Resume a paused workflow.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "message": "Workflow resumed successfully",
  "status": "running",
  "resumed_at": "2024-01-01T12:35:00Z"
}
```

#### POST /workflows/{workflow_id}/cancel

Cancel a workflow execution.

**Path Parameters:**
- `workflow_id` (required): The workflow ID

**Response:**
```json
{
  "message": "Workflow cancelled successfully",
  "status": "cancelled",
  "cancelled_at": "2024-01-01T12:40:00Z"
}
```

---

### Agent Management

#### GET /api/v1/agents

Retrieve all agents with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by agent status (`idle`, `busy`, `unavailable`, `error`)
- `category` (optional): Filter by agent category (`creative`, `analytical`, `technical`, `coordination`, `research`, `content`)
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "test-agent-3c9a38a0-2143-46de-850f-410c0a5820e5",
    "name": "Story Creation Agent",
    "category": "creative",
    "status": "idle",
    "capabilities": [
      "story_creation",
      "character_development"
    ],
    "specializations": [],
    "version": "1.0.0",
    "description": "",
    "performance_score": 0.0,
    "reliability_score": 0.0,
    "max_concurrent_tasks": 1,
    "current_task_count": 0,
    "health_status": {},
    "created_at": "2025-09-25T23:59:19.788949",
    "updated_at": "2025-09-25T23:59:19.788949"
  }
]
```

#### GET /agents/{agent_id}

Retrieve a specific agent by ID.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Response:**
```json
{
  "id": "agent-1",
  "name": "Script Writer",
  "category": "content_creation",
  "status": "available",
  "capabilities": ["script_writing", "content_generation"],
  "specializations": ["promotional_videos", "educational_content"],
  "version": "1.0.0",
  "description": "AI agent specialized in writing video scripts",
  "author": "LangGraph Team",
  "resource_limits": {
    "max_concurrent_tasks": 3,
    "max_memory_mb": 512
  },
  "performance_metrics": {
    "tasks_completed": 150,
    "average_completion_time": 1800,
    "success_rate": 0.95,
    "total_errors": 5,
    "last_error_at": null
  },
  "health_status": "healthy",
  "health_check_interval": 60,
  "created_at": "2024-01-01T08:00:00Z",
  "last_active": "2024-01-01T12:00:00Z",
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

#### POST /agents

Register a new agent.

**Request Body:**
```json
{
  "name": "Video Editor",
  "category": "video_production",
  "capabilities": ["video_editing", "color_grading", "audio_mixing"],
  "specializations": ["promotional_videos", "social_media"],
  "version": "1.0.0",
  "description": "AI agent for video editing and post-production",
  "resource_limits": {
    "max_concurrent_tasks": 2,
    "max_memory_mb": 1024
  }
}
```

**Response:**
```json
{
  "id": "agent-2",
  "message": "Agent registered successfully",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### PUT /agents/{agent_id}

Update an existing agent.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Request Body:**
```json
{
  "description": "Updated description",
  "capabilities": ["video_editing", "color_grading", "audio_mixing", "motion_graphics"]
}
```

**Response:**
```json
{
  "id": "agent-2",
  "message": "Agent updated successfully",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

#### DELETE /agents/{agent_id}

Unregister an agent.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Response:**
```json
{
  "message": "Agent unregistered successfully"
}
```

#### GET /agents/{agent_id}/health

Check agent health status.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Response:**
```json
{
  "agent_id": "agent-1",
  "status": "healthy",
  "last_check": "2024-01-01T12:00:00Z",
  "response_time_ms": 45,
  "memory_usage_mb": 256,
  "cpu_usage_percent": 15.2
}
```

#### POST /agents/{agent_id}/reset

Reset an agent to available state.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Response:**
```json
{
  "message": "Agent reset successfully",
  "status": "available"
}
```

#### GET /agents/{agent_id}/tasks

Get tasks assigned to an agent.

**Path Parameters:**
- `agent_id` (required): The agent ID

**Query Parameters:**
- `status` (optional): Filter by task status
- `limit` (optional): Maximum number of results (default: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "tasks": [
    {
      "id": "task-123",
      "name": "Generate video script",
      "status": "in_progress",
      "priority": "high",
      "created_at": "2024-01-01T11:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

### Project Management

#### GET /projects

Retrieve all projects.

**Query Parameters:**
- `active` (optional): Filter by active status (true/false)
- `limit` (optional): Maximum number of results (default: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "projects": [
    {
      "id": "project-456",
      "name": "Marketing Campaign 2024",
      "description": "Video content for Q1 marketing campaign",
      "type": "marketing",
      "domain": "technology",
      "active": true,
      "created_at": "2024-01-01T08:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### GET /projects/{project_id}

Retrieve a specific project by ID.

**Path Parameters:**
- `project_id` (required): The project ID

**Response:**
```json
{
  "id": "project-456",
  "name": "Marketing Campaign 2024",
  "description": "Video content for Q1 marketing campaign",
  "type": "marketing",
  "domain": "technology",
  "configuration": {
    "default_workflow_type": "video_creation",
    "quality_settings": "high"
  },
  "resource_limits": {
    "max_workflows": 50,
    "max_agents": 20,
    "max_concurrent_tasks": 100
  },
  "active": true,
  "created_at": "2024-01-01T08:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### POST /projects

Create a new project.

**Request Body:**
```json
{
  "name": "Educational Series",
  "description": "Educational video series for online learning",
  "type": "education",
  "domain": "academic",
  "configuration": {
    "default_workflow_type": "video_creation",
    "quality_settings": "high"
  },
  "resource_limits": {
    "max_workflows": 30,
    "max_agents": 15,
    "max_concurrent_tasks": 50
  }
}
```

**Response:**
```json
{
  "id": "project-789",
  "message": "Project created successfully",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### PUT /projects/{project_id}

Update an existing project.

**Path Parameters:**
- `project_id` (required): The project ID

**Request Body:**
```json
{
  "name": "Updated Marketing Campaign",
  "description": "Updated description",
  "resource_limits": {
    "max_workflows": 60
  }
}
```

**Response:**
```json
{
  "id": "project-789",
  "message": "Project updated successfully",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

#### DELETE /projects/{project_id}

Delete a project.

**Path Parameters:**
- `project_id` (required): The project ID

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

#### GET /projects/{project_id}/workflows

Get workflows associated with a project.

**Path Parameters:**
- `project_id` (required): The project ID

**Query Parameters:**
- `status` (optional): Filter by workflow status
- `limit` (optional): Maximum number of results (default: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "workflows": [
    {
      "id": "workflow-123",
      "status": "running",
      "title": "Product Demo Video",
      "progress": 65.5,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Workflow not found",
    "details": {
      "workflow_id": "workflow-123"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `RESOURCE_NOT_FOUND` | Requested resource not found | 404 |
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `CONFLICT` | Resource conflict | 409 |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard endpoints**: 100 requests per minute per IP
- **Workflow operations**: 50 requests per minute per IP
- **Bulk operations**: 20 requests per minute per IP

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1640995200
```

---

## WebSocket Support

Real-time updates are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('Workflow update:', update);
};
```

WebSocket events include:
- `workflow.status_changed`
- `workflow.progress_updated`
- `agent.status_changed`
- `task.completed`

---

## SDK and Examples

### Python SDK Example

```python
import requests
import json

# Initialize client
base_url = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# Create a workflow
workflow_data = {
    "project_id": "project-456",
    "type": "video_creation",
    "title": "Product Demo Video",
    "description": "Create a promotional video",
    "genre": "promotional",
    "duration": 120,
    "priority": "high"
}

response = requests.post(
    f"{base_url}/workflows",
    headers=headers,
    data=json.dumps(workflow_data)
)

workflow = response.json()
print(f"Created workflow: {workflow['id']}")

# Start the workflow
response = requests.post(f"{base_url}/workflows/{workflow['id']}/start")
print(f"Workflow started: {response.json()['message']}")

# Monitor progress
response = requests.get(f"{base_url}/workflows/{workflow['id']}")
workflow_status = response.json()
print(f"Progress: {workflow_status['progress']}%")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const client = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json'
    }
});

// Create and start workflow
async function createAndStartWorkflow() {
    try {
        // Create workflow
        const workflowResponse = await client.post('/workflows', {
            project_id: 'project-456',
            type: 'video_creation',
            title: 'Product Demo Video',
            description: 'Create a promotional video',
            genre: 'promotional',
            duration: 120,
            priority: 'high'
        });

        const workflow = workflowResponse.data;
        console.log('Created workflow:', workflow.id);

        // Start workflow
        const startResponse = await client.post(`/workflows/${workflow.id}/start`);
        console.log('Workflow started:', startResponse.data.message);

        // Monitor progress
        const statusResponse = await client.get(`/workflows/${workflow.id}`);
        console.log('Progress:', statusResponse.data.progress + '%');

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

createAndStartWorkflow();
```

---

## Best Practices

### 1. Error Handling
Always implement proper error handling and retry logic:

```python
def create_workflow_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{base_url}/workflows", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Pagination
Use pagination for large result sets:

```python
def get_all_workflows(page_size=100):
    workflows = []
    offset = 0
    
    while True:
        response = requests.get(
            f"{base_url}/workflows",
            params={'limit': page_size, 'offset': offset}
        )
        data = response.json()
        workflows.extend(data['workflows'])
        
        if len(data['workflows']) < page_size:
            break
        offset += page_size
    
    return workflows
```

### 3. WebSocket Reconnection
Implement automatic reconnection for WebSocket connections:

```javascript
function connectWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onclose = function() {
        console.log('WebSocket closed, reconnecting in 5 seconds...');
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    return ws;
}

const ws = connectWebSocket();
```

### 4. Rate Limiting
Respect rate limits and implement backoff strategies:

```python
def make_request_with_rate_limiting(url, method='GET', **kwargs):
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 429:  # Rate limit exceeded
            retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
            print(f"Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        response.raise_for_status()
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API release
- Basic workflow management
- Agent registration and management
- Project management
- Health monitoring
- WebSocket support

### Planned Features
- Advanced workflow templates
- Multi-language support
- Enhanced monitoring and analytics
- Machine learning integration
- Advanced error recovery

---

## Support

For API support and questions:
- **Documentation**: [API Documentation](README.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: support@langgraph-orchestrator.com