# Multi-Agent Intelligence Platform - Docker Setup Script
# For Windows PowerShell

param(
    [Parameter(Position = 0)]
    [ValidateSet('help', 'build', 'up', 'down', 'restart', 'logs', 'clean', 'pull-models', 'test', 'setup', 'status')]
    [string]$Command = 'help'
)

function Show-Help {
    Write-Host ""
    Write-Host "Multi-Agent Intelligence Platform - Docker Commands" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\docker.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  build        - Build all Docker images"
    Write-Host "  up           - Start all services"
    Write-Host "  down         - Stop all services"
    Write-Host "  restart      - Restart all services"
    Write-Host "  logs         - View logs from all services"
    Write-Host "  clean        - Stop and remove all containers, networks, and volumes"
    Write-Host "  pull-models  - Pull required Ollama models"
    Write-Host "  test         - Run backend tests"
    Write-Host "  setup        - Full setup (build, start, pull models)"
    Write-Host "  status       - Check service status"
    Write-Host ""
}

function Build-Images {
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    docker-compose build
}

function Start-Services {
    Write-Host "Starting services..." -ForegroundColor Yellow
    docker-compose up -d
    Write-Host ""
    Write-Host "✅ Services started!" -ForegroundColor Green
    Write-Host "Application: http://localhost (port 80)" -ForegroundColor Cyan
    Write-Host "  - Frontend served via Nginx reverse proxy" -ForegroundColor Gray
    Write-Host "  - Backend API: http://localhost/api" -ForegroundColor Gray
    Write-Host "  - API Docs: http://localhost/docs" -ForegroundColor Gray
    Write-Host "  - WebSocket: ws://localhost/ws" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Don't forget to pull Ollama models: .\docker.ps1 pull-models" -ForegroundColor Yellow
}

function Stop-Services {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Services stopped!" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "Restarting services..." -ForegroundColor Yellow
    docker-compose restart
    Write-Host "✅ Services restarted!" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    docker-compose logs -f
}

function Clean-All {
    Write-Host "⚠️  WARNING: This will remove all containers, networks, and volumes!" -ForegroundColor Red
    $confirmation = Read-Host "Are you sure? (y/n)"
    if ($confirmation -eq 'y') {
        docker-compose down -v
        docker system prune -f
        Write-Host "✅ Cleaned up!" -ForegroundColor Green
    }
    else {
        Write-Host "Cancelled." -ForegroundColor Yellow
    }
}

function Pull-Models {
    Write-Host "Pulling Ollama models..." -ForegroundColor Yellow
    Write-Host "This may take a while (models are 5-10GB each)..." -ForegroundColor Cyan
    docker-compose exec ollama ollama pull gpt-oss:120b-cloud
    docker-compose exec ollama ollama pull nomic-embed-text
    Write-Host "✅ Models downloaded!" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "Running backend tests..." -ForegroundColor Yellow
    docker-compose exec backend pytest tests/unit -v
}

function Setup-All {
    Write-Host "Starting full setup..." -ForegroundColor Yellow
    Build-Images
    Start-Services
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    Pull-Models
    Write-Host ""
    Write-Host "✅ Setup complete!" -ForegroundColor Green
    Write-Host "Visit http://localhost:5173 to start using the platform" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Default login credentials:" -ForegroundColor Yellow
    Write-Host "  Admin: admin:admin"
    Write-Host "  Developer: dev:dev"
    Write-Host "  User: user:user"
}

function Show-Status {
    Write-Host "Service status:" -ForegroundColor Yellow
    docker-compose ps
}

# Main command dispatcher
switch ($Command) {
    'help' { Show-Help }
    'build' { Build-Images }
    'up' { Start-Services }
    'down' { Stop-Services }
    'restart' { Restart-Services }
    'logs' { Show-Logs }
    'clean' { Clean-All }
    'pull-models' { Pull-Models }
    'test' { Run-Tests }
    'setup' { Setup-All }
    'status' { Show-Status }
    default { Show-Help }
}
