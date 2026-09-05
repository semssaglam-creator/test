@echo off
rem ===========================================================
rem  Ortak alt yordam: calisacak Python'u bulur.
rem
rem  Sonuc IKI degiskene yazilir:
rem    PYEXE - calistirilacak dosya ya da komut  (tirnak icinde kullanin)
rem    PYARG - varsa ek argumanlar               (tirnaksiz kullanin)
rem
rem  Cagirma bicimi HER ZAMAN soyle olmali:
rem      "%PYEXE%" %PYARG% main.py
rem
rem  Neden ikiye bolundu: PYEXE bir yol olabilir ve uygulama klasorunun
rem  yolunda BOSLUK bulunabilir ("...\Desktop\KDV Inceleme Calismasi\").
rem  Tirnaksiz yazilirsa cmd yolu ilk boslukta keser ve
rem  "'C:\Users\...\Desktop\KDV' is not recognized" hatasi verir. Ama tek
rem  degiskene "py -3" konulup tirnaklanirsa bu kez "py -3" adinda bir
rem  dosya aranir. Ikisi ayrilinca her iki durum da dogru calisir.
rem
rem  Sira: 1) klasordeki tasinabilir Python  2) sistemde kurulu 3.9+
rem        3) tasinabilir Python'u bir kereligine indir
rem  Basarisizsa PYEXE bos kalir ve ERRORLEVEL 1 doner.
rem ===========================================================

set "PYEXE="
set "PYARG="
set "PYSURUM=3.12.8"
set "PYMIMARI={{MIMARI}}"
set "PYZIP=python-%PYSURUM%-embed-%PYMIMARI%.zip"
set "PYURL=https://www.python.org/ftp/python/%PYSURUM%/%PYZIP%"

rem --- 1) Daha once indirilmis / pakete konmus tasinabilir Python
if exist "%~dp0python\python.exe" (
    set "PYEXE=%~dp0python\python.exe"
    exit /b 0
)

rem --- 2) Sistemde kurulu Python 3.9+ var mi?
where py >nul 2>&1
if not errorlevel 1 (
    set "PYEXE=py"
    set "PYARG=-3"
    goto surumDenetimi
)
where python >nul 2>&1
if not errorlevel 1 (
    set "PYEXE=python"
    goto surumDenetimi
)
goto indir

:surumDenetimi
rem Microsoft Store'un "python.exe" saplamasi da bu denetimde elenir:
rem magazayi acar, kod calistirmaz, sifirdan farkli deger doner.
"%PYEXE%" %PYARG% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if not errorlevel 1 exit /b 0
set "PYEXE="
set "PYARG="

:indir
echo.
echo   Ilk calistirma: tasinabilir Python indiriliyor (yaklasik 11 MB).
echo   Bu yalnizca bir kez olur; bilgisayara hicbir sey KURULMAZ.
echo.

pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYZIP%' -UseBasicParsing; Expand-Archive -Path '%PYZIP%' -DestinationPath 'python' -Force; Remove-Item '%PYZIP%' -Force; exit 0 } catch { Write-Host ''; Write-Host ('   ' + $_.Exception.Message); exit 1 }"
set "INDIRME=%ERRORLEVEL%"
popd

if not "%INDIRME%"=="0" goto indirmeHatasi
if not exist "%~dp0python\python.exe" goto indirmeHatasi

rem Gomulu Python kendi klasorunun disini gormez; uygulama klasorlerini
rem ._pth dosyasina yazmazsak "ModuleNotFoundError: app" alinir.
call :pthYaz

set "PYEXE=%~dp0python\python.exe"
exit /b 0

:pthYaz
rem findstr /c: LITERAL metin arar; ters egik cizgi kacis karakteri DEGILDIR.
rem "..\\lib" yazilirsa iki ters egik cizgi aranir, hicbir zaman eslesmez ve
rem satirlar her calistirmada yeniden eklenir.
for %%D in ("%~dp0python\python*._pth") do (
    findstr /c:"..\lib" "%%~D" >nul 2>&1 || (
        echo.>>"%%~D"
        echo ..>>"%%~D"
        echo ..\lib>>"%%~D"
        echo ..\lib_ek>>"%%~D"
        echo import site>>"%%~D"
    )
)
exit /b 0

:indirmeHatasi
echo.
echo   Tasinabilir Python indirilemedi.
echo   ^(Kurum agi indirmeyi engelliyor olabilir.^)
echo.
echo   ELLE COZUM - iki adim:
echo     1^) Su dosyayi baska bir bilgisayardan indirin:
echo        %PYURL%
echo     2^) Icindekileri bu klasorde "python" adli yeni bir klasore
echo        cikarin. Sonuc soyle gorunmeli:
echo        %~dp0python\python.exe
echo.
echo   Alternatif: bilgisayara normal Python 3 kurarsaniz da calisir.
echo     https://www.python.org/downloads/windows/
echo     ^(kurulumda "Add python.exe to PATH" kutusunu isaretleyin^)
echo.
set "PYEXE="
set "PYARG="
exit /b 1
