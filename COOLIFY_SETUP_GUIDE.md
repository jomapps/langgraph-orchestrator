# 🚀 Coolify Setup Guide - LangGraph Orchestrator

**Complete step-by-step guide to deploy LangGraph Orchestrator on Coolify**

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ Access to your Coolify dashboard
- ✅ Admin/deployment permissions in Coolify
- ✅ GitHub repository access (this repo: `jomapps/langgraph-orchestrator`)
- ✅ Domain name ready (optional, can use Coolify subdomain)

## 🏗️ What We're Deploying

### **Application Stack**
- **Main App**: FastAPI application (Python 3.11)
- **Database**: Redis for state management
- **Port**: 8003 (main application)
- **Health Check**: `/health` endpoint

### **Key Features Being Deployed**
- 🛡️ **Type-safe Redis operations** (70+ fixes applied)
- 🔄 **Workflow orchestration** for AI video creation
- 📊 **Agent management system**
- 🎯 **Task execution and monitoring**
- 📈 **Performance monitoring and logging**

## 🚀 Step-by-Step Coolify Setup

### **Step 1: Access Coolify Dashboard**

1. **Open your Coolify dashboard**
   - Navigate to your Coolify URL (e.g., `https://coolify.yourdomain.com`)
   - Log in with your credentials

2. **Create a New Project** (if needed)
   - Click "**+ New Project**" or use an existing one
   - Name: `langgraph-orchestrator`
   - Description: `AI Workflow Orchestrator with Type Safety Improvements`

### **Step 2: Add the Application**

1. **Click "Add Resource"**
   - Choose "**Application**"
   - Select "**Docker Compose**" as the type

2. **Repository Configuration**
   - **Repository URL**: `https://github.com/jomapps/langgraph-orchestrator.git`
   - **Branch**: `master`
   - **Auto-deploy**: ✅ Enable (recommended)

3. **Docker Compose Configuration**
   - **Docker Compose Location**: `.coolify.yml` (already exists in repo)
   - **Build Pack**: Auto-detect should work

### **Step 3: Configure Environment Variables**

In the Coolify dashboard, add these environment variables:

#### **🔐 Security & Core**
```env
SECRET_KEY=generate-secure-32-char-key
API_KEY=generate-uuid-here
ENVIRONMENT=production
DEBUG=false
```

#### **🔧 Application Settings**
```env
API_HOST=0.0.0.0
API_PORT=8003
LOG_LEVEL=INFO
LOG_FORMAT=pretty
ENABLE_PERFORMANCE_LOGGING=true
ENABLE_STRUCTURED_LOGGING=false
```

#### **⚡ Performance Settings**
```env
MAX_WORKFLOWS=50
MAX_AGENTS=10
WORKER_PROCESSES=4
```

#### **🔗 External Services**
```env
AUTO_MOVIE_BASE_URL=https://auto-movie.ft.tc
BRAIN_SERVICE_BASE_URL=https://brain.ft.tc  
TASK_SERVICE_BASE_URL=https://tasks.ft.tc
```

#### **💾 Database Configuration**
```env
# Redis (managed by Coolify via .coolify.yml)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Neo4j (if you have a separate Neo4j instance)
NEO4J_URI=https://neo4j.ft.tc
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

### **Step 4: Configure Domain & SSL**

1. **Domain Settings**
   - **Option A**: Use Coolify subdomain (e.g., `langgraph.coolify.io`)
   - **Option B**: Use custom domain (e.g., `agents.ft.tc`)

2. **SSL Configuration**
   - ✅ Enable SSL (Let's Encrypt)
   - ✅ Force HTTPS redirect

### **Step 5: Deploy the Application**

1. **Review Configuration**
   - Verify all environment variables are set
   - Check Docker Compose file is detected
   - Ensure domain is configured

2. **Start Deployment**
   - Click "**Deploy**"
   - Monitor deployment logs in real-time
   - Wait for "Deployment successful" message

### **Step 6: Verify Deployment**

Once deployment completes, test these endpoints:

```bash
# Health Check
curl https://your-domain.com/health
# Expected: {"status":"healthy","timestamp":"..."}

# API Documentation  
curl https://your-domain.com/api/docs
# Expected: Swagger UI HTML

# Agents Endpoint
curl https://your-domain.com/api/v1/agents
# Expected: JSON array (may be empty initially)

# Workflows Endpoint
curl https://your-domain.com/api/v1/workflows  
# Expected: JSON array (may be empty initially)
```

## 🔧 Advanced Configuration

### **Resource Limits** (Optional)
In Coolify, you can set resource limits:
- **Memory**: 512MB - 1GB (recommended)
- **CPU**: 0.5 - 1.0 cores
- **Storage**: 5GB for logs and temp files

### **Scaling Options**
- **Replicas**: Start with 1, scale up as needed
- **Auto-restart**: Enable for production
- **Health checks**: Already configured in Docker Compose

### **Logging Configuration**
Coolify will automatically collect logs from:
- Application stdout/stderr
- Health check results
- Container metrics

## 🎯 Expected Results

### **After Successful Deployment**

1. **Service Status**
   - ✅ Main application running on port 8003
   - ✅ Redis container running and connected
   - ✅ Health checks passing
   - ✅ SSL certificate active

2. **API Functionality**
   - ✅ `/health` endpoint responds with 200 OK
   - ✅ `/api/docs` shows interactive API documentation
   - ✅ All API endpoints accessible and functional
   - ✅ Redis connection stable (no null reference errors)

3. **Performance Benefits**
   - 🛡️ **Zero Redis null reference crashes** (70+ fixes applied)
   - ⚡ **Improved response reliability**
   - 📊 **Better error handling and logging**
   - 🔄 **Stable workflow execution**

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### **🔴 Build Failures**
- **Symptom**: Docker build fails
- **Solution**: Check requirements.txt and Dockerfile syntax
- **Check**: Ensure Python 3.11 base image is available

#### **🔴 Environment Variables Missing**
- **Symptom**: App starts but fails with configuration errors
- **Solution**: Verify all required environment variables are set in Coolify
- **Check**: Sensitive variables should be marked as "Secret"

#### **🔴 Redis Connection Issues**
- **Symptom**: "Redis not connected" errors
- **Solution**: Ensure Redis container is healthy and `REDIS_HOST=redis`
- **New Safety**: Type-safe connection handling will prevent crashes

#### **🔴 Health Check Failures**
- **Symptom**: Container restarts frequently
- **Solution**: Check if app is binding to correct port (8003)
- **Debug**: Check application logs in Coolify dashboard

#### **🔴 External Service Connectivity**
- **Symptom**: External API calls fail
- **Solution**: Verify URLs for auto-movie, brain, and task services
- **Check**: Network connectivity from Coolify to external services

### **Debugging Commands**

Access the container via Coolify terminal:
```bash
# Check application status
curl localhost:8003/health

# Check Redis connectivity
redis-cli ping

# Check logs
tail -f logs/app.log

# Test environment variables
env | grep -E "(SECRET_KEY|API_KEY|REDIS)"
```

## 📊 Monitoring & Maintenance

### **What to Monitor**
1. **Health Status**: `/health` endpoint response time
2. **Error Rates**: Should be significantly lower with type safety fixes
3. **Memory Usage**: Monitor Redis and app memory consumption
4. **Response Times**: API endpoint performance
5. **Connection Stability**: Redis connection health

### **Maintenance Tasks**
- **Weekly**: Review application logs for any issues
- **Monthly**: Update dependencies if needed
- **Quarterly**: Review and optimize resource allocation

## 🎉 Success Checklist

After completing deployment, verify:

- [ ] ✅ Coolify dashboard shows service as "Running"
- [ ] ✅ Health check endpoint returns 200 OK
- [ ] ✅ API documentation accessible at `/api/docs`
- [ ] ✅ All environment variables properly set
- [ ] ✅ SSL certificate active and HTTPS working
- [ ] ✅ Application logs show no critical errors
- [ ] ✅ Redis connection stable and responding
- [ ] ✅ External service URLs accessible (if configured)

## 🚀 You're Ready!

Once all checks pass, your **enhanced LangGraph Orchestrator** is live in production with:

- 🛡️ **70+ type safety improvements**
- 🔄 **Reliable workflow orchestration**
- 📊 **Comprehensive monitoring**
- ⚡ **Production-ready performance**

**Welcome to your new, more reliable LangGraph Orchestrator!** 🎊