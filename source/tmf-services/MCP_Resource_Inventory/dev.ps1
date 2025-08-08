#!/usr/bin/env pwsh
# Development script for Resource Inventory MCP Server

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

switch ($Command.ToLower()) {
    "setup" {
        Write-Host "Setting up development environment..." -ForegroundColor Green
        uv sync --dev
        if (!(Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "Created .env file from template. Please review and customize." -ForegroundColor Yellow
        }
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        uv run pytest -v
    }
    
    "test-api" {
        Write-Host "Testing API connectivity..." -ForegroundColor Green
        uv run python test_resource_inventory_api.py
    }
    
    "run" {
        Write-Host "Starting MCP Server (stdio mode)..." -ForegroundColor Green
        uv run python resource_inventory_mcp_server.py
    }
    
    "run-sse" {
        Write-Host "Starting MCP Server (SSE mode on port 3001)..." -ForegroundColor Green
        uv run python resource_inventory_mcp_server.py --transport=sse --port=3001
    }
    
    "dev" {
        Write-Host "Starting development server with auto-reload..." -ForegroundColor Green
        uv run uvicorn resource_inventory_mcp_server:app --reload --port 3001
    }
    
    "format" {
        Write-Host "Formatting code..." -ForegroundColor Green
        uv run black .
        uv run isort .
    }
    
    "lint" {
        Write-Host "Running linters..." -ForegroundColor Green
        uv run flake8 .
        uv run mypy .
    }
    
    "check" {
        Write-Host "Running all quality checks..." -ForegroundColor Green
        uv run black .
        uv run isort .
        uv run flake8 .
        uv run mypy .
        uv run pytest
    }
    
    "clean" {
        Write-Host "Cleaning up..." -ForegroundColor Green
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue @(
            ".pytest_cache",
            "htmlcov",
            "__pycache__",
            "*.pyc",
            ".coverage"
        )
        Get-ChildItem -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Green
        uv sync
    }
    
    "install-dev" {
        Write-Host "Installing development dependencies..." -ForegroundColor Green
        uv sync --dev
    }
    
    "update" {
        Write-Host "Updating dependencies..." -ForegroundColor Green
        uv lock --upgrade
        uv sync --dev
    }
    
    default {
        Write-Host "Resource Inventory MCP Server - Development Commands" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Available commands:" -ForegroundColor White
        Write-Host "  setup       - Initialize development environment" -ForegroundColor Gray
        Write-Host "  install     - Install production dependencies" -ForegroundColor Gray
        Write-Host "  install-dev - Install development dependencies" -ForegroundColor Gray
        Write-Host "  update      - Update all dependencies" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  run         - Start MCP server (stdio mode)" -ForegroundColor Gray
        Write-Host "  run-sse     - Start MCP server (SSE mode)" -ForegroundColor Gray
        Write-Host "  dev         - Start development server with auto-reload" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  test        - Run all tests" -ForegroundColor Gray  
        Write-Host "  test-api    - Test API connectivity" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  format      - Format code with black and isort" -ForegroundColor Gray
        Write-Host "  lint        - Run linters (flake8, mypy)" -ForegroundColor Gray
        Write-Host "  check       - Run all quality checks" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  clean       - Clean up temporary files" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Usage: .\dev.ps1 <command>" -ForegroundColor Yellow
        Write-Host "Example: .\dev.ps1 setup" -ForegroundColor Yellow
    }
}
