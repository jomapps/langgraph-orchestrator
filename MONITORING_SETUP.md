# Monitoring and Observability Setup

This document outlines the comprehensive monitoring and observability setup for the LangGraph Orchestrator system.

## Overview

The monitoring stack provides:
- **Metrics Collection**: System and application performance metrics
- **Health Monitoring**: Service health checks and alerting
- **Performance Tracking**: Workflow execution and agent performance
- **Error Tracking**: Error detection and analysis
- **Resource Monitoring**: CPU, memory, disk, and network usage

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Prometheus    │───▶│     Grafana     │
│   (Metrics)     │    │   (Metrics DB)  │    │  (Dashboards)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis         │    │   Alertmanager  │    │   Dashboards    │
│   (Health)      │───▶│   (Alerting)    │    │   (Custom)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Prometheus

Prometheus is the core metrics collection and storage system.

**Configuration**: `monitoring/prometheus.yml`

**Key Metrics Collected**:
- Application metrics (custom)
- System metrics (CPU, memory, disk)
- Redis metrics (connection, memory, commands)
- HTTP request metrics (latency, status codes)
- Workflow execution metrics
- Agent performance metrics

**Access**: http://localhost:9090

### 2. Grafana

Grafana provides visualization and dashboarding for collected metrics.

**Default Credentials**:
- Username: `admin`
- Password: `admin123`

**Access**: http://localhost:3000

**Pre-configured Dashboards**:
- System Overview
- Application Performance
- Workflow Execution
- Agent Performance
- Redis Monitoring
- Error Analysis

### 3. Alertmanager

Alertmanager handles alert routing and notification.

**Configuration**: `monitoring/alertmanager.yml`

**Alert Rules**: `monitoring/rules/*.yml`

## Metrics

### Application Metrics

#### Workflow Metrics
```python
# Workflow creation counter
workflow_created_total{project_id, type, priority}

# Workflow completion counter
workflow_completed_total{project_id, type, status}

# Workflow duration histogram
workflow_duration_seconds{project_id, type}

# Active workflows gauge
workflows_active{project_id, type}

# Workflow errors counter
workflow_errors_total{project_id, type, error_type}
```

#### Agent Metrics
```python
# Agent registration counter
agent_registered_total{category, version}

# Agent task assignment counter
agent_tasks_assigned_total{agent_id, task_type}

# Agent task completion counter
agent_tasks_completed_total{agent_id, status}

# Agent performance histogram
agent_task_duration_seconds{agent_id, task_type}

# Agent health status
agent_health_status{agent_id}

# Agent errors counter
agent_errors_total{agent_id, error_type}
```

#### Task Metrics
```python
# Task creation counter
task_created_total{workflow_id, task_type, priority}

# Task completion counter
task_completed_total{workflow_id, task_type, status}

# Task duration histogram
task_duration_seconds{workflow_id, task_type}

# Task retry counter
task_retries_total{workflow_id, task_type}

# Active tasks gauge
tasks_active{workflow_id, task_type}
```

#### HTTP Metrics
```python
# HTTP request counter
http_requests_total{method, endpoint, status_code}

# HTTP request duration histogram
http_request_duration_seconds{method, endpoint}

# HTTP request size histogram
http_request_size_bytes{method, endpoint}

# HTTP response size histogram
http_response_size_bytes{method, endpoint}
```

#### System Metrics
```python
# Process metrics
process_cpu_seconds_total
process_resident_memory_bytes
process_virtual_memory_bytes
process_open_fds
process_max_fds

# Python-specific metrics
python_info{implementation, version}
python_gc_collections_total{generation}
python_gc_objects_collected_total{generation}
```

### Redis Metrics

#### Connection Metrics
```python
redis_connected_clients
redis_blocked_clients
redis_tracking_clients
```

#### Memory Metrics
```python
redis_memory_used_bytes
redis_memory_peak_bytes
redis_memory_fragmentation_ratio
```

#### Performance Metrics
```python
redis_commands_processed_total
redis_keyspace_hits_total
redis_keyspace_misses_total
redis_expired_keys_total
redis_evicted_keys_total
```

## Dashboards

### 1. System Overview Dashboard

**URL**: http://localhost:3000/d/system-overview

**Panels**:
- CPU Usage
- Memory Usage
- Disk I/O
- Network I/O
- Process Count
- Load Average

### 2. Application Performance Dashboard

**URL**: http://localhost:3000/d/app-performance

**Panels**:
- Request Rate
- Response Time
- Error Rate
- Active Connections
- Memory Usage
- GC Activity

### 3. Workflow Execution Dashboard

**URL**: http://localhost:3000/d/workflow-execution

**Panels**:
- Workflow Creation Rate
- Workflow Completion Rate
- Average Workflow Duration
- Workflow Success Rate
- Active Workflows
- Workflow Errors

### 4. Agent Performance Dashboard

**URL**: http://localhost:3000/d/agent-performance

**Panels**:
- Agent Registration Status
- Task Assignment Rate
- Task Completion Rate
- Average Task Duration
- Agent Health Status
- Agent Errors

### 5. Redis Monitoring Dashboard

**URL**: http://localhost:3000/d/redis-monitoring

**Panels**:
- Connected Clients
- Memory Usage
- Command Rate
- Hit/Miss Ratio
- Expired Keys
- Slow Queries

### 6. Error Analysis Dashboard

**URL**: http://localhost:3000/d/error-analysis

**Panels**:
- Error Rate by Type
- Error Rate by Endpoint
- Error Rate by Agent
- Error Rate by Workflow
- Recent Errors
- Error Trends

## Alerting

### Critical Alerts

#### Service Down
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.instance }} is down"
    description: "Service {{ $labels.instance }} has been down for more than 1 minute"
```

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is above 10% for more than 2 minutes"
```

#### High Memory Usage
```yaml
- alert: HighMemoryUsage
  expr: process_resident_memory_bytes / 1024 / 1024 > 1024
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage"
    description: "Memory usage is above 1GB for more than 5 minutes"
```

#### Workflow Failures
```yaml
- alert: WorkflowFailures
  expr: rate(workflow_completed_total{status="failed"}[5m]) > 0.05
  for: 3m
  labels:
    severity: warning
  annotations:
    summary: "High workflow failure rate"
    description: "Workflow failure rate is above 5% for more than 3 minutes"
```

#### Agent Health Issues
```yaml
- alert: AgentHealthIssues
  expr: agent_health_status != 1
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Agent health issues detected"
    description: "Agent {{ $labels.agent_id }} is reporting health issues"
```

### Warning Alerts

#### High CPU Usage
```yaml
- alert: HighCPUUsage
  expr: rate(process_cpu_seconds_total[5m]) > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage"
    description: "CPU usage is above 80% for more than 5 minutes"
```

#### Slow Response Times
```yaml
- alert: SlowResponseTimes
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Slow response times"
    description: "95th percentile response time is above 2 seconds"
```

#### Redis Connection Issues
```yaml
- alert: RedisConnectionIssues
  expr: redis_connected_clients < 1
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Redis connection issues"
    description: "No active Redis connections detected"
```

## Health Checks

### Application Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "redis": "connected",
    "database": "connected"
  },
  "metrics": {
    "uptime_seconds": 3600,
    "memory_usage_mb": 512,
    "active_workflows": 5,
    "active_agents": 10
  }
}
```

### Redis Health Check

**Command**: `redis-cli ping`

**Expected Response**: `PONG`

### System Health Check

**Metrics Monitored**:
- CPU usage < 80%
- Memory usage < 90%
- Disk space > 10%
- Network connectivity
- Process running status

## Logging

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information about application operation
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical problems that require immediate attention

### Log Format

```json
{
  "timestamp": "2024-01-01T12:00:00.123Z",
  "level": "INFO",
  "logger": "workflow_orchestrator",
  "message": "Workflow started successfully",
  "context": {
    "workflow_id": "workflow-123",
    "project_id": "project-456"
  },
  "metadata": {
    "request_id": "req-789",
    "user_id": "user-123"
  }
}
```

### Log Locations

- **Application logs**: `./logs/app.log`
- **Error logs**: `./logs/error.log`
- **Access logs**: `./logs/access.log`
- **Performance logs**: `./logs/performance.log`

## Performance Monitoring

### Key Performance Indicators (KPIs)

#### System KPIs
- **Uptime**: > 99.9%
- **Response Time**: < 500ms (p50), < 2s (p95)
- **Error Rate**: < 1%
- **Memory Usage**: < 80%
- **CPU Usage**: < 80%

#### Business KPIs
- **Workflow Success Rate**: > 95%
- **Average Workflow Duration**: < 30 minutes
- **Agent Utilization**: > 70%
- **Task Completion Rate**: > 95%
- **User Satisfaction**: > 4.5/5

### Performance Baselines

#### Response Time Baselines
- Health check: < 100ms
- Workflow creation: < 500ms
- Workflow status: < 200ms
- Agent registration: < 300ms
- Task assignment: < 400ms

#### Throughput Baselines
- Workflow creation: > 100/minute
- Task processing: > 1000/minute
- Agent operations: > 500/minute
- HTTP requests: > 10,000/minute

## Troubleshooting

### Common Issues

#### High Memory Usage
1. Check for memory leaks in application code
2. Review Redis memory usage and configuration
3. Analyze object retention patterns
4. Check garbage collection frequency

#### Slow Response Times
1. Check database query performance
2. Review Redis connection pool settings
3. Analyze CPU and memory usage
4. Check network latency

#### High Error Rate
1. Review error logs for patterns
2. Check service dependencies
3. Analyze request payload validation
4. Review rate limiting configuration

#### Workflow Failures
1. Check agent health status
2. Review task error messages
3. Analyze workflow state transitions
4. Check resource availability

### Diagnostic Commands

```bash
# Check service health
curl -f http://localhost:8000/health

# Check Redis connectivity
redis-cli ping

# Check system resources
top -p $(pgrep -f "python src/main.py")

# Check log files
tail -f logs/app.log logs/error.log

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Check Grafana dashboards
curl -s http://admin:admin123@localhost:3000/api/search | jq '.[].title'
```

## Maintenance

### Regular Tasks

#### Daily
- Review critical alerts
- Check system health dashboard
- Verify backup procedures
- Monitor error rates

#### Weekly
- Review performance trends
- Update alert thresholds
- Clean up old logs
- Review capacity planning

#### Monthly
- Update monitoring configurations
- Review and optimize queries
- Update dashboard layouts
- Conduct capacity planning review

### Backup and Recovery

#### Configuration Backup
```bash
# Backup monitoring configurations
cp -r monitoring/ backups/monitoring-$(date +%Y%m%d)

# Backup Grafana dashboards
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/search | jq -r '.[].uri' | \
  xargs -I {} curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -o backups/grafana-$(date +%Y%m%d)/{}.json \
  http://localhost:3000/api/dashboards/{}
```

#### Recovery Procedures
1. Restore configuration files from backup
2. Restart monitoring services
3. Verify data integrity
4. Test alert functionality
5. Validate dashboard functionality

## Integration

### CI/CD Integration

Include monitoring health checks in deployment pipelines:

```yaml
# GitHub Actions example
- name: Health Check
  run: |
    curl -f http://localhost:8000/health
    curl -f http://localhost:9090/-/healthy
    curl -f http://localhost:3000/api/health
```

### External Monitoring

Integrate with external monitoring services:

- **PagerDuty**: For critical alert escalation
- **Slack**: For team notifications
- **DataDog**: For external monitoring
- **New Relic**: For APM integration

## Security

### Access Control
- Use strong passwords for Grafana
- Implement network segmentation
- Use TLS for external access
- Regular security updates

### Data Protection
- Encrypt sensitive metrics
- Implement audit logging
- Regular security assessments
- Compliance monitoring

## Support

For monitoring support:
- **Documentation**: [Monitoring Setup](monitoring/README.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: monitoring@langgraph-orchestrator.com