@echo off
REM Change to the directory of the script
cd /d %~dp0

REM Stop Docker Compose services
docker compose down -v

REM Check if 'tmf' network exists, create it if not
for /f "tokens=*" %%i in ('docker network ls ^| findstr /R "\<tmf\>"') do set FOUND=true

if not defined FOUND (
    docker network create tmf
)

REM Start Docker Compose services
docker compose up
