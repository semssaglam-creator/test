@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -3 ocr_kur.py) || (python ocr_kur.py)
