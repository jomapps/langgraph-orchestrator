# Monitoring Configuration

This directory contains all monitoring and observability configurations for the LangGraph Orchestrator system.

## Directory Structure

```
monitoring/
├── prometheus.yml          # Prometheus server configuration
├── alertmanager.yml        # Alertmanager configuration
├── rules/                  # Alert rules
│   ├── system.yml         # System-level alerts
│   ├── application.yml    # Application-specific alerts
│   └── redis.yml          # Redis-specific alerts
├── dashboards/            # Grafana dashboard JSON files
│   ├── system-overview.json
│   ├── application-performance.json
│   ├── workflow-execution.json
│   ├── agent-performance.json
│   ├── redis-monitoring.json
│   └── error-analysis.json
└── exporters/             # Custom metric exporters
    └── app_exporter.py
```

## Configuration Files

### prometheus.yml
Main Prometheus configuration file that defines:
- Global settings (scrape intervals, timeouts)
- Alertmanager integration
- Scrape configurations for all services
- Rule file locations

### alertmanager.yml
Alertmanager configuration for:
- Alert routing and grouping
- Notification channels (email, Slack, PagerDuty)
- Alert inhibition rules
- Receiver configurations

### rules/
Alert rule definitions organized by category:
- **system.yml**: Infrastructure and system alerts
- **application.yml**: Application-specific alerts
- **redis.yml**: Redis database alerts

### dashboards/
Grafana dashboard configurations in JSON format:
- Pre-configured panels and queries
- Custom visualizations
- Drill-down capabilities

### exporters/
Custom metric exporters for application-specific metrics:
- Application business metrics
- Custom instrumentation
- Integration with monitoring stack

## Setup Instructions

### 1. Start Monitoring Stack

Using Docker Compose:
```bash
docker-compose up -d prometheus grafana
```

### 2. Access Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

### 3. Import Dashboards

1. Navigate to Grafana (http://localhost:3000)
2. Login with admin/admin123
3. Go to Dashboards → Import
4. Upload JSON files from `dashboards/` directory
5. Select Prometheus as data source

### 4. Configure Alerts

1. Edit `alertmanager.yml` with your notification settings
2. Restart Alertmanager container
3. Test alerts by triggering conditions

## Custom Metrics

### Adding Application Metrics

Add custom metrics to your application:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
workflow_created = Counter('workflow_created_total', 'Total workflows created')
workflow_duration = Histogram('workflow_duration_seconds', 'Workflow execution duration')
active_workflows = Gauge('active_workflows', 'Number of active workflows')

# Use metrics
workflow_created.inc()
workflow_duration.observe(duration)
active_workflows.set(count)
```

### Creating Custom Dashboards

1. Create new dashboard in Grafana
2. Add panels with PromQL queries
3. Configure visualization options
4. Save dashboard JSON to `dashboards/` directory

## Troubleshooting

### Prometheus Issues

**Problem**: Prometheus not scraping targets
**Solution**: 
1. Check target status: http://localhost:9090/targets
2. Verify network connectivity
3. Check scrape configuration
4. Review Prometheus logs

**Problem**: Metrics not appearing
**Solution**:
1. Verify metric names in queries
2. Check data retention settings
3. Review metric exporters
4. Test with curl commands

### Grafana Issues

**Problem**: Dashboards not loading
**Solution**:
1. Check data source connectivity
2. Verify dashboard JSON format
3. Review panel queries
4. Check Grafana logs

**Problem**: Alerts not firing
**Solution**:
1. Check alert rule syntax
2. Verify alertmanager configuration
3. Test alert conditions
4. Review notification channels

### Alert Issues

**Problem**: Alerts not sending notifications
**Solution**:
1. Check alertmanager logs
2. Verify receiver configurations
3. Test notification channels
4. Review alert routing rules

## Best Practices

### 1. Metric Naming
- Use consistent naming conventions
- Include units in metric names
- Use labels for dimensions
- Keep names descriptive but concise

### 2. Alert Design
- Set appropriate thresholds
- Include runbook URLs
- Use meaningful alert names
- Avoid alert fatigue

### 3. Dashboard Design
- Focus on key metrics
- Use appropriate visualizations
- Include context and explanations
- Design for different user roles

### 4. Performance
- Limit high-cardinality metrics
- Use recording rules for complex queries
- Optimize query performance
- Monitor monitoring system itself

## Maintenance

### Regular Tasks

#### Daily
- Review critical alerts
- Check system health dashboards
- Verify data collection

#### Weekly
- Review alert effectiveness
- Update thresholds if needed
- Clean up old dashboards

#### Monthly
- Review metric retention
- Update monitoring configurations
- Conduct capacity planning

### Backup Procedures

#### Configuration Backup
```bash
# Backup all configurations
cp -r monitoring/ backups/monitoring-$(date +%Y%m%d)

# Backup Prometheus data (if needed)
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-data-$(date +%Y%m%d).tar.gz /data
```

#### Dashboard Backup
```bash
# Export Grafana dashboards
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/search | jq -r '.[].uri' | \
  xargs -I {} curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -o backups/grafana-$(date +%Y%m%d)/{}.json \
  http://localhost:3000/api/dashboards/{}
```

## Integration

### CI/CD Integration

Include monitoring health checks in deployment:
```yaml
# In your CI/CD pipeline
- name: Verify Monitoring
  run: |
    curl -f http://localhost:9090/-/healthy
    curl -f http://localhost:3000/api/health
    curl -f http://localhost:8000/health
```

### External Services

Integrate with external monitoring:
- **PagerDuty**: For critical alert escalation
- **Slack**: For team notifications
- **DataDog**: For external monitoring
- **New Relic**: For APM integration

## Security Considerations

### Access Control
- Use strong passwords for all services
- Implement network segmentation
- Enable TLS for external access
- Regular security updates

### Data Protection
- Encrypt sensitive metrics
- Implement audit logging
- Regular security assessments
- Compliance monitoring

## Support

For monitoring support:
- **Documentation**: See main monitoring documentation
- **Issues**: Create GitHub issues for problems
- **Configuration**: Review configuration files
- **Logs**: Check service logs for errors