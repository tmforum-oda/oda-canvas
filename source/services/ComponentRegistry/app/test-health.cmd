@echo off
:START
curl http://localhost:8080/health
goto START
