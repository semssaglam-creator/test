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

rem --- 1) Acilis kaydi
rem Uygulama acilmadiginda ekranda ne yazdigini kullaniciya aktarmak bir tur
rem alip veriyor ve cogu zaman eksik geliyor. Baslatici kendi adimlarini bir
rem dosyaya yaziyor; kullanici tek dosyayi oldugu gibi gonderiyor.
rem Yazma HER ZAMAN hatasi yutularak yapilir (2>nul): salt okunur bir
rem klasorde bile acilis bundan dolayi durmamali.
set "KAYIT=%~dp0ACILIS KAYDI.txt"
>"%KAYIT%" echo {{UYGULAMA_ADI}} - acilis kaydi 2>nul
>>"%KAYIT%" echo Tarih  : %DATE% %TIME% 2>nul
>>"%KAYIT%" echo Klasor : %~dp0 2>nul
>>"%KAYIT%" echo. 2>nul

rem --- 2) Python
>>"%KAYIT%" echo [1] Python araniyor... 2>nul
call "%~dp0_python_bul.bat"
if not defined PYEXE (
    >>"%KAYIT%" echo     BULUNAMADI - yukaridaki aciklamaya bakin. 2>nul
    echo.
    echo   Bu ekranda yazanlar su dosyaya da kaydedildi:
    echo     ACILIS KAYDI.txt
    echo.
    pause
    exit /b 1
)
>>"%KAYIT%" echo     Bulundu: %PYEXE% %PYARG% 2>nul

rem --- 3) Calistir
>>"%KAYIT%" echo [2] Uygulama baslatiliyor... 2>nul
echo.
echo   {{UYGULAMA_ADI}} baslatiliyor...
echo   Adres birazdan asagida yazacak.
echo.

"%PYEXE%" %PYARG% main.py
set "SONUC=%ERRORLEVEL%"
>>"%KAYIT%" echo [3] Uygulama kapandi. Cikis kodu: %SONUC% 2>nul

echo.
if "%SONUC%"=="0" goto kapandi
echo   Uygulama hata vererek kapandi (kod %SONUC%).
echo.
echo   Ayni klasorde su iki dosya olustu; ikisini de gonderin:
echo     ACILIS KAYDI.txt
echo     KDV HATA - BUNU GONDERIN.txt  (varsa)
echo.
echo   Sebebi arastirmak icin tani.bat dosyasina da cift tiklayabilirsiniz.
echo.
pause
exit /b %SONUC%

:kapandi
echo   Uygulama kapandi.
echo.
pause
endlocal
