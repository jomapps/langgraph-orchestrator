# Deployment Guide

This guide provides step-by-step instructions for deploying the LangGraph Orchestrator system across different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

**Minimum Requirements**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- Network: 1 Gbps

**Recommended Requirements**:
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: 10 Gbps

### Software Dependencies

**Required Software**:
- Docker Engine 20.10+
- Docker Compose 1.29+
- Git 2.25+
- Python 3.9+ (for local development)

**Optional Software**:
- Kubernetes 1.20+ (for K8s deployment)
- Helm 3.0+ (for K8s package management)
- Terraform 1.0+ (for infrastructure as code)

### Network Requirements

**Ports to Open**:
- 80: HTTP (redirect to HTTPS)
- 443: HTTPS
- 6379: Redis (internal only)
- 9090: Prometheus (restricted)
- 3000: Grafana (restricted)
- 9093: Alertmanager (restricted)

### Security Requirements

**SSL Certificates**:
- Valid SSL certificate for your domain
- Certificate chain properly configured
- Auto-renewal setup (Let's Encrypt recommended)

**Access Control**:
- SSH key-based authentication
- Firewall configured
- VPN access for monitoring tools

## Development Deployment

### Quick Start

1. **Clone Repository**:
```bash
git clone https://github.com/your-org/langgraph-orchestrator.git
cd langgraph-orchestrator
```

2. **Configure Environment**:
```bash
cp .env.example .env.development
# Edit .env.development with your settings
```

3. **Start Services**:
```bash
docker-compose up -d
```

4. **Verify Deployment**:
```bash
curl http://localhost:8000/health
```

### Detailed Development Setup

#### Step 1: Environment Preparation

```bash
# Create project directory
mkdir -p ~/projects/langgraph-orchestrator
cd ~/projects/langgraph-orchestrator

# Clone repository
git clone https://github.com/your-org/langgraph-orchestrator.git .

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 2: Configuration Setup

```bash
# Copy environment template
cp .env.example .env.development

# Edit configuration
nano .env.development
```

**Development Environment Variables**:
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

# Development specific
HOT_RELOAD=true
DEBUG_MODE=true
```

#### Step 3: Service Startup

```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 4: Verification

```bash
# Health check
curl http://localhost:8000/health

# API test
curl http://localhost:8000/api/workflows

# Redis connection test
docker-compose exec redis redis-cli ping

# Monitoring access
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana
```

## Staging Deployment

### Environment Setup

#### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment user
sudo useradd -m -s /bin/bash deployer
sudo usermod -aG docker deployer
```

#### Step 2: Application Deployment

```bash
# Switch to deployer user
sudo su - deployer

# Create deployment directory
mkdir -p ~/staging/langgraph-orchestrator
cd ~/staging/langgraph-orchestrator

# Clone repository
git clone https://github.com/your-org/langgraph-orchestrator.git .

# Copy staging configuration
cp docker-compose.staging.yml docker-compose.yml
cp .env.staging .env
```

#### Step 3: Staging Configuration

**Staging Environment Variables** (`.env.staging`):
```bash
# Application
APP_ENV=staging
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# Redis with persistence
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=staging-redis-password
REDIS_PERSISTENCE_ENABLED=true

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO

# Staging specific
SSL_ENABLED=true
DOMAIN=staging.yourdomain.com
```

#### Step 4: SSL Setup

```bash
# Install Certbot
sudo apt install certbot -y

# Generate SSL certificate
sudo certbot certonly --standalone -d staging.yourdomain.com

# Copy certificates to deployment directory
sudo cp /etc/letsencrypt/live/staging.yourdomain.com/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/staging.yourdomain.com/privkey.pem ./certs/
sudo chown deployer:deployer ./certs/*
```

#### Step 5: Service Deployment

```bash
# Start services
docker-compose up -d

# Check deployment
curl -f https://staging.yourdomain.com/health

# Monitor logs
docker-compose logs -f --tail=100
```

## Production Deployment

### Pre-Production Checklist

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] SSL certificates ready
- [ ] Domain configured
- [ ] Firewall rules set
- [ ] Rollback plan prepared

### Production Setup

#### Step 1: Infrastructure Setup

**Load Balancer Configuration**:
```bash
# Install HAProxy (alternative to Nginx)
sudo apt install haproxy -y

# Configure HAProxy
sudo nano /etc/haproxy/haproxy.cfg
```

**HAProxy Configuration**:
```
global
    maxconn 4096
    log /dev/log local0
    log /dev/log local1 notice

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend web_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/yourdomain.pem
    redirect scheme https if !{ ssl_fc }
    default_backend app_servers

backend app_servers
    balance leastconn
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check
```

#### Step 2: Application Servers Setup

**Server 1 Configuration**:
```bash
# On app server 1 (10.0.1.10)
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Create deployment user
sudo useradd -m -s /bin/bash deployer
sudo usermod -aG docker deployer

# Switch to deployer user
sudo su - deployer

# Setup application
git clone https://github.com/your-org/langgraph-orchestrator.git ~/production
cd ~/production
cp docker-compose.prod.yml docker-compose.yml
cp .env.production .env
```

#### Step 3: Redis Cluster Setup

**Redis Master Configuration**:
```bash
# On Redis master server
docker run -d --name redis-master \
  -p 6379:6379 \
  -v redis-data:/data \
  -e REDIS_PASSWORD=your-secure-password \
  redis:7-alpine redis-server \
  --appendonly yes \
  --requirepass your-secure-password
```

**Redis Slave Configuration**:
```bash
# On Redis slave servers
docker run -d --name redis-slave \
  -p 6379:6379 \
  -v redis-data:/data \
  -e REDIS_PASSWORD=your-secure-password \
  redis:7-alpine redis-server \
  --appendonly yes \
  --slaveof redis-master 6379 \
  --masterauth your-secure-password \
  --requirepass your-secure-password
```

**Redis Sentinel Configuration**:
```bash
# On Sentinel servers
docker run -d --name redis-sentinel \
  -p 26379:26379 \
  -v sentinel-config:/usr/local/etc/redis \
  redis:7-alpine redis-sentinel \
  /usr/local/etc/redis/sentinel.conf
```

#### Step 4: Production Configuration

**Production Environment Variables** (`.env.production`):
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
REDIS_PASSWORD=your-secure-redis-password
REDIS_SENTINEL_HOSTS=redis-sentinel-1:26379,redis-sentinel-2:26379,redis-sentinel-3:26379

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
API_RATE_LIMIT=100/minute
CORS_ORIGINS=https://yourdomain.com

# Performance
WORKER_PROCESSES=4
MAX_WORKERS=10
QUEUE_TIMEOUT=300

# Production specific
SSL_ENABLED=true
DOMAIN=api.yourdomain.com
CDN_ENABLED=true
CACHE_TTL=3600
```

#### Step 5: Monitoring Setup

**Prometheus Configuration**:
```bash
# Create Prometheus config directory
mkdir -p ~/production/monitoring/prometheus

# Copy configuration
cp monitoring/prometheus.yml ~/production/monitoring/prometheus/
```

**Grafana Configuration**:
```bash
# Create Grafana provisioning directory
mkdir -p ~/production/monitoring/grafana/provisioning/{dashboards,datasources}

# Copy dashboard configurations
cp monitoring/dashboards/*.json ~/production/monitoring/grafana/provisioning/dashboards/
```

#### Step 6: Security Hardening

**Firewall Configuration**:
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis (internal)
sudo ufw enable
```

**Fail2ban Configuration**:
```bash
# Install fail2ban
sudo apt install fail2ban -y

# Configure for SSH
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### Step 7: Production Deployment

```bash
# Deploy on all application servers
for server in app1 app2 app3; do
  ssh deployer@$server "cd ~/production && docker-compose up -d"
done

# Verify deployment
curl -f https://api.yourdomain.com/health

# Check load balancer
curl -f https://api.yourdomain.com/api/workflows
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.20+
- kubectl configured
- Helm 3.0+ installed
- Container registry access

### Deployment Steps

#### Step 1: Namespace Creation

```bash
# Create namespace
kubectl create namespace langgraph-orchestrator

# Set default namespace
kubectl config set-context --current --namespace=langgraph-orchestrator
```

#### Step 2: Configuration Setup

**ConfigMap Configuration** (`k8s/configmap.yaml`):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  APP_DEBUG: "false"
  APP_PORT: "8000"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  LOG_LEVEL: "INFO"
```

**Secret Configuration** (`k8s/secret.yaml`):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  REDIS_PASSWORD: <base64-encoded-password>
  SECRET_KEY: <base64-encoded-secret>
```

#### Step 3: Application Deployment

**Deployment Configuration** (`k8s/deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langgraph-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: langgraph-app
  template:
    metadata:
      labels:
        app: langgraph-app
    spec:
      containers:
      - name: app
        image: your-registry/langgraph-orchestrator:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service Configuration** (`k8s/service.yaml`):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: langgraph-service
spec:
  selector:
    app: langgraph-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

**Ingress Configuration** (`k8s/ingress.yaml`):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: langgraph-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: langgraph-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: langgraph-service
            port:
              number: 80
```

#### Step 4: Redis Deployment

**Redis StatefulSet** (`k8s/redis-statefulset.yaml`):
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command: ["redis-server", "--appendonly", "yes"]
        volumeMounts:
        - name: redis-storage
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

#### Step 5: Monitoring Setup

**Prometheus Deployment** (`k8s/prometheus.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

#### Step 6: Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress

# Check logs
kubectl logs -f deployment/langgraph-app
```

## Post-Deployment

### Verification Steps

#### 1. Health Checks

```bash
# Application health
curl -f https://api.yourdomain.com/health

# Detailed health check
curl -f https://api.yourdomain.com/health/detailed

# Dependency health check
curl -f https://api.yourdomain.com/health/dependencies
```

#### 2. API Testing

```bash
# Test workflow creation
curl -X POST https://api.yourdomain.com/api/workflows \
  -H "Content-Type: application/json" \
  -d '{"name": "test-workflow", "type": "video_processing"}'

# Test agent registration
curl -X POST https://api.yourdomain.com/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "test-agent", "capabilities": ["video_processing"]}'
```

#### 3. Monitoring Verification

```bash
# Check Prometheus targets
curl http://prometheus.yourdomain.com/api/v1/targets

# Check Grafana dashboards
open http://grafana.yourdomain.com

# Check Alertmanager
open http://alertmanager.yourdomain.com
```

#### 4. Performance Testing

```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 https://api.yourdomain.com/api/workflows

# Load testing with wrk
wrk -t12 -c400 -d30s https://api.yourdomain.com/api/workflows
```

### Configuration Validation

#### 1. Security Validation

```bash
# SSL certificate check
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Security headers check
curl -I https://api.yourdomain.com/health

# Rate limiting test
for i in {1..200}; do curl -s -o /dev/null -w "%{http_code}\n" https://api.yourdomain.com/api/workflows; done
```

#### 2. Performance Validation

```bash
# Response time check
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/api/workflows

# Throughput test
ab -n 10000 -c 100 https://api.yourdomain.com/api/workflows
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptoms**: Services fail to start or keep restarting

**Diagnosis**:
```bash
# Check service logs
docker-compose logs app1

# Check resource usage
docker system df
docker stats

# Check configuration
docker-compose config
```

**Solutions**:
- Check environment variables
- Verify port availability
- Check disk space
- Review resource limits

#### 2. Redis Connection Issues

**Symptoms**: Application can't connect to Redis

**Diagnosis**:
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Verify network connectivity
docker network ls
docker network inspect bridge
```

**Solutions**:
- Check Redis configuration
- Verify network settings
- Check firewall rules
- Review authentication

#### 3. High Memory Usage

**Symptoms**: System running out of memory

**Diagnosis**:
```bash
# Monitor memory usage
docker stats --no-stream
free -h
top

# Check for memory leaks
docker exec app1 python -m memory_profiler
```

**Solutions**:
- Increase memory limits
- Optimize application code
- Add more application instances
- Review Redis memory usage

#### 4. SSL Certificate Issues

**Symptoms**: SSL certificate warnings or failures

**Diagnosis**:
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect api.yourdomain.com:443

# Check certificate expiration
echo | openssl s_client -servername api.yourdomain.com -connect api.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**Solutions**:
- Renew SSL certificates
- Check certificate chain
- Verify domain configuration
- Review Nginx/HAProxy settings

### Performance Issues

#### 1. Slow Response Times

**Diagnosis**:
```bash
# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/api/workflows

# Monitor Redis performance
docker exec redis redis-cli INFO stats

# Check database queries
# Enable query logging in application
```

**Solutions**:
- Optimize database queries
- Add Redis caching
- Scale application instances
- Review network latency

#### 2. High CPU Usage

**Diagnosis**:
```bash
# Monitor CPU usage
docker stats --no-stream
top -p $(pgrep python)

# Profile application
docker exec app1 python -m cProfile -o profile.stats src/main.py
```

**Solutions**:
- Optimize application code
- Increase CPU resources
- Add more application instances
- Review background tasks

### Log Analysis

#### Application Logs

```bash
# View application logs
docker-compose logs -f app1 --tail=100

# Search for errors
docker-compose logs app1 | grep ERROR

# Filter by time range
docker-compose logs app1 --since="2024-01-01T00:00:00" --until="2024-01-01T23:59:59"
```

#### System Logs

```bash
# System logs
journalctl -u docker.service -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Redis logs
docker-compose logs -f redis
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks

- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Check backup status

#### Weekly Tasks

- [ ] Review monitoring dashboards
- [ ] Check SSL certificate expiration
- [ ] Update security patches
- [ ] Review performance metrics

#### Monthly Tasks

- [ ] Performance optimization review
- [ ] Security audit
- [ ] Capacity planning
- [ ] Documentation updates

### Update Procedures

#### Application Updates

```bash
# Backup current deployment
docker-compose exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb ./backups/redis-backup-$(date +%Y%m%d).rdb

# Pull latest code
git pull origin main

# Update configuration
cp .env.production .env

# Rolling update
docker-compose up -d --no-deps app1
docker-compose up -d --no-deps app2
docker-compose up -d --no-deps app3

# Verify update
curl -f https://api.yourdomain.com/health
```

#### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt upgrade docker-ce docker-ce-cli containerd.io -y

# Restart services
sudo systemctl restart docker
sudo systemctl restart haproxy
```

### Backup Procedures

#### Automated Backups

```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/langgraph-orchestrator/$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Redis
docker-compose exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Backup application data
tar -czf $BACKUP_DIR/app-data.tar.gz /app/data/

# Backup configuration
cp docker-compose.yml $BACKUP_DIR/
cp .env $BACKUP_DIR/

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/langgraph-orchestrator/$DATE/

# Cleanup old backups (keep last 30 days)
find /backups/langgraph-orchestrator -type d -mtime +30 -exec rm -rf {} \;
```

#### Recovery Procedures

```bash
# Service recovery
docker-compose restart app1

# Data recovery
docker stop redis
docker cp /backups/redis-backup-latest.rdb redis:/data/dump.rdb
docker start redis

# Full system recovery
docker-compose down
docker-compose up -d
```

### Support and Documentation

For deployment support:
- **Documentation**: [Full Documentation](README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/langgraph-orchestrator/issues)
- **Email**: support@langgraph-orchestrator.com
- **Monitoring**: https://grafana.yourdomain.com
- **Emergency**: +1-XXX-XXX-XXXX