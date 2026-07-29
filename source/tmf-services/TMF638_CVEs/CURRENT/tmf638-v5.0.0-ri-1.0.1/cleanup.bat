@echo off
REM Change to the directory of the script
cd /d %~dp0

REM Stop Docker Compose services
docker compose down --rmi all --volumes --remove-orphans

REM Remove 'tmf' network if it exists
for /f "tokens=*" %%i in ('docker network ls ^| findstr /R "\<tmf\>"') do set FOUND=true

if defined FOUND (
    docker network rm tmf
)

