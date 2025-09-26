#!/bin/bash

# LangGraph Orchestrator - Coolify Deployment Script
# Usage: ./deploy-coolify.sh

set -e

echo "🚀 LangGraph Orchestrator - Coolify Deployment"
echo "==============================================="

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed."
    exit 1
fi

# Generate secure keys if not exists
echo "🔐 Generating secure keys..."

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
API_KEY=$(python3 -c "import uuid; print(str(uuid.uuid4()))" 2>/dev/null || uuidgen)

echo "✅ Generated SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "✅ Generated API_KEY: ${API_KEY:0:20}..."

# Create .env template for local reference
cat > .env.example << EOF
# Security & Core Configuration
SECRET_KEY=${SECRET_KEY}
API_KEY=${API_KEY}
ENVIRONMENT=production
DEBUG=false

# Redis Configuration  
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=WARNING

# Performance Settings
MAX_WORKFLOWS=500
MAX_AGENTS=100
WORKER_PROCESSES=4

# External Service URLs
AUTO_MOVIE_BASE_URL=https://auto-movie.ft.tc
BRAIN_SERVICE_BASE_URL=https://brain.ft.tc
TASK_SERVICE_BASE_URL=https://tasks.ft.tc

# Neo4j Database Connection
NEO4J_URI=https://neo4j.ft.tc
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Monitoring
LOG_FORMAT=json
ENABLE_STRUCTURED_LOGGING=true
EOF

echo "✅ Created .env.example file"

# Commit changes if in git repo
if [ -d ".git" ]; then
    echo "📦 Committing deployment files..."
    git add .coolify.yml COOLIFY_DEPLOYMENT.md .env.example deploy-coolify.sh
    git commit -m "Add Coolify deployment configuration" || echo "⚠️  No changes to commit"
    
    echo "🔄 Pushing to remote repository..."
    git push origin $(git branch --show-current) || echo "⚠️  Failed to push, please push manually"
else
    echo "⚠️  Not a git repository, skipping commit"
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Copy the environment variables from .env.example"
echo "2. In Coolify dashboard:"
echo "   - Create new project: 'langgraph-orchestrator'"
echo "   - Add Docker Compose service"
echo "   - Set Git repository URL"
echo "   - Configure environment variables"
echo "   - Set domain: your-domain.com"
echo "   - Deploy!"
echo ""
echo "📚 Full guide: COOLIFY_DEPLOYMENT.md"
echo "🌐 After deployment, visit: https://your-domain.com/api/docs"

# Show environment variables for easy copy-paste
echo ""
echo "🔑 ENVIRONMENT VARIABLES TO ADD IN COOLIFY:"
echo "=========================================="
cat .env.example
echo "=========================================="