# Deployment Guide

**Project:** Multi-Agent Intelligence Platform  
**Version:** 1.0.0  
**Last Updated:** January 22, 2026

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development Setup](#local-development-setup)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (223+/297)
- [ ] 0 TypeScript errors
- [ ] Code review completed
- [ ] No console warnings/errors
- [ ] Performance benchmarks met
- [ ] Security audit completed

### Documentation
- [ ] API documentation current
- [ ] Deployment guide reviewed
- [ ] Environment variables documented
- [ ] Database schema documented
- [ ] Runbooks created for common issues

### Infrastructure
- [ ] Database backups configured
- [ ] Monitoring tools installed
- [ ] Logging aggregation setup
- [ ] CDN configured (if applicable)
- [ ] SSL certificates valid
- [ ] Firewall rules configured

### Testing
- [ ] Unit tests: ✅ Passing
- [ ] Integration tests: ✅ Passing
- [ ] E2E tests: ✅ Passing
- [ ] Load tests: ✅ Results reviewed
- [ ] Security tests: ✅ Completed
- [ ] Backup/restore tested

### Team Readiness
- [ ] Deployment team trained
- [ ] On-call schedule established
- [ ] Incident response plan ready
- [ ] Communication channels ready
- [ ] Rollback procedures documented

---

## Local Development Setup

### Prerequisites

```bash
# System requirements
- Node.js 16+
- Python 3.10+
- Docker (optional)
- Git
- 8GB+ RAM
- 10GB+ disk space
```

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python -c "from src.infrastructure.persistence.database import init_db; init_db()"

# 4. Start Ollama (separate terminal)
ollama serve
ollama pull nomic-embed-text
ollama pull gpt-oss:120b-cloud

# 5. Run backend
python -m uvicorn src.presentation.api.app:create_app --reload
```

**Output:** Backend on http://localhost:8000

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Start dev server
npm run dev
```

**Output:** Frontend on http://localhost:5173

### Environment Variables

**Backend (.env):**
```
DATABASE_URL=sqlite:///data/agent_system.db
JWT_SECRET=your-secret-key-here
OLLAMA_BASE_URL=http://localhost:11434
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
DEBUG=false
```

**Frontend (.env.local):**
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENV=development
```

---

## Staging Deployment

### Staging Environment Setup

```bash
# 1. Create staging directory
mkdir -p /opt/staging/multi-agent-platform
cd /opt/staging/multi-agent-platform

# 2. Clone repository
git clone <repo-url> .

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup frontend
cd ../frontend
npm install
npm run build

# 5. Configure environment
cp .env.example .env
# Edit .env with staging values

# 6. Initialize database
cd ../backend
python -c "from src.infrastructure.persistence.database import init_db; init_db()"
```

### Staging Server Configuration

**Nginx Configuration** (`/etc/nginx/sites-available/staging`)

```nginx
upstream backend {
    server localhost:8001;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 443 ssl;
    server_name staging.example.com;
    
    ssl_certificate /etc/letsencrypt/live/staging.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.example.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Staging Deployment Steps

```bash
# 1. Stop current instance (if running)
sudo systemctl stop multi-agent-platform || true

# 2. Deploy new version
cd /opt/staging/multi-agent-platform
git pull origin staging
npm install --prefix frontend
npm run build --prefix frontend
pip install -r backend/requirements.txt

# 3. Run migrations
cd backend
python -c "from src.infrastructure.persistence.database import init_db; init_db()"

# 4. Start service
cd /opt/staging/multi-agent-platform
sudo systemctl start multi-agent-platform

# 5. Verify
curl -I https://staging.example.com/health
```

### Staging Testing

```bash
# 1. Health check
curl https://staging.example.com/health/details

# 2. Login test
curl -X POST https://staging.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# 3. WebSocket test
wscat -c wss://staging.example.com/ws/chat

# 4. Load test (optional)
artillery quick --count 100 --num 10 https://staging.example.com/api/health
```

---

## Production Deployment

### Blue-Green Deployment Strategy

```
Current State (Blue):
  - Production-v1 (running)
  - Database: prod-db (current)
  - Traffic: 100% → Blue

Deployment:
  1. Provision Green environment
  2. Deploy application to Green
  3. Run smoke tests on Green
  4. Switch traffic: 100% → Green
  5. Keep Blue as fallback
  6. Monitor for 1 hour
  7. Decommission Blue after 24h

Rollback:
  - Switch traffic back to Blue immediately
  - Green issue fixed separately
```

### Production Deployment Steps

```bash
# 1. Pre-deployment backup
pg_dump prod_db > backup_$(date +%Y%m%d_%H%M%S).sql
aws s3 cp backup_*.sql s3://backups/

# 2. Deploy to Green environment
cd /opt/production/green
git clone <repo-url> .
git checkout v1.0.0  # Use specific tag

# 3. Install dependencies
cd /opt/production/green
npm install --prefix frontend
npm run build --prefix frontend
pip install -r backend/requirements.txt

# 4. Run database migrations
cd backend
python -c "from src.infrastructure.persistence.database import init_db; init_db()"

# 5. Health checks
curl http://localhost:8001/health

# 6. Smoke tests
npm run test:e2e --prefix frontend

# 7. DNS switch (traffic routing)
# Update load balancer to route traffic to Green
aws elb register-instances-with-load-balancer \
  --load-balancer-name prod-lb \
  --instances i-green-instance

# 8. Monitor
watch -n 2 'curl -s http://localhost:8001/metrics | grep -E "http_request|error"'
```

### Production Server Configuration

**AWS Lambda / ECS Configuration:**

```yaml
# ecs-task-definition.json
{
  "family": "multi-agent-platform",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "registry.example.com/multi-agent:1.0.0",
      "portMappings": [{"containerPort": 8000, "hostPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "ENV", "value": "production"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/multi-agent",
          "awslogs-region": "us-east-1"
        }
      }
    },
    {
      "name": "frontend",
      "image": "registry.example.com/multi-agent-frontend:1.0.0",
      "portMappings": [{"containerPort": 3000, "hostPort": 3000}]
    }
  ]
}
```

---

## Post-Deployment Verification

### Immediate Checks (First 5 minutes)

```bash
# 1. Health endpoint
curl -X GET https://api.example.com/health
# Expected: 200 OK with health data

# 2. API endpoints
curl -X GET https://api.example.com/v1/domains
# Expected: 200 with domain list

# 3. WebSocket connection
wscat -c wss://api.example.com/ws/chat
# Expected: Connection successful

# 4. Frontend load
curl -I https://example.com
# Expected: 200 OK

# 5. Error rates
curl -X GET https://api.example.com/metrics | grep "http_requests_total{status=\"5"
# Expected: No 5xx errors
```

### Smoke Tests (First 15 minutes)

```bash
# 1. Login functionality
npm run test:login --prefix frontend

# 2. Chat functionality
npm run test:chat --prefix frontend

# 3. Admin panel load
npm run test:admin --prefix frontend

# 4. Database connectivity
curl -X GET https://api.example.com/v1/conversations

# 5. Metrics collection
curl -X GET https://api.example.com/metrics | grep -c "http_request"
```

### Full Validation (First Hour)

```bash
# 1. Run full test suite
pytest backend/testing/

# 2. E2E tests
npm run test:e2e --prefix frontend

# 3. Performance baseline
npm run test:performance --prefix frontend

# 4. Security scan
npm audit --prefix frontend
pip audit

# 5. Database integrity
python scripts/validate_db.py
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

```
Application:
  - HTTP response time (p50, p95, p99)
  - Error rate (4xx, 5xx)
  - Request throughput
  - WebSocket connections
  - API endpoint latency

Infrastructure:
  - CPU utilization
  - Memory usage
  - Disk space
  - Network bandwidth
  - Database connections

Business:
  - Active users
  - Conversations count
  - Tool runs count
  - Chat messages count
```

### Monitoring Setup (Prometheus)

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'multi-agent-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 10m
        annotations:
          summary: "High latency detected"
      
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 1.5e9
        for: 5m
        annotations:
          summary: "High memory usage"
```

### Log Aggregation

```bash
# ELK Stack setup
docker run -d --name elasticsearch \
  -e discovery.type=single-node \
  docker.elastic.co/elasticsearch/elasticsearch:7.14.0

docker run -d --name kibana \
  -p 5601:5601 \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  docker.elastic.co/kibana/kibana:7.14.0

# Log shipper (Filebeat)
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/multi-agent-platform/*.log

output.elasticsearch:
  hosts: ["localhost:9200"]
```

---

## Rollback Procedures

### Immediate Rollback (Issue within 5 minutes)

```bash
# 1. Switch traffic back to Blue
aws elb deregister-instances-from-load-balancer \
  --load-balancer-name prod-lb \
  --instances i-green-instance

aws elb register-instances-with-load-balancer \
  --load-balancer-name prod-lb \
  --instances i-blue-instance

# 2. Verify health
curl https://api.example.com/health

# 3. Monitor error rates
watch -n 2 'curl -s https://api.example.com/metrics | grep http_requests'
```

### Rollback with Database Issues

```bash
# 1. Stop Green application
docker stop multi-agent-green

# 2. Restore database from backup
restore_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
pg_restore --clean --if-exists -d prod_db \
  s3://backups/backup_${restore_time}.sql

# 3. Switch traffic to Blue
aws elb deregister-instances-from-load-balancer \
  --load-balancer-name prod-lb \
  --instances i-green-instance

# 4. Verify
curl https://api.example.com/health
```

### Partial Rollback (Canary Rollback)

```bash
# 1. Reduce Green traffic to 10%
aws elbv2 modify-rule \
  --rule-arn arn:aws:elasticloadbalancing:... \
  --conditions Field=path-pattern,Values="/api/*" \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/green/...
  # Set weight to 10

# 2. Monitor Green errors
curl https://api.example.com/metrics | grep "5.."

# 3. If errors found:
#    - Increase traffic back to Blue (90%)
#    - Debug Green
#    - Fix and redeploy

# 4. If no errors:
#    - Gradually increase Green (25%, 50%, 100%)
#    - Monitor at each step
```

---

## Troubleshooting

### Application Won't Start

```bash
# 1. Check logs
docker logs multi-agent-platform

# 2. Verify environment variables
env | grep -E "DATABASE|JWT|OLLAMA"

# 3. Test database connection
python -c "from src.infrastructure.persistence.database import get_session; print(get_session())"

# 4. Check port availability
netstat -tuln | grep 8000

# 5. Verify dependencies
pip check
npm audit
```

### High Error Rate After Deployment

```bash
# 1. Check API logs
tail -f /var/log/multi-agent-platform/api.log

# 2. Check database connection pool
SELECT * FROM pg_stat_activity;

# 3. Monitor system resources
top -b -n 1 | head -20

# 4. Test specific endpoint
curl -v https://api.example.com/v1/domains

# 5. Rollback if needed
# See rollback procedures above
```

### WebSocket Connection Issues

```bash
# 1. Test WebSocket connection
wscat -c wss://api.example.com/ws/chat

# 2. Check proxy settings (Nginx/HAProxy)
cat /etc/nginx/sites-available/production

# 3. Verify SSL certificates
openssl s_client -connect api.example.com:443

# 4. Check firewall rules
sudo iptables -L -n | grep 443

# 5. Monitor WebSocket connections
curl https://api.example.com/metrics | grep websocket
```

### Database Performance Issues

```bash
# 1. Check slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# 2. Check indexes
SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname != 'pg_toast';

# 3. Run VACUUM
VACUUM ANALYZE;

# 4. Check connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# 5. Monitor query time
curl https://api.example.com/metrics | grep histogram_quantile
```

---

## Deployment Checklist

### Pre-Deployment (T-1 day)

- [ ] All tests passing
- [ ] Code review completed
- [ ] Staging deployment successful
- [ ] Backups verified
- [ ] Team trained
- [ ] On-call engineer assigned
- [ ] Communication channels ready

### During Deployment (T-0 hours)

- [ ] Announce deployment window
- [ ] Take backup
- [ ] Deploy to Green
- [ ] Run smoke tests
- [ ] Switch traffic
- [ ] Monitor error rates
- [ ] Verify key metrics

### Post-Deployment (T+1 hour)

- [ ] Run full validation
- [ ] Check all dashboards
- [ ] Verify metrics
- [ ] Monitor for issues
- [ ] Document any changes
- [ ] Communicate success

### After Deployment (T+24 hours)

- [ ] Decommission Blue environment
- [ ] Archive logs
- [ ] Update documentation
- [ ] Conduct retrospective
- [ ] Plan Phase 7

---

## Success Criteria

✅ **Deployment Successful If:**
- All health checks pass
- Error rate < 0.5%
- Response time p95 < 1s
- No database errors
- WebSocket connections stable
- All smoke tests pass
- Team confirms readiness

❌ **Trigger Rollback If:**
- Error rate > 5%
- Response time p95 > 5s
- Database connection pool exhausted
- Memory usage > 90%
- Multiple failed health checks
- WebSocket connection failures
- Critical customer reports issues

---

**Document:** DEPLOYMENT_GUIDE.md  
**Version:** 1.0  
**Date:** January 22, 2026  
**Status:** Ready for Deployment
