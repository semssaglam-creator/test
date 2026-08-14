@echo off
rem ===========================================================
rem  {{UYGULAMA_ADI}} - tani araci
rem
rem  Uygulama acilmiyorsa buna cift tiklayin. Sebebi arastirir ve
rem  ayni klasore bir rapor dosyasi birakir; o dosyayi gonderin.
rem ===========================================================

setlocal
cd /d "%~dp0"
title {{UYGULAMA_ADI}} - tani
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"

if exist "app\tani.py" goto klasorTamam
echo.
echo   Tani araci bulunamadi (app\tani.py yok).
echo   ZIP eksik acilmis olabilir: ZIP'e sag tiklayip
echo   "Tumunu ayikla" deyin ve cikan klasorden calistirin.
echo.
pause
exit /b 1
:klasorTamam

call "%~dp0_python_bul.bat"
if not defined PY (
    echo.
    echo   Python bulunamadigi icin tani calistirilamadi.
    echo   Bu ekranin fotografini gonderin: sebep budur.
    echo.
    pause
    exit /b 1
)

echo.
%PY% app\tani.py
echo.
pause
endlocal
