@echo off
cd /d %~dp0
call homeymind\Scripts\activate.bat
python main.py
pause
