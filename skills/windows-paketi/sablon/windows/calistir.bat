@echo off
rem ===========================================================
rem  {{UYGULAMA_ADI}} - Windows baslatici
rem
rem  Cift tiklayin, yeter. Bilgisayara hicbir sey KURULMAZ.
rem  Klasoru silmek uygulamayi tamamen kaldirir.
rem ===========================================================

setlocal
cd /d "%~dp0"
title {{UYGULAMA_ADI}}
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"

rem --- 0) Bu dosya uygulama klasorunun icinde mi?
rem Zip'in ICINDEN cift tiklanirsa Windows yalnizca bu dosyayi gecici bir
rem klasore cikarir; app\ ve main.py yanina gelmez, pencere aninda kapanir.
if exist "main.py" goto klasorTamam
echo.
echo   Bu baslatici, uygulama klasorunun icinde degil.
echo   Buyuk olasilikla ZIP dosyasinin icinden calistirdiniz.
echo.
echo   COZUM: Zip dosyasina sag tiklayin ^> "Tumunu ayikla" deyin,
echo   sonra CIKAN KLASORUN icindeki bu dosyaya cift tiklayin.
echo.
pause
exit /b 1
:klasorTamam

rem --- 1) Python
call "%~dp0_python_bul.bat"
if not defined PY (
    pause
    exit /b 1
)

rem --- 2) Calistir
echo.
echo   {{UYGULAMA_ADI}} baslatiliyor...
echo   Adres birazdan asagida yazacak.
echo.

%PY% main.py
set "SONUC=%ERRORLEVEL%"

echo.
if "%SONUC%"=="0" goto kapandi
echo   Uygulama hata vererek kapandi (kod %SONUC%).
echo.
echo   Sebebini ogrenmek icin ayni klasordeki
echo     tani.bat
echo   dosyasina cift tiklayin; olusan rapor dosyasini gonderin.
echo.
pause
exit /b %SONUC%

:kapandi
echo   Uygulama kapandi.
echo.
pause
endlocal
