@echo off
cd /d %~dp0
call .\homeymind\Scripts\activate.bat

if "%~1"=="" (
    echo No script specified, running main.py
    python main.py
) else (
    echo Running script: %~1
    python %~1
)

pause 