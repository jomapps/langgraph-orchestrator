# 🚀 Coolify Deployment Guide - LangGraph Orchestrator

## Overview
This guide provides step-by-step instructions to deploy the LangGraph Orchestrator service on a Coolify server with production-grade configuration.

## Prerequisites
- ✅ Coolify server running (v4.0+ recommended)
- ✅ Domain/subdomain ready (e.g., `orchestrator.yourdomain.com`)
- ✅ Git repository accessible to Coolify
- ✅ SSL certificate (handled automatically by Coolify)

---

## Step 1: Repository Preparation

### 1.1 Commit Current Changes
```bash
git add .
git commit -m "Add Coolify deployment configuration"
git push origin main
```

### 1.2 Verify Required Files
Ensure these files exist in your repository:
- ✅ `Dockerfile` (optimized for production)
- ✅ `.coolify.yml` (Coolify-specific config)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `src/` directory with application code

---

## Step 2: Coolify Project Setup

### 2.1 Create New Project
1. Login to your Coolify dashboard
2. Click **"New Project"**
3. Enter project details:
   - **Name**: `langgraph-orchestrator`
   - **Description**: `AI Agent Orchestrator for Movie Production`

### 2.2 Add Application Service
1. In your project, click **"New Resource"**
2. Select **"Docker Compose"**
3. Configure source:
   - **Git Repository**: `https://github.com/yourusername/langgraph-orchestrator.git`
   - **Branch**: `main`
   - **Build Pack**: `Docker Compose`
   - **Docker Compose File**: `.coolify.yml`

---

## Step 3: Environment Configuration

### 3.1 Required Environment Variables
Add these in Coolify's Environment Variables section:

#### **Security & Core**
```env
SECRET_KEY=your-super-secure-secret-key-change-this
API_KEY=your-api-key-for-external-services
ENVIRONMENT=production
DEBUG=false
```

#### **Redis Configuration**
```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional-redis-password
```

#### **API Configuration**
```env
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=https://orchestrator.yourdomain.com
LOG_LEVEL=WARNING
```

#### **Performance & Scaling**
```env
MAX_WORKFLOWS=500
MAX_AGENTS=100
WORKER_PROCESSES=4
MAX_CONCURRENT_TASKS_PER_AGENT=5
DEFAULT_TIMEOUT_HOURS=4
```

#### **External Service URLs**
```env
AUTO_MOVIE_BASE_URL=https://auto-movie.ft.tc
BRAIN_SERVICE_BASE_URL=https://brain.ft.tc
TASK_SERVICE_BASE_URL=https://tasks.ft.tc
SERVICE_TIMEOUT_SECONDS=60
```

#### **Monitoring & Logging**
```env
LOG_FORMAT=json
ENABLE_STRUCTURED_LOGGING=true
ENABLE_PERFORMANCE_LOGGING=true
PROMETHEUS_ENABLED=true
```

### 3.2 Generate Secure Keys
```bash
# Generate SECRET_KEY (run locally)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API_KEY
python -c "import uuid; print(str(uuid.uuid4()))"
```

---

## Step 4: Domain & SSL Configuration

### 4.1 Domain Setup
1. In Coolify, go to your application
2. Click **"Domains"**
3. Add your domain: `orchestrator.yourdomain.com`
4. Enable **"Generate SSL Certificate"**

### 4.2 DNS Configuration
Point your domain to Coolify server:
```dns
Type: A
Name: orchestrator
Value: YOUR_COOLIFY_SERVER_IP
TTL: 300
```

---

## Step 5: Deployment Process

### 5.1 Deploy Services
1. Click **"Deploy"** in Coolify dashboard
2. Monitor deployment logs
3. Wait for both services to be healthy:
   - ✅ `redis` service
   - ✅ `app` service

### 5.2 Verify Deployment
Check these endpoints:

#### **Health Check**
```bash
curl https://orchestrator.yourdomain.com/health
```
Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "redis": "connected"
  }
}
```

#### **API Documentation**
Visit: `https://orchestrator.yourdomain.com/api/docs`

---

## Step 6: Production Optimization

### 6.1 Resource Limits (Optional)
In Coolify, set resource limits:
```yaml
resources:
  limits:
    memory: 2G
    cpus: "1.0"
  reservations:
    memory: 1G
    cpus: "0.5"
```

### 6.2 Scaling Configuration
```yaml
deploy:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 10s
  restart_policy:
    condition: on-failure
    max_attempts: 3
```

---

## Step 7: Monitoring Setup

### 7.1 Built-in Health Checks
Coolify monitors these automatically:
- ✅ Application health endpoint (`/health`)
- ✅ Redis connectivity
- ✅ Container resource usage

### 7.2 Application Metrics
Access metrics at:
- **Prometheus**: `https://orchestrator.yourdomain.com/metrics`
- **Redis Stats**: Via health endpoint

---

## Step 8: Post-Deployment Testing

### 8.1 Smoke Tests
```bash
# Test workflow creation
curl -X POST https://orchestrator.yourdomain.com/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "project_id": "test-project",
    "workflow_type": "movie_creation",
    "title": "Test Movie"
  }'

# Test agent registration
curl -X POST https://orchestrator.yourdomain.com/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "agent_id": "test-agent",
    "agent_type": "story",
    "capabilities": ["story_creation"],
    "endpoint_url": "https://test-agent.com/api"
  }'
```

### 8.2 Load Testing (Optional)
```bash
# Install hey (HTTP load testing tool)
# Test with 100 concurrent requests
hey -n 1000 -c 100 https://orchestrator.yourdomain.com/health
```

---

## Troubleshooting

### Common Issues & Solutions

#### **1. Application Won't Start**
```bash
# Check logs in Coolify dashboard
# Common causes:
# - Missing environment variables
# - Redis connection failed
# - Port already in use
```

#### **2. Redis Connection Failed**
```yaml
# Verify in .coolify.yml:
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

#### **3. SSL Certificate Issues**
- Verify domain DNS points to Coolify server
- Check Coolify proxy configuration
- Ensure port 443 is open

#### **4. High Memory Usage**
```env
# Adjust Redis memory limit
REDIS_MAXMEMORY=256mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

---

## Maintenance & Updates

### 1. Application Updates
```bash
# Push code changes
git add .
git commit -m "Update application"
git push origin main

# Redeploy in Coolify (automatic or manual trigger)
```

### 2. Backup Strategy
```bash
# Redis data is persisted in Docker volumes
# Coolify handles volume backups automatically
```

### 3. Log Management
```bash
# View logs in Coolify dashboard
# Logs are structured JSON for easy parsing
```

---

## Performance Expectations

### **Expected Metrics (Production)**
- **Concurrent Workflows**: 500+
- **Agent Capacity**: 100+ agents
- **Response Time**: <100ms for API calls
- **Throughput**: 1000+ requests/min
- **Memory Usage**: ~1-2GB
- **CPU Usage**: ~0.5-1.0 cores

### **Scaling Thresholds**
- Scale up when CPU > 80%
- Scale up when memory > 1.5GB
- Scale up when workflow queue > 100

---

## Security Checklist

- ✅ Strong SECRET_KEY generated
- ✅ API_KEY properly configured
- ✅ SSL/TLS enabled via Coolify
- ✅ Environment variables secured
- ✅ Non-root user in container
- ✅ Health checks configured
- ✅ Redis access restricted to app network

---

## Support & Resources

### **Documentation**
- API Docs: `https://orchestrator.yourdomain.com/api/docs`
- Redoc: `https://orchestrator.yourdomain.com/api/redoc`

### **Monitoring**
- Health: `https://orchestrator.yourdomain.com/health`
- Metrics: `https://orchestrator.yourdomain.com/metrics`

### **Logs**
- Application logs: Coolify dashboard
- Structured JSON format for analysis

---

**🎉 Your LangGraph Orchestrator is now live on Coolify!**

Visit: `https://orchestrator.yourdomain.com/api/docs` to start using the API.