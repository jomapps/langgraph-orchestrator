# Deployment Configuration

This document provides comprehensive deployment configuration for the LangGraph Orchestrator system across different environments.

## Overview

The deployment setup supports multiple environments:
- **Development**: Local development with Docker Compose
- **Staging**: Pre-production testing environment
- **Production**: High-availability production deployment
- **Kubernetes**: Container orchestration deployment

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Application   │    │   Redis Cluster │
│   (Nginx/HAProxy)│───▶│   (FastAPI)     │───▶│   (High Avail)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Monitoring    │    │   Monitoring    │
│   (Prometheus)  │    │   (Grafana)     │    │   (Alertmanager)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Environment Configurations

### Development Environment

**File**: `docker-compose.yml`

**Characteristics**:
- Single application instance
- Single Redis instance
- Basic monitoring setup
- Local development focus

**Deployment**:
```bash
docker-compose up -d
```

### Staging Environment

**File**: `docker-compose.staging.yml`

**Characteristics**:
- Multiple application instances (2-3)
- Redis with persistence
- Full monitoring stack
- Production-like configuration

**Deployment**:
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production Environment

**File**: `docker-compose.prod.yml`

**Characteristics**:
- Multiple application instances (3+)
- Redis cluster with high availability
- Load balancer configuration
- Comprehensive monitoring
- Security hardening
- Backup and recovery

**Deployment**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Files

### Environment Variables

**Development** (`.env.development`):
```bash
# Application
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=DEBUG
```

**Production** (`.env.production`):
```bash
# Application
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# Redis Cluster
REDIS_HOST=redis-cluster
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-secure-password
REDIS_SENTINEL_HOSTS=redis-sentinel-1:26379,redis-sentinel-2:26379,redis-sentinel-3:26379

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key
API_RATE_LIMIT=100/minute
CORS_ORIGINS=https://yourdomain.com

# Performance
WORKER_PROCESSES=4
MAX_WORKERS=10
QUEUE_TIMEOUT=300
```

### Docker Configuration

**Base Dockerfile**:
```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY monitoring/ ./monitoring/

# Create necessary directories
RUN mkdir -p logs data backups && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "src.main"]
```

### Load Balancer Configuration

**Nginx Configuration** (`nginx/nginx.conf`):
```nginx
upstream langgraph_app {
    least_conn;
    server app1:8000 max_fails=3 fail_timeout=30s;
    server app2:8000 max_fails=3 fail_timeout=30s;
    server app3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.langgraph-orchestrator.com;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://langgraph_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://langgraph_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://langgraph_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Deployment Procedures

### Pre-deployment Checklist

- [ ] Environment variables configured
- [ ] Secrets management setup
- [ ] Database backups verified
- [ ] Monitoring configured
- [ ] Health checks working
- [ ] Load balancer tested
- [ ] SSL certificates installed
- [ ] Security scanning completed
- [ ] Performance testing done
- [ ] Rollback plan prepared

### Deployment Steps

#### 1. Environment Setup
```bash
# Create deployment directory
mkdir -p /opt/langgraph-orchestrator
cd /opt/langgraph-orchestrator

# Copy configuration files
cp docker-compose.prod.yml .
cp .env.production .env

# Set proper permissions
chmod 600 .env
```

#### 2. Database Preparation
```bash
# Backup existing data (if upgrading)
docker-compose exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb ./backups/redis-backup-$(date +%Y%m%d).rdb

# Prepare Redis cluster
docker-compose up -d redis-master redis-slave redis-sentinel
```

#### 3. Application Deployment
```bash
# Pull latest images
docker-compose pull

# Start services in order
docker-compose up -d redis-cluster
docker-compose up -d monitoring-stack
docker-compose up -d app-instances
docker-compose up -d load-balancer
```

#### 4. Health Verification
```bash
# Check service health
curl -f https://api.langgraph-orchestrator.com/health

# Verify monitoring
curl -f https://prometheus.langgraph-orchestrator.com/-/healthy
curl -f https://grafana.langgraph-orchestrator.com/api/health

# Check logs
docker-compose logs -f app1
docker-compose logs -f redis-master
```

### Rollback Procedures

#### Quick Rollback
```bash
# Stop current version
docker-compose down

# Restore previous version
git checkout previous-stable-tag
docker-compose up -d

# Verify rollback
curl -f https://api.langgraph-orchestrator.com/health
```

#### Database Rollback
```bash
# Stop application
docker-compose stop app1 app2 app3

# Restore Redis backup
docker cp ./backups/redis-backup-latest.rdb redis:/data/dump.rdb
docker-compose restart redis

# Restart application
docker-compose start app1 app2 app3
```

## Security Configuration

### Network Security

**Firewall Rules**:
```bash
# Allow HTTPS traffic
ufw allow 443/tcp

# Allow monitoring access (restricted IPs)
ufw allow from 10.0.0.0/8 to any port 9090
ufw allow from 10.0.0.0/8 to any port 3000

# Deny all other traffic
ufw default deny incoming
```

### SSL/TLS Configuration

**Certificate Management**:
```bash
# Generate SSL certificates
sudo certbot certonly --nginx -d api.langgraph-orchestrator.com

# Auto-renewal
sudo crontab -e
# Add: 0 2 * * * certbot renew --quiet
```

### Access Control

**API Authentication**:
```python
# In application code
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if not validate_jwt_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
```

## Monitoring and Alerting

### Health Checks

**Application Health**:
```bash
# Basic health check
curl -f http://localhost:8000/health

# Detailed health check
curl -f http://localhost:8000/health/detailed

# Dependency health check
curl -f http://localhost:8000/health/dependencies
```

### Performance Monitoring

**Key Metrics**:
- Response time: < 500ms (p50), < 2s (p95)
- Error rate: < 1%
- Uptime: > 99.9%
- Throughput: > 1000 req/s

### Alert Configuration

**Critical Alerts**:
- Service down > 1 minute
- Error rate > 10%
- Memory usage > 90%
- CPU usage > 90%

**Warning Alerts**:
- Response time > 2s (p95)
- High number of active workflows
- Redis connection issues
- SSL certificate expiration

## Backup and Recovery

### Automated Backups

**Redis Backup**:
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
docker exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb /backups/redis/redis-backup-$DATE.rdb
find /backups/redis -name "redis-backup-*.rdb" -mtime +7 -delete
```

**Application Data Backup**:
```bash
# Backup application data
tar -czf /backups/app/app-data-$(date +%Y%m%d).tar.gz /app/data/
```

### Recovery Procedures

**Service Recovery**:
```bash
# Restart failed service
docker-compose restart app1

# Scale up if needed
docker-compose up -d --scale app=5

# Emergency restart
docker-compose down && docker-compose up -d
```

**Data Recovery**:
```bash
# Restore Redis data
docker stop redis
docker cp /backups/redis/redis-backup-latest.rdb redis:/data/dump.rmb
docker start redis
```

## Scaling Configuration

### Horizontal Scaling

**Application Scaling**:
```bash
# Scale application instances
docker-compose up -d --scale app=5

# Scale Redis cluster
docker-compose up -d --scale redis-slave=3
```

**Load Balancer Scaling**:
```bash
# Multiple load balancer instances
docker-compose up -d --scale nginx=2
```

### Vertical Scaling

**Resource Limits**:
```yaml
# In docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Troubleshooting

### Common Issues

**Service Won't Start**:
```bash
# Check logs
docker-compose logs app1

# Check resources
docker system df
docker stats

# Check configuration
docker-compose config
```

**High Memory Usage**:
```bash
# Monitor memory usage
docker stats --no-stream

# Check for memory leaks
docker exec app1 python -m memory_profiler
```

**Network Issues**:
```bash
# Check network connectivity
docker network ls
docker network inspect bridge

# Test service connectivity
docker exec app1 curl -f http://redis:6379
```

### Performance Issues

**Slow Response Times**:
```bash
# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/workflows

# Monitor Redis performance
docker exec redis redis-cli INFO stats

# Check database queries
# Enable query logging in application
```

**High CPU Usage**:
```bash
# Monitor CPU usage
docker stats --no-stream

# Profile application
docker exec app1 python -m cProfile -o profile.stats src/main.py
```

## Maintenance

### Regular Maintenance

**Weekly Tasks**:
- Review monitoring dashboards
- Check backup integrity
- Update SSL certificates
- Review security logs

**Monthly Tasks**:
- Performance optimization
- Security updates
- Capacity planning
- Documentation updates

### Update Procedures

**Rolling Updates**:
```bash
# Update with zero downtime
docker-compose up -d --no-deps app1
docker-compose up -d --no-deps app2
docker-compose up -d --no-deps app3
```

**Database Updates**:
```bash
# Backup before updates
docker-compose exec redis redis-cli SAVE

# Apply updates
docker-compose pull redis
docker-compose up -d redis
```

## Support and Documentation

For deployment support:
- **Documentation**: [Deployment Guide](DEPLOYMENT_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: support@langgraph-orchestrator.com
- **Monitoring**: https://grafana.langgraph-orchestrator.com