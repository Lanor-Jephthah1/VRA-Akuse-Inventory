@echo off
title VRA Akuse - MIS & Stores Inventory System
echo =====================================================================
echo   VOLTA RIVER AUTHORITY (VRA) - AKUSE / KPONG GENERATING STATION
echo   MIS ^& Multi-Departmental Inventory Management System
echo =====================================================================
echo.
echo Starting server at http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
