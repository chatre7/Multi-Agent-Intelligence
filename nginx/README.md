# Nginx Reverse Proxy Configuration

## Overview

This directory contains the Nginx configuration for the Multi-Agent Intelligence Platform. Nginx acts as a reverse proxy, routing requests to the appropriate services (frontend or backend) and solving CORS issues.

## Architecture

```
                    ┌─────────────────────┐
                    │   Client Browser    │
                    │  (http://localhost) │
                    └──────────┬──────────┘
                               │
                               │ Port 80
                               ▼
                    ┌─────────────────────┐
                    │   Nginx Container   │
                    │  (Reverse Proxy)    │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
        / (root)          /api, /ws      /docs, /metrics
               │               │               │
               ▼               ▼               ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  Frontend    │  │   Backend    │  │   Backend    │
    │ (React:5173) │  │ (FastAPI:8000)│  │ (API Docs)   │
    └──────────────┘  └──────────────┘  └──────────────┘
```

## Routing Rules

### Frontend Routes
- **`/`** → Frontend container (React app)
- All static assets served from frontend

### Backend Routes
- **`/api/*`** → Backend container (FastAPI endpoints)
- **`/ws/*`** → Backend container (WebSocket connections)
- **`/health`** → Backend health check
- **`/metrics`** → Prometheus metrics
- **`/docs`** → Swagger UI
- **`/openapi.json`** → OpenAPI schema

## Configuration Files

### `nginx.conf`
Main Nginx configuration with:
- **Upstream definitions** - Points to backend and frontend containers
- **Server block** - Listens on port 80
- **Location blocks** - Routing rules for each path
- **CORS headers** - Prevents CORS errors
- **WebSocket support** - Proper upgrade headers for WebSocket connections
- **Gzip compression** - Optimized content delivery

### `Dockerfile`
Nginx container build file:
- Based on `nginx:alpine` (lightweight)
- Copies custom `nginx.conf`
- Exposes port 80
- Includes health check

## Benefits

### 🔒 CORS Resolution
- All services accessed from same origin (localhost:80)
- No need for CORS headers in backend
- No browser security issues

### 🔄 Single Entry Point
- One port for all services (port 80)
- Easier to use and remember
- Production-ready setup

### 🚀 Better Performance
- Gzip compression enabled
- Static file caching
- Efficient request routing

### 🔧 Easy Configuration
- Centralized routing rules
- Easy to add new endpoints
- Simple SSL/TLS setup (for production)

## Development

### Testing Nginx Configuration
```bash
# Test config syntax
docker compose exec nginx nginx -t

# Reload config without restart
docker compose exec nginx nginx -s reload
```

### View Nginx Logs
```bash
# All logs
docker compose logs nginx -f

# Access logs only
docker compose exec nginx tail -f /var/log/nginx/access.log

# Error logs only
docker compose exec nginx tail -f /var/log/nginx/error.log
```

### Debugging
```bash
# Check if nginx is running
docker compose ps nginx

# Enter nginx container
docker compose exec nginx sh

# Check nginx process
docker compose exec nginx ps aux | grep nginx
```

## Configuration Details

### CORS Headers
Nginx adds these headers to API responses:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: DNT, User-Agent, X-Requested-With, If-Modified-Since, Cache-Control, Content-Type, Range, Authorization`

### WebSocket Configuration
Special headers for WebSocket connections:
- `Upgrade: websocket`
- `Connection: upgrade`
- Long timeout (24 hours) for persistent connections

### Compression
Gzip enabled for:
- Text files (HTML, CSS, JS, JSON)
- Fonts (TrueType, OpenType, SVG)
- XML and RSS feeds

## Production Considerations

### SSL/TLS
For production, add SSL configuration:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

### Security Headers
Add these headers for better security:
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### Rate Limiting
Prevent abuse with rate limits:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api {
    limit_req zone=api burst=20;
    # ... rest of config
}
```

## Troubleshooting

### 502 Bad Gateway
- **Cause**: Backend/Frontend containers not running
- **Fix**: Check container status with `docker compose ps`

### CORS Still Blocked
- **Cause**: Browser cached old response
- **Fix**: Hard refresh (Ctrl+Shift+R) or clear cache

### WebSocket Connection Failed
- **Cause**: Incorrect WebSocket URL in frontend
- **Fix**: Ensure using `ws://localhost/ws` (not `ws://localhost:8000/ws`)

### 404 Not Found
- **Cause**: Route not matching any location block
- **Fix**: Check nginx logs and update routing rules

### Cannot Access on Port 80
- **Cause**: Port 80 already in use
- **Fix**: Stop other services using port 80 or change nginx port in docker-compose.yml

## Files in This Directory

```
nginx/
├── Dockerfile       # Container build configuration
├── nginx.conf       # Main Nginx configuration
└── README.md        # This file
```

## Testing Access

After starting services:

```bash
# Test frontend
curl http://localhost/

# Test backend API
curl http://localhost/api/v1/health

# Test docs
open http://localhost/docs
```

## Updates and Modifications

To modify routing:
1. Edit `nginx.conf`
2. Rebuild nginx container: `docker compose up --build nginx -d`
3. Or reload config: `docker compose exec nginx nginx -s reload`

---

**Last Updated**: January 22, 2026  
**Version**: 1.0.0
