@echo off
REM Fake News Detection System - Deployment Script for Windows
REM This script automates the Docker deployment process

echo ========================================
echo Fake News Detection System - Docker Deployment
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    echo         Visit: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    echo         Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo [OK] Docker is installed
docker --version
echo [OK] Docker Compose is installed
docker-compose --version
echo.

REM Check if models exist
echo [INFO] Checking for required model files...
if not exist "models\text_model" (
    echo [WARNING] Model directories not found!
    echo           Please ensure models are trained and available in the models\ directory
    echo           Run: python scripts\train_pipeline.py
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo [OK] Model directories found
)
echo.

REM Stop any running containers
echo [INFO] Stopping any running containers...
docker-compose down 2>nul
echo.

REM Build and start services
echo [INFO] Building Docker images...
docker-compose build --no-cache

echo.
echo [INFO] Starting services...
docker-compose up -d

echo.
echo [INFO] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo.
    echo [ERROR] Deployment failed. Check logs:
    echo         docker-compose logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Deployment successful!
echo ========================================
echo.
echo Access points:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Health:    http://localhost:8000/health
echo.
echo View logs:
echo   docker-compose logs -f
echo.
echo Stop services:
echo   docker-compose down
echo.
pause
