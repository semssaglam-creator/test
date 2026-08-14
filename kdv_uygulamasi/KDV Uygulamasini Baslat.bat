@echo off
rem ===========================================================
rem  KDV Inceleme Calismasi - Windows baslatici
rem
rem  Cift tiklayin, yeter. Bilgisayara hicbir sey KURULMAZ.
rem  Python bulunamazsa, tasinabilir Python bu klasorun icindeki
rem  "python" alt klasorune bir kereligine indirilir; sisteme
rem  dokunmaz, PATH'e yazmaz, yonetici yetkisi istemez.
rem  Klasoru silmek uygulamayi tamamen kaldirir.
rem ===========================================================

setlocal
cd /d "%~dp0"
title KDV Inceleme Calismasi
rem Turkce karakterlerin her Windows dil ayarinda dogru islenmesi icin
set "PYTHONUTF8=1"

set "PYSURUM=3.12.8"
set "PYZIP=python-%PYSURUM%-embed-amd64.zip"
set "PYURL=https://www.python.org/ftp/python/%PYSURUM%/%PYZIP%"

rem --- 1) Daha once indirilmis tasinabilir Python var mi?
if exist "python\python.exe" goto tasinabilir

rem --- 2) Sistemde kurulu Python 3.9+ var mi? (varsa indirmeye gerek yok)
set "PY="
where py >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto surumDenetimi

where python >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY goto indir

:surumDenetimi
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if not errorlevel 1 goto calistir
set "PY="
goto indir

:tasinabilir
set "PY=python\python.exe"
goto calistir

rem --- 3) Yoksa tasinabilir Python'u bir kereligine indir
:indir
echo.
echo   Ilk calistirma: tasinabilir Python indiriliyor (yaklasik 11 MB).
echo   Bu yalnizca bir kez olur; bilgisayara hicbir sey kurulmaz.
echo   Bittiginde uygulama kendiliginden acilacak.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYZIP%' -UseBasicParsing; Expand-Archive -Path '%PYZIP%' -DestinationPath 'python' -Force; Remove-Item '%PYZIP%' -Force; exit 0 } catch { Write-Host ''; Write-Host ('   ' + $_.Exception.Message); exit 1 }"

if errorlevel 1 goto indirmeHatasi
if not exist "python\python.exe" goto indirmeHatasi
set "PY=python\python.exe"

:calistir
echo.
echo   KDV Inceleme Calismasi baslatiliyor...
echo   Adres birazdan asagida yazacak.
echo.

%PY% main.py
set "SONUC=%ERRORLEVEL%"

echo.
if "%SONUC%"=="0" goto kapandi
echo   Uygulama hata vererek kapandi (kod %SONUC%).
echo   Ayrinti icin ayni klasordeki
echo     KDV HATA - BUNU GONDERIN.txt
echo   dosyasina bakin; icerigini bildirmek sorunun bulunmasina yeter.
echo.
pause
exit /b %SONUC%

:kapandi
echo   Uygulama kapandi.
echo.
pause
goto son

:indirmeHatasi
echo.
echo   Tasinabilir Python indirilemedi.
echo   (Kurum agi indirmeyi engelliyor olabilir.)
echo.
echo   ELLE COZUM - iki adim:
echo     1^) Su dosyayi indirin:
echo        %PYURL%
echo     2^) Icindekileri bu klasorde "python" adli yeni bir klasore
echo        cikarin. Sonuc soyle gorunmeli:
echo        %~dp0python\python.exe
echo     Sonra bu dosyayi yeniden cift tiklayin.
echo.
echo   Alternatif: bilgisayara normal Python 3 kurarsaniz da calisir.
echo     https://www.python.org/downloads/windows/
echo     ^(kurulumda "Add python.exe to PATH" kutusunu isaretleyin^)
echo.
pause
exit /b 1

:son
endlocal
